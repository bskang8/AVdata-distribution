"""0-D: 6-분류 분포 액션 맵 (Density × LID × 신뢰도)
GMM BIC K=1~3 + brentq 실제 교차점으로 임계값 결정.
경계 구역 정량화 후 0-D에서 k-민감도 재계산(0-C 중앙값 근사 → GMM 확정값으로 보정).
"""

import json
import numpy as np
from config import ISOLATION_THRESHOLD, BOUNDARY_MARGIN_LID, K_SENSITIVE_THRESHOLD
from utils import P, require_files, compute_lid_mle, gmm_threshold, already_done


def run(force=False):
    if not force and already_done('0-D', 'quadrant_assignment.npy', 'thresholds.json'):
        return
    require_files(
        'density_per_clip.npy', 'lid_per_clip.npy',
        'uniqueness_weight.npy', 'lid_reliable.npy',
        'lid_k15.npy', 'lid_k25.npy',
        'knn_foundation.npz',
        step='step_c_lid.py',
    )
    print("[0-D] 6-분류 Action Map 시작")

    density          = np.load(P('density_per_clip.npy'))
    lid_per_clip     = np.load(P('lid_per_clip.npy'))
    uniqueness_weight = np.load(P('uniqueness_weight.npy'))
    lid_reliable     = np.load(P('lid_reliable.npy'))
    knn_sim          = np.load(P('knn_foundation.npz'))['knn_sim']

    density_threshold, d_best_k, d_bics = gmm_threshold(density)
    lid_threshold,     l_best_k, l_bics = gmm_threshold(lid_per_clip)

    if l_best_k == 1:
        print("  [경고] LID 분포 단봉(K=1) — Q2/Q3 구분이 median 50:50 분할. "
              "lid_threshold_unimodal=True")
    if d_best_k == 1:
        print("  [경고] 밀도 분포 단봉(K=1) — 고/저밀도 분리 구조 없음.")

    high_d = density    >= density_threshold
    high_l = lid_per_clip >= lid_threshold

    quadrant = np.full(len(density), -1, dtype=int)
    quadrant[high_d  & high_l]                  = 0   # KEEP
    quadrant[high_d  & ~high_l & lid_reliable]  = 1   # PRUNE
    quadrant[high_d  & ~high_l & ~lid_reliable] = 5   # PRUNE_UNCERTAIN
    quadrant[~high_d & high_l  & lid_reliable]  = 2   # COLLECT
    quadrant[~high_d & ~high_l & lid_reliable]  = 3   # EVALUATE → 0-E-2
    quadrant[~high_d & ~lid_reliable]           = 4   # LID_UNCERTAIN → 0-E-1

    quadrant_profile = {}
    for q in range(6):
        mask = quadrant == q
        quadrant_profile[q] = {
            'count': int(mask.sum()),
            'pct':   round(float(mask.sum()) / len(density) * 100, 1),
            'effective_n_contribution': float(uniqueness_weight[mask].sum()),
            'mean_density': float(density[mask].mean())    if mask.any() else 0.0,
            'mean_lid':     float(lid_per_clip[mask].mean()) if mask.any() else 0.0,
        }
    np.save(P('quadrant_assignment.npy'), quadrant)
    with open(P('quadrant_profile.json'), 'w') as f:
        json.dump({str(q): v for q, v in quadrant_profile.items()}, f, indent=2)

    # Q4 고립 진단
    r_max_dist_all    = 1.0 - knn_sim[:, 19]
    q4_isolated_count = int(((quadrant == 4) & (r_max_dist_all > ISOLATION_THRESHOLD)).sum())

    thresholds = {
        'density_threshold':          density_threshold,
        'lid_threshold':              lid_threshold,
        'density_gmm_best_k':         d_best_k,
        'lid_gmm_best_k':             l_best_k,
        'density_bics':               {str(k): round(v, 1) for k, v in d_bics.items()},
        'lid_bics':                   {str(k): round(v, 1) for k, v in l_bics.items()},
        'lid_threshold_unimodal':     l_best_k == 1,
        'density_threshold_unimodal': d_best_k == 1,
        'q4_isolated_clip_count':     q4_isolated_count,
        'q4_isolation_threshold':     ISOLATION_THRESHOLD,
    }
    with open(P('thresholds.json'), 'w') as f:
        json.dump(thresholds, f, indent=2)

    # 경계 구역 정량화 — 0-D-val 트리거 기준
    lid_margin        = (lid_per_clip - lid_threshold) / max(lid_threshold, 1.0)
    lid_boundary_zone = (np.abs(lid_margin) < BOUNDARY_MARGIN_LID) & lid_reliable & ~high_d
    np.save(P('lid_margin.npy'),        lid_margin)
    np.save(P('lid_boundary_zone.npy'), lid_boundary_zone)

    _q3_boundary = int(((quadrant == 3) & lid_boundary_zone).sum())
    _q3_total    = int((quadrant == 3).sum())
    thresholds.update({
        'q3_boundary_count': _q3_boundary,
        'q3_total_count':    _q3_total,
        'q3_boundary_rate':  round(_q3_boundary / max(_q3_total, 1), 4),
    })
    with open(P('thresholds.json'), 'w') as f:
        json.dump(thresholds, f, indent=2)

    # k-민감도 GMM 기반 재계산 (0-C는 중앙값 근사, 여기서 확정값으로 보정)
    lid_k15 = np.load(P('lid_k15.npy'))
    lid_k25 = np.load(P('lid_k25.npy'))
    flip_any_gmm = (
        ((lid_per_clip < lid_threshold) & (lid_k15 >= lid_threshold) |
         (lid_per_clip < lid_threshold) & (lid_k25 >= lid_threshold))
        & ~high_d & lid_reliable
    )
    k_sensitive_gmm = float(flip_any_gmm.mean())

    lid_stats = json.load(open(P('lid_stats.json')))
    lid_stats['k_sensitive_rate_approx'] = lid_stats.get('k_sensitive_rate', None)
    lid_stats['k_sensitive_rate']        = round(k_sensitive_gmm, 4)
    lid_stats['flipd_recommended']       = bool(k_sensitive_gmm > K_SENSITIVE_THRESHOLD)
    lid_stats['k_sensitive_rate_source'] = 'GMM BIC 교차점 기반 (0-D 확정 임계값)'
    with open(P('lid_stats.json'), 'w') as f:
        json.dump(lid_stats, f, indent=2)

    q_counts = {q: quadrant_profile[q]['count'] for q in range(6)}
    print(f"[0-D] 임계값: density={density_threshold:.4f}(K={d_best_k}), "
          f"lid={lid_threshold:.4f}(K={l_best_k})")
    print(f"  6-분류: {q_counts}")
    print(f"  Q3 경계 구역: {_q3_boundary}/{_q3_total} "
          f"({_q3_boundary/max(_q3_total,1):.1%}), "
          f"k-민감도={k_sensitive_gmm:.4f}")


if __name__ == '__main__':
    run()
