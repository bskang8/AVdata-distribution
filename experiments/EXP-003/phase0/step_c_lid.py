"""0-C: Local Intrinsic Dimensionality (LID) + 신뢰도 + k-민감도
희소 영역이 "다양한 변주 미수집"인지 "본질적 단조"인지 구분.
k-민감도: k=15/20/25 비교로 MLE 안정성 정량화 → 0-D-val 트리거 신호.
"""

import json
import numpy as np
from config import K_LID, LID_RELIABLE_RMAX, K_SENSITIVE_THRESHOLD
from utils import P, require_files, compute_lid_mle, already_done


def run(force=False):
    if not force and already_done('0-C', 'lid_per_clip.npy', 'lid_stats.json'):
        return
    require_files('knn_foundation.npz', 'density_per_clip.npy', step='step_b_diversity.py')
    print("[0-C] LID + 신뢰도 + k-민감도 시작")

    knn_sim      = np.load(P('knn_foundation.npz'))['knn_sim']
    density      = np.load(P('density_per_clip.npy'))

    lid_per_clip = compute_lid_mle(knn_sim, k_lid=K_LID)
    lid_quartile = np.digitize(lid_per_clip, np.percentile(lid_per_clip, [25, 50, 75]))

    # LID 신뢰도: k번째 이웃이 너무 멀면 log 비율 분산 폭발
    r_max_dist  = 1.0 - knn_sim[:, K_LID - 1]
    lid_reliable = r_max_dist < LID_RELIABLE_RMAX

    lid_stats = {
        'mean':               float(lid_per_clip.mean()),
        'median':             float(np.median(lid_per_clip)),
        'p10':                float(np.percentile(lid_per_clip, 10)),
        'p90':                float(np.percentile(lid_per_clip, 90)),
        'lid_reliable_ratio': round(float(lid_reliable.mean()), 3),
    }

    # k-민감도: k=15/25로 재계산 후 k=20 기준 분류와 얼마나 다른지 측정
    # 0-D GMM 확정 전 중앙값을 임시 임계값으로 사용 (0-D에서 정확한 값으로 재계산됨)
    lid_k15 = compute_lid_mle(knn_sim, k_lid=15)
    lid_k25 = compute_lid_mle(knn_sim, k_lid=25)
    np.save(P('lid_k15.npy'), lid_k15)
    np.save(P('lid_k25.npy'), lid_k25)

    lid_approx_thresh = float(np.median(lid_per_clip))
    den_approx_thresh = float(np.median(density))
    low_d_approx      = density < den_approx_thresh

    flip_k15  = (lid_per_clip < lid_approx_thresh) & (lid_k15 >= lid_approx_thresh)
    flip_k25  = (lid_per_clip < lid_approx_thresh) & (lid_k25 >= lid_approx_thresh)
    flip_any  = (flip_k15 | flip_k25) & low_d_approx & lid_reliable
    k_sensitive_rate = float(flip_any.mean())

    lid_stats['k_sensitive_rate']  = round(k_sensitive_rate, 4)
    lid_stats['flipd_recommended'] = bool(k_sensitive_rate > K_SENSITIVE_THRESHOLD)
    lid_stats['k_sensitivity_note'] = (
        'k_sensitive_rate < 0.02 → MLE 충분, 0-D-val 생략 가능'
        if k_sensitive_rate < 0.02 else
        '0.02~0.05 → 0-D-val 실행 후 q3_boundary_rate 확인 권고'
        if k_sensitive_rate < K_SENSITIVE_THRESHOLD else
        'k_sensitive_rate > 0.05 → 0-D-val FLIPD 실행 필요'
    )

    np.save(P('lid_per_clip.npy'), lid_per_clip)
    np.save(P('lid_quartile.npy'), lid_quartile)
    np.save(P('lid_reliable.npy'), lid_reliable)
    with open(P('lid_stats.json'), 'w') as f:
        json.dump(lid_stats, f, indent=2)

    print(f"[0-C] median LID={lid_stats['median']:.2f}, "
          f"신뢰 비율={lid_stats['lid_reliable_ratio']:.1%}, "
          f"k-민감도={k_sensitive_rate:.4f} "
          f"→ flipd_recommended={lid_stats['flipd_recommended']}")


if __name__ == '__main__':
    run()
