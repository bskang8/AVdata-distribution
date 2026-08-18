#!/usr/bin/env python
"""
G-Q1 / S0 — 모델 유래 신호 주입 + 발산 판정 완성.

설계: r1_gates/S0_MODEL_SIGNALS_DESIGN.md (옵션 A). s0_features.py의 model-free 신호에
모델 유래 신호를 붙여 per-clip/cluster 발산 행렬을 완성한다. **무재학습**(stage1 동결):
  - uncertainty     : planning_score(command행) mode-엔트로피        [results.pkl, 오프라인]
  - scaling_gain    : final_planning vs GT per-clip L2 tail-error     [results.pkl+GT, 오프라인]
  - recoverability  : cluster별 1-step reducible loss(stage2 헤드 1스텝) [--recov, 모델/GPU]

정렬: results.pkl(val 6019) ↔ val infos 인덱스 정렬. s0_features도 **val**로 돌려 토큰 일치.
재사용: 발산 계산은 s0_features.{spearman,topk_jaccard,divergence,_rank} 그대로 import.

용법:
  # 1) s0_features를 val로 (클러스터·model-free 신호·토큰)
  python s0_features.py --infos data/infos/nuscenes_infos_val.pkl --outdir output_val
  # 2) 오프라인 모델신호 + 발산(권장 먼저)
  python s0_model_signals.py --results .../results.pkl --infos .../nuscenes_infos_val.pkl \
         --s0dir output_val
  # 3) recoverability 추가(모델 필요, GPU1)
  CUDA_VISIBLE_DEVICES=1 python s0_model_signals.py ... --recov \
         --config projects/configs/sparsedrive_small_stage2.py --ckpt ckpt/sparsedrive_stage2.pth
"""
import os, sys, json, argparse
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from s0_features import spearman, topk_jaccard, divergence, _rank  # 재사용(재구현 금지)

N_MODE_CMD = 6  # planning_score shape (3 command, 6 mode)


# ----------------------------- 오프라인 신호 -----------------------------
def _softmax(x):
    x = np.asarray(x, np.float64)
    x = x - x.max()
    e = np.exp(x)
    return e / (e.sum() + 1e-12)


def mode_entropy(scores):
    """command행 mode 점수(6,) → 정규화 엔트로피 ∈[0,1]. 높을수록 불확실(모드 평평)."""
    p = _softmax(scores)
    H = -np.sum(p * np.log(p + 1e-12))
    return float(H / np.log(len(p)))  # /log K = [0,1] 정규화


def gt_positions(info):
    """gt_ego_fut_trajs(6,2) step offset → 누적 위치(6,2). planning_eval와 동일(cumsum)."""
    off = np.asarray(info["gt_ego_fut_trajs"], np.float64)
    return np.cumsum(off, axis=0)


def gt_mask(info):
    m = info.get("gt_ego_fut_masks", None)
    if m is None:
        return np.ones(6, bool)
    return np.asarray(m, bool).reshape(-1)[:6]


def offline_signals(results, infos):
    """results[i] ↔ infos[i] 정렬. per-clip uncertainty·scaling_gain·valid.
    ⚠️ results.pkl 순서 = eval dataloader 순서 = **timestamp 정렬**(nuscenes_3d_dataset.py:282,
    load_interval=1). raw infos 순서로 짝지으면 스크램블 → L2가 5~6m로 폭주. 반드시 timestamp 정렬."""
    infos = sorted(infos, key=lambda e: e["timestamp"])  # dataloader 순서에 정렬
    n = len(results)
    assert n == len(infos), f"정렬 불일치 results={n} infos={len(infos)}"
    unc = np.full(n, np.nan)
    scg = np.full(n, np.nan)
    valid = np.zeros(n, bool)
    toks = np.array([inf["token"] for inf in infos])
    for i, (res, inf) in enumerate(zip(results, infos)):
        e = res["img_bbox"]
        cmd = int(np.argmax(inf["gt_ego_fut_cmd"]))
        ps = np.asarray(e["planning_score"], np.float64)  # (3,6)
        unc[i] = mode_entropy(ps[cmd])
        # scaling_gain = per-clip L2 tail-error (mask 완전할 때만; planning_eval 규칙)
        mask = gt_mask(inf)
        if not mask.all():
            continue  # 불완전 GT → eval에서 스킵. valid=False
        pred = np.asarray(e["final_planning"], np.float64)[:6, :2]  # 누적 위치
        gt = gt_positions(inf)[:6, :2]
        l2 = np.linalg.norm(pred - gt, axis=1)  # (6,)
        scg[i] = float(l2.mean())
        valid[i] = True
    return dict(uncertainty=unc, scaling_gain=scg, valid=valid, tokens=toks)


# ----------------------------- 정렬/병합 -----------------------------
def load_s0(s0dir):
    d = np.load(os.path.join(s0dir, "gq1_s0_perclip.npz"), allow_pickle=True)
    return dict(tokens=d["tokens"].astype(str), subdef=d["subdef"].astype(int),
               diversity=d["diversity"], coverage_redundancy=d["coverage_redundancy"])


def align(model_sig, s0):
    """s0(model-free)와 model_sig(모델유래)를 token으로 정렬. 공통 token만."""
    idx_of = {t: i for i, t in enumerate(model_sig["tokens"])}
    keep_s0, keep_m = [], []
    for j, t in enumerate(s0["tokens"]):
        i = idx_of.get(t)
        if i is not None:
            keep_s0.append(j); keep_m.append(i)
    keep_s0 = np.array(keep_s0); keep_m = np.array(keep_m)
    out = {
        "tokens": s0["tokens"][keep_s0],
        "subdef": s0["subdef"][keep_s0],
        "diversity": s0["diversity"][keep_s0],
        "coverage_redundancy": s0["coverage_redundancy"][keep_s0],
        "uncertainty": model_sig["uncertainty"][keep_m],
        "scaling_gain": model_sig["scaling_gain"][keep_m],
        "valid": model_sig["valid"][keep_m],
    }
    return out


# ----------------------------- 발산·판정 -----------------------------
def s0_divergence(merged, recov_cluster=None):
    """per-clip 오프라인 신호 divergence + (있으면) cluster-level(회복가치 포함)."""
    v = merged["valid"]  # scaling_gain 정의된 clip만(uncertainty·diversity는 전체지만 공통 부분집합 사용)
    perclip = {
        "uncertainty": merged["uncertainty"][v],
        "scaling_gain": merged["scaling_gain"][v],
        "diversity": merged["diversity"][v],
        "coverage_redundancy": merged["coverage_redundancy"][v],
    }
    result = {"n_valid": int(v.sum()), "per_clip": divergence(perclip)}

    if recov_cluster is not None:
        # 클러스터 평균으로 집계 → recoverability와 같은 granularity에서 상관
        cids = sorted(recov_cluster.keys())
        agg = {"recoverability": np.array([recov_cluster[c] for c in cids])}
        for name in ["uncertainty", "scaling_gain", "diversity", "coverage_redundancy"]:
            arr = merged[name]; sd = merged["subdef"]
            agg[name] = np.array([np.nanmean(arr[(sd == int(c)) & v]) for c in cids])
        result["cluster_level"] = {"cluster_ids": cids, "divergence": divergence(agg)}
    return result


def verdict(div):
    """사전등록 조기 컷(GQ1 §3-S0/§4). recoverability 있으면 그것 기준, 없으면 오프라인 신호 요약."""
    if "cluster_level" not in div:
        return {"stage": "S0-offline", "note": "recoverability 미포함(--recov 필요). 오프라인 신호 발산만 보고."}
    sp = div["cluster_level"]["divergence"]["spearman"]
    r_unc = abs(sp.get("recoverability|uncertainty", 0.0))
    r_div = abs(sp.get("recoverability|diversity", 0.0))
    mx = max(r_unc, r_div)
    if mx >= 0.7:
        v = "RED(scoop 경보)"
    elif mx <= 0.5:
        v = "DIVERGE(→S1 진행 정당)"
    else:
        v = "AMBIGUOUS(→S1 확인)"
    return {"stage": "S0", "max_abs_rho_recov_vs_{unc,div}": round(mx, 4),
            "rho_recov_uncertainty": round(sp.get("recoverability|uncertainty", 0.0), 4),
            "rho_recov_diversity": round(sp.get("recoverability|diversity", 0.0), 4),
            "verdict": v}


# ----------------------------- recoverability (모델, --recov) -----------------------------
def recoverability_1step(config, ckpt, infos, subdef, valid, gpu=0, lr=1e-4, max_per_cluster=32):
    """cluster별 1-step reducible loss = planning loss 감소량(stage2 헤드 1스텝, stage1 동결).
    별도 검증 필요(모델 forward_train 경로). 반환 {cluster_id: Δloss}."""
    import torch
    from mmcv import Config
    from mmcv.runner import load_checkpoint
    from mmcv.parallel import collate, MMDataParallel
    from mmdet.datasets import build_dataset
    from mmdet.models import build_detector  # SparseDrive는 mmdet 레지스트리(test.py와 동일)
    from copy import deepcopy

    cfg = Config.fromfile(config)
    if getattr(cfg, "plugin", False):
        import importlib
        sys.path.insert(0, os.getcwd())
        importlib.import_module(cfg.plugin_dir.replace("/", ".").rstrip("."))
    # train 파이프라인 데이터셋(GT 포함) — val ann_file에 train 파이프라인
    dcfg = deepcopy(cfg.data.train)
    dcfg["ann_file"] = cfg.data.val["ann_file"]
    ds = build_dataset(dcfg)
    torch.cuda.set_device(gpu)
    model = build_detector(cfg.model, train_cfg=cfg.get("train_cfg"), test_cfg=cfg.get("test_cfg"))
    load_checkpoint(model, ckpt, map_location="cpu")
    model = model.cuda(gpu).train()
    # stage1 동결: planning/motion 헤드만 학습
    plan_params = []
    for name, p in model.named_parameters():
        train_it = ("motion" in name) or ("planning" in name) or ("plan" in name)
        p.requires_grad_(train_it)
        if train_it:
            plan_params.append(p)
    assert plan_params, "planning-head 파라미터를 못 찾음 — 이름 규칙 확인"
    mmdp = MMDataParallel(model, device_ids=[gpu])  # DataContainer scatter를 위임(정식 경로)
    opt = torch.optim.SGD(plan_params, lr=lr)

    def plan_loss(ids):
        """train_step으로 forward → log_vars의 planning 손실 합(스텝 없음)."""
        batch = collate([ds[i] for i in ids], samples_per_gpu=len(ids))
        out = mmdp.train_step(batch, opt)
        return float(sum(v for k, v in out["log_vars"].items() if "plan" in k)), out["loss"]

    def one_step(ids):
        batch = collate([ds[i] for i in ids], samples_per_gpu=len(ids))
        out = mmdp.train_step(batch, opt)
        opt.zero_grad(); out["loss"].backward(); opt.step()

    # ds 순서 = val infos 순서(index 정렬 가정) → subdef 인덱스 그대로 사용
    recov = {}
    B = 4  # per-step 배치(메모리 안전)
    for c in sorted(set(int(x) for x in subdef if x >= 0)):
        ids = list(np.where((subdef == c) & valid)[0][:max_per_cluster])
        if len(ids) < B:
            continue
        with torch.no_grad():
            l_before, _ = plan_loss(ids[:B])
        one_step(ids[:B])
        with torch.no_grad():
            l_after, _ = plan_loss(ids[:B])
        recov[str(c)] = l_before - l_after  # 감소량 = 회복가치 프록시(클수록 회복여지 큼)
    return recov


# ----------------------------- main -----------------------------
def run(results_path, infos_path, s0dir, outdir=None, recov=False, config=None, ckpt=None, gpu=0):
    import mmcv
    outdir = outdir or s0dir
    results = mmcv.load(results_path)
    infos = mmcv.load(infos_path)["infos"]
    msig = offline_signals(results, infos)
    s0 = load_s0(s0dir)
    merged = align(msig, s0)

    recov_cluster = None
    if recov:
        assert config and ckpt, "--recov엔 --config/--ckpt 필요"
        recov_cluster = recoverability_1step(config, ckpt, infos, merged["subdef"], merged["valid"], gpu=gpu)

    div = s0_divergence(merged, recov_cluster)
    vd = verdict(div)
    out = {"n_clips": len(results), "n_valid": div["n_valid"],
           "signals": ["uncertainty", "scaling_gain", "diversity", "coverage_redundancy"]
                      + (["recoverability"] if recov_cluster else []),
           "divergence": div, "verdict": vd,
           "preregistered": {"uncertainty": "mode-entropy(정규화)", "scaling_gain": "per-clip L2 tail",
                             "recoverability": "cluster 1-step reducible loss" if recov_cluster else "deferred(--recov)"}}
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "gq1_s0_model.json"), "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    np.savez(os.path.join(outdir, "gq1_s0_model_perclip.npz"),
             tokens=merged["tokens"], uncertainty=merged["uncertainty"],
             scaling_gain=merged["scaling_gain"], valid=merged["valid"], subdef=merged["subdef"])
    return out


def demo():
    """ponytail 셀프체크: 엔트로피 경계·L2·정렬 조인·발산 불변식(모델/GPU 무의존)."""
    # 엔트로피: 균등 모드=최대(≈1), 단일 지배=최소(≈0)
    assert abs(mode_entropy(np.ones(6)) - 1.0) < 1e-6, "균등 엔트로피!=1"
    assert mode_entropy(np.array([10., 0, 0, 0, 0, 0])) < 0.2, "단일지배 엔트로피 큼"
    # scaling_gain: 완벽예측 L2=0
    inf = {"gt_ego_fut_trajs": np.tile([0.0, 1.0], (6, 1)), "gt_ego_fut_cmd": np.eye(3)[2],
           "gt_ego_fut_masks": np.ones(6), "token": "t0", "timestamp": 0}
    gt = gt_positions(inf)
    res = [{"img_bbox": {"planning_score": np.ones((3, 6)), "final_planning": gt}}]
    ms = offline_signals(res, [inf])
    assert ms["valid"][0] and abs(ms["scaling_gain"][0]) < 1e-9, "완벽예측 scaling_gain!=0"
    assert abs(ms["uncertainty"][0] - 1.0) < 1e-6
    # 정렬 조인: token 교집합만
    msig = {"tokens": np.array(["a", "b", "c"]), "uncertainty": np.array([1., 2, 3]),
            "scaling_gain": np.array([.1, .2, .3]), "valid": np.array([True, True, True])}
    s0 = {"tokens": np.array(["b", "c", "d"]), "subdef": np.array([0, 1, 2]),
          "diversity": np.array([9., 8, 7]), "coverage_redundancy": np.array([1., 1, 1])}
    m = align(msig, s0)
    assert list(m["tokens"]) == ["b", "c"], "token 조인 오류"
    assert list(m["uncertainty"]) == [2., 3.], "조인 후 값 정렬 오류"
    # 발산 불변식
    d = s0_divergence({"valid": np.ones(4, bool), "uncertainty": np.array([1., 2, 3, 4]),
                       "scaling_gain": np.array([1., 2, 3, 4]), "diversity": np.array([4., 3, 2, 1]),
                       "coverage_redundancy": np.array([1., 1, 2, 2]), "subdef": np.array([0, 0, 1, 1])})
    sp = d["per_clip"]["spearman"]
    assert abs(sp["uncertainty|scaling_gain"] - 1.0) < 1e-6, "동일신호 ρ!=1"
    assert abs(sp["uncertainty|diversity"] + 1.0) < 1e-6, "역신호 ρ!=-1"
    print("demo OK — entropy/L2/align/divergence 불변식 통과")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="work_dirs/sparsedrive_small_stage2/results.pkl")
    ap.add_argument("--infos", default="data/infos/nuscenes_infos_val.pkl")
    ap.add_argument("--s0dir", default=os.path.join(os.path.dirname(__file__), "output_val"))
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--recov", action="store_true")
    ap.add_argument("--config", default=None)
    ap.add_argument("--ckpt", default=None)
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--selfcheck", action="store_true")
    a = ap.parse_args()
    if a.selfcheck:
        demo()
    else:
        out = run(a.results, a.infos, a.s0dir, a.outdir, a.recov, a.config, a.ckpt, a.gpu)
        print("verdict:", json.dumps(out["verdict"], ensure_ascii=False))
        print("per_clip spearman:", out["divergence"]["per_clip"]["spearman"])
