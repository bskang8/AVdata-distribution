"""학습형 성능 대리지표 — 전역 예측기의 per-clip 예측난이도(ADE/FDE).

방법론 §5의 첫 관문: CV(클립별 자기적합) → **전역 학습모델**(fleet 평균 동역학)로 교체.
CV 오차 = 기동의 절대복잡도. 학습모델 오차 = "이 클립이 fleet 기준 얼마나 비전형인가"
→ 분포 의존적 model_error. same-clip 누수 없는 GroupKFold OOF로 "모델이 실제 못 본
조건에서 틀린다"를 성립시킨다.

방법:
  각 슬라이딩 창(관측 OBS_S → 미래 FUT_S)을 canonical frame으로 정규화
  (분기점=원점, 관측 heading=+x축 회전). 관측 kinematics feature → 미래 6지평
  변위 target(12-dim). 전역 MLP(StandardScaler∘MLP)를 GroupKFold(clip)로 OOF 예측.
  per-clip ADE/FDE = 창별 오차 평균. 회전·평행이동은 거리 보존 → 오차는 canonical에서 계산.

CV(compute_surrogate.py)와 같은 창 정의·같은 clip_ids 정렬 → 직접 비교/교체 가능.
실행:  ../../../.venv/bin/python learned_surrogate.py [--limit N] [--demo]
       (첫 실행은 창 추출 캐시 output/windows.npz 생성; 이후 재사용)
"""
import os, sys, json, numpy as np
import pyarrow.parquet as pq
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import GroupKFold

ROOT       = os.path.dirname(os.path.abspath(__file__))
PHASE0_OUT = os.path.join(ROOT, '..', 'phase0', 'output')
OUT        = os.path.join(ROOT, 'output'); os.makedirs(OUT, exist_ok=True)
EGO_DIR    = '/Data1/home/bskang/cds-data/egomotion_offline'

OBS_S, FUT_S, STRIDE_S = 2.0, 3.0, 2.5
MIN_OBS, MIN_FUT = 5, 5
HZN = np.array([0.5, 1.0, 1.5, 2.0, 2.5, 3.0])   # 미래 예측 지평(canonical 변위 target)
N_FOLDS = 5


def load_xy_t(cid):
    p = os.path.join(EGO_DIR, f'{cid}.egomotion.offline.parquet')
    if not os.path.exists(p):
        return None
    tb = pq.read_table(p, columns=['timestamp', 'x', 'y'])
    t = np.asarray(tb['timestamp']).astype(float)
    if t.size < MIN_OBS + MIN_FUT:
        return None
    xy = np.column_stack([np.asarray(tb['x']).astype(float), np.asarray(tb['y']).astype(float)])
    t = t - t[0]
    scale = 1e6 if t[-1] > 1e6 else 1e3 if t[-1] > 1e3 else 1.0
    t = t / scale
    o = np.argsort(t)
    return t[o], xy[o]


def _interp_xy(t, xy, tq):
    return np.column_stack([np.interp(tq, t, xy[:, 0]), np.interp(tq, t, xy[:, 1])])


def window_feat_target(t, xy, t0):
    """창 → (feature[6], target[12] canonical 미래변위) 또는 None."""
    tsplit = t0 + OBS_S
    obs = (t >= t0) & (t <= tsplit)
    if obs.sum() < MIN_OBS or (t >= tsplit).sum() < 1 or t[-1] < tsplit + FUT_S - 1e-6:
        return None
    to, xo = t[obs], xy[obs]
    p_split = _interp_xy(t, xy, np.array([tsplit]))[0]
    # heading: 관측 마지막 ~0.6s 속도
    late = to >= tsplit - 0.6
    if late.sum() < 2:
        late = slice(-3, None)
    vv = np.polyfit(to[late] - tsplit, xo[late], 1)[0]      # (vx,vy)
    speed = float(np.hypot(*vv))
    theta = float(np.arctan2(vv[1], vv[0]))
    c, s = np.cos(-theta), np.sin(-theta)
    R = np.array([[c, -s], [s, c]])                          # heading→+x 회전
    # feature: 속도 + 관측 2차적합의 가·감속(long/lat) + yaw_rate + 곡률
    A = np.column_stack([(to - tsplit) ** 2, to - tsplit, np.ones_like(to)])
    qcoef, *_ = np.linalg.lstsq(A, xo, rcond=None)           # (3,2): [½a, v, p]
    a_vec = R @ (2 * qcoef[0])                               # canonical 가속
    early = to <= t0 + 0.6
    v0 = np.polyfit(to[early] - t0, xo[early], 1)[0] if early.sum() >= 2 else vv
    yaw_rate = float(np.arctan2(vv[1], vv[0]) - np.arctan2(v0[1], v0[0])) / OBS_S
    feat = np.array([speed, a_vec[0], a_vec[1], yaw_rate,
                     yaw_rate / (speed + 1e-3), speed ** 2])
    # target: 미래 canonical 변위
    fut = _interp_xy(t, xy, tsplit + HZN)
    tgt = (fut - p_split) @ R.T                              # (6,2) → flatten
    return feat, tgt.ravel()


def extract(ids, do_cache=False):
    """전 클립 창 추출 → X, Y, clip_idx(그룹). full run만 캐시(부분 run과 혼입 방지)."""
    cache = os.path.join(OUT, 'windows.npz')
    if do_cache and os.path.exists(cache):
        z = np.load(cache)
        return z['X'], z['Y'], z['grp']
    X, Y, grp = [], [], []
    for i, cid in enumerate(ids):
        r = load_xy_t(cid)
        if r is None:
            continue
        t, xy = r
        t0, tmax = float(t[0]), float(t[-1])
        while t0 + OBS_S + FUT_S <= tmax + 1e-6:
            ft = window_feat_target(t, xy, t0)
            if ft:
                X.append(ft[0]); Y.append(ft[1]); grp.append(i)
            t0 += STRIDE_S
        if (i + 1) % 5000 == 0:
            print(f"  extract {i+1}/{len(ids)}  windows={len(X)}")
    X, Y, grp = np.array(X), np.array(Y), np.array(grp)
    if do_cache:
        np.savez(cache, X=X, Y=Y, grp=grp)
    return X, Y, grp


def oof_errors(X, Y, grp):
    """GroupKFold OOF 예측 → 창별 (ade, fde). 회전불변 → canonical 거리."""
    pred = np.zeros_like(Y)
    gkf = GroupKFold(n_splits=N_FOLDS)
    for f, (tr, te) in enumerate(gkf.split(X, Y, grp)):
        m = make_pipeline(StandardScaler(),
                          MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=200,
                                       early_stopping=True, n_iter_no_change=8,
                                       random_state=0))
        m.fit(X[tr], Y[tr])
        pred[te] = m.predict(X[te])
        print(f"  fold {f+1}/{N_FOLDS} fit  train={len(tr)} test={len(te)}")
    P, G = pred.reshape(-1, 6, 2), Y.reshape(-1, 6, 2)
    d = np.linalg.norm(P - G, axis=2)                        # (win,6)
    return d.mean(1), d[:, -1]                               # ade, fde


def main(limit=None):
    ids = [str(x) for x in np.load(os.path.join(PHASE0_OUT, 'clip_ids.npy'), allow_pickle=True)]
    N = len(ids)
    sel = ids[:limit] if limit else ids
    X, Y, grp = extract(sel, do_cache=limit is None)
    print(f"windows={len(X)}  clips_with_windows={len(set(grp.tolist()))}")
    w_ade, w_fde = oof_errors(X, Y, grp)
    ade = np.full(N, np.nan); fde = np.full(N, np.nan)
    for g in np.unique(grp):
        mask = grp == g
        ade[g] = w_ade[mask].mean(); fde[g] = w_fde[mask].mean()
    ok = np.isfinite(ade)
    suffix = f'_n{limit}' if limit else ''
    np.save(os.path.join(OUT, f'learned_ade_per_clip{suffix}.npy'), ade)
    np.save(os.path.join(OUT, f'learned_fde_per_clip{suffix}.npy'), fde)
    summ = {'model': 'MLP(64,32) GroupKFold-OOF, canonical 미래변위 회귀',
            'processed': len(sel), 'valid': int(ok.sum()), 'windows': int(len(X)),
            'params': {'OBS_S': OBS_S, 'FUT_S': FUT_S, 'STRIDE_S': STRIDE_S, 'horizons': HZN.tolist()},
            'ade': {'mean': float(np.nanmean(ade)), 'p50': float(np.percentile(ade[ok], 50)),
                    'p90': float(np.percentile(ade[ok], 90)), 'max': float(ade[ok].max())},
            'fde': {'mean': float(np.nanmean(fde)), 'p50': float(np.percentile(fde[ok], 50)),
                    'p90': float(np.percentile(fde[ok], 90))},
            'note': '전역 학습모델 예측난이도. CV와 달리 fleet 기준 비전형성 반영(분포 의존).'}
    json.dump(summ, open(os.path.join(OUT, f'learned_surrogate_summary{suffix}.json'), 'w'),
              ensure_ascii=False, indent=2)
    print(json.dumps(summ, ensure_ascii=False, indent=2))


def demo():
    """canonical 회전불변 + 등속창 target 검증."""
    t = np.linspace(0, 6, 61)
    xy = np.column_stack([3 * t, -2 * t])                    # 등속
    ft = window_feat_target(t, xy, 0.5)
    assert ft is not None
    feat, tgt = ft
    tg = tgt.reshape(6, 2)
    assert np.allclose(tg[:, 1], 0, atol=1e-6), f"등속인데 canonical 횡변위≠0: {tg[:,1]}"
    assert np.all(np.diff(tg[:, 0]) > 0), "canonical 종변위 단조증가 아님"
    assert abs(feat[0] - np.hypot(3, 2)) < 1e-3, f"speed 오차: {feat[0]}"
    assert abs(feat[3]) < 1e-3, f"등속인데 yaw_rate≠0: {feat[3]}"
    print(f"demo ✓  speed={feat[0]:.3f} yaw={feat[3]:.2e} 종변위={tg[:,0].round(2)}")


if __name__ == '__main__':
    if '--demo' in sys.argv:
        demo()
    else:
        lim = int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else None
        main(lim)
