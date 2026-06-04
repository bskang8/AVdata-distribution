"""
Phase 6 Step 2: ODD Coverage Matrix

Counts (weather × time_of_day × road_type × hazard_level) combination coverage
from odd_tags.json and reports zero-coverage gaps.

Run:
  uv run python -m avdata.phase6.odd_coverage_matrix
"""
import json
from collections import Counter
from itertools import product
from pathlib import Path

from avdata.config import ACTIVE_DIR, ODD_COVERAGE_PATH, ODD_FIELDS

AXES = ["weather", "time_of_day", "road_type", "hazard_level"]


def run(output_path: Path = ODD_COVERAGE_PATH) -> dict:
    tags_path = ACTIVE_DIR / "odd_tags.json"
    odd_tags: dict = json.loads(tags_path.read_text())

    combo_counter: Counter = Counter()
    field_counter: dict[str, Counter] = {ax: Counter() for ax in AXES}

    for tags in odd_tags.values():
        combo = tuple(tags.get(ax, "unknown") for ax in AXES)
        combo_counter[combo] += 1
        for ax in AXES:
            field_counter[ax][tags.get(ax, "unknown")] += 1

    total = len(odd_tags)
    all_vals = [ODD_FIELDS.get(ax, ["unknown"]) for ax in AXES]
    possible_combos = list(product(*all_vals))
    possible = len(possible_combos)

    zero_combos = [
        dict(zip(AXES, combo))
        for combo in possible_combos
        if combo not in combo_counter
    ]
    covered = possible - len(zero_combos)  # within-taxonomy only

    output = {
        "total_clips": total,
        "axes": AXES,
        "possible_combinations": possible,
        "covered_combinations": covered,
        "coverage_rate": round(covered / possible, 4),
        "per_field_distribution": {
            ax: dict(sorted(field_counter[ax].items(), key=lambda x: -x[1]))
            for ax in AXES
        },
        "top_50_combos": [
            {"combo": dict(zip(AXES, k)), "count": v}
            for k, v in combo_counter.most_common(50)
        ],
        "bottom_50_combos": [
            {"combo": dict(zip(AXES, k)), "count": v}
            for k, v in combo_counter.most_common()[:-51:-1]
        ],
        "zero_coverage_count": len(zero_combos),
        "zero_coverage_combos": zero_combos[:100],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))

    print(f"Total clips          : {total:,}")
    print(f"Possible combos      : {possible}")
    print(f"Covered combos       : {covered} ({covered/possible:.1%})")
    print(f"Zero-coverage gaps   : {len(zero_combos)}")
    print(f"\nPer-field top-3:")
    for ax in AXES:
        top3 = list(field_counter[ax].most_common(3))
        print(f"  {ax:20s}: {top3}")
    print(f"\n→ {output_path}")
    return output


if __name__ == "__main__":
    run()
