"""0-E-2: 저밀도 갭 슬라이스 정밀 분석
Q2+Q3+Q4 클립을 시나리오 단위로 그룹화 → 수집 전략 결정.
mean_lid 직접 사용으로 Q2 비율 순환성 제거.
"""

import json
import numpy as np
import joblib
from config import GAP_RATIO_HIGH_PRIORITY, LID_UNCERTAIN_RATIO, MIN_GAP_SIZE, VENDI_SUPPRESSION_HIGH
from utils import P, require_files, load_captions, already_done


def _collect_confidence(gap_q2_ratio):
    if gap_q2_ratio >= 0.5: return 'HIGH'
    if gap_q2_ratio >= 0.3: return 'MED'
    return 'LOW'


def run(force=False):
    if not force and already_done('0-E-2', 'collect_candidates.json'):
        return
    require_files(
        'quadrant_assignment.npy', 'lid_per_clip.npy', 'lid_reliable.npy',
        'uniqueness_weight.npy', 'scenario_labels.npy', 'scenario_profiles.json',
        'thresholds.json', 'tfidf_vectorizer.joblib', 'boundary_sensitive_scenarios.json',
        step='step_e1_scenario.py',
    )
    print("[0-E-2] 갭 슬라이스 분석 시작")

    captions, _ = load_captions()

    quadrant          = np.load(P('quadrant_assignment.npy'))
    lid_per_clip      = np.load(P('lid_per_clip.npy'))
    lid_reliable      = np.load(P('lid_reliable.npy'))
    uniqueness_weight = np.load(P('uniqueness_weight.npy'))
    scenario_labels   = np.load(P('scenario_labels.npy'))

    scenario_profiles = {int(k): v
                         for k, v in json.load(open(P('scenario_profiles.json'))).items()}
    K_scenario    = len(scenario_profiles)
    lid_threshold = json.load(open(P('thresholds.json')))['lid_threshold']
    boundary_ids  = {b['scenario_id']
                     for b in json.load(open(P('boundary_sensitive_scenarios.json')))}

    tfidf_e1      = joblib.load(P('tfidf_vectorizer.joblib'))
    X_tfidf       = tfidf_e1.transform(captions)
    feature_names = np.array(tfidf_e1.get_feature_names_out())

    gap_mask   = np.isin(quadrant, [2, 3, 4])
    gap_slices = {}

    for k in range(K_scenario):
        k_gap = gap_mask & (scenario_labels == k)
        if k_gap.sum() < MIN_GAP_SIZE:
            continue

        total_in_scen         = int((scenario_labels == k).sum())
        gap_in_scenario_ratio = float(k_gap.sum() / total_in_scen)
        mean_lid_gap          = float(lid_per_clip[k_gap].mean())
        lid_rel_ratio         = float(lid_reliable[k_gap].mean())

        sup_ratio = scenario_profiles[k].get('vendi_suppression_ratio', 1.0)

        if lid_rel_ratio < LID_UNCERTAIN_RATIO:
            action = 'UNCERTAIN_CHECK_SEMANTIC'
        elif mean_lid_gap >= lid_threshold:
            if gap_in_scenario_ratio > GAP_RATIO_HIGH_PRIORITY or sup_ratio >= VENDI_SUPPRESSION_HIGH:
                action = 'COLLECT_HIGH_PRIORITY'
            else:
                action = 'COLLECT'
        else:
            action = 'SYNTHETIC_OR_ACCEPT'

        gap_q_counts = {f'Q{q}': int((quadrant[k_gap] == q).sum()) for q in [2, 3, 4]}
        gap_q2_ratio = gap_q_counts['Q2'] / max(int(k_gap.sum()), 1)

        # 갭 클립 특이 어휘 (시나리오 전체 대비 차분)
        cluster_gap = X_tfidf[k_gap].mean(axis=0).A1
        cluster_all = X_tfidf[scenario_labels == k].mean(axis=0).A1
        diff_idx    = (cluster_gap - cluster_all).argsort()[-8:][::-1]
        gap_terms   = list(feature_names[diff_idx])

        q2_eff_n = float(uniqueness_weight[(scenario_labels == k) & (quadrant == 2)].sum())
        scen_lid = scenario_profiles[k]['mean_lid']
        lid_context_caution = bool(scen_lid < lid_threshold and mean_lid_gap >= lid_threshold)

        gap_slices[k] = {
            'scenario_id':           k,
            'scenario_terms':        scenario_profiles[k]['top_terms'],
            'gap_specific_terms':    gap_terms,
            'gap_count':             int(k_gap.sum()),
            'gap_in_scenario_ratio': round(gap_in_scenario_ratio, 3),
            'gap_quadrant_composition': gap_q_counts,
            'gap_q2_ratio':          round(gap_q2_ratio, 3),
            'q2_effective_n':        round(q2_eff_n, 1),
            'mean_lid':              round(mean_lid_gap, 2),
            'scenario_mean_lid':     round(scen_lid, 2),
            'lid_context_caution':   lid_context_caution,
            'lid_reliable_ratio':    round(lid_rel_ratio, 3),
            'vendi_suppression_ratio': round(sup_ratio, 3),
            'action':                action,
            'prune_flag':            scenario_profiles[k].get('prune_flag'),
            'boundary_sensitive':    k in boundary_ids,
        }

    # 소규모 스킵 기록
    skipped = [
        {'scenario_id': k,
         'gap_count':     int((gap_mask & (scenario_labels == k)).sum()),
         'scenario_size': int((scenario_labels == k).sum()),
         'reason':        'below_min_gap_size'}
        for k in range(K_scenario)
        if 0 < (gap_mask & (scenario_labels == k)).sum() < MIN_GAP_SIZE
    ]
    with open(P('skipped_small_gaps.json'), 'w') as f:
        json.dump(skipped, f, indent=2)

    # 후보 목록 생성
    collect_candidates = [
        {
            'scenario_id':       k,
            'scenario_context':  v['scenario_terms'][:5],
            'gap_specifics':     v['gap_specific_terms'],
            'priority':          'HIGH' if v['action'] == 'COLLECT_HIGH_PRIORITY' else 'NORMAL',
            'gap_count':         v['gap_count'],
            'q2_effective_n':    v['q2_effective_n'],
            'mean_lid':          v['mean_lid'],
            'gap_q2_ratio':      v['gap_q2_ratio'],
            'collect_confidence': _collect_confidence(v['gap_q2_ratio']),
            'lid_context_caution': v.get('lid_context_caution', False),
            'vendi_suppression_ratio': v['vendi_suppression_ratio'],
            'prune_flag':        v['prune_flag'],
        }
        for k, v in gap_slices.items()
        if v['action'] in ('COLLECT_HIGH_PRIORITY', 'COLLECT')
    ]
    collect_candidates.sort(
        key=lambda x: (x['priority'] == 'HIGH',
                       not x.get('lid_context_caution', False),
                       x['q2_effective_n'],
                       x['mean_lid']),
        reverse=True,
    )

    synthetic_candidates = [
        {
            'scenario_id':       k,
            'scenario_terms':    v['scenario_terms'],
            'gap_count':         v['gap_count'],
            'mean_lid':          v['mean_lid'],
            'partial_collect_flag': v['gap_q2_ratio'] >= 0.2,
            'q2_effective_n':    v['q2_effective_n'],
            'gap_q2_ratio':      v['gap_q2_ratio'],
            'note': ('Q2 클립 존재 — EXP-004 합성 전 Q2 클립 별도 수집 검토'
                     if v['gap_q2_ratio'] >= 0.2 else 'Q2 클립 미미 — 합성으로 충분'),
        }
        for k, v in gap_slices.items() if v['action'] == 'SYNTHETIC_OR_ACCEPT'
    ]

    uncertain_candidates = [
        {
            'scenario_id':       k,
            'top_terms':         scenario_profiles[k]['top_terms'][:5],
            'size':              scenario_profiles[k]['size'],
            'gap_count':         v['gap_count'],
            'lid_reliable_ratio': v['lid_reliable_ratio'],
            'gap_specific_terms': v['gap_specific_terms'],
            'quadrant_distribution': scenario_profiles[k]['quadrant_distribution'],
            'boundary_sensitive': v['boundary_sensitive'],
            'note':              'LID 불신뢰 — 0-E-1 시나리오 프로파일 수동 확인',
        }
        for k, v in gap_slices.items() if v['action'] == 'UNCERTAIN_CHECK_SEMANTIC'
    ]

    for fname, obj in [
        ('gap_slices.json',           gap_slices),
        ('collect_candidates.json',   collect_candidates),
        ('synthetic_candidates.json', synthetic_candidates),
        ('uncertain_candidates.json', uncertain_candidates),
    ]:
        with open(P(fname), 'w') as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)

    print(f"[0-E-2] COLLECT={len(collect_candidates)}, "
          f"SYNTHETIC={len(synthetic_candidates)}, "
          f"UNCERTAIN={len(uncertain_candidates)}, "
          f"SKIPPED={len(skipped)}")


if __name__ == '__main__':
    run()
