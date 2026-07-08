"""0-D-val: Targeted FLIPD 검증 [조건부]
실행 조건: k_sensitive_rate > 0.05 OR q3_boundary_rate > 0.3
Q3 중 lid_boundary_zone 클립만 FLIPD 재추정 → 필요 시 Q3→Q2 재분류.
SKIP 포함 항상 flipd_validation.json 기록.
"""

import json
import numpy as np
from config import K_SENSITIVE_THRESHOLD, Q3_BOUNDARY_THRESHOLD
from utils import P, require_files, compute_lid_mle, already_done


def _compute_flipd(knn_dist, k=20):
    """Cresswell et al. (NeurIPS 2024 FLIPD) — Poisson 과정 경계 보정 LID.
    boundary_correction = 1 + (2/k) Σ_j [ j * (r_j/r_k)^mle ]
    반환: (flipd_lid, mle_lid)
    """
    r     = knn_dist
    r_k   = r[:, -1:] + 1e-10
    log_r = np.log(r / r_k + 1e-10)
    mle   = np.clip(-1.0 / (log_r.mean(axis=1) + 1e-10), 1.0, 50.0)
    j_arr = np.arange(1, k + 1, dtype=float)
    bc    = 1.0 + (2.0/k) * np.sum(j_arr * (r/r_k)**mle.reshape(-1, 1), axis=1)
    return np.clip(mle * bc, 1.0, 200.0), mle


def run(force=False):
    if not force and already_done('0-E-val', 'flipd_validation.json'):
        return
    require_files(
        'lid_stats.json', 'thresholds.json',
        'quadrant_assignment.npy', 'lid_boundary_zone.npy', 'knn_foundation.npz',
        step='step_d_quadrant.py',
    )
    print("[0-E-val] FLIPD 조건 확인")

    lid_stats  = json.load(open(P('lid_stats.json')))
    thresholds = json.load(open(P('thresholds.json')))
    flipd_needed = (
        lid_stats.get('flipd_recommended', False) or
        thresholds.get('q3_boundary_rate', 0.0) > Q3_BOUNDARY_THRESHOLD
    )

    if not flipd_needed:
        print(f"  SKIP: k_sensitive_rate={lid_stats.get('k_sensitive_rate'):.4f} ≤ {K_SENSITIVE_THRESHOLD}, "
              f"q3_boundary_rate={thresholds.get('q3_boundary_rate',0):.4f} ≤ {Q3_BOUNDARY_THRESHOLD}")
        with open(P('flipd_validation.json'), 'w') as f:
            json.dump({
                'flipd_applied':    False,
                'skip_reason':      f'k_sensitive_rate ≤ {K_SENSITIVE_THRESHOLD} and '
                                    f'q3_boundary_rate ≤ {Q3_BOUNDARY_THRESHOLD}',
                'k_sensitive_rate': lid_stats.get('k_sensitive_rate'),
                'q3_boundary_rate': thresholds.get('q3_boundary_rate'),
            }, f, indent=2)
        return

    print(f"  실행: flipd_recommended={lid_stats.get('flipd_recommended')}, "
          f"q3_boundary_rate={thresholds.get('q3_boundary_rate',0):.4f}")

    quadrant          = np.load(P('quadrant_assignment.npy'))
    lid_boundary_zone = np.load(P('lid_boundary_zone.npy'))
    knn_sim_all       = np.load(P('knn_foundation.npz'))['knn_sim']
    lid_threshold     = thresholds['lid_threshold']

    # Q3 + 경계 구역만 대상 (비용 최소화)
    target_mask    = (quadrant == 3) & lid_boundary_zone
    target_indices = np.where(target_mask)[0]
    print(f"  FLIPD 대상: {len(target_indices)}개 "
          f"({len(target_indices)/len(quadrant):.1%}, "
          f"Q3의 {len(target_indices)/max(int((quadrant==3).sum()),1):.1%})")

    # 원본 83k 공간 kNN 슬라이싱 — 재계산 없이 전체 공간 맥락 유지
    knn_dist_target = 1.0 - knn_sim_all[target_indices, :20]
    flipd_lid, mle_lid = _compute_flipd(knn_dist_target, k=20)

    upgraded_mask   = flipd_lid >= lid_threshold
    upgrade_rate    = float(upgraded_mask.mean())
    upgraded_global = target_indices[upgraded_mask]

    result = {
        'flipd_applied':           True,
        'target_clip_count':       len(target_indices),
        'upgraded_count':          int(upgraded_mask.sum()),
        'upgrade_rate':            round(upgrade_rate, 4),
        'median_flipd_correction': round(float(np.median(flipd_lid - mle_lid)), 4),
        'recommended_action': (
            'quadrant 변경 없음 — MLE 분류 안정' if upgrade_rate < 0.05 else
            'Q3→Q2 재분류 반영 권고'              if upgrade_rate < 0.15 else
            'lid_threshold 하향 보정 검토 + Q3→Q2 재분류'
        ),
        'quadrant_updated': upgrade_rate >= 0.05,
    }

    if upgrade_rate >= 0.05:
        np.save(P('quadrant_assignment_pre_flipd.npy'), quadrant.copy())
        quadrant[upgraded_global] = 2
        np.save(P('quadrant_assignment.npy'), quadrant)
        np.save(P('flipd_upgraded_clips.npy'), upgraded_global)
        print(f"  quadrant 업데이트: {len(upgraded_global)}개 Q3→Q2")

    with open(P('flipd_validation.json'), 'w') as f:
        json.dump(result, f, indent=2)
    print(f"[0-E-val] upgrade_rate={upgrade_rate:.3f} → {result['recommended_action']}")


if __name__ == '__main__':
    run()
