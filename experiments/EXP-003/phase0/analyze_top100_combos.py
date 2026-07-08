"""Top 100 ODD 조합 필드별 구성 분석 → 결과를 stdout + markdown으로 출력.

기본: odd_compat_v2 (AV 성능 11개 필드)
옵션: python analyze_top100_combos.py odd_compat
"""

import json
import sys
from collections import Counter

ODD_COVERAGE = "output/odd_coverage.json"

schema_key = sys.argv[1] if len(sys.argv) > 1 else "odd_compat_v2"

with open(ODD_COVERAGE) as f:
    d = json.load(f)

top100 = d[schema_key]["combos"]["top100_combos"]
field_names = list(d[schema_key]["fields"].keys())

total_combos = len(top100)
total_clips = sum(x["count"] for x in top100)

# ── 필드별 집계 ──────────────────────────────────────────────────────────
field_stats = {}
for f in field_names:
    val_combos = Counter()
    val_clips = Counter()
    for item in top100:
        v = item["combo"].get(f, "N/A")
        val_combos[v] += 1
        val_clips[v] += item["count"]
    field_stats[f] = {
        "n_unique": len(val_combos),
        "val_combos": val_combos,
        "val_clips": val_clips,
        "is_fixed": len(val_combos) == 1,
    }

fixed_fields = [f for f in field_names if field_stats[f]["is_fixed"]]
varied_fields = [f for f in field_names if not field_stats[f]["is_fixed"]]

# ── 조합 레벨 중복 분석: 변동 필드만 사용한 조합 키 ───────────────────────
varied_key_counter = Counter()
for item in top100:
    key = tuple(item["combo"].get(f, "N/A") for f in varied_fields)
    varied_key_counter[key] += 1

n_duplicated_by_varied = sum(v - 1 for v in varied_key_counter.values() if v > 1)

# ── 출력 ─────────────────────────────────────────────────────────────────
print(f"## Top 100 조합 필드별 구성 분석 [{schema_key}]\n")
print(f"- 총 조합 수: {total_combos}개 | 총 클립 수: {total_clips:,}개")
print(f"- 완전 고정 필드 ({len(fixed_fields)}개): 100개 조합 모두 동일 값 → 이 필드로는 조합을 구분 불가")
print(f"- 변동 필드 ({len(varied_fields)}개): 조합 간 값이 달라지는 필드")
print(f"- 변동 필드 기준 중복 조합: {n_duplicated_by_varied}개 (변동 필드 값 조합이 같은 항목)\n")

# 표 1: 필드별 요약
print("### 표 1. 필드별 요약\n")
print(f"| 필드 | 고유 값 수 | 고정여부 | 최빈 값 | 최빈 조합 수 | 최빈 클립 수 |")
print(f"|------|--------:|:------:|--------|----------:|-----------:|")
for f in field_names:
    s = field_stats[f]
    top_val, top_combo_cnt = s["val_combos"].most_common(1)[0]
    top_clip_cnt = s["val_clips"][top_val]
    fixed_mark = "✓" if s["is_fixed"] else ""
    print(f"| `{f}` | {s['n_unique']} | {fixed_mark} | `{top_val}` | {top_combo_cnt} | {top_clip_cnt:,} |")

# 표 2: 변동 필드 세부 분포
print("\n### 표 2. 변동 필드 세부 값 분포 (top 100 조합 기준)\n")
print(f"| 필드 | 값 | 조합 수 | 조합 비율 | 클립 수 | 클립 비율 |")
print(f"|------|---|------:|--------:|-------:|--------:|")
for f in varied_fields:
    s = field_stats[f]
    for val, c_cnt in s["val_combos"].most_common():
        cl_cnt = s["val_clips"][val]
        print(
            f"| `{f}` | `{val}` | {c_cnt} | {c_cnt/total_combos*100:.0f}% "
            f"| {cl_cnt:,} | {cl_cnt/total_clips*100:.1f}% |"
        )

# 표 3: 고정 필드 목록
print("\n### 표 3. 완전 고정 필드 (100/100 조합에서 단일 값)\n")
print(f"| 필드 | 고정 값 | 의미 |")
print(f"|------|--------|------|")
meanings = {
    "lane_marking_quality": "차선 마킹 선명 — 불량/미존재 사례 없음",
    "precipitation": "강수 없음 — 비·눈 시나리오 상위 100 부재",
    "fog": "안개 없음 — 안개 시나리오 상위 100 부재",
    "road_user_types": "차량만 — 보행자·자전거 상위 100 부재",
    "construction_zone": "공사구간 없음",
    "special_event": "특수 이벤트 없음 (사고·장애물 0)",
    "occlusion_level": "폐색 낮음 — 고폐색 시나리오 상위 100 부재",
    "scene_ambiguity": "장면 모호성 낮음 — 판단 난이도 높은 케이스 부재",
    "unexpected_element": "예상치 못한 요소 없음",
}
for f in fixed_fields:
    val = list(field_stats[f]["val_combos"].keys())[0]
    meaning = meanings.get(f, "")
    print(f"| `{f}` | `{val}` | {meaning} |")

# 표 4: 중복 상위 20개 튜플 구성
n_top = 20
all_top = d[schema_key]["combos"]["top100_combos"]
total_all = d[schema_key]["combos"]["n_clips"]

# 상위 N개 기준 고정/변동 필드 재판정
top_n = all_top[:n_top]
fixed_in_topn = [f for f in field_names
                 if len({item["combo"].get(f) for item in top_n}) == 1]
varied_in_topn = [f for f in field_names if f not in fixed_in_topn]

fixed_vals = {f: top_n[0]["combo"].get(f) for f in fixed_in_topn}

print(f"\n### 표 4. 중복 상위 {n_top}개 튜플 구성\n")
print(f"고정 필드 ({len(fixed_in_topn)}개, 상위 {n_top}개 전체 공통):")
for f, v in fixed_vals.items():
    print(f"  `{f}` = `{v}`")
print()

header = "| 순위 | 클립 수 | 비율 | " + " | ".join(f"`{f}`" for f in varied_in_topn) + " |"
sep    = "|:---:|-------:|:---:|" + "|".join("---" for _ in varied_in_topn) + "|"
print(header)
print(sep)
for rank, item in enumerate(top_n, 1):
    vals = " | ".join(item["combo"].get(f, "N/A") for f in varied_in_topn)
    pct = item["count"] / total_all * 100
    print(f"| {rank} | **{item['count']:,}** | {pct:.2f}% | {vals} |")
