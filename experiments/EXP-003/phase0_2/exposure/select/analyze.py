"""§8·§9 분석 — 핵심 운행영역 누적절단 + self 대조(full-joint).

design §8: P_ext 내림차순 누적 95/99% = 핵심 운행영역("상위 N조합 = 주행의 X%").
design §9: P_self(phase0 재집계, pself.py) 대조.
  (a) 과수집 r=self/ext ≫1  (b) 시급 = P_ext 큰데 self≈0.
  **결합 단위** {road_type, weather, fog} (P_ext의 road_surface는 weather서 규칙유도라
  결합비교 제외 — §12-R '규칙 vs 관측'). unknown 제외·공통지지 재정규화.

입력: output/P_ext.json, output/P_self.json (pself.py 먼저)
출력: output/analysis.json + stdout    실행: python3 analyze.py
"""
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from paths import OUTPUT as OUT

PEXT_AXES = ["road_type", "weather", "fog", "road_surface"]
JOINT_AXES = ["road_type", "weather", "fog"]


def load_pext():
    d = json.load(open(os.path.join(OUT, "P_ext.json")))
    return {tuple(k.split("|")): p for k, p in d["P_ext"].items()}


def load_pself():
    d = json.load(open(os.path.join(OUT, "P_self.json")))
    joint = {tuple(k.split("|")): p for k, p in d["P_self"].items()}
    return joint, d["marginals"]


def cumulative_cut(P, targets=(0.95, 0.99)):
    ordered = sorted(P.items(), key=lambda x: -x[1])
    hit = {t: None for t in targets}
    acc = 0.0
    for i, (c, p) in enumerate(ordered, 1):
        acc += p
        for t in targets:
            if hit[t] is None and acc >= t:
                hit[t] = i
    return ordered, hit


def pext_joint(P):
    """P_ext(4축) → {road_type,weather,fog} marginal(road_surface 합산 제거)."""
    m = defaultdict(float)
    for c, p in P.items():
        m[c[:3]] += p                          # (road_type, weather, fog)
    return dict(m)


def marginal(dist, i):
    m = defaultdict(float)
    for c, p in dist.items():
        m[c[i]] += p
    return dict(m)


def compare(ext, self_, key_fmt=str):
    """공통지지 재정규화 후 r=self/ext. 반환: rows, ext_only(시급), self_only(한계)."""
    common = set(ext) & set(self_)
    ce = sum(ext[k] for k in common) or 1e-12
    cs = sum(self_[k] for k in common) or 1e-12
    rows = []
    for k in sorted(common, key=lambda k: -ext[k]):
        pe, ps = ext[k] / ce, self_[k] / cs
        rows.append(dict(cell=key_fmt(k), P_ext=round(pe, 4), P_self=round(ps, 4),
                         ratio=round(ps / pe, 2) if pe else None))
    ext_only = sorted(set(ext) - set(self_), key=lambda k: -ext[k])   # self=0 → 시급
    self_only = sorted(set(self_) - set(ext), key=lambda k: -self_[k])  # P_ext 미표현
    return rows, [(key_fmt(k), round(ext[k], 4)) for k in ext_only], \
                 [(key_fmt(k), round(self_[k], 4)) for k in self_only]


def main():
    P = load_pext()
    self_joint, self_marg = load_pself()
    ordered, hit = cumulative_cut(P)
    report = {}

    print(f"=== §8 핵심 운행영역 (신뢰 4축, {len(P)}셀) ===")
    for t in (0.95, 0.99):
        print(f"  누적 {int(t*100)}% → 상위 {hit[t]}/{len(P)} 조합")
    report["cut"] = {f"{int(t*100)}pct": hit[t] for t in (0.95, 0.99)}
    print("  상위 5:")
    for c, p in ordered[:5]:
        print(f"    {p:.4f}  {c}")

    # ── §9 결합 단위 대조 ──────────────────────────────────────────
    ej = pext_joint(P)
    fmt = lambda k: "×".join(k)
    rows, ext_only, self_only = compare(ej, self_joint, fmt)
    report["joint"] = dict(rows=rows, urgent_ext_only=ext_only, pself_only_limit=self_only)
    print(f"\n=== §9(결합 {'×'.join(JOINT_AXES)}) self 대조 (full-joint, pself.py) ===")
    print("  (공통지지 재정규화; r=self/ext ≫1 과수집·≪1 과소)")
    for r in rows:
        flag = "  ← 과수집" if r["ratio"] and r["ratio"] > 1.5 else (
               "  ← 과소" if r["ratio"] and r["ratio"] < 0.5 else "")
        print(f"    {r['cell']:28s} ext={r['P_ext']:.3f} self={r['P_self']:.3f} r={r['ratio']}{flag}")
    if ext_only:
        print(f"  🚩 시급(P_ext 있음·self=0), P_ext순: {ext_only}")
    if self_only:
        print(f"  · P_self에만(P_ext 미표현=한계① urban/rural): {self_only[:6]}")

    # ── §9 marginal (참고, road_surface 포함) ─────────────────────
    print("\n=== §9 marginal (참고) ===")
    report["marginals"] = {}
    for i, axis in enumerate(PEXT_AXES):
        em = marginal(P, i)
        sm = self_marg.get(axis, {})
        rows_m, eo, so = compare(em, sm)
        report["marginals"][axis] = dict(rows=rows_m, ext_only=eo, self_only=so)
        note = " (규칙유도 vs 관측 — 주의)" if axis == "road_surface" else ""
        cells = " ".join(f"{r['cell']}:{r['ratio']}" for r in rows_m)
        print(f"  [{axis}]{note} r=self/ext → {cells}")

    json.dump(report, open(os.path.join(OUT, "analysis.json"), "w"),
              ensure_ascii=False, indent=2)
    print(f"\n[OK] → output/analysis.json")
    print("주의: §9 비교는 신뢰 4축(고속+국도 2종)에서만 유효. road_type 2/4 한계로 urban·rural은 "
          "P_ext 부재(=P_self에만) → 전체 주행으로 확대해석 금지. 희귀-위험은 criticality.py(§10)·extrapolate.py.")


if __name__ == "__main__":
    main()
