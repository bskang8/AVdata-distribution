#!/usr/bin/env python
"""
G-Q1 / S0 — 결핍 클러스터 정의 + per-clip model-free 신호 + 발산 행렬.

설계: r1_gates/GQ1_design.md §3(S0). 이 스크립트는 **무재학습**으로 가능한 부분만 계산한다:
  - 결핍 클러스터(kinematics/map/agent 메타, planning-relevant 실패군, n>=15 서브결핍)
  - model-agnostic 신호: diversity(coverage) · coverage_redundancy(SemDeDup식)
  - 발산 행렬(가용 신호 간 Spearman + top-k Jaccard)
모델 의존 신호(recoverability_proxy · uncertainty · scaling_gain)는 M0 학습 후
s0_model_signals.py가 같은 하니스에 주입한다(여기선 deferred 슬롯).

입력: SparseDrive infos pkl (nuscenes_infos_train.pkl).
필드(확정): ego_status[0:3]=accel, [3:6]=rot_rate(yaw=5), [6:9]=vel(vx=6 전방), [9]=steer;
  gt_ego_fut_trajs(6,2)=ego프레임 step offset(x=lateral,y=longitudinal), dt=0.5s;
  gt_ego_fut_cmd=[右,左,直] one-hot; gt_boxes(N,7) ego프레임; valid_flag; gt_velocity(N,2);
  map_annos={0:ped_crossing,1:divider,2:boundary} 폴리라인(ego프레임).
"""
import os, json, argparse
import numpy as np

DT = 0.5  # nuScenes keyframe 간격(s)
FEATURE_KEYS = [  # 클러스터링·발산에 쓰는 수치 feature(모두 model-agnostic)
    "speed", "accel_long", "curvature", "abs_lateral_final", "yaw_rate_abs",
    "n_agents", "min_dist", "n_close", "agent_speed_max",
    "pedx_present", "pedx_min_dist", "n_divider",
]


def _cmd(info):
    # [右,左,直] → 0/1/2
    return int(np.argmax(info["gt_ego_fut_cmd"]))


def extract_features(info):
    """per-clip 스칼라 feature dict. 전부 nuScenes 네이티브(백본 無)."""
    off = np.asarray(info["gt_ego_fut_trajs"], np.float64)  # (6,2) step offset
    mag = np.linalg.norm(off, axis=1)                        # per-step 이동거리
    speed = float(mag.mean() / DT)                           # m/s (미래평균)
    accel_long = float((mag[-1] - mag[0]) / DT / max(len(mag) - 1, 1))
    # 곡률: 연속 offset 벡터 간 heading 변화 총합 / 경로길이
    ang = np.arctan2(off[:, 1], off[:, 0])
    dang = np.abs(np.diff(np.unwrap(ang)))
    path = float(mag.sum()) + 1e-6
    curvature = float(dang.sum() / path)                     # rad/m
    curvature = 0.0 if speed < 2.0 else min(curvature, 1.0)  # 저속 division 노이즈 차단 + 물리 상한
    abs_lateral_final = float(abs(np.cumsum(off[:, 0])[-1]))  # 최종 횡변위 크기

    es = np.asarray(info["ego_status"], np.float64)
    yaw_rate_abs = float(abs(es[5])) if np.any(es) else float("nan")

    valid = np.asarray(info["valid_flag"], bool)
    boxes = np.asarray(info["gt_boxes"], np.float64)
    vel = np.asarray(info["gt_velocity"], np.float64)
    if valid.sum() > 0:
        xy = boxes[valid, :2]
        dist = np.linalg.norm(xy, axis=1)
        n_agents = int(valid.sum())
        min_dist = float(dist.min())
        n_close = int((dist < 10.0).sum())
        agent_speed_max = float(np.linalg.norm(vel[valid], axis=1).max())
    else:
        n_agents, min_dist, n_close, agent_speed_max = 0, 60.0, 0, 0.0

    ma = info["map_annos"]
    pedx = ma.get(0, [])   # ped_crossing
    div = ma.get(1, [])    # divider
    if len(pedx):
        pd = min(float(np.linalg.norm(np.asarray(p), axis=1).min()) for p in pedx)
    else:
        pd = 60.0
    feats = {
        "speed": speed, "accel_long": accel_long, "curvature": curvature,
        "abs_lateral_final": abs_lateral_final, "yaw_rate_abs": yaw_rate_abs,
        "n_agents": float(n_agents), "min_dist": min_dist, "n_close": float(n_close),
        "agent_speed_max": agent_speed_max,
        "pedx_present": 1.0 if len(pedx) else 0.0, "pedx_min_dist": pd,
        "n_divider": float(len(div)),
    }
    feats["_cmd"] = _cmd(info)                 # 0右1左2直
    feats["_scene"] = info["scene_token"]
    feats["_city"] = info.get("map_location", "?")
    feats["_token"] = info["token"]
    return feats


def build_matrix(feat_dicts):
    """feature dict 리스트 → 표준화 행렬 (yaw_rate_abs NaN은 열중앙값 대체)."""
    X = np.array([[fd[k] for k in FEATURE_KEYS] for fd in feat_dicts], np.float64)
    for j in range(X.shape[1]):                # NaN → 열 중앙값
        col = X[:, j]
        m = np.isnan(col)
        if m.any():
            col[m] = np.nanmedian(col)
    mu, sd = X.mean(0), X.std(0) + 1e-9
    return (X - mu) / sd, X


def rule_tags(fd, thr):
    """해석가능 결핍 태그(§5-1). thr=분위 기반 tail 임계. 다중 태그 가능.
    occlusion은 model-free 추론 불가(n_agents/밀도로는 42% 오탐) → S0 제외, M0/perception 필요."""
    tags = []
    if fd["_cmd"] != 2 and fd["speed"] >= 2.0 and fd["abs_lateral_final"] >= thr["lat_hi"]:
        tags.append("sharp_turn")
    if fd["_cmd"] == 1 and fd["n_agents"] >= thr["agents_hi"] and (fd["pedx_present"] > 0 or fd["pedx_min_dist"] < 15):
        tags.append("unprotected_left")
    if fd["min_dist"] <= thr["dist_lo"] or fd["n_close"] >= thr["close_hi"]:
        tags.append("high_interaction")
    return tags


def spearman(a, b):
    ra, rb = _rank(a), _rank(b)
    ra, rb = ra - ra.mean(), rb - rb.mean()
    d = np.sqrt((ra * ra).sum() * (rb * rb).sum()) + 1e-12
    return float((ra * rb).sum() / d)


def _rank(a):
    o = np.argsort(np.argsort(a))
    return o.astype(np.float64)


def topk_jaccard(a, b, frac=0.10):
    k = max(int(len(a) * frac), 1)
    sa = set(np.argsort(a)[::-1][:k]); sb = set(np.argsort(b)[::-1][:k])
    return len(sa & sb) / len(sa | sb)


def divergence(signals):
    """signals: {name: per-clip array}. → Spearman·Jaccard 행렬(대칭)."""
    names = list(signals)
    sp = {}; jc = {}
    for i, n1 in enumerate(names):
        for n2 in names[i:]:
            s = spearman(signals[n1], signals[n2]); j = topk_jaccard(signals[n1], signals[n2])
            sp[f"{n1}|{n2}"] = round(s, 4); sp[f"{n2}|{n1}"] = round(s, 4)
            jc[f"{n1}|{n2}"] = round(j, 4); jc[f"{n2}|{n1}"] = round(j, 4)
    return {"signals": names, "spearman": sp, "topk_jaccard": jc}


def run(infos, outdir, n_sub=20):
    from sklearn.cluster import KMeans
    from sklearn.neighbors import NearestNeighbors
    os.makedirs(outdir, exist_ok=True)

    fds = [extract_features(e) for e in infos]
    Z, Xraw = build_matrix(fds)

    # 규칙 임계 = 분위 기반 tail(각 태그가 소수가 되도록)
    col = lambda k: np.array([fd[k] for fd in fds], float)
    thr = {
        "lat_hi": float(np.nanquantile(col("abs_lateral_final"), 0.92)),   # 급한 횡변위 상위 8%
        "dist_lo": float(np.nanquantile(col("min_dist"), 0.12)),           # 근접 하위 12%
        "close_hi": float(np.nanquantile(col("n_close"), 0.95)),           # 밀집 상위 5%
        "agents_hi": float(np.nanquantile(col("n_agents"), 0.60)),
    }
    for fd in fds:
        fd["_tags"] = rule_tags(fd, thr)
    cand = np.array([len(fd["_tags"]) > 0 for fd in fds])

    # 서브결핍: 후보 clip에 KMeans → n_sub개, 지배 태그+도시로 라벨
    sub = -np.ones(len(fds), int)
    if cand.sum() >= n_sub:
        km = KMeans(n_clusters=n_sub, random_state=0, n_init=10).fit(Z[cand])
        sub[cand] = km.labels_
    clusters = {}
    for cid in range(n_sub):
        idx = np.where(sub == cid)[0]
        if len(idx) == 0:
            continue
        tagc = {}
        for i in idx:
            for t in fds[i]["_tags"]:
                tagc[t] = tagc.get(t, 0) + 1
        dom = max(tagc, key=tagc.get) if tagc else "mixed"
        cities = {}
        for i in idx:
            cities[fds[i]["_city"]] = cities.get(fds[i]["_city"], 0) + 1
        clusters[str(cid)] = {
            "n": int(len(idx)), "dominant_tag": dom, "tag_counts": tagc,
            "top_city": max(cities, key=cities.get),
            "mean_speed": round(float(np.mean([fds[i]["speed"] for i in idx])), 2),
            "mean_min_dist": round(float(np.mean([fds[i]["min_dist"] for i in idx])), 2),
        }

    # model-free 신호(per-clip)
    nn = NearestNeighbors(n_neighbors=11).fit(Z)
    dknn, _ = nn.kneighbors(Z)
    diversity = dknn[:, 1:].mean(1)             # kNN 평균거리 ↑ = 희소/다양
    coverage_redundancy = 1.0 / (dknn[:, 1] + 1e-6)  # 최근접 유사 ↑ = 중복(SemDeDup식)

    signals = {"diversity": diversity, "coverage_redundancy": coverage_redundancy}
    deferred = ["recoverability_proxy", "uncertainty", "scaling_gain"]  # M0 필요

    div = divergence(signals)
    out = {
        "n_clips": len(fds), "n_candidate": int(cand.sum()),
        "n_subdeficiencies": int(len({c for c in sub if c >= 0})),
        "feature_keys": FEATURE_KEYS, "rule_thresholds": thr,
        "tag_totals": _tag_totals(fds),
        "clusters": clusters,
        "signals_computed": list(signals), "signals_deferred": deferred,
        "divergence": div,
        "note": ("S0 model-free 부분만. 발산 판정(G-Q1)은 recoverability(oracle/proxy)"
                 "·uncertainty·scaling_gain 주입 후 완성 → s0_model_signals.py."),
    }
    with open(os.path.join(outdir, "gq1_s0.json"), "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    # per-clip 신호·서브결핍은 npz로(후속 주입용)
    np.savez(os.path.join(outdir, "gq1_s0_perclip.npz"),
             tokens=np.array([fd["_token"] for fd in fds]),
             subdef=sub, diversity=diversity, coverage_redundancy=coverage_redundancy,
             features=Xraw, feature_keys=np.array(FEATURE_KEYS))
    return out


def _tag_totals(fds):
    t = {}
    for fd in fds:
        for tag in fd["_tags"]:
            t[tag] = t.get(tag, 0) + 1
    return t


def demo():
    """ponytail 셀프체크: 합성 데이터로 불변식 검증(무의존)."""
    rng = np.random.default_rng(0)
    fds = []
    for _ in range(600):
        off = rng.normal(0, 1, (6, 2)); off[:, 1] += 4  # 전방 이동
        fds.append({
            "gt_ego_fut_trajs": off, "ego_status": rng.normal(0, 1, 10),
            "gt_ego_fut_cmd": np.eye(3)[rng.integers(3)],
            "gt_boxes": rng.normal(0, 15, (10, 7)), "valid_flag": rng.random(10) > 0.3,
            "gt_velocity": rng.normal(0, 3, (10, 2)),
            "map_annos": {0: [rng.normal(0, 10, (2, 2))], 1: [], 2: []},
            "scene_token": f"s{_ % 20}", "map_location": "x", "token": f"t{_}",
        })
    feats = [extract_features(e) for e in fds]
    Z, X = build_matrix(feats)
    assert np.isfinite(Z).all(), "표준화 행렬 NaN/inf"
    assert Z.shape == (600, len(FEATURE_KEYS))
    a = X[:, 0]; b = X[:, 1]
    assert abs(spearman(a, a) - 1.0) < 1e-6, "self-Spearman!=1"
    assert -1.0 <= spearman(a, b) <= 1.0
    d = divergence({"a": a, "b": b, "c": -a})
    assert abs(d["spearman"]["a|c"] + 1.0) < 1e-6, "역상관 신호 ρ!=-1"
    assert abs(d["spearman"]["a|a"] - 1.0) < 1e-6
    assert 0.0 <= topk_jaccard(a, b) <= 1.0
    print("demo OK — feature/표준화/Spearman/Jaccard/divergence 불변식 통과")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--infos", default="data/infos/nuscenes_infos_train.pkl")
    ap.add_argument("--outdir", default=os.path.join(os.path.dirname(__file__), "output"))
    ap.add_argument("--n_sub", type=int, default=20)
    ap.add_argument("--selfcheck", action="store_true")
    a = ap.parse_args()
    if a.selfcheck:
        demo()
    else:
        import mmcv
        infos = mmcv.load(a.infos)["infos"]
        out = run(infos, a.outdir, a.n_sub)
        print(f"clips={out['n_clips']} candidate={out['n_candidate']} "
              f"subdef={out['n_subdeficiencies']} tags={out['tag_totals']}")
        print("divergence(model-free):", out["divergence"]["spearman"])
