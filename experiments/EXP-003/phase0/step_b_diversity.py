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
from scipy.stats import spearmanr
from config import (K_UNIQUENESS, K_DENSITY, VENDI_ANCHOR_GLOBAL,
                    VENDI_MAX_RUNS, ODD_DIR, ODD_DIMS, ODD_SPEARMAN_PAIRS)
from utils import (P, require_files, already_done, load_odd_compat, odd_diversity_stats,
                   _vendi_once, _vendi_until_stable)


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

    # ── ODD 사전 로딩 (Vendi topk pool 분석에서 재사용) ─────────────
    clip_ids = list(np.load(P('clip_ids.npy'), allow_pickle=True))
    odd_recs = load_odd_compat(clip_ids, ODD_DIR)

    # ── Vendi Score — 세 가지 앵커 전략 ─────────────────────────────
    # 1) Random: 균등 샘플링 — 현재 분포 그대로 (훈련 시 모델이 받는 신호)
    print("  [Vendi-random] 균등 샘플링 수렴 중...")
    v_random, _random_scores, _random_anchors = _vendi_until_stable(
        embeddings_f32, VENDI_ANCHOR_GLOBAL, rng, p=None)

    # 2) Dedup: 중요도 샘플링 ∝ uniqueness_weight — 중복 제거 후 분포
    print("  [Vendi-dedup]  중요도 샘플링 수렴 중...")
    probs    = uniqueness_weight / uniqueness_weight.sum()
    v_dedup, _dedup_scores, _dedup_anchors = _vendi_until_stable(
        embeddings_f32, VENDI_ANCHOR_GLOBAL, rng, p=probs)

    # 3) Top-K: 고유성 상위 Effective_N개 풀에서 앵커 선택
    #    풀 크기 = ceil(effective_N), 앵커 수 = VENDI_ANCHOR_GLOBAL
    #    풀 ≤ 앵커수: 풀 전체 사용 → 결정적 (1회)
    #    풀 > 앵커수: 풀 안에서 균등 무작위 샘플링 → Sequential stopping
    pool_size = min(len(embeddings_f32), int(np.ceil(effective_N)))
    pool_idx  = np.argsort(uniqueness_weight)[-pool_size:]
    pool_emb  = embeddings_f32[pool_idx]
    odd_topk_stats = odd_diversity_stats([odd_recs[i] for i in pool_idx], ODD_DIMS)
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
        _topk_scores  = [v_topk['mean']]
        _topk_anchors = [pool_idx]          # 풀 전체 = 글로벌 인덱스
    else:
        # 풀이 앵커 수보다 큼 → 풀 안에서 균등 샘플링 반복
        v_topk, _topk_scores, _topk_local = _vendi_until_stable(
            pool_emb, VENDI_ANCHOR_GLOBAL, rng, p=None)
        v_topk['pool_size'] = pool_size
        v_topk['mode']      = 'sampled'
        _topk_anchors = [pool_idx[local_idx] for local_idx in _topk_local]

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
    # ── ODD 다양성 분석 ───────────────────────────────────────────
    print("  [ODD] ODD 다양성 분석 중...")
    odd_stats = odd_diversity_stats(odd_recs, ODD_DIMS)

    # 임베딩–ODD 정렬 검증: Spearman(ODD Hamming거리, 코사인거리)
    # rho>0.3→정렬, 0.1~0.3→부분, <0.1→미정렬(Vendi가 ODD 다양성 ≠ 임베딩 다양성)
    valid_idx = np.array([i for i, r in enumerate(odd_recs) if r is not None])
    if len(valid_idx) >= 100:
        rng2 = np.random.default_rng(99)
        n_v  = len(valid_idx)
        pi_a = rng2.choice(n_v, ODD_SPEARMAN_PAIRS * 2, replace=True)
        pi_b = rng2.choice(n_v, ODD_SPEARMAN_PAIRS * 2, replace=True)
        keep = (pi_a != pi_b)
        pi_a, pi_b = pi_a[keep][:ODD_SPEARMAN_PAIRS], pi_b[keep][:ODD_SPEARMAN_PAIRS]
        # ODD Hamming 거리 (string 비교)
        odd_mat = np.array([[odd_recs[vi].get(d, 'unknown') for d in ODD_DIMS]
                             for vi in valid_idx], dtype=object)
        ham_dist = (odd_mat[pi_a] != odd_mat[pi_b]).mean(axis=1).astype(float)
        # 임베딩 코사인 거리
        emb_v    = embeddings_f32[valid_idx]
        cos_dist = 1.0 - (emb_v[pi_a] * emb_v[pi_b]).sum(axis=1)
        rho, pval = spearmanr(ham_dist, cos_dist)
        interp = 'aligned' if rho > 0.3 else ('partial' if rho > 0.1 else 'misaligned')
        odd_stats['embedding_odd_alignment'] = {
            'spearman_rho':  round(float(rho), 4),
            'p_value':       round(float(pval), 6),
            'n_pairs':       int(len(pi_a)),
            'interpretation': interp,
        }
    result['odd_diversity'] = odd_stats
    result['odd_topk_diversity'] = odd_topk_stats  # 고유성 상위 클립 ODD 분포

    # ── Per-run Vendi vs ODD entropy 정렬 검증 (3전략) ─────────────
    # Vendi 수렴은 5회에서 끝나지만, ODD 정렬 분석은 VENDI_MAX_RUNS까지 추가 샘플링
    # Vendi 계산 자체는 변경 없음 — 추가 샘플은 ODD 정렬 분석 전용
    print("  [Vendi-ODD run 정렬] per-run 상관 계산 중...")

    def _run_alignment(scores, anchors, extra_sampler):
        """Vendi runs에서 수집한 앵커 + 추가 샘플링으로 VENDI_MAX_RUNS까지 확장"""
        all_scores  = list(scores)
        all_anchors = list(anchors)
        while len(all_scores) < VENDI_MAX_RUNS:
            v, idx = extra_sampler()
            all_scores.append(v)
            all_anchors.append(idx)
        odd_entropy = [
            odd_diversity_stats([odd_recs[i] for i in idx], ODD_DIMS)
            .get('mean_norm_entropy', 0.0)
            for idx in all_anchors
        ]
        entry = {
            'per_run_vendi':       [round(v, 4) for v in all_scores],
            'per_run_odd_entropy': [round(e, 4) for e in odd_entropy],
            'n_runs':              len(all_scores),
        }
        if len(set(odd_entropy)) > 1:
            rho, pval = spearmanr(all_scores, odd_entropy)
            entry['spearman_rho'] = round(float(rho), 4)
            entry['p_value']      = round(float(pval), 6)
        else:
            entry['spearman_rho'] = None
            entry['p_value']      = None
        return entry

    def _sample_random():
        idx = rng.choice(len(embeddings_f32), VENDI_ANCHOR_GLOBAL, replace=False)
        return _vendi_once(embeddings_f32[idx]), idx

    def _sample_dedup():
        idx = rng.choice(len(embeddings_f32), VENDI_ANCHOR_GLOBAL, replace=False, p=probs)
        return _vendi_once(embeddings_f32[idx]), idx

    def _sample_topk():
        li = rng.choice(len(pool_emb), VENDI_ANCHOR_GLOBAL, replace=False)
        return _vendi_once(pool_emb[li]), pool_idx[li]

    result['vendi_odd_run_alignment'] = {
        'random': _run_alignment(_random_scores, _random_anchors, _sample_random),
        'dedup':  _run_alignment(_dedup_scores,  _dedup_anchors,  _sample_dedup),
        'topk':   _run_alignment(_topk_scores,   _topk_anchors,   _sample_topk),
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
    align = odd_stats.get('embedding_odd_alignment', {})
    print(f"  ODD 전체    : 고유조합={odd_stats.get('n_unique_combos', 'N/A')}, "
          f"mean_norm_entropy={odd_stats.get('mean_norm_entropy', 'N/A')}")
    print(f"  ODD topk    : 고유조합={odd_topk_stats.get('n_unique_combos', 'N/A')}, "
          f"mean_norm_entropy={odd_topk_stats.get('mean_norm_entropy', 'N/A')} "
          f"(pool={pool_size}개)")
    print(f"  임베딩↔ODD 정렬: {align.get('interpretation', 'N/A')} "
          f"(ρ={align.get('spearman_rho', 'N/A')})")
    ra = result['vendi_odd_run_alignment']
    for strategy in ('random', 'dedup', 'topk'):
        r = ra[strategy]
        print(f"  Vendi-ODD run [{strategy:6s}]: ρ={r.get('spearman_rho', 'N/A')} "
              f"(n={r['n_runs']}runs)")
        print(f"    vendi : {r['per_run_vendi']}")
        print(f"    ODD H : {r['per_run_odd_entropy']}")


if __name__ == '__main__':
    run()
