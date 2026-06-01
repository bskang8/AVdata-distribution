"""
Build evaluation set by sampling captions and writing eval_set.json.

Run:
  uv run python -m avdata.eval.build_eval_set          # interactive review mode
  uv run python -m avdata.eval.build_eval_set --auto   # keyword-match auto-label

Auto mode uses keyword heuristics to assign relevant clip IDs per query.
This gives a weak but usable baseline eval set (refine manually later).
"""
import json
import random
import re
from pathlib import Path

from avdata.config import CAPTION_SUFFIX, CAPTIONS_DIR, EVAL_SET_PATH

# 20 representative queries covering key scenario types in the dataset
QUERIES = [
    # Night scenarios
    "pedestrian crossing at night intersection",
    "nighttime driving on poorly lit street",
    "night urban driving with streetlights",
    # Highway scenarios
    "highway driving with truck overtaking",
    "highway lane change merging",
    "highway poor visibility warning sign",
    # Hazard / braking
    "vehicle sudden braking ahead",
    "emergency braking to avoid collision",
    "red light stopping intersection",
    # Pedestrians
    "pedestrian suddenly enters road",
    "pedestrian crossing with dog",
    "children near school zone",
    # Weather
    "foggy conditions reduced visibility",
    "rainy road wet conditions",
    # Parking / slow manoeuvre
    "parking lot reversing",
    "narrow road parked vehicles on both sides",
    # Special agents
    "cyclist entering road unexpectedly",
    "truck parked blocking lane",
    "bus stop with passengers",
    # OOD / rare
    "animal crossing road wildlife",
]


def keyword_relevance(text: str, query: str) -> bool:
    """All long query words (len>3) must appear in the caption."""
    text_lower  = text.lower()
    query_words = [w for w in re.split(r"\W+", query.lower()) if len(w) > 3]
    if not query_words:
        return False
    return all(w in text_lower for w in query_words)


def build_auto(sample_size: int = 5000, min_relevant: int = 2):
    caption_files = sorted(CAPTIONS_DIR.glob(f"*{CAPTION_SUFFIX}"))
    rng           = random.Random(42)
    sample_files  = rng.sample(caption_files, min(sample_size, len(caption_files)))

    # Load texts into memory
    print(f"Loading {len(sample_files):,} captions …")
    corpus = {
        f.name[: -len(CAPTION_SUFFIX)]: f.read_text(encoding="utf-8", errors="replace")
        for f in sample_files
    }

    eval_set: dict[str, list[str]] = {}
    for query in QUERIES:
        relevant = [
            cid for cid, text in corpus.items()
            if keyword_relevance(text, query)
        ]
        if len(relevant) < min_relevant:
            print(f"  SKIP (too few): '{query}'  ({len(relevant)} hits)")
            continue
        print(f"  '{query[:50]}'  →  {len(relevant)} clips")
        eval_set[query] = relevant

    EVAL_SET_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVAL_SET_PATH.write_text(
        json.dumps(eval_set, indent=2, ensure_ascii=False)
    )
    total_relevant = sum(len(v) for v in eval_set.values())
    print(f"\n  → {EVAL_SET_PATH}  ({len(eval_set)} queries, {total_relevant} total relevance labels)")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true",
                        help="Auto-label using keyword heuristics (default)")
    parser.add_argument("--sample", type=int, default=5000,
                        help="Number of captions to sample for auto-labelling")
    args = parser.parse_args()
    build_auto(sample_size=args.sample)

