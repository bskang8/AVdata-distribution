"""
EXP-002 Axis B — Extract 7-dimensional continuous ODD variables from captions.

7D ODD space:
  visibility_level       [0.0=dense fog, 1.0=clear day]
  precipitation_intensity[0.0=none,      1.0=heavy rain/snow]
  traffic_density_cont   [0.0=empty,     1.0=standstill]
  hazard_proximity       [0.0=safe,       1.0=imminent collision]
  agent_density          [0.0=no agents, 1.0=many complex agents]
  lighting_level         [0.0=pitch dark, 1.0=bright daylight]
  road_type_encoded      [parking_lot=0.05 … highway=0.90]

Strategy:
  1. Convert existing regex tags → approximate continuous values (full 299k, free)
  2. LLM refinement for low-coverage clips (53k unknown clips, ~$5)

Run:
  # Regex baseline only (no LLM cost)
  uv run python -m avdata.phase3.extract_odd_continuous --target all --no-llm

  # LLM refinement for unknown-heavy clips
  uv run python -m avdata.phase3.extract_odd_continuous --target unknown --batch 200

  # Full LLM pass (expensive: ~$30 for 299k)
  uv run python -m avdata.phase3.extract_odd_continuous --target all --batch 500
"""
import argparse
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

from avdata.config import (
    CAPTION_SUFFIX,
    CAPTIONS_DIR,
    ODD_CONTINUOUS_PATH,
    ODD_TAGS_PATH,
    TAGS_DIR,
)

ODD_DIMS = [
    "visibility_level",
    "precipitation_intensity",
    "traffic_density_cont",
    "hazard_proximity",
    "agent_density",
    "lighting_level",
    "road_type_encoded",
]

# ── Regex-tag → continuous mapping ───────────────────────────────────────────

_WEATHER_MAP: dict[str, dict] = {
    "fog":     {"visibility_level": 0.12, "precipitation_intensity": 0.05},
    "rain":    {"visibility_level": 0.60, "precipitation_intensity": 0.65},
    "snow":    {"visibility_level": 0.50, "precipitation_intensity": 0.72},
    "cloudy":  {"visibility_level": 0.80, "precipitation_intensity": 0.02},
    "clear":   {"visibility_level": 0.98, "precipitation_intensity": 0.00},
    "unknown": {"visibility_level": None,  "precipitation_intensity": None},
}

_TRAFFIC_MAP: dict[str, float] = {
    "congested": 0.85,
    "moderate":  0.50,
    "free":      0.10,
    "unknown":   None,
}

_HAZARD_MAP: dict[str, float] = {
    "high":    0.85,
    "medium":  0.50,
    "low":     0.20,
    "none":    0.03,
    "unknown": None,
}

_TIME_MAP: dict[str, float] = {
    "night":   0.08,
    "dawn":    0.28,
    "dusk":    0.32,
    "day":     0.92,
    "unknown": None,
}

_ROAD_MAP: dict[str, float] = {
    "parking_lot":   0.05,
    "tunnel":        0.20,
    "urban":         0.35,
    "intersection":  0.42,
    "rural":         0.60,
    "bridge":        0.70,
    "highway":       0.92,
    "unknown":       None,
}


def _agent_density(agent_type) -> float | None:
    if isinstance(agent_type, list):
        active = [a for a in agent_type if a != "none"]
    elif isinstance(agent_type, str):
        active = [] if agent_type in ("none", "unknown") else [agent_type]
    else:
        return None
    n = len(active)
    if n == 0:
        return 0.05
    if n == 1:
        return 0.30
    if n == 2:
        return 0.60
    return 0.85


def regex_tags_to_continuous(tags: dict) -> dict:
    weather  = tags.get("weather", "unknown")
    w_vals   = _WEATHER_MAP.get(weather, _WEATHER_MAP["unknown"])

    return {
        "visibility_level":        w_vals["visibility_level"],
        "precipitation_intensity": w_vals["precipitation_intensity"],
        "traffic_density_cont":    _TRAFFIC_MAP.get(
                                       tags.get("traffic_density", "unknown"),
                                       None),
        "hazard_proximity":        _HAZARD_MAP.get(
                                       tags.get("hazard_level", "unknown"),
                                       None),
        "agent_density":           _agent_density(tags.get("agent_type", "unknown")),
        "lighting_level":          _TIME_MAP.get(
                                       tags.get("time_of_day", "unknown"),
                                       None),
        "road_type_encoded":       _ROAD_MAP.get(
                                       tags.get("road_type", "unknown"),
                                       None),
        "source": "regex",
    }


# ── LLM extraction ────────────────────────────────────────────────────────────

_LLM_SYSTEM = """\
You are an autonomous driving data analyst.
Extract 7 continuous ODD (Operational Design Domain) variables from a clip caption.
Return ONLY valid JSON with exactly these 7 float keys."""

_LLM_USER = """\
Caption: {caption}

Extract continuous values (all 0.0–1.0):
- visibility_level:        0.0=dense fog/smoke, 1.0=perfectly clear
- precipitation_intensity: 0.0=none, 1.0=heavy rain/blizzard
- traffic_density_cont:    0.0=empty road, 1.0=complete standstill gridlock
- hazard_proximity:        0.0=no hazard, 1.0=imminent collision
- agent_density:           0.0=no other agents, 1.0=crowded with many complex agents
- lighting_level:          0.0=pitch dark, 1.0=bright daylight
- road_type_encoded:       0.05=parking lot, 0.20=tunnel, 0.35=urban, 0.42=intersection, 0.60=rural, 0.70=bridge, 0.92=highway

Return JSON: {{"visibility_level": float, "precipitation_intensity": float,
"traffic_density_cont": float, "hazard_proximity": float, "agent_density": float,
"lighting_level": float, "road_type_encoded": float}}"""

_LLM_KEYS = [
    "visibility_level", "precipitation_intensity", "traffic_density_cont",
    "hazard_proximity", "agent_density", "lighting_level", "road_type_encoded",
]


def _llm_extract_batch(client, model: str, items: list[tuple[str, str]]) -> list[dict]:
    results = []
    for clip_id, caption in items:
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": _LLM_SYSTEM},
                    {"role": "user",   "content": _LLM_USER.format(
                        caption=caption[:2500])},
                ],
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=128,
            )
            parsed = json.loads(resp.choices[0].message.content)
            # Clamp to [0, 1]
            row = {k: max(0.0, min(1.0, float(parsed.get(k, 0.5))))
                   for k in _LLM_KEYS}
            row["source"] = "llm"
        except Exception as e:
            print(f"  LLM error on {clip_id}: {e}")
            row = {k: None for k in _LLM_KEYS}
            row["source"] = "error"
        results.append((clip_id, row))
        time.sleep(0.05)  # gentle rate limit
    return results


def _has_nulls(vec: dict) -> bool:
    return any(vec.get(k) is None for k in _LLM_KEYS)


def build(
    target: str = "unknown",
    use_llm: bool = True,
    llm_model: str = "gpt-4o-mini",
    batch_size: int = 200,
    limit: int | None = None,
):
    # ── Step 1: regex baseline from existing tags ──────────────────────
    all_continuous: dict[str, dict] = {}

    if ODD_TAGS_PATH.exists():
        print(f"Loading regex tags from {ODD_TAGS_PATH} …")
        odd_tags = json.loads(ODD_TAGS_PATH.read_text())
        for clip_id, tags in tqdm(odd_tags.items(), desc="Regex → continuous"):
            all_continuous[clip_id] = regex_tags_to_continuous(tags)
    else:
        print("  odd_tags.json not found — skipping regex baseline")
        print("  Run phase3/extract_odd_tags.py first for better coverage")

    # ── Step 2: enumerate captions not yet converted ───────────────────
    caption_files = sorted(CAPTIONS_DIR.glob(f"*{CAPTION_SUFFIX}"))
    if limit:
        caption_files = caption_files[:limit]

    for f in caption_files:
        cid = f.name[: -len(CAPTION_SUFFIX)]
        if cid not in all_continuous:
            all_continuous[cid] = {k: None for k in _LLM_KEYS}
            all_continuous[cid]["source"] = "missing"

    # ── Step 3: LLM refinement ─────────────────────────────────────────
    if use_llm:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

        if target == "unknown":
            # Only clips with any None value
            to_process = [
                cid for cid, vec in all_continuous.items() if _has_nulls(vec)
            ]
        else:
            to_process = list(all_continuous.keys())

        print(f"LLM extraction for {len(to_process):,} clips …")

        for i in tqdm(range(0, len(to_process), batch_size),
                      desc="LLM batches"):
            batch_ids = to_process[i: i + batch_size]
            items = []
            for cid in batch_ids:
                path = CAPTIONS_DIR / f"{cid}{CAPTION_SUFFIX}"
                if path.exists():
                    items.append((cid, path.read_text(
                        encoding="utf-8", errors="replace")[:2500]))

            for cid, row in _llm_extract_batch(client, llm_model, items):
                if row["source"] != "error":
                    all_continuous[cid] = row

    # ── Save ───────────────────────────────────────────────────────────
    TAGS_DIR.mkdir(parents=True, exist_ok=True)
    ODD_CONTINUOUS_PATH.write_text(
        json.dumps(all_continuous, ensure_ascii=False, indent=None)
    )
    print(f"\n  ODD continuous → {ODD_CONTINUOUS_PATH}  ({len(all_continuous):,} clips)")

    # Coverage report
    null_counts = {k: 0 for k in _LLM_KEYS}
    for vec in all_continuous.values():
        for k in _LLM_KEYS:
            if vec.get(k) is None:
                null_counts[k] += 1
    total = len(all_continuous)
    print("\n  Coverage:")
    for k, null_n in null_counts.items():
        pct = (total - null_n) / max(total, 1) * 100
        print(f"    {k:<30} {pct:5.1f}%  ({null_n:,} null)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target",  choices=["unknown", "all"], default="unknown")
    parser.add_argument("--no-llm",  action="store_true", help="Regex baseline only")
    parser.add_argument("--llm-model", default="gpt-4o-mini")
    parser.add_argument("--batch",   type=int, default=200)
    parser.add_argument("--limit",   type=int, default=None)
    args = parser.parse_args()
    build(
        target=args.target,
        use_llm=not args.no_llm,
        llm_model=args.llm_model,
        batch_size=args.batch,
        limit=args.limit,
    )
