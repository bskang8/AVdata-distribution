"""전사: raw/ktdb/vkt_sample.csv → sources/vkt_weight.csv (w_vkt 블록).

raw는 (grade, share) — 등급별 관측교통량 구성비. sources 계약은 (road_type, vkt_share),
keys=[]이므로 전 행 합=1. grade→road_type는 mapping.yaml §5-3.

# ponytail: 지방도·국지도(dtype 3,5)는 API 백엔드 502(구조적 미제공), urban·tunnel은 itmsh
#           대상 자체가 아님 → 이 표는 전체 road_type 분포가 아니라 '고속+일반국도 노출
#           구성비'. 한계는 sources/COVERAGE.md + recon vocab_missing에 명시. 복구 시 재실행.
실행:  python3 transcribe_vkt.py   (이후 loader.py로 계약 검증)
"""
import csv
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from paths import RAW, SOURCES

SRC = os.path.join(RAW, "ktdb", "vkt_sample.csv")
OUT = os.path.join(SOURCES, "vkt_weight.csv")

GRADE2ROAD = {          # mapping.yaml §5-3
    "고속도로": "highway",
    "일반도로": "national_road",
    "지방도": "rural",
    "국가지원지방도": "rural",
}


def main():
    by_road = defaultdict(float)     # road_type -> share (등급 여러 개가 한 road_type이면 합산)
    for r in csv.DictReader(open(SRC)):
        road = GRADE2ROAD.get(r["grade"])
        if not road:
            continue
        by_road[road] += float(r["share"])

    # 커버된 등급 안에서 재정규화(합=1 보장) — 미확보 등급은 애초 분모에 없음(그게 한계)
    s = sum(by_road.values()) or 1.0
    rows = [(road, round(by_road[road] / s, 5)) for road in sorted(by_road)]

    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["road_type", "vkt_share"])
        w.writerows(rows)

    assert abs(sum(sh for _, sh in rows) - 1) < 0.01, f"합≠1: {rows}"
    print(f"[OK] {len(rows)}개 road_type = {rows} → {OUT}")
    print(f"     ⚠ 커버 road_type: {sorted(by_road)} (urban·tunnel·rural[지방도/국지도] 미포함 — COVERAGE.md 참조)")


if __name__ == "__main__":
    main()
