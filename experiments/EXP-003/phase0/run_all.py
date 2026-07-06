"""Phase 0 전체 순차 실행
이미 완료된 단계는 자동 스킵. 재실행 방법:
  python3 run_all.py --force          # 전체 강제 재실행
  python3 run_all.py --force 0-D 0-E-1  # 특정 단계만 강제 재실행
  python3 step_d_quadrant.py          # 단일 단계 직접 실행
"""

import step_a_knn
import step_b_diversity
import step_c_lid
import step_d_quadrant
import step_d_val_flipd
import step_e1_scenario
import step_e2_gap

import json
import numpy as np
from utils import P

STEPS = [
    ('0-A', step_a_knn.run),
    ('0-B', step_b_diversity.run),
    ('0-C', step_c_lid.run),
    ('0-D', step_d_quadrant.run),
    ('0-D-val', step_d_val_flipd.run),
    ('0-E-1', step_e1_scenario.run),
    ('0-E-2', step_e2_gap.run),
]

if __name__ == '__main__':
    import argparse
    import time

    parser = argparse.ArgumentParser()
    parser.add_argument('--force', nargs='*', metavar='STEP',
                        help='강제 재실행할 단계 (생략 시 전체, 예: --force 0-A 0-B)')
    args = parser.parse_args()

    if args.force is None:
        forced = set()
    elif len(args.force) == 0:
        forced = {name for name, _ in STEPS}
    else:
        forced = set(args.force)

    timings = {}
    for name, fn in STEPS:
        t0 = time.time()
        fn(force=(name in forced))
        timings[name] = round(time.time() - t0, 1)
        print()

    # 최종 요약
    dp    = json.load(open(P('diversity_profile.json')))
    qp    = json.load(open(P('quadrant_profile.json')))
    ls    = json.load(open(P('lid_stats.json')))
    sds   = json.load(open(P('scenario_diversity_summary.json')))
    cc    = json.load(open(P('collect_candidates.json')))
    sc    = json.load(open(P('synthetic_candidates.json')))

    print("=" * 60)
    print("Phase 0 완료 요약")
    print("=" * 60)
    print(f"  Effective N:    {dp['effective_N_soft']:.0f}  (중복률 {dp['redundancy_ratio']:.1%})")
    print(f"  Vendi random:   {dp['vendi_random']['mean']:.3f} ± {dp['vendi_random']['std']:.3f} "
          f"(n={dp['vendi_random']['n_runs']}, converged={dp['vendi_random']['converged']})")
    print(f"  Vendi dedup:    {dp['vendi_dedup']['mean']:.3f} ± {dp['vendi_dedup']['std']:.3f} "
          f"(n={dp['vendi_dedup']['n_runs']}, converged={dp['vendi_dedup']['converged']})")
    print(f"  Vendi topk:     {dp['vendi_topk']['mean']:.3f} ± {dp['vendi_topk']['std']:.3f} "
          f"(pool={dp['vendi_topk']['pool_size']}, {dp['vendi_topk']['mode']})")
    print(f"  억압 계수:      {dp['vendi_suppression_ratio']:.3f}")
    odd = dp.get('odd_diversity', {})
    align = odd.get('embedding_odd_alignment', {})
    print(f"  ODD 고유 조합:  {odd.get('n_unique_combos', 'N/A')}  "
          f"mean_norm_entropy={odd.get('mean_norm_entropy', 'N/A')}")
    print(f"  ODD 커버리지:   {odd.get('found_ratio', 'N/A'):.1%}  "
          f"임베딩 정렬={align.get('interpretation', 'N/A')} "
          f"(ρ={align.get('spearman_rho', 'N/A')})")
    print(f"  LID 신뢰 비율:  {ls['lid_reliable_ratio']:.1%}")
    print(f"  6-분류:")
    for q, lbl in [(0,'KEEP'),(1,'PRUNE'),(2,'COLLECT'),
                    (3,'EVALUATE'),(4,'LID_UNCERTAIN'),(5,'PRUNE_UNCERTAIN')]:
        pct = qp[str(q)]['pct']
        print(f"    Q{q} {lbl:<16}: {qp[str(q)]['count']:>6}개 ({pct:.1f}%)")
    print(f"  두 공간 독립성: {sds['two_space_independence_ok']}")
    print(f"  수집 후보:      {len(cc)}개  합성 후보: {len(sc)}개")
    print(f"\n  단계별 소요 시간: {timings}")
