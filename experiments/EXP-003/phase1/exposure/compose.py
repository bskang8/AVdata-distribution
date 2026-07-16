"""§7 P_ext 조립 — 신뢰 부분공간 정확 enumerate.

design §7 + §13-R. 손앵커 축(speed·agent·lighting·**density**)을 marginalize out 한
신뢰 부분공간에서 P_ext를 정확 합산한다.
  · design §13-R은 5축 {road_type,weather,fog,road_surface,density}였으나, 본 세션에서
    P3_density를 HAND_ANCHOR로 재분류(V/C=용량편람 문서) → density도 제외 → **4축**
    {road_type, weather, fog, road_surface}. 전부 SUPPORTED 소스로만 지지됨.

층 s=(m,h,k), w(s) ∝ VKT(s) = vkt_weight(k)·hourly_profile(h|k)·(1/12 균등월).
  (월별 VKT 분포 데이터 없음 → v0 균등월. weather 계절성은 P1(weather|m,h) 합산이 나름.)
road_surface = weather 결정적 파생(clear→dry, rain→wet, snow→snow). ρ 젖음지속은 v1(§13).
MC 아님 — dict 곱 정확 enumerate (공간 작음: 층 576 × 소수 축).

주의(§12-R): road_type이 w_vkt의 2/4 등급(highway·national_road)만 → P_ext는 도시부/지방도
노출을 담지 못함(한계 ①). urban·rural 조합은 이 P_ext에 존재하지 않는다.

출력: output/P_ext.json    실행: python3 compose.py
"""
import json
import os

import loader
from paths import OUTPUT as OUT

MONTHS = range(1, 13)
HOURS = range(24)
SURFACE = {"clear": "dry", "rain": "wet", "snow": "snow"}   # §5-2 결정적(ρ=v1)


def build_strata(tables):
    """(m,h,k) -> w(s). VKT 비례·월 균등, 합=1."""
    vkt = tables["w_vkt"][()]                    # {road_type: P(road_type)}
    hourly = tables["w_hourly"]                  # {(k,): {hour: share}}
    w = {}
    for k, pk in vkt.items():
        hp = hourly[(k,)]
        for m in MONTHS:
            for h in HOURS:
                w[(m, h, k)] = pk * hp.get(h, 0.0) / 12.0
    tot = sum(w.values()) or 1.0
    return {s: v / tot for s, v in w.items()}


def compose(tables):
    """신뢰 4축 결합확률 P_ext[(road_type, weather, fog, road_surface)]."""
    w = build_strata(tables)
    weather_t = tables["P1_weather"]             # {(m,h): {weather: p}}
    fog_t = tables["P1_fog"]                      # {(m,h): P(fog present)}
    P = {}
    for (m, h, k), ws in w.items():
        pf = fog_t[(m, h)]
        for weather, pw in weather_t[(m, h)].items():
            rs = SURFACE[weather]
            for fog, pfog in (("present", pf), ("none", 1.0 - pf)):
                c = (k, weather, fog, rs)
                P[c] = P.get(c, 0.0) + ws * pw * pfog
    return P


def main():
    tables = loader.load_all()
    P = compose(tables)
    tot = sum(P.values())
    assert abs(tot - 1) < 1e-6, f"P_ext 합≠1: {tot}"
    os.makedirs(OUT, exist_ok=True)
    ser = {"|".join(map(str, c)): round(p, 8)
           for c, p in sorted(P.items(), key=lambda x: -x[1])}
    with open(os.path.join(OUT, "P_ext.json"), "w") as f:
        json.dump({"axes": ["road_type", "weather", "fog", "road_surface"],
                   "note": "신뢰 4축(손앵커 marginalize). design §7·§13-R. road_type=2/4등급(한계①)",
                   "n_cells": len(ser), "sum": round(tot, 8), "P_ext": ser},
                  f, ensure_ascii=False, indent=2)
    print(f"[OK] P_ext {len(P)}셀 (합={tot:.6f}) → output/P_ext.json")
    for c, p in sorted(P.items(), key=lambda x: -x[1])[:6]:
        print(f"   {p:.4f}  {c}")


def _selfcheck():
    assert SURFACE["rain"] == "wet"
    t = {"w_vkt": {(): {"highway": 0.4, "national_road": 0.6}},
         "w_hourly": {("highway",): {h: 1 / 24 for h in HOURS},
                      ("national_road",): {h: 1 / 24 for h in HOURS}},
         "P1_weather": {(m, h): {"clear": 0.8, "rain": 0.15, "snow": 0.05}
                        for m in MONTHS for h in HOURS},
         "P1_fog": {(m, h): 0.1 for m in MONTHS for h in HOURS}}
    P = compose(t)
    assert abs(sum(P.values()) - 1) < 1e-9, sum(P.values())
    # clear→dry 질량이 최대여야 (0.8·0.9 등)
    top = max(P.items(), key=lambda x: x[1])[0]
    assert top[1] == "clear" and top[3] == "dry", top
    print("[OK] compose self-check 통과")


if __name__ == "__main__":
    _selfcheck()
    main()
