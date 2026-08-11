"""§9 full-joint P_self 배선 — phase0 clip 재집계 (phase0 무수정).

phase0 `odd_coverage.json`은 필드 marginal + top100 조합만 저장(꼬리 버림). §9(b) 시급은
꼬리 조합이 핵심이라, 여기서 **10만 클립을 재집계**해 P_ext와 같은 축의 결합분포를 만든다.
phase0 crosswalk 원시함수(`_flatten_final`·`_SURFACE_MAP`)를 import해 축정합을 보장하되,
weather는 **fog 병합 없이 precipitation 기반 독립**으로 계산(P_ext=fog 독립축, §12-R).

축: 결합·비교용 {road_type, weather, fog} + road_surface(독립관측 marginal — P_ext는 weather
    에서 규칙유도라 '규칙 vs 관측' 혼입, 별도·주의). unknown 포함 조합 제외 후 정규화.

출력: output/P_self.json   실행: python3 pself.py   (phase0 config/utils import)
"""
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from paths import OUTPUT as OUT                                # import 시 phase0도 sys.path에 얹힘
from step_a_odd_coverage import _flatten_final, _SURFACE_MAP   # noqa: E402  phase0 무수정 재사용
from config import ODD_DIR                                     # noqa: E402

JOINT_AXES = ["road_type", "weather", "fog"]
MARG_AXES = ["road_type", "weather", "fog", "road_surface"]


def weather_indep(flat):
    """precipitation → weather (fog 병합 안 함, P_ext 정합)."""
    return {"none": "clear", "rain": "rain", "snow": "snow"}.get(
        flat.get("precipitation", "unknown"), "unknown")


def axes_of(flat):
    return {"road_type": flat.get("road_type", "unknown"),
            "weather": weather_indep(flat),
            "fog": flat.get("fog", "unknown"),
            "road_surface": _SURFACE_MAP.get(flat.get("road_surface", "unknown"), "unknown")}


def main():
    joint = Counter()
    marg = {a: Counter() for a in MARG_AXES}
    n = n_clean = 0
    for fn in sorted(os.listdir(ODD_DIR)):
        if not fn.endswith(".json"):
            continue
        try:
            d = json.load(open(os.path.join(ODD_DIR, fn)))
        except (json.JSONDecodeError, OSError):
            continue
        if not d.get("odd_final"):
            continue
        ax = axes_of(_flatten_final(d["odd_final"]))
        n += 1
        for a in MARG_AXES:
            if ax[a] != "unknown":
                marg[a][ax[a]] += 1
        key = tuple(ax[a] for a in JOINT_AXES)
        if "unknown" not in key:
            joint[key] += 1
            n_clean += 1

    jtot = sum(joint.values()) or 1
    P_self = {"|".join(k): round(v / jtot, 8)
              for k, v in sorted(joint.items(), key=lambda x: -x[1])}
    marginals = {a: {v: round(c / (sum(marg[a].values()) or 1), 6)
                     for v, c in marg[a].most_common()} for a in MARG_AXES}
    os.makedirs(OUT, exist_ok=True)
    json.dump({"joint_axes": JOINT_AXES, "n_clips": n, "n_clean_joint": n_clean,
               "n_joint_cells": len(joint),
               "road_surface_note": "독립관측. P_ext는 weather서 규칙유도 → 결합비교 제외, marginal만 주의",
               "P_self": P_self, "marginals": marginals},
              open(os.path.join(OUT, "P_self.json"), "w"), ensure_ascii=False, indent=2)
    print(f"[OK] P_self 재집계: {n:,}클립 · clean joint {n_clean:,} → {len(joint)}셀 → output/P_self.json")
    print(f"   상위 결합 5:")
    for k, v in sorted(joint.items(), key=lambda x: -x[1])[:5]:
        print(f"     {v/jtot:.4f}  {k}")
    print(f"   road_type marginal: {dict(list(marginals['road_type'].items())[:6])}")


if __name__ == "__main__":
    main()
