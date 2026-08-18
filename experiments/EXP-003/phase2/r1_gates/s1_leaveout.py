#!/usr/bin/env python
"""
G-Q1 / S1 — 클러스터 오라클 인과 회복가치(leave-out) 하네스 (offline 부분).

설계: GQ1_S1_DESIGN.md, GQ1_design.md §3-S1. S0(발산 스크리닝)를 오라클로 확증한다.
오라클 회복가치 c = ΔTail_c = Tail_c(train-minus-c 재학습) − Tail_c(full 재학습),
  stage2-only(stage1 동결), Tail_c = c의 **val eval 슬라이스** 평균 planning L2.
발산 확증: 오라클 vs {uncertainty, diversity, scaling_gain} Spearman ρ + top-⌈n/3⌉ Jaccard.

이 파일 = GPU 불필요 offline 3단:
  prep   : train 클러스터 centroid 재현 + val→train centroid 투영(정렬 버그 방지) + leave-out pkl 생성
  tail   : 한 arm의 results.pkl → per-cluster val-슬라이스 tail(mean L2)
  oracle : baseline+leaveout tail 취합 → ΔTail → S0 싼신호와 발산 행렬 + 사전등록 판정

⚠️ 정렬 함정(핵심): s0_features.run()은 train/val을 **독립 KMeans**로 클러스터링한다
   (Z[cand] 재적합·random_state=0·데이터셋별 표준화) → train c번 ≠ val c번.
   따라서 val eval 슬라이스는 반드시 **train centroid에 투영**해 정의한다(아래 project_val).

학습/eval은 s1_run.sh (--launcher none, setsid+PYTHONUNBUFFERED).
"""
import os, sys, json, argparse
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from s0_features import extract_features, FEATURE_KEYS, rule_tags   # 재사용(재구현 금지)
from s0_model_signals import offline_signals, divergence            # per-clip L2 tail·발산 재사용

N_SUB = 20


# ---------------------- train 클러스터 재현 + val 투영 ----------------------
def _train_space(train_npz):
    """저장된 train Xraw(nan-fill 완료)에서 표준화(mu,sd)+centroid 재현.
    s0_features.build_matrix/run과 동일: mu/sd는 전 train, KMeans는 candidate에만(random_state=0)."""
    from sklearn.cluster import KMeans
    d = np.load(train_npz, allow_pickle=True)
    Xraw = d["features"].astype(np.float64)            # (28130,12) nan-fill 완료
    sub = d["subdef"].astype(int)
    mu, sd = Xraw.mean(0), Xraw.std(0) + 1e-9
    Z = (Xraw - mu) / sd
    cand = sub >= 0
    km = KMeans(n_clusters=N_SUB, random_state=0, n_init=10).fit(Z[cand])
    # 재현 검증: 재적합 라벨이 저장 subdef와 일치해야 centroid가 같은 클러스터를 가리킴
    repro = -np.ones(len(sub), int); repro[cand] = km.labels_
    agree = (repro[cand] == sub[cand]).mean()
    return dict(mu=mu, sd=sd, centroids=km.cluster_centers_, repro_agree=float(agree))


def project_val(val_infos, train_npz, thr):
    """val clip을 train 클러스터에 투영. candidate(train 임계 tail)만, train centroid 최근접.
    반환 val_subdef(train-aligned, -1=비후보/원거리 없음)."""
    sp = _train_space(train_npz)
    mu, sd, cen = sp["mu"], sp["sd"], sp["centroids"]
    fds = [extract_features(e) for e in val_infos]
    X = np.array([[fd[k] for k in FEATURE_KEYS] for fd in fds], np.float64)
    for j in range(X.shape[1]):                        # NaN→train 기준이 아닌 열 median(build_matrix와 동일 관용)
        m = np.isnan(X[:, j])
        if m.any():
            X[m, j] = np.nanmedian(X[:, j])
    Z = (X - mu) / sd                                  # ⚠️ train mu/sd로 표준화(투영 일관성)
    val_sub = -np.ones(len(fds), int)
    for i, fd in enumerate(fds):
        if not rule_tags(fd, thr):                     # train 규칙으로 candidacy 재현
            continue
        val_sub[i] = int(np.argmin(((Z[i] - cen) ** 2).sum(1)))
    toks = np.array([fd["_token"] for fd in fds])
    return val_sub, toks, sp["repro_agree"]


# ---------------------- leave-out pkl ----------------------
def make_leaveout(train_infos, train_sub, cluster, out_pkl, metadata):
    """train에서 cluster c clip 제거한 infos pkl 작성. 반환 (kept, removed).
    ⚠️ 원본 metadata(특히 'version')를 보존해야 함 — dataset이 metadata['version'] 읽음(load_annotations)."""
    import mmcv
    keep = [inf for inf, c in zip(train_infos, train_sub) if c != cluster]
    os.makedirs(os.path.dirname(out_pkl), exist_ok=True)
    meta = dict(metadata or {}); meta["leaveout_cluster"] = int(cluster)  # version 등 원본 유지 + 표식
    assert "version" in meta, "원본 metadata에 version 없음 — dataset load_annotations 크래시함"
    mmcv.dump(dict(infos=keep, metadata=meta), out_pkl)
    return len(keep), len(train_infos) - len(keep)


# ---------------------- per-cluster tail ----------------------
def cluster_tail(results, val_infos, val_sub):
    """results.pkl(한 arm) → per-cluster val-슬라이스 tail. Tail_c = mean per-clip planning L2.
    per-clip L2 = offline_signals의 scaling_gain(planning_eval 마스킹 준수, timestamp 정렬).
    ⚠️ offline_signals는 timestamp 정렬 순서로 반환 → val_sub(raw infos 순서)와 **token으로 조인**."""
    ms = offline_signals(results, val_infos)           # tokens/scaling_gain/valid = timestamp 정렬 순서
    l2_by_tok = {t: (l2, v) for t, l2, v in zip(ms["tokens"], ms["scaling_gain"], ms["valid"])}
    raw_tok = [inf["token"] for inf in val_infos]       # val_sub[j] ↔ raw_tok[j]
    tail = {}
    for c in sorted(set(int(x) for x in val_sub if x >= 0)):
        vals = [l2_by_tok[raw_tok[j]][0] for j in np.where(val_sub == c)[0]
                if raw_tok[j] in l2_by_tok and l2_by_tok[raw_tok[j]][1]]
        if not vals:
            continue
        tail[str(c)] = dict(mean_l2=float(np.nanmean(vals)), n=len(vals))
    return tail
    # ponytail: tail=mean L2만. collision-rate per-slice는 후속(per-clip collision 미계산). upgrade시 offline_signals에 col 추가.


# ---------------------- oracle 발산·판정 ----------------------
def oracle_divergence(baseline_tail, leaveout_tails, s0_model_npz, val_sub, val_sub_tokens):
    """ΔTail_c = Tail_c(leaveout_c) − Tail_c(baseline) → S0 싼신호와 cluster-level 발산.
    싼신호(uncertainty·scaling_gain·diversity)는 같은 val 슬라이스(train-aligned)로 집계."""
    dm = np.load(s0_model_npz, allow_pickle=True)       # uncertainty·scaling_gain·valid (raw val 순서)
    unc, scg, mvalid = dm["uncertainty"], dm["scaling_gain"], dm["valid"]
    # diversity: output_val model-free npz(raw val 순서 동일)
    dvpath = os.path.join(os.path.dirname(s0_model_npz), "gq1_s0_perclip.npz")
    dv = np.load(dvpath, allow_pickle=True)
    div_signal = dv["diversity"]
    # 인덱스 정렬 가정(모두 raw val 순서) 방어: token 일치 확인
    assert list(dm["tokens"].astype(str)) == list(dv["tokens"].astype(str)) == list(val_sub_tokens), \
        "npz 순서 불일치 — s0_model/diversity/val_sub이 같은 raw val 순서여야 함(token-join 필요시 재작성)"

    cids = sorted(leaveout_tails.keys(), key=int)
    recov, agg = [], {"uncertainty": [], "scaling_gain": [], "diversity": []}
    kept = []
    for c in cids:
        if c not in baseline_tail or c not in leaveout_tails:
            continue
        recov.append(leaveout_tails[c]["mean_l2"] - baseline_tail[c]["mean_l2"])
        sel = (val_sub == int(c)) & mvalid
        agg["uncertainty"].append(float(np.nanmean(unc[sel])))
        agg["scaling_gain"].append(float(np.nanmean(scg[sel])))
        agg["diversity"].append(float(np.nanmean(div_signal[(val_sub == int(c))])))
        kept.append(c)
    sig = {"recoverability": np.array(recov), "uncertainty": np.array(agg["uncertainty"]),
           "scaling_gain": np.array(agg["scaling_gain"]), "diversity": np.array(agg["diversity"])}
    div = divergence(sig)
    sp = div["spearman"]; jc = div["topk_jaccard"]
    mx_rho = max(abs(sp["recoverability|uncertainty"]), abs(sp["recoverability|diversity"]))
    mx_jac = max(jc["recoverability|uncertainty"], jc["recoverability|diversity"], jc["recoverability|scaling_gain"])
    if mx_rho >= 0.7:
        v = "FAIL(scoop): recov≈uncertainty/diversity"
    elif mx_rho <= 0.5 and mx_jac <= 0.5:
        v = "DIVERGE 확증(→S2 우위 검증 진입)"
    else:
        v = "AMBIGUOUS"
    return {"cluster_ids": kept, "n": len(kept), "recoverability": recov,
            "divergence": div, "verdict": v,
            "max_abs_rho_recov_vs_{unc,div}": round(mx_rho, 4),
            "max_jaccard_recov_vs_cheap": round(mx_jac, 4)}


# ---------------------- CLI ----------------------
def cmd_prep(a):
    import mmcv
    train_data = mmcv.load(a.train_infos)
    train_infos = train_data["infos"]
    train_meta = train_data.get("metadata", {})       # 원본 metadata(version) 보존용
    train_sub = np.load(a.train_npz, allow_pickle=True)["subdef"].astype(int)
    assert len(train_infos) == len(train_sub), "train infos↔subdef 정렬 불일치"
    val_infos = mmcv.load(a.val_infos)["infos"]
    thr = json.load(open(a.s0json))["rule_thresholds"]
    val_sub, toks, agree = project_val(val_infos, a.train_npz, thr)
    np.savez(os.path.join(a.outdir, "val_subdef_trainaligned.npz"), subdef=val_sub, tokens=toks)
    clusters = a.clusters or sorted(set(int(x) for x in train_sub if x >= 0))
    made = {}
    for c in clusters:
        pkl = os.path.join(a.leaveout_dir, f"train_minus_c{c}.pkl")
        kept, removed = make_leaveout(train_infos, train_sub, c, pkl, train_meta)
        made[str(c)] = dict(pkl=pkl, kept=kept, removed=removed)
    import collections
    vc = collections.Counter(val_sub[val_sub >= 0].tolist())
    print(f"[prep] KMeans centroid 재현 일치율={agree:.4f} (≈1이어야 centroid 정합)")
    print(f"[prep] val 투영 슬라이스 크기(train-aligned): "
          f"{ {int(k): vc[k] for k in sorted(vc)} }")
    print(f"[prep] leave-out pkl {len(made)}개 → {a.leaveout_dir}")
    json.dump({"repro_agree": agree, "val_slice_sizes": {int(k): vc[k] for k in sorted(vc)},
               "leaveouts": made}, open(os.path.join(a.outdir, "s1_prep.json"), "w"), indent=2)


def cmd_tail(a):
    import mmcv
    results = mmcv.load(a.results)
    val_infos = mmcv.load(a.val_infos)["infos"]
    val_sub = np.load(a.val_sub)["subdef"].astype(int)
    tail = cluster_tail(results, val_infos, val_sub)
    out = os.path.join(a.outdir, f"tail_{a.arm}.json")
    json.dump({"arm": a.arm, "tail": tail}, open(out, "w"), indent=2)
    print(f"[tail] arm={a.arm}: {len(tail)} clusters → {out}")
    print({k: round(v['mean_l2'], 4) for k, v in sorted(tail.items(), key=lambda x: int(x[0]))})


def cmd_oracle(a):
    baseline = json.load(open(a.baseline))["tail"]
    leaveout = {}
    for f in a.leaveout_tails:
        d = json.load(open(f))
        c = str(d["arm"]).replace("c", "").replace("leaveout_", "")
        # arm 이름 규칙: leaveout_c<K> → cluster K의 자기 슬라이스 tail만 사용
        cl = "".join(ch for ch in d["arm"] if ch.isdigit())
        if cl in d["tail"]:
            leaveout[cl] = d["tail"][cl]
    vs = np.load(a.val_sub, allow_pickle=True)
    val_sub = vs["subdef"].astype(int)
    res = oracle_divergence(baseline, leaveout, a.s0_model_npz, val_sub, list(vs["tokens"].astype(str)))
    json.dump(res, open(os.path.join(a.outdir, "gq1_s1.json"), "w"), indent=2, ensure_ascii=False)
    print("[oracle] verdict:", res["verdict"])
    print("  recov vs {unc,div} max|ρ|=", res["max_abs_rho_recov_vs_{unc,div}"],
          " max Jaccard=", res["max_jaccard_recov_vs_cheap"])
    print("  spearman:", res["divergence"]["spearman"])


def demo():
    """ponytail 셀프체크: 투영 정합·tail 슬라이싱·오라클 발산 불변식(무 GPU·무 데이터)."""
    # 1) leave-out: cluster 제거가 정확히 그 clip만 뺀다
    infos = [{"token": f"t{i}"} for i in range(10)]
    sub = np.array([0, 0, 1, 1, -1, 2, 2, 2, -1, 0])
    import tempfile, mmcv
    with tempfile.TemporaryDirectory() as td:
        pkl = os.path.join(td, "lo.pkl")
        kept, removed = make_leaveout(infos, sub, 2, pkl, {"version": "v1.0-trainval"})
        assert removed == 3 and kept == 7, (kept, removed)
        loaded = mmcv.load(pkl)
        assert loaded["metadata"]["version"] == "v1.0-trainval", "metadata version 유실"  # 회귀 방지
        got = loaded["infos"]
        assert all(x["token"] not in ("t5", "t6", "t7") for x in got), "제거 누락"
    # 2) cluster_tail: 슬라이스 평균이 맞는지(합성 results/infos)
    def mkinfo(cmd=2, tok="x", ts=0):
        return {"gt_ego_fut_trajs": np.tile([0.0, 1.0], (6, 1)), "gt_ego_fut_cmd": np.eye(3)[cmd],
                "gt_ego_fut_masks": np.ones(6), "token": tok, "timestamp": ts}
    vi = [mkinfo(tok="a", ts=0), mkinfo(tok="b", ts=1), mkinfo(tok="c", ts=2)]
    gt = np.cumsum(np.tile([0.0, 1.0], (6, 1)), 0)
    res = [  # clip0 완벽(L2=0), clip1 오프셋1, clip2 오프셋2
        {"img_bbox": {"planning_score": np.ones((3, 6)), "final_planning": gt}},
        {"img_bbox": {"planning_score": np.ones((3, 6)), "final_planning": gt + np.array([1.0, 0])}},
        {"img_bbox": {"planning_score": np.ones((3, 6)), "final_planning": gt + np.array([2.0, 0])}}]
    vs = np.array([0, 0, 1])
    tail = cluster_tail(res, vi, vs)
    assert abs(tail["0"]["mean_l2"] - 0.5) < 1e-9, tail   # (0+1)/2
    assert abs(tail["1"]["mean_l2"] - 2.0) < 1e-9, tail
    # 3) 오라클 발산: recov가 uncertainty와 완전상관이면 FAIL, 독립이면 DIVERGE (divergence 재사용 확인)
    from s0_features import spearman
    a = np.array([1., 2, 3, 4, 5]); b = a.copy()
    assert abs(spearman(a, b) - 1.0) < 1e-9
    print("demo OK — leaveout/tail-slice/spearman 불변식 통과")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=False)
    dfl = dict(train_infos="data/infos/nuscenes_infos_train.pkl",
               val_infos="data/infos/nuscenes_infos_val.pkl")

    p = sub.add_parser("prep"); p.set_defaults(fn=cmd_prep)
    p.add_argument("--train_infos", default=dfl["train_infos"])
    p.add_argument("--val_infos", default=dfl["val_infos"])
    p.add_argument("--train_npz", default=os.path.join(HERE, "output/gq1_s0_perclip.npz"))
    p.add_argument("--s0json", default=os.path.join(HERE, "output/gq1_s0.json"))
    p.add_argument("--outdir", default=os.path.join(HERE, "output_val"))
    p.add_argument("--leaveout_dir", default="data/infos/leaveout")
    p.add_argument("--clusters", type=int, nargs="*", default=None)

    p = sub.add_parser("tail"); p.set_defaults(fn=cmd_tail)
    p.add_argument("--results", required=True)
    p.add_argument("--arm", required=True, help="baseline | leaveout_c<K>")
    p.add_argument("--val_infos", default=dfl["val_infos"])
    p.add_argument("--val_sub", default=os.path.join(HERE, "output_val/val_subdef_trainaligned.npz"))
    p.add_argument("--outdir", default=os.path.join(HERE, "output_val"))

    p = sub.add_parser("oracle"); p.set_defaults(fn=cmd_oracle)
    p.add_argument("--baseline", required=True)
    p.add_argument("--leaveout_tails", nargs="+", required=True)
    p.add_argument("--val_sub", default=os.path.join(HERE, "output_val/val_subdef_trainaligned.npz"))
    p.add_argument("--s0_model_npz", default=os.path.join(HERE, "output_val/gq1_s0_model_perclip.npz"))
    p.add_argument("--outdir", default=os.path.join(HERE, "output_val"))

    ap.add_argument("--selfcheck", action="store_true")
    a = ap.parse_args()
    if a.selfcheck or a.cmd is None:
        demo()
    else:
        a.fn(a)
