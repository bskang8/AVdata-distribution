"""ADE/FDE per-clip → ODD 셀별·임베딩 사분면별 집계 + 획득함수 model_error(c).

방법론 §2 획득함수의 마지막 인자 `model_error(c)`를 산출한다.
입력은 전부 phase0 `clip_ids.npy` 순서(길이 100,398)로 정렬:
  - ade/fde_per_clip.npy           (phase1, egomotion CV 예측난이도; 미처리=NaN)
  - quadrant_assignment.npy        (phase0, 임베딩 렌즈 2×2: density × LID, 0..3)
  - odd_codes_compat_v2.npy        (phase0, (N,11) ODD 축코드 → 유니크 행 = ODD 셀)
  - density_quartile.npy           (phase0, Domino density축)

산출(output/):
  - error_by_quadrant.json          임베딩 사분면별 ADE/FDE 분포
  - model_error_by_odd_cell.json    ODD 셀별 mean ADE/FDE + model_error(c)∈[0,1]
  - model_error_per_clip.npy        각 클립이 속한 셀의 model_error (없으면 NaN)
  - domino_density_x_error.json     low-density×high-error 최우선 수집 셀(README #1)

model_error(c) 정의: 셀 mean ADE의 **클립수 가중 경험 CDF**(= 그 셀보다 오차 낮은
클립 비율)로 [0,1] 정규화. max=19 아웃라이어에 강건, 다른 [0,1] 인자와 곱 가능.
n<MIN_CELL 셀은 추정 불안정 → NaN, 획득함수는 사분면 prior로 폴백(출력에 명시).

실행:  ../../../.venv/bin/python aggregate_error.py [--demo]
"""
import os, sys, json, numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
P0   = os.path.join(ROOT, '..', 'phase0', 'output')
OUT  = os.path.join(ROOT, 'output')
MIN_CELL = 20          # 셀 model_error 추정 최소 클립수(그 미만=불안정→NaN)
HI_ERR_Q = 0.75        # 'high-error' 분위 기준(가중 CDF 상위 25%)


def _stats(v):
    return {'n': int(v.size), 'mean': float(v.mean()),
            'p50': float(np.percentile(v, 50)), 'p90': float(np.percentile(v, 90))}


def weighted_cdf(cell_means, cell_counts):
    """셀 mean 값 → 클립수 가중 경험 CDF(그 값 이하 클립 비율)∈[0,1]."""
    order = np.argsort(cell_means)
    cum = np.cumsum(cell_counts[order])
    tot = cum[-1]
    cdf = np.empty_like(cell_means, dtype=float)
    # 각 셀에 '자기 포함 누적비율의 중점' 부여(동률 안정)
    prev = 0
    for rank, idx in enumerate(order):
        cdf[idx] = (prev + cum[rank]) / 2.0 / tot
        prev = cum[rank]
    return cdf


def main(prefix=''):
    # prefix='learned_' → 학습형 대리지표로 model_error 재산출(§5). 산출물도 접두 부여.
    ade = np.load(os.path.join(ROOT, 'output', f'{prefix}ade_per_clip.npy'))
    fde = np.load(os.path.join(ROOT, 'output', f'{prefix}fde_per_clip.npy'))
    quad = np.load(os.path.join(P0, 'quadrant_assignment.npy'))
    dq   = np.load(os.path.join(P0, 'density_quartile.npy'))
    odd  = np.load(os.path.join(P0, 'odd_codes_compat_v2.npy'))
    N = ade.size
    assert quad.size == odd.shape[0] == N, "정렬 길이 불일치"

    ok = np.isfinite(ade)                     # 유효 성능신호 있는 클립만
    print(f"clips={N} valid_error={ok.sum()}")

    # ---- 임베딩 사분면별 (0..3) ----
    QNAME = {0: 'Q0 high-density × high-LID', 1: 'Q1 high-density × low-LID',
             2: 'Q2 low-density × high-LID', 3: 'Q3 low-density × low-LID'}
    by_quad = {}
    for q in sorted(set(quad.tolist())):
        m = ok & (quad == q)
        if m.sum() == 0:
            continue
        by_quad[int(q)] = {'label': QNAME.get(int(q), str(q)),
                           'ade': _stats(ade[m]), 'fde': _stats(fde[m])}
    json.dump({'note': '임베딩 렌즈(density×LID) 사분면별 egomotion 예측난이도',
               'quadrants': by_quad},
              open(os.path.join(OUT, f'{prefix}error_by_quadrant.json'), 'w'),
              ensure_ascii=False, indent=2)

    # ---- ODD 셀별 (유니크 11-tuple) ----
    keys = np.array(['-'.join(map(str, r)) for r in odd])
    cell_of = {}
    for i in np.nonzero(ok)[0]:
        cell_of.setdefault(keys[i], []).append(i)
    cells = [(k, np.array(idx)) for k, idx in cell_of.items() if len(idx) >= MIN_CELL]
    cmean = np.array([ade[idx].mean() for _, idx in cells])
    ccnt  = np.array([idx.size for _, idx in cells], dtype=float)
    me = weighted_cdf(cmean, ccnt)            # model_error(c) ∈ [0,1]

    cell_tbl = {}
    for (k, idx), a_mean, c, e in zip(cells, cmean, ccnt, me):
        cell_tbl[k] = {'n': int(c), 'mean_ade': float(a_mean),
                       'mean_fde': float(fde[idx].mean()), 'model_error': float(e)}
    json.dump({'note': f'ODD 셀별 model_error(c). n<{MIN_CELL} 셀은 제외(불안정)→사분면 prior 폴백.',
               'min_cell': MIN_CELL, 'n_cells': len(cells),
               'n_clips_covered': int(ccnt.sum()),
               'cells': dict(sorted(cell_tbl.items(),
                                    key=lambda kv: -kv[1]['model_error']))},
              open(os.path.join(OUT, f'{prefix}model_error_by_odd_cell.json'), 'w'),
              ensure_ascii=False, indent=2)

    # per-clip model_error (셀 매핑; 미포함=NaN)
    me_clip = np.full(N, np.nan)
    for (k, idx), e in zip(cells, me):
        me_clip[idx] = e
    np.save(os.path.join(OUT, f'{prefix}model_error_per_clip.npy'), me_clip)

    # ---- Domino: density(quartile) × error → 최우선 수집(low-density × high-error) ----
    hi_err = me_clip >= HI_ERR_Q
    lo_dens = ok & (dq == 0)                  # density 최하 분위 = 희소
    domino = {'hi_err_thresh_quantile': HI_ERR_Q,
              'cells_low_density_high_error': []}
    for k, idx in cells:
        e = cell_tbl[k]['model_error']
        frac_lodens = float((dq[idx] == 0).mean())
        if e >= HI_ERR_Q and frac_lodens >= 0.5:
            domino['cells_low_density_high_error'].append(
                {'cell': k, 'n': cell_tbl[k]['n'], 'model_error': e,
                 'mean_ade': cell_tbl[k]['mean_ade'], 'frac_low_density': frac_lodens})
    domino['cells_low_density_high_error'].sort(key=lambda d: -d['model_error'])
    domino['count'] = len(domino['cells_low_density_high_error'])
    json.dump(domino, open(os.path.join(OUT, f'{prefix}domino_density_x_error.json'), 'w'),
              ensure_ascii=False, indent=2)

    print(f"cells(n>={MIN_CELL})={len(cells)} covering {int(ccnt.sum())} clips")
    print(f"model_error range [{me.min():.3f},{me.max():.3f}] mean {me.mean():.3f}")
    print(f"domino low-density×high-error cells: {domino['count']}")
    for q, d in by_quad.items():
        print(f"  {d['label']}: ADE p50={d['ade']['p50']:.2f} mean={d['ade']['mean']:.2f} (n={d['ade']['n']})")


def demo():
    """weighted_cdf 자기검증: 큰 오차 셀 → 높은 model_error, 단조."""
    means = np.array([1.0, 2.0, 3.0, 5.0])
    cnt   = np.array([10., 10., 10., 10.])
    e = weighted_cdf(means, cnt)
    assert np.all(np.diff(e) > 0), f"단조 아님: {e}"
    assert 0 < e.min() and e.max() < 1, f"[0,1] 벗어남: {e}"
    # 클립수 가중: 첫 셀에 클립 몰리면 나머지 CDF 상승
    e2 = weighted_cdf(means, np.array([70., 10., 10., 10.]))
    assert e2[-1] > e[-1], "가중 반영 안 됨"
    print(f"demo ✓  e={np.round(e,3)}  weighted_last {e[-1]:.3f}→{e2[-1]:.3f}")


if __name__ == '__main__':
    if '--demo' in sys.argv:
        demo()
    else:
        pfx = 'learned_' if '--learned' in sys.argv else ''
        main(pfx)
