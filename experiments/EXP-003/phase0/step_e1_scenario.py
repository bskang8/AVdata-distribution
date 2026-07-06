"""0-E-1: 전체 시나리오 의미 지도 (TF-IDF 공간, 83k 전체)
임베딩 공간(0-D)과 독립적인 TF-IDF 공간에서 K-Means 클러스터링.
사분면(기하학) × 시나리오(의미) 교차표로 진정한 새 정보 생성.
"""

import json
import numpy as np
import joblib
from config import (VENDI_ANCHOR_SCENARIO, SIL_K_CANDIDATES, SIL_FLAT_THRESHOLD,
                    K_SCENARIO_FALLBACK, MIN_HEALTHY_SIZE, MIN_Q0_PCT,
                    BOUNDARY_MARGIN_SCENARIO, Q5_CONCENTRATION_MULT, PRUNE_DOMINANT_MULT,
                    VENDI_MIN_RUNS, VENDI_MAX_RUNS, VENDI_TARGET_CV, VENDI_SUPPRESSION_HIGH,
                    ODD_DIR, ODD_DIMS)
from utils import (P, require_files, load_captions, already_done,
                   load_odd_compat, odd_diversity_stats)


def _vendi_stable(embeddings, weights, n_anchor, rng):
    """시나리오 내 random + dedup Vendi — Sequential Stopping Rule"""
    n = len(embeddings)

    def _once(idx):
        anc = embeddings[idx].astype(np.float64)
        K = anc @ anc.T
        ev = np.maximum(np.linalg.eigvalsh(K), 0)
        p = ev / (ev.sum() + 1e-12)
        return float(np.exp(-np.sum(p * np.log(p + 1e-12))))

    if n <= n_anchor:
        v = _once(np.arange(n))
        entry = {'mean': round(v, 3), 'std': 0.0, 'cv': 0.0, 'n_runs': 1, 'converged': True}
        return entry, entry

    def _run(p=None):
        scores = []
        for _ in range(VENDI_MAX_RUNS):
            idx = rng.choice(n, n_anchor, replace=False, p=p)
            scores.append(_once(idx))
            if len(scores) >= VENDI_MIN_RUNS:
                se = np.std(scores, ddof=1) / np.sqrt(len(scores))
                if se / (np.mean(scores) + 1e-10) < VENDI_TARGET_CV:
                    break
        arr = np.array(scores)
        return {'mean':      round(float(arr.mean()), 3),
                'std':       round(float(arr.std(ddof=1)), 3),
                'cv':        round(float(arr.std(ddof=1) / (arr.mean() + 1e-10)), 4),
                'n_runs':    len(scores),
                'converged': len(scores) < VENDI_MAX_RUNS}

    probs = weights / (weights.sum() + 1e-10)
    return _run(p=None), _run(p=probs)


def _prune_flag(q1_pct, q5_pct, vendi, median_vendi,
                prune_thresh, q5_thresh):
    prune_signal = q1_pct + q5_pct
    if prune_signal <= prune_thresh:
        return None
    if q5_pct > q5_thresh and vendi > median_vendi:
        return 'CAUTION'
    if q5_pct > q5_thresh:
        return 'Q5_UNCERTAIN'
    if vendi > median_vendi:
        return 'CAUTION'
    return 'OK'


def _caution_note(flag, q5_pct, q5_thresh):
    if flag == 'Q5_UNCERTAIN':
        return 'Q5 비율 집중 — LID 불신뢰. PRUNE 확정 불가. 수동 검토 필요.'
    if flag == 'CAUTION' and q5_pct > q5_thresh:
        return 'Q5 집중 + Vendi 높음 — LID 불신뢰 + 다양성 불일치. 반드시 수동 검토.'
    return 'Q1 우세이지만 Vendi 높음 — 임베딩 단조 vs 내부 다양성 불일치. 수동 검토.'


def run(force=False):
    if not force and already_done('0-E-1', 'scenario_profiles.json', 'scenario_labels.npy'):
        return
    require_files(
        'quadrant_assignment.npy', 'quadrant_profile.json', 'thresholds.json',
        'uniqueness_weight.npy', 'density_per_clip.npy', 'density_quartile.npy',
        'lid_per_clip.npy', 'lid_quartile.npy', 'lid_reliable.npy',
        'embeddings.npy', 'clip_ids.npy',
        step='step_d_quadrant.py',
    )
    print("[0-E-1] 시나리오 의미 지도 시작")

    captions, _ = load_captions()
    clip_ids     = list(np.load(P('clip_ids.npy'), allow_pickle=True))
    odd_recs     = load_odd_compat(clip_ids, ODD_DIR)

    quadrant          = np.load(P('quadrant_assignment.npy'))
    uniqueness_weight = np.load(P('uniqueness_weight.npy'))
    density_per_clip  = np.load(P('density_per_clip.npy'))
    density_quartile  = np.load(P('density_quartile.npy'))
    lid_per_clip      = np.load(P('lid_per_clip.npy'))
    lid_quartile      = np.load(P('lid_quartile.npy'))
    lid_reliable      = np.load(P('lid_reliable.npy'))
    embeddings_f32    = np.load(P('embeddings.npy'))

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    from sklearn.metrics import (silhouette_score,
                                  normalized_mutual_info_score,
                                  adjusted_rand_score)

    tfidf_e1     = TfidfVectorizer(max_features=3000, ngram_range=(1, 2),
                                    stop_words='english', min_df=3)
    X_tfidf      = tfidf_e1.fit_transform(captions)
    feature_names = np.array(tfidf_e1.get_feature_names_out())

    # K 실루엣 검증
    best_models, sil_scores = {}, {}
    for k_try in SIL_K_CANDIDATES:
        km = KMeans(n_clusters=k_try, random_state=42, n_init=10).fit(X_tfidf)
        sil_scores[k_try] = silhouette_score(X_tfidf, km.labels_,
                                              sample_size=5000, random_state=42)
        best_models[k_try] = km
    sil_range = max(sil_scores.values()) - min(sil_scores.values())
    flat_fallback = sil_range < SIL_FLAT_THRESHOLD
    K_scenario    = K_SCENARIO_FALLBACK if flat_fallback else max(sil_scores, key=sil_scores.get)
    print(f"  실루엣: {sil_scores} → K={K_scenario} (flat_fallback={flat_fallback})")

    with open(P('silhouette_scores.json'), 'w') as f:
        json.dump({
            'scores':        {str(k): round(v, 4) for k, v in sil_scores.items()},
            'K_selected':    K_scenario,
            'sil_range':     round(sil_range, 4),
            'flat_fallback': flat_fallback,
        }, f, indent=2)

    kmeans_e1      = best_models[K_scenario]
    scenario_labels = kmeans_e1.labels_
    np.save(P('scenario_labels.npy'), scenario_labels)

    # 시나리오별 프로파일
    scenario_profiles = {}
    for k in range(K_scenario):
        k_mask = scenario_labels == k
        total  = int(k_mask.sum())

        q_dist = {f'Q{q}': int((quadrant[k_mask] == q).sum()) for q in range(6)}
        q_pct  = {f'Q{q}_pct': round(q_dist[f'Q{q}'] / total * 100, 1) for q in range(6)}
        dominant_q = int(max(q_dist, key=q_dist.get).replace('Q', ''))

        top_terms = list(feature_names[kmeans_e1.cluster_centers_[k].argsort()[-12:][::-1]])
        eff_n         = float(uniqueness_weight[k_mask].sum())
        local_weights = uniqueness_weight[k_mask]
        scen_rng      = np.random.default_rng(42 + k)
        v_random, v_dedup = _vendi_stable(
            embeddings_f32[k_mask], local_weights, VENDI_ANCHOR_SCENARIO, scen_rng)
        sup_ratio = round(v_dedup['mean'] / (v_random['mean'] + 1e-10), 3)
        k_indices = np.where(k_mask)[0]
        odd_div_k = odd_diversity_stats([odd_recs[i] for i in k_indices], ODD_DIMS)

        dq = density_quartile[k_mask]
        lq = lid_quartile[k_mask]
        scenario_profiles[k] = {
            'size':             total,
            'top_terms':        top_terms,
            'quadrant_distribution': {**q_dist, **q_pct},
            'dominant_quadrant': f'Q{dominant_q}',
            'effective_n':      round(eff_n, 1),
            'global_redundancy_in_dtrain': round(1.0 - eff_n / total, 3),
            'mean_density':     round(float(density_per_clip[k_mask].mean()), 4),
            'density_quartile_dist': {str(q): round(float((dq==q).mean()), 3) for q in range(4)},
            'mean_lid':         round(float(lid_per_clip[k_mask].mean()), 2),
            'lid_quartile_dist': {str(q): round(float((lq==q).mean()), 3) for q in range(4)},
            'lid_reliable_ratio': round(float(lid_reliable[k_mask].mean()), 3),
            'vendi_score':           round(v_random['mean'], 1),  # backward compat
            'vendi_random':          v_random,
            'vendi_dedup':           v_dedup,
            'vendi_suppression_ratio': sup_ratio,
            'vendi_reliable':        v_random['converged'],
            'odd_diversity':         odd_div_k,
        }

    # prune_flag 부여
    q_profile         = json.load(open(P('quadrant_profile.json')))
    global_q5_pct     = q_profile['5']['pct']
    global_prune_pct  = q_profile['1']['pct'] + global_q5_pct
    Q5_THRESH         = max(15.0, Q5_CONCENTRATION_MULT  * global_q5_pct)
    PRUNE_THRESH      = max(40.0, PRUNE_DOMINANT_MULT     * global_prune_pct)
    median_vendi      = float(np.median([scenario_profiles[k]['vendi_score'] for k in range(K_scenario)]))

    for k in range(K_scenario):
        p = scenario_profiles[k]
        p['prune_flag'] = _prune_flag(
            p['quadrant_distribution']['Q1_pct'],
            p['quadrant_distribution']['Q5_pct'],
            p['vendi_score'], median_vendi, PRUNE_THRESH, Q5_THRESH,
        )

    with open(P('scenario_profiles.json'), 'w') as f:
        json.dump(scenario_profiles, f, indent=2, ensure_ascii=False)

    # caution_scenarios
    _REVIEW = ('CAUTION', 'Q5_UNCERTAIN')
    caution_scenarios = [
        {
            'scenario_id':    k,
            'scenario_terms': scenario_profiles[k]['top_terms'],
            'q1_pct':         scenario_profiles[k]['quadrant_distribution']['Q1_pct'],
            'q5_pct':         scenario_profiles[k]['quadrant_distribution']['Q5_pct'],
            'vendi_score':    scenario_profiles[k]['vendi_score'],
            'size':           scenario_profiles[k]['size'],
            'prune_flag':     scenario_profiles[k]['prune_flag'],
            'note':           _caution_note(
                scenario_profiles[k]['prune_flag'],
                scenario_profiles[k]['quadrant_distribution']['Q5_pct'],
                Q5_THRESH,
            ),
        }
        for k in range(K_scenario) if scenario_profiles[k]['prune_flag'] in _REVIEW
    ]
    with open(P('caution_scenarios.json'), 'w') as f:
        json.dump(caution_scenarios, f, indent=2, ensure_ascii=False)

    # healthy_scenarios
    healthy_scenarios = [
        {
            'scenario_id':    k,
            'scenario_terms': scenario_profiles[k]['top_terms'],
            'q0_pct':         scenario_profiles[k]['quadrant_distribution']['Q0_pct'],
            'q2_pct':         scenario_profiles[k]['quadrant_distribution']['Q2_pct'],
            'vendi_score':    scenario_profiles[k]['vendi_score'],
            'effective_n':    scenario_profiles[k]['effective_n'],
            'size':           scenario_profiles[k]['size'],
        }
        for k in range(K_scenario)
        if (scenario_profiles[k]['dominant_quadrant'] == 'Q0'
            and scenario_profiles[k]['quadrant_distribution']['Q0_pct'] >= MIN_Q0_PCT
            and scenario_profiles[k]['size'] >= MIN_HEALTHY_SIZE)
    ]
    with open(P('healthy_scenarios.json'), 'w') as f:
        json.dump(healthy_scenarios, f, indent=2, ensure_ascii=False)

    joblib.dump(tfidf_e1, P('tfidf_vectorizer.joblib'))

    # Vendi 분산 + 두 공간 독립성 (NMI/ARI)
    vendi_arr = np.array([scenario_profiles[k]['vendi_score'] for k in range(K_scenario)])
    sup_arr   = np.array([scenario_profiles[k]['vendi_suppression_ratio'] for k in range(K_scenario)])
    sorted_v  = np.sort(vendi_arr)
    n_s       = len(sorted_v)
    gini      = float((2*np.sum(np.arange(1,n_s+1)*sorted_v))/(n_s*sorted_v.sum()) - (n_s+1)/n_s)
    nmi_sq    = float(normalized_mutual_info_score(scenario_labels, quadrant))
    ari_sq    = float(adjusted_rand_score(scenario_labels, quadrant))

    summary = {
        'vendi_mean':    round(float(vendi_arr.mean()), 1),
        'vendi_std':     round(float(vendi_arr.std()), 1),
        'vendi_cv':      round(float(vendi_arr.std()) / (float(vendi_arr.mean()) + 1e-6), 3),
        'vendi_gini':    round(max(gini, 0.0), 3),
        'vendi_max_scenario': int(np.argmax(vendi_arr)),
        'vendi_min_scenario': int(np.argmin(vendi_arr)),
        'vendi_unreliable_count': int(sum(
            1 for k in range(K_scenario) if not scenario_profiles[k]['vendi_reliable']
        )),
        'suppression_ratio_mean':   round(float(sup_arr.mean()), 3),
        'suppression_ratio_max':    round(float(sup_arr.max()), 3),
        'suppression_ratio_min':    round(float(sup_arr.min()), 3),
        'high_suppression_count':   int((sup_arr >= VENDI_SUPPRESSION_HIGH).sum()),
        'nmi_scenario_vs_quadrant':  round(nmi_sq, 4),
        'ari_scenario_vs_quadrant':  round(ari_sq, 4),
        'two_space_independence_ok': nmi_sq < 0.15 and ari_sq < 0.1,
    }
    with open(P('scenario_diversity_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # 임계값 민감 시나리오
    thresholds = json.load(open(P('thresholds.json')))
    boundary_sensitive = [
        {
            'scenario_id':          k,
            'scenario_terms':       scenario_profiles[k]['top_terms'][:5],
            'mean_density':         scenario_profiles[k]['mean_density'],
            'mean_lid':             scenario_profiles[k]['mean_lid'],
            'density_near_threshold': abs(scenario_profiles[k]['mean_density'] - thresholds['density_threshold']) < BOUNDARY_MARGIN_SCENARIO,
            'lid_near_threshold':   abs(scenario_profiles[k]['mean_lid'] - thresholds['lid_threshold']) < BOUNDARY_MARGIN_SCENARIO,
            'note': '임계값 ±5% 이내 — action 역전 가능성.',
        }
        for k in range(K_scenario)
        if (abs(scenario_profiles[k]['mean_density'] - thresholds['density_threshold']) < BOUNDARY_MARGIN_SCENARIO or
            abs(scenario_profiles[k]['mean_lid'] - thresholds['lid_threshold']) < BOUNDARY_MARGIN_SCENARIO)
    ]
    with open(P('boundary_sensitive_scenarios.json'), 'w') as f:
        json.dump(boundary_sensitive, f, indent=2, ensure_ascii=False)

    print(f"[0-E-1] K={K_scenario}, Vendi CV={summary['vendi_cv']:.3f}, "
          f"independence_ok={summary['two_space_independence_ok']}, "
          f"임계값민감={len(boundary_sensitive)}개")


if __name__ == '__main__':
    run()
