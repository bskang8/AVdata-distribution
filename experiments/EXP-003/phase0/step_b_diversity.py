"""0-B: Effective N + Vendi Score + 연속 밀도장
Effective N(SoftDedup): 중복 보정 독립 클립 수
Vendi Score(Nyström): 고유값 스펙트럼 기반 다양성 차원 수
"""

import json
import numpy as np
from config import K_UNIQUENESS, K_DENSITY, VENDI_ANCHOR_GLOBAL
from utils import P, require_files, already_done


def run(force=False):
    if not force and already_done('0-B', 'diversity_profile.json', 'density_per_clip.npy'):
        return
    require_files('knn_foundation.npz', 'embeddings.npy', step='step_a_knn.py')
    print("[0-B] Effective N + Vendi Score + 밀도장 시작")

    knn_sim        = np.load(P('knn_foundation.npz'))['knn_sim']
    embeddings_f32 = np.load(P('embeddings.npy'))

    # Effective N (Yao et al. ACL 2024 SoftDedup)
    soft_commonness  = knn_sim[:, :K_UNIQUENESS].mean(axis=1)
    uniqueness_weight = np.clip(1.0 - soft_commonness, 0, 1)
    effective_N      = float(uniqueness_weight.sum())

    near_dup_hard    = (knn_sim[:, :K_UNIQUENESS] > 0.95).sum(axis=1)
    uniqueness_hard  = 1.0 / (1.0 + near_dup_hard.astype(float))
    effective_N_hard = float(uniqueness_hard.sum())

    # Vendi Score (Friedman & Dieng, TMLR 2023) — Nyström 근사
    rng        = np.random.default_rng(42)
    anchor_idx = rng.choice(len(embeddings_f32), VENDI_ANCHOR_GLOBAL, replace=False)
    anchors    = embeddings_f32[anchor_idx]
    K_mm       = (anchors @ anchors.T).astype(np.float64)
    eigenvalues = np.maximum(np.linalg.eigvalsh(K_mm), 0)
    ev_norm     = eigenvalues / (eigenvalues.sum() + 1e-12)
    vendi_score = float(np.exp(-np.sum(ev_norm * np.log(ev_norm + 1e-12))))

    # 연속 밀도장: k=K_DENSITY 평균 유사도
    local_density    = knn_sim[:, :K_DENSITY].mean(axis=1)
    density_quartile = np.digitize(local_density, np.percentile(local_density, [25, 50, 75]))

    result = {
        'effective_N_soft':      effective_N,
        'effective_N_hard':      effective_N_hard,
        'redundancy_ratio':      round(1 - effective_N / len(knn_sim), 4),
        'grey_zone_contribution': round(effective_N - effective_N_hard, 1),
        'vendi_score':           vendi_score,
        'vendi_diversity_ratio': round(vendi_score / len(knn_sim), 5),
        'density_p10':           float(np.percentile(local_density, 10)),
        'density_median':        float(np.median(local_density)),
        'density_p75':           float(np.percentile(local_density, 75)),
    }
    with open(P('diversity_profile.json'), 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    np.save(P('density_per_clip.npy'),  local_density)
    np.save(P('density_quartile.npy'),  density_quartile)
    np.save(P('uniqueness_weight.npy'), uniqueness_weight)

    print(f"[0-B] Effective N={effective_N:.0f} (중복률={result['redundancy_ratio']:.1%}), "
          f"Vendi={vendi_score:.1f}")


if __name__ == '__main__':
    run()
