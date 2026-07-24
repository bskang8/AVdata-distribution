"""per-clip 성능 대리지표 — egomotion 궤적의 예측난이도(ADE/FDE).

방법론 §2 `model_error` 인자 + §5 검증층 성능신호의 구현.
라벨 없이, ego 궤적 자체를 GT로: 과거 OBS_S초 관측 → 미래 FUT_S초 등속(CV) 예측 →
예측오차(ADE/FDE). 오차 큼 = 단순 운동prior가 실패 = 복잡한 기동(정지·회전·가감속)
= "그 조건에서 예측이 어렵다"의 대리. 클립 전체를 STRIDE_S로 슬라이딩해 평균.

de-risk 통과 근거: 커버율 97.4% · 6-DoF 포즈 ~10Hz·20s (phase0/derisk_egomotion.py).
CV는 첫 베이스라인(가장 lazy) — 나중에 학습모델로 교체하면 절대난이도가 아니라
'특정 모델의 실패'로 격상(§5 leave-out에서 실제 예측기 사용).

실행:  .venv/bin/python compute_surrogate.py [--limit N] [--demo]
       (phase0 산출물이 numpy2 → 반드시 .venv 인터프리터)
"""
import os, sys, glob, json, numpy as np
import pyarrow.parquet as pq

ROOT       = os.path.dirname(os.path.abspath(__file__))
PHASE0_OUT = os.path.join(ROOT, '..', 'phase0', 'output')
OUT        = os.path.join(ROOT, 'output'); os.makedirs(OUT, exist_ok=True)
EGO_DIR    = '/Data1/home/bskang/cds-data/egomotion_offline'

OBS_S, FUT_S, STRIDE_S = 2.0, 3.0, 2.5   # 관측 2s → 예측 3s, 2.5s 간격 슬라이딩
MIN_OBS, MIN_FUT = 5, 5                   # 창당 최소 관측/미래 점수(≥5 ⇒ ~10Hz에서 안정)


def load_xy_t(cid):
    """parquet → (t[초, 0시작·정렬], xy[N,2]).  없거나 짧으면 None."""
    p = os.path.join(EGO_DIR, f'{cid}.egomotion.offline.parquet')
    if not os.path.exists(p):
        return None
    tb = pq.read_table(p, columns=['timestamp', 'x', 'y'])
    t = np.asarray(tb['timestamp']).astype(float)
    if t.size < MIN_OBS + MIN_FUT:
        return None
    xy = np.column_stack([np.asarray(tb['x']).astype(float),
                          np.asarray(tb['y']).astype(float)])
    t = t - t[0]
    scale = 1e6 if t[-1] > 1e6 else 1e3 if t[-1] > 1e3 else 1.0   # μs/ms/s 자동추정
    t = t / scale
    o = np.argsort(t)
    return t[o], xy[o]


def window_err(t, xy, t0):
    """[t0,t0+OBS]로 CV 적합 → [t0+OBS,+FUT] 예측오차 (ade, fde). 자료부족 시 None."""
    tsplit = t0 + OBS_S
    obs = (t >= t0) & (t < tsplit)
    fut = (t >= tsplit) & (t <= t0 + OBS_S + FUT_S)
    if obs.sum() < MIN_OBS or fut.sum() < MIN_FUT:
        return None
    to = t[obs]
    A = np.column_stack([to - tsplit, np.ones_like(to)])        # pos = v·(t-tsplit) + p_split
    coef, *_ = np.linalg.lstsq(A, xy[obs], rcond=None)          # (2,2): [v; p_split]
    v, p_split = coef[0], coef[1]
    tf = t[fut]
    pred = p_split[None, :] + np.outer(tf - tsplit, v)          # 등속 외삽
    d = np.linalg.norm(pred - xy[fut], axis=1)
    return float(d.mean()), float(d[-1])


def clip_err(t, xy):
    """클립 전체 슬라이딩 창 평균 (ade, fde).  유효 창 없으면 (nan, nan)."""
    errs, t0, tmax = [], float(t[0]), float(t[-1])
    while t0 + OBS_S + FUT_S <= tmax + 1e-6:
        r = window_err(t, xy, t0)
        if r:
            errs.append(r)
        t0 += STRIDE_S
    if not errs:
        return np.nan, np.nan
    a = np.asarray(errs)
    return a[:, 0].mean(), a[:, 1].mean()


def demo():
    """CV 예측기 자기검증: 직선(등속)→오차0, 곡선(가속)→오차>0."""
    t = np.linspace(0, 6, 61)                    # 10Hz, 6s
    straight = np.column_stack([3 * t, -2 * t])  # 등속
    a, f = clip_err(t, straight)
    assert a < 1e-6 and f < 1e-6, f"등속인데 오차 발생: {a},{f}"
    curved = np.column_stack([t ** 2, np.zeros_like(t)])  # 등가속 → CV 과소예측
    a2, f2 = clip_err(t, curved)
    assert a2 > 0.1 and f2 >= a2, f"곡선 오차 이상: {a2},{f2}"
    print(f"demo ✓  직선 ade={a:.2e}  곡선 ade={a2:.3f} fde={f2:.3f}")


def main(limit=None):
    ids = [str(x) for x in np.load(os.path.join(PHASE0_OUT, 'clip_ids.npy'), allow_pickle=True)]
    N = len(ids)
    sel = ids[:limit] if limit else ids
    ade = np.full(N, np.nan); fde = np.full(N, np.nan)
    done = miss = 0
    for i, cid in enumerate(sel):
        r = load_xy_t(cid)
        if r is None:
            miss += 1; continue
        ade[i], fde[i] = clip_err(*r)
        done += 1
        if (i + 1) % 2000 == 0:
            print(f"  {i+1}/{len(sel)}  valid={done} miss={miss}")
    a, f = ade[:len(sel)], fde[:len(sel)]     # 처리한 구간만(미처리=NaN 제외)
    ok = np.isfinite(a)
    suffix = f'_n{limit}' if limit else ''
    np.save(os.path.join(OUT, f'ade_per_clip{suffix}.npy'), ade)
    np.save(os.path.join(OUT, f'fde_per_clip{suffix}.npy'), fde)
    summ = {
        'processed': len(sel), 'valid': int(ok.sum()),
        'missing_or_short': int(len(sel) - ok.sum()), 'no_parquet': miss,
        'params': {'OBS_S': OBS_S, 'FUT_S': FUT_S, 'STRIDE_S': STRIDE_S},
        'ade': {'mean': float(np.nanmean(a)), 'p50': float(np.percentile(a[ok], 50)),
                'p90': float(np.percentile(a[ok], 90)), 'max': float(a[ok].max())},
        'fde': {'mean': float(np.nanmean(fde[:len(sel)])), 'p50': float(np.percentile(f[ok], 50)),
                'p90': float(np.percentile(f[ok], 90))},
        'note': 'CV 베이스라인 예측난이도. 큰 값 = 복잡 기동. 단위=egomotion 위치(추정 m).',
    }
    with open(os.path.join(OUT, f'surrogate_summary{suffix}.json'), 'w') as f:
        json.dump(summ, f, ensure_ascii=False, indent=2)
    print(json.dumps(summ, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    if '--demo' in sys.argv:
        demo()
    else:
        lim = None
        if '--limit' in sys.argv:
            lim = int(sys.argv[sys.argv.index('--limit') + 1])
        main(lim)
