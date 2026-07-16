"""§11 민감도 스윕 실행 — 손값이 결론을 바꾸는지 측정 (RESULTS.md §6 설계).

두 부분:
  A. **exposure 선정 불변 확인** — compose는 손앵커 블록(speed·agent·density·lighting)을
     marginalize out(§13-R 게이트 A). 손앵커 소스를 흔들어도 P_ext(§8·§9 선정)가 변하지 않음을
     assert로 증명 → §6 설계의 '손앵커 소스 스윕'은 exposure엔 무의미(=Robust by construction).
  B. **criticality 배수 스윕** — 손값이 실제로 무는 곳은 §10 crit의 published 배수다.
     각 배수 블록을 ±30% OAT로 흔들어(1+(m-1)·f, f∈{0.7,1.3}) crit 랭킹 재계산 →
     Top-K Jaccard + 전체 Spearman로 안정성. Robust(Jaccard≥0.9)/Fragile(<0.8) 판정.
     = design §10 '가중치 ±30% → 순위 안정' 검증 + §11 스윕의 실체.

출력: output/sweep.json + stdout   실행: python3 sweep.py  (criticality.py 먼저)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import compose
import criticality as C
import loader
from paths import OUTPUT as OUT

TOPK = 30
FACTORS = (0.7, 1.3)


def _rank(vals):
    """평균순위(동점 평균)."""
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    r = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def _pearson(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    da = sum((x - ma) ** 2 for x in a) ** 0.5
    db = sum((x - mb) ** 2 for x in b) ** 0.5
    return num / (da * db) if da and db else 1.0


def spearman(a, b):
    return _pearson(_rank(a), _rank(b))


def jaccard(s1, s2):
    return len(s1 & s2) / len(s1 | s2) if (s1 or s2) else 1.0


def perturb(table, f):
    """배수 m → 1+(m-1)·f. f<1 중립화, f>1 증폭."""
    return {v: 1 + (m - 1) * f for v, m in table.items()}


def part_a_exposure_invariance():
    """손앵커 소스 교란 → P_ext 불변 assert."""
    tables = loader.load_all()
    base = compose.compose(tables)
    # agent·speed·density·lighting 값을 크게 흔들어도 P_ext 동일해야
    for blk in ("P3_agent", "P4_speed", "P3_density", "P5_lighting"):
        t2 = dict(tables)                        # 얕은 복사 — 교란할 블록만 교체
        t2[blk] = {}
        for key, vals in tables[blk].items():    # 첫 범주에 몰아주기(분포 왜곡)
            first = next(iter(vals))
            t2[blk][key] = {kk: (0.99 if kk == first else 0.01 / max(len(vals) - 1, 1))
                            for kk in vals}
        p2 = compose.compose(t2)
        assert all(abs(base[c] - p2.get(c, 0)) < 1e-12 for c in base), f"{blk} 교란이 P_ext를 바꿈!"
    return len(base)


def part_b_criticality_sweep():
    combos = [c for c in __import__("itertools").product(*[t.keys() for t in C.TABLES])
              if C.crit(c) > 0]
    base_vals = [C.crit(c) for c in combos]
    base_top = set(sorted(range(len(combos)), key=lambda i: -base_vals[i])[:TOPK])

    results = []
    for bi, axis in enumerate(C.AXES):
        worst_j, worst_s, worst_f = 1.0, 1.0, None
        for f in FACTORS:
            tabs = list(C.TABLES)
            tabs[bi] = perturb(C.TABLES[bi], f)
            vals = [C.crit(c, tabs) for c in combos]
            top = set(sorted(range(len(combos)), key=lambda i: -vals[i])[:TOPK])
            j, s = jaccard(base_top, top), spearman(base_vals, vals)
            if j < worst_j:
                worst_j, worst_f = j, f
            worst_s = min(worst_s, s)
        verdict = "✅ Robust" if worst_j >= 0.9 else ("🚩 Fragile" if worst_j < 0.8 else "⚠️ 주의")
        results.append(dict(block=axis, min_jaccard=round(worst_j, 3),
                            min_spearman=round(worst_s, 3), worst_factor=worst_f, verdict=verdict))
    return len(combos), results


def main():
    n_ext = part_a_exposure_invariance()
    print("=== A. exposure 선정 불변 (게이트 A) ===")
    print(f"  손앵커 4블록 소스를 크게 교란해도 P_ext {n_ext}셀 전부 불변 → "
          f"§8·§9 선정은 손앵커에 Robust by construction. ✅")

    n_combo, res = part_b_criticality_sweep()
    print(f"\n=== B. criticality 배수 ±30% 스윕 (OAT, {n_combo}조합, Top-{TOPK}) ===")
    print(f"  {'block':16s} {'Jaccard':>8s} {'Spearman':>9s}  verdict")
    for r in res:
        print(f"  {r['block']:16s} {r['min_jaccard']:>8.3f} {r['min_spearman']:>9.3f}  {r['verdict']}")

    fragile = [r["block"] for r in res if "Fragile" in r["verdict"]]
    print(f"\n  판정: Fragile={fragile or '없음'} "
          f"(Fragile이면 §10 배수 앵커 보강 or crit 결론에 민감 경고)")

    json.dump({"topk": TOPK, "factors": FACTORS,
               "exposure_invariant": True, "n_pext_cells": n_ext,
               "criticality_sweep": res, "fragile_blocks": fragile},
              open(os.path.join(OUT, "sweep.json"), "w"), ensure_ascii=False, indent=2)
    print(f"\n[OK] → output/sweep.json")


def _selfcheck():
    assert abs(spearman([1, 2, 3], [1, 2, 3]) - 1.0) < 1e-9
    assert abs(spearman([1, 2, 3], [3, 2, 1]) + 1.0) < 1e-9
    assert jaccard({1, 2, 3}, {1, 2, 3}) == 1.0 and jaccard({1, 2}, {3, 4}) == 0.0
    assert perturb({"a": 1.0, "b": 3.0}, 0.5) == {"a": 1.0, "b": 2.0}
    print("[OK] sweep self-check 통과")


if __name__ == "__main__":
    _selfcheck()
    main()
