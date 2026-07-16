"""§10+ 이웃 확률외삽 — 미관측 위험조합의 수집 우선순위 정식화.

situation-coverage-grid.md(arXiv 2507.12158): 미관측 셀을 '발생 0/위험 0'으로 낙관하지 않고
이웃 셀에서 확률 외삽. 원논문은 '이웃 **실패율** → 미관측 실패율 상한'이나, phase1엔 모델
실패율 데이터가 없다(다운스트림 EXP-002/004) → 방법의 정신을 **발생가능성(occurrence)을
이웃 coverage에서 외삽**으로 대체:
  · 미관측 셀의 1축 이웃(관측 6축, Hamming-1)의 n_self 평균 = est_occurrence
  · 이웃이 많이 관측됨 → 이 셀도 실제로 흔한데 우리가 놓침 = **진짜 수집 갭**
  · 이웃도 다 비었음 → 실제로도 희소/불가능 = **합성·존재확인** 대상
  수집우선순위 = crit(worst-case over speed) × est_occurrence
  → '위험 ∧ 실제 발생 ∧ 데이터 0' 을 정식 랭킹 (미관측을 균일 취급하던 §10 flag를 대체·정밀화).

입력: criticality 모듈(crit·coverage 캐시)   출력: output/extrapolation.json + stdout
실행: python3 extrapolate.py   (criticality.py 먼저 — P_self_crit.json 캐시 사용)
"""
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import criticality as C
from paths import OUTPUT as OUT
PLAUSIBLE_MIN = 10.0     # 이웃 평균 관측 이 이상 → '실제 발생 유력(수집 갭)', 미만 → '희소(합성)'


def forbidden6(six):
    return six[0] == "highway" and six[4] in ("pedestrians", "cyclists")


def crit_worst(six):
    """이 관측셀의 최악(고속) severity — speed는 미관측이라 worst-case."""
    return max(C.crit(six + (sp,)) for sp in C.SPEED)


def neighbors(six, obs_tables):
    """관측 6축에서 Hamming-1 이웃 (forbidden 제외)."""
    for ai in range(C.N_OBS):
        for val in obs_tables[ai]:
            if val == six[ai]:
                continue
            nb = six[:ai] + (val,) + six[ai + 1:]
            if not forbidden6(nb):
                yield nb


def main():
    cov, n_clips = C.pself_coverage()
    obs_tables = C.TABLES[:C.N_OBS]
    cells = [c for c in itertools.product(*[t.keys() for t in obs_tables]) if not forbidden6(c)]

    rows = []
    for six in cells:
        if cov.get(six, 0) > 0:                     # 관측된 셀은 외삽 불필요
            continue
        nbs = list(neighbors(six, obs_tables))
        obs_nbs = [cov.get(nb, 0) for nb in nbs]
        est = sum(obs_nbs) / len(obs_nbs) if obs_nbs else 0.0   # 이웃 평균 관측 = 발생가능성 외삽
        cw = crit_worst(six)
        rows.append(dict(cell=six, crit=round(cw, 1), est_occurrence=round(est, 2),
                         n_obs_neighbors=sum(1 for x in obs_nbs if x > 0),
                         priority=round(cw * est, 1),
                         kind="수집갭(실제발생 유력)" if est >= PLAUSIBLE_MIN else "희소→합성/존재확인"))

    rows.sort(key=lambda r: -r["priority"])
    gap = [r for r in rows if r["kind"].startswith("수집갭")]
    rare = [r for r in rows if not r["kind"].startswith("수집갭")]

    print(f"=== §10+ 이웃 확률외삽 (미관측 {len(rows)}셀 / 관측 6축 grid {len(cells)}) ===")
    print(f"  분류: 수집갭(이웃 관측≥{PLAUSIBLE_MIN:.0f}) {len(gap)} · 희소(이웃도 빔) {len(rare)}")
    print(f"\n  ── 🎯 수집 우선순위 top (crit × 이웃외삽 발생가능성) ──")
    for r in gap[:12]:
        print(f"    P={r['priority']:8.0f}  crit={r['crit']:5.1f} est_occ={r['est_occurrence']:8.1f} "
              f"이웃관측 {r['n_obs_neighbors']:2d}  {'×'.join(r['cell'])}")
    print(f"\n  ── ⚗️ 희소(이웃도 비어 실제 발생 불확실 → 합성/존재확인) 상위 crit ──")
    for r in sorted(rare, key=lambda r: -r["crit"])[:5]:
        print(f"    crit={r['crit']:5.1f} est_occ={r['est_occurrence']:.1f} 이웃관측 {r['n_obs_neighbors']}  {'×'.join(r['cell'])}")

    json.dump({"n_clips": n_clips, "n_unobserved": len(rows), "n_grid": len(cells),
               "n_collection_gap": len(gap), "n_rare_synth": len(rare), "plausible_min": PLAUSIBLE_MIN,
               "note": "occurrence(coverage) 외삽으로 미관측 랭킹. 원논문 failure율 외삽의 대체 "
                       "(phase1 모델실패율 부재). speed는 crit worst-case, coverage는 관측 6축.",
               "collection_gap": gap[:100], "rare_synth": sorted(rare, key=lambda r: -r["crit"])[:50]},
              open(os.path.join(OUT, "extrapolation.json"), "w"), ensure_ascii=False, indent=2)
    print(f"\n[OK] → output/extrapolation.json (수집갭 {len(gap)} · 희소 {len(rare)})")


def _selfcheck():
    # 이웃 외삽: 이웃이 큰 값이면 est 큼, 다 0이면 est 0
    obs_tables = C.TABLES[:C.N_OBS]
    six = ("urban", "snow", "present", "poorly_lit", "pedestrians", "dense")
    assert not forbidden6(six)
    assert forbidden6(("highway", "clear", "none", "well_lit", "pedestrians", "sparse"))
    nbs = list(neighbors(six, obs_tables))
    assert all(len(nb) == C.N_OBS for nb in nbs) and six not in nbs
    assert crit_worst(six) == max(C.crit(six + (sp,)) for sp in C.SPEED)
    print("[OK] extrapolate self-check 통과")


if __name__ == "__main__":
    _selfcheck()
    main()
