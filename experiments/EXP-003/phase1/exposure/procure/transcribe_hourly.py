"""전사: raw/ktdb/itmsh_sample.csv → sources/hourly_profile.csv (w_hourly 블록).

raw는 (grade, hour, share) — KTDB 등급 이름. sources 계약은 (road_type, hour, traffic_share),
road_type별 합=1. grade→road_type는 mapping.yaml §5-3. share는 등급 내 이미 정규화됨.

# ponytail: 지방도·국지도(dtype 3,5)는 API 서버 502 지속 → 현재 highway·national_road만.
#           복구되면 fetch_ktdb 재실행 후 이 스크립트만 다시 돌리면 됨.
실행:  python3 transcribe_hourly.py   (이후 loader.py로 계약 검증)
"""
import csv
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from paths import RAW, SOURCES

SRC = os.path.join(RAW, "ktdb", "itmsh_sample.csv")
OUT = os.path.join(SOURCES, "hourly_profile.csv")

GRADE2ROAD = {          # mapping.yaml §5-3
    "고속도로": "highway",
    "일반도로": "national_road",
    "지방도": "rural",
    "국가지원지방도": "rural",
}


def main():
    by_road = defaultdict(dict)     # road_type -> {hour: share}
    for r in csv.DictReader(open(SRC)):
        road = GRADE2ROAD.get(r["grade"])
        if not road:
            continue
        by_road[road][int(r["hour"])] = float(r["share"])

    rows = []
    for road in sorted(by_road):
        dist = by_road[road]
        s = sum(dist.values()) or 1.0
        for h in range(24):
            rows.append((road, h, round(dist.get(h, 0.0) / s, 5)))   # 등급 재정규화(합=1 보장)

    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["road_type", "hour", "traffic_share"])
        w.writerows(rows)

    # 가드: road_type별 합=1
    chk = defaultdict(float)
    for road, _, sh in rows:
        chk[road] += sh
    bad = {r: round(v, 4) for r, v in chk.items() if abs(v - 1) > 0.01}
    assert not bad, f"합≠1: {bad}"
    print(f"[OK] {len(by_road)}개 road_type × 24시 = {len(rows)}행 → {OUT}")
    print(f"     road_type: {sorted(by_road)}")


if __name__ == "__main__":
    main()
