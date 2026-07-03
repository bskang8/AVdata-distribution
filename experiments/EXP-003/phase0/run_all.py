"""Phase 0 전체 순차 실행
각 단계를 독립적으로 재실행하려면 해당 step_*.py를 직접 실행:
  python3 step_d_quadrant.py   # 0-D부터 재실행
  python3 step_e1_scenario.py  # 0-E-1만 재실행
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
    import time
    timings = {}
    for name, fn in STEPS:
        t0 = time.time()
        fn()
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
    print(f"  Vendi Score:    {dp['vendi_score']:.1f}")
    print(f"  LID 신뢰 비율:  {ls['lid_reliable_ratio']:.1%}")
    print(f"  6-분류:")
    for q, lbl in [(0,'KEEP'),(1,'PRUNE'),(2,'COLLECT'),
                    (3,'EVALUATE'),(4,'LID_UNCERTAIN'),(5,'PRUNE_UNCERTAIN')]:
        pct = qp[str(q)]['pct']
        print(f"    Q{q} {lbl:<16}: {qp[str(q)]['count']:>6}개 ({pct:.1f}%)")
    print(f"  두 공간 독립성: {sds['two_space_independence_ok']}")
    print(f"  수집 후보:      {len(cc)}개  합성 후보: {len(sc)}개")
    print(f"\n  단계별 소요 시간: {timings}")
