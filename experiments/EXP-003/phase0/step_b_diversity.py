"""0-B: Effective N + Vendi Score + 연속 밀도장
Effective N(SoftDedup): 중복 보정 독립 클립 수
Vendi Score(Nyström): 세 가지 앵커 전략으로 다양성 차원 수 추정
  - vendi_random : 균등 무작위 샘플링 — 현재 분포 그대로
  - vendi_dedup  : 중요도 샘플링(∝ uniqueness_weight) — 중복 제거 후 분포
  - vendi_topk   : 고유성 상위 Effective_N개 풀에서 샘플링 — 상한 추정
    * Effective_N ≤ anchor수: 풀 전체 사용 → 결정적 (1회)
    * Effective_N > anchor수: 풀 안에서 균등 샘플링 → Sequential stopping
반복 횟수: Sequential Stopping Rule (Law & Kelton 2000) 로 자동 결정.
"""

import json
import numpy as np
from config import (K_UNIQUENESS, K_DENSITY, VENDI_ANCHOR_GLOBAL,
                    VENDI_MIN_RUNS, VENDI_MAX_RUNS, VENDI_TARGET_CV)
from utils import P, require_files, already_done


def _vendi_once(anchors):
    """단일 앵커 세트에서 Vendi Score 계산"""
    K  = anchors.astype(np.float64) @ anchors.astype(np.float64).T
    ev = np.maximum(np.linalg.eigvalsh(K), 0)
    p  = ev / (ev.sum() + 1e-12)
    return float(np.exp(-np.sum(p * np.log(p + 1e-12))))


def _vendi_until_stable(embeddings, n_anchor, rng, p=None):
    """Sequential Stopping Rule — Law & Kelton (2000)
    평균의 상대 표준오차(SE/mean)가 VENDI_TARGET_CV 미만이 되면 중단.
    p=None: 균등 샘플링 / p=weights: 중요도 샘플링
    """
    scores = []
    for _ in range(VENDI_MAX_RUNS):
        idx = rng.choice(len(embeddings), n_anchor, replace=False, p=p)
        scores.append(_vendi_once(embeddings[idx]))
        if len(scores) >= VENDI_MIN_RUNS:
            se_of_mean = np.std(scores, ddof=1) / np.sqrt(len(scores))
            if se_of_mean / (np.mean(scores) + 1e-10) < VENDI_TARGET_CV:
                break
    arr = np.array(scores)
    return {
        'mean':      round(float(arr.mean()), 3),
        'std':       round(float(arr.std(ddof=1)), 3),
        'cv':        round(float(arr.std(ddof=1) / (arr.mean() + 1e-10)), 4),
        'n_runs':    len(scores),
        'converged': len(scores) < VENDI_MAX_RUNS,
    }


def run(force=False):
    if not force and already_done('0-B', 'diversity_profile.json', 'density_per_clip.npy'):
        return
    require_files('knn_foundation.npz', 'embeddings.npy', step='step_a_knn.py')
    print("[0-B] Effective N + Vendi Score + 밀도장 시작")

    knn_sim        = np.load(P('knn_foundation.npz'))['knn_sim']
    embeddings_f32 = np.load(P('embeddings.npy'))
    rng            = np.random.default_rng(42)

    # ── Effective N (Yao et al. ACL 2024 SoftDedup) ──────────────────
    soft_commonness   = knn_sim[:, :K_UNIQUENESS].mean(axis=1)
    uniqueness_weight = np.clip(1.0 - soft_commonness, 0, 1)
    effective_N       = float(uniqueness_weight.sum())

    near_dup_hard    = (knn_sim[:, :K_UNIQUENESS] > 0.95).sum(axis=1)
    uniqueness_hard  = 1.0 / (1.0 + near_dup_hard.astype(float))
    effective_N_hard = float(uniqueness_hard.sum())

    # ── Vendi Score — 세 가지 앵커 전략 ─────────────────────────────
    # 1) Random: 균등 샘플링 — 현재 분포 그대로 (훈련 시 모델이 받는 신호)
    print("  [Vendi-random] 균등 샘플링 수렴 중...")
    v_random = _vendi_until_stable(embeddings_f32, VENDI_ANCHOR_GLOBAL, rng, p=None)

    # 2) Dedup: 중요도 샘플링 ∝ uniqueness_weight — 중복 제거 후 분포
    print("  [Vendi-dedup]  중요도 샘플링 수렴 중...")
    probs    = uniqueness_weight / uniqueness_weight.sum()
    v_dedup  = _vendi_until_stable(embeddings_f32, VENDI_ANCHOR_GLOBAL, rng, p=probs)

    # 3) Top-K: 고유성 상위 Effective_N개 풀에서 앵커 선택
    #    풀 크기 = ceil(effective_N), 앵커 수 = VENDI_ANCHOR_GLOBAL
    #    풀 ≤ 앵커수: 풀 전체 사용 → 결정적 (1회)
    #    풀 > 앵커수: 풀 안에서 균등 무작위 샘플링 → Sequential stopping
    pool_size = min(len(embeddings_f32), int(np.ceil(effective_N)))
    pool_idx  = np.argsort(uniqueness_weight)[-pool_size:]
    pool_emb  = embeddings_f32[pool_idx]
    print(f"  [Vendi-topk]   고유 풀={pool_size}개 "
          f"({'결정적' if pool_size <= VENDI_ANCHOR_GLOBAL else '반복 샘플링'}) 수렴 중...")
    if pool_size <= VENDI_ANCHOR_GLOBAL:
        # 풀 전체가 앵커 수 이하 → 전부 사용, 분산 없음
        v_topk = {'mean':      round(_vendi_once(pool_emb), 3),
                  'std':       0.0,
                  'cv':        0.0,
                  'n_runs':    1,
                  'converged': True,
                  'pool_size': pool_size,
                  'mode':      'deterministic'}
    else:
        # 풀이 앵커 수보다 큼 → 풀 안에서 균등 샘플링 반복
        v_topk = _vendi_until_stable(pool_emb, VENDI_ANCHOR_GLOBAL, rng, p=None)
        v_topk['pool_size'] = pool_size
        v_topk['mode']      = 'sampled'

    suppression_ratio = round(v_dedup['mean'] / (v_random['mean'] + 1e-10), 3)

    # ── 연속 밀도장: k=K_DENSITY 평균 유사도 ────────────────────────
    local_density    = knn_sim[:, :K_DENSITY].mean(axis=1)
    density_quartile = np.digitize(local_density, np.percentile(local_density, [25, 50, 75]))

    result = {
        'effective_N_soft':       effective_N,
        'effective_N_hard':       effective_N_hard,
        'redundancy_ratio':       round(1 - effective_N / len(knn_sim), 4),
        'grey_zone_contribution': round(effective_N - effective_N_hard, 1),
        # Vendi 세 가지 전략
        'vendi_random':           v_random,   # 현재 분포 — 균등 샘플링
        'vendi_dedup':            v_dedup,    # 중복 제거 후 — 중요도 샘플링
        'vendi_topk':             v_topk,     # 고유성 상위 Effective_N 풀 앵커
        'vendi_suppression_ratio': suppression_ratio,  # dedup/random 비율
        # 하위 호환용 (기존 코드가 참조하는 키)
        'vendi_score':            v_random['mean'],
        'vendi_diversity_ratio':  round(v_random['mean'] / len(knn_sim), 5),
        'density_p10':            float(np.percentile(local_density, 10)),
        'density_median':         float(np.median(local_density)),
        'density_p75':            float(np.percentile(local_density, 75)),
    }
    with open(P('diversity_profile.json'), 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    np.save(P('density_per_clip.npy'),  local_density)
    np.save(P('density_quartile.npy'),  density_quartile)
    np.save(P('uniqueness_weight.npy'), uniqueness_weight)

    print(f"[0-B] Effective N={effective_N:.0f} (중복률={result['redundancy_ratio']:.1%})")
    print(f"  Vendi random : {v_random['mean']:.3f} ± {v_random['std']:.3f} "
          f"(n={v_random['n_runs']}, converged={v_random['converged']})")
    print(f"  Vendi dedup  : {v_dedup['mean']:.3f} ± {v_dedup['std']:.3f} "
          f"(n={v_dedup['n_runs']}, converged={v_dedup['converged']})")
    topk_info = (f"{v_topk['mean']:.3f} ± {v_topk['std']:.3f} "
                 f"(n={v_topk['n_runs']}, pool={v_topk['pool_size']}, {v_topk['mode']})")
    print(f"  Vendi topk   : {topk_info}")
    print(f"  억압 계수(dedup/random): {suppression_ratio:.3f}")


if __name__ == '__main__':
    run()
