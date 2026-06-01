"""
Phase 3 — Extract ODD (Operational Design Domain) tags from English narrative
captions using regex heuristics (fast, no LLM cost) + optional LLM fallback.

Run:
  # Regex-only (free, fast, ~83k clips in minutes)
  uv run python -m avdata.phase3.extract_odd_tags

  # LLM fallback for clips with low regex coverage
  uv run python -m avdata.phase3.extract_odd_tags --llm --llm-batch 50

Produces:
  data/tags/odd_tags.json   {clip_id: {field: value, ...}, ...}
  data/tags/odd_coverage.json   coverage statistics per field
"""
import argparse
import json
import re
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

from avdata.config import (
    CAPTION_SUFFIX,
    CAPTIONS_DIR,
    ODD_FIELDS,
    ODD_TAGS_PATH,
    TAGS_DIR,
)

# ── Regex heuristics ──────────────────────────────────────────────────────────
# Each entry: (value_label, list_of_regex_patterns)
_HEURISTICS: dict[str, list[tuple[str, list[str]]]] = {
    "time_of_day": [
        ("night",   [r"\bnighttime\b", r"\bnight\b", r"\bnocturnal\b",
                     r"\bafter dark\b", r"\bdarkness\b",
                     r"\bpitch[- ]?black\b", r"\bheadlights?\b",
                     r"\bstreet[- ]?lights?\b"]),
        ("dawn",    [r"\bdawn\b", r"\bearly morning\b", r"\bsunrise\b",
                     r"\bfirst light\b", r"\bpre[- ]?dawn\b"]),
        ("dusk",    [r"\bdusk\b", r"\bevening\b", r"\bsunset\b",
                     r"\btwilight\b", r"\bnightfall\b", r"\bfading light\b"]),
        ("day",     [r"\bdaytime\b", r"\bday\b", r"\bdaylight\b",
                     r"\bsunny\b", r"\bbright\b",
                     r"\bmorning\b", r"\bafternoon\b", r"\bmidday\b", r"\bnoon\b",
                     r"\bwell[- ]?lit\b"]),
    ],
    "weather": [
        ("rain",    [r"\brain\b", r"\brainy\b", r"\braining\b",
                     r"\bwet road\b", r"\bshower\b",
                     r"\bdrizzle\b", r"\bprecipitation\b",
                     r"\bdownpour\b", r"\bpuddles?\b"]),
        ("fog",     [r"\bfog\b", r"\bfoggy\b", r"\bvisibility\b.*poor",
                     r"\bpoor visibility\b",
                     r"\bmist\b", r"\bmisty\b", r"\bhaze\b", r"\bhazy\b",
                     r"\blow[- ]?visibility\b"]),
        ("snow",    [r"\bsnow\b", r"\bsnowy\b", r"\bice\b", r"\bicy\b",
                     r"\bwinter condition\b",
                     r"\bsleet\b", r"\bfrost\b", r"\bblack ice\b", r"\bslippery\b"]),
        ("cloudy",  [r"\bcloudy\b", r"\bovercast\b", r"\bgloomy\b"]),
        ("clear",   [r"\bclear\b", r"\bfair\b", r"\bdry road\b"]),
    ],
    "road_type": [
        ("highway",      [r"\bhighway\b", r"\bfreeway\b", r"\bmotorway\b",
                          r"\bexpressway\b", r"\binterstate\b"]),
        ("intersection", [r"\bintersection\b", r"\bjunction\b",
                          r"\bcrossroad\b", r"\btraffic light\b",
                          r"\bstop sign\b", r"\btraffic signal\b"]),
        ("parking_lot",  [r"\bparking\b", r"\bparked\b", r"\bparking lot\b",
                          r"\bparking area\b"]),
        ("tunnel",       [r"\btunnel\b"]),
        ("bridge",       [r"\bbridge\b", r"\boverpass\b"]),
        ("urban",        [r"\burban\b", r"\bcity\b", r"\bstreet\b",
                          r"\bblock\b", r"\bboulevard\b", r"\bavenue\b"]),
        ("rural",        [r"\brural\b", r"\bcountry road\b", r"\bfarm\b",
                          r"\bfield\b"]),
    ],
    "traffic_density": [
        ("congested", [r"\bcongested\b", r"\bheavy traffic\b",
                       r"\btraffic jam\b", r"\bbumper[- ]to[- ]bumper\b",
                       r"\bqueue\b",
                       r"\bslow[- ]?moving\b", r"\bstop[- ]and[- ]go\b",
                       r"\bbacked[- ]?up\b", r"\bstandstill\b",
                       r"\bgridlock\b", r"\bdense traffic\b", r"\bcrawling\b"]),
        ("moderate",  [r"\bmoderate traffic\b", r"\bsome traffic\b",
                       r"\bseveral vehicles\b",
                       r"\bsteady traffic\b", r"\bmoving vehicles\b"]),
        ("free",      [r"\blight traffic\b", r"\bfree[- ]flowing\b",
                       r"\bminimal traffic\b", r"\bempty road\b",
                       r"\bopen road\b", r"\bsparse traffic\b",
                       r"\bno traffic\b", r"\bdeserted\b"]),
    ],
    "agent_type": [
        ("pedestrian",        [r"\bpedestrian\b", r"\bwalker\b",
                                r"\bperson crossing\b", r"\bpeople crossing\b"]),
        ("cyclist",           [r"\bcyclist\b", r"\bbicycle\b", r"\bbike\b"]),
        ("motorcycle",        [r"\bmotorcycle\b", r"\bmotorbike\b",
                                r"\bscooter\b"]),
        ("truck",             [r"\btruck\b", r"\blorry\b", r"\btrailer\b",
                                r"\bsemi[- ]truck\b"]),
        ("bus",               [r"\bbus\b"]),
        ("emergency_vehicle", [r"\bambulance\b", r"\bfire truck\b",
                                r"\bpolice car\b", r"\bemergency vehicle\b"]),
        ("animal",            [r"\bdog\b", r"\bcat\b", r"\banimal\b",
                                r"\bwildlife\b"]),
    ],
    "hazard_level": [
        ("high",   [r"\bhazard\b", r"\bdanger\b", r"\bcollision\b",
                    r"\bcrash\b", r"\baccident\b", r"\bemergency brake\b",
                    r"\bsudden stop\b", r"\bimminent\b",
                    r"\bnear[- ]?miss\b", r"\bclose[- ]?call\b",
                    r"\baggressive driving\b", r"\bswerved?\b",
                    r"\breckless\b"]),
        ("medium", [r"\bcaution\b", r"\bcareful\b", r"\bprudent\b",
                    r"\baware\b", r"\bvigilant\b", r"\bslow down\b",
                    r"\brisky\b", r"\berratic\b", r"\bunexpected\b"]),
        ("low",    [r"\bsafe\b", r"\bnormal\b", r"\bsmooth\b"]),
        ("none",   [r"\bno hazard\b", r"\bno incident\b"]),
    ],
    "ego_action": [
        ("braking",      [r"\bbrake\b", r"\bbraking\b", r"\bslows? down\b",
                          r"\breduces? speed\b"]),
        ("stopping",     [r"\bstop[ps]?\b", r"\bstands? still\b",
                          r"\bstops? at\b", r"\bhalt\b"]),
        ("left_turn",    [r"\bleft turn\b", r"\bturns? left\b"]),
        ("right_turn",   [r"\bright turn\b", r"\bturns? right\b"]),
        ("uturn",        [r"\bu[- ]?turn\b"]),
        ("lane_change",  [r"\blane change\b", r"\bchanges? lane\b",
                          r"\bmerge\b", r"\bmerging\b", r"\bovertake\b"]),
        ("reversing",    [r"\breverse\b", r"\breversing\b", r"\bback up\b"]),
        ("straight",     [r"\bcontinues?\b", r"\bproceeds?\b",
                          r"\bmaintains? course\b", r"\bstraight\b"]),
    ],
}


def extract_tags_regex(text: str) -> dict[str, str | list[str]]:
    """Return ODD tags extracted by regex heuristics."""
    text_lower = text.lower()
    tags: dict[str, str | list[str]] = {}

    for field, rules in _HEURISTICS.items():
        matched: list[str] = []
        for value, patterns in rules:
            if any(re.search(p, text_lower) for p in patterns):
                matched.append(value)
                if field not in ("agent_type", "ego_action"):
                    break  # first match wins for single-value fields

        if field in ("agent_type", "ego_action"):
            tags[field] = matched if matched else ["none"]
        else:
            tags[field] = matched[0] if matched else "unknown"

    return tags


def coverage_stats(all_tags: dict) -> dict:
    from collections import Counter
    stats: dict[str, dict] = {}
    for field in ODD_FIELDS:
        values = [
            (t[field] if isinstance(t[field], str) else t[field][0])
            for t in all_tags.values()
            if field in t
        ]
        stats[field] = {
            "coverage_pct": round(
                sum(1 for v in values if v != "unknown") / max(len(values), 1) * 100, 1
            ),
            "distribution": dict(Counter(values).most_common()),
        }
    return stats


def build(limit: int | None = None, use_llm: bool = False, llm_batch: int = 50):
    caption_files = sorted(CAPTIONS_DIR.glob(f"*{CAPTION_SUFFIX}"))
    if limit:
        caption_files = caption_files[:limit]

    all_tags: dict[str, dict] = {}

    for txt_file in tqdm(caption_files, desc="Extracting ODD tags"):
        clip_id = txt_file.name[: -len(CAPTION_SUFFIX)]
        text    = txt_file.read_text(encoding="utf-8", errors="replace")
        all_tags[clip_id] = extract_tags_regex(text)

    # ── Optional LLM pass for low-coverage clips ──────────────────────
    if use_llm:
        _llm_fallback(all_tags, caption_files, batch=llm_batch)

    TAGS_DIR.mkdir(parents=True, exist_ok=True)
    ODD_TAGS_PATH.write_text(json.dumps(all_tags, ensure_ascii=False, indent=2))
    print(f"  ODD tags → {ODD_TAGS_PATH}  ({len(all_tags):,} clips)")

    cov = coverage_stats(all_tags)
    cov_path = TAGS_DIR / "odd_coverage.json"
    cov_path.write_text(json.dumps(cov, ensure_ascii=False, indent=2))
    print(f"  Coverage → {cov_path}")
    for field, stat in cov.items():
        print(f"    {field:<20} coverage={stat['coverage_pct']}%")


def _llm_fallback(
    all_tags: dict,
    caption_files: list[Path],
    batch: int,
):
    """Fill 'unknown' fields using an LLM (requires OPENAI_API_KEY env var)."""
    import os
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    unknown_clips = [
        f for f in caption_files
        if any(
            v == "unknown"
            for v in all_tags.get(f.name[: -len(CAPTION_SUFFIX)], {}).values()
        )
    ]
    print(f"  LLM fallback for {len(unknown_clips):,} clips …")

    fields_schema = json.dumps(
        {k: v for k, v in ODD_FIELDS.items()}, ensure_ascii=False
    )

    for i in range(0, min(len(unknown_clips), batch), 1):
        f       = unknown_clips[i]
        clip_id = f.name[: -len(CAPTION_SUFFIX)]
        text    = f.read_text(encoding="utf-8", errors="replace")[:2000]

        prompt = (
            "Extract ODD (Operational Design Domain) tags from the following "
            "autonomous driving clip description.\n"
            f"Return ONLY a JSON object with these fields and allowed values:\n{fields_schema}\n\n"
            f"Description:\n{text}"
        )
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0,
            )
            parsed = json.loads(resp.choices[0].message.content)
            # Merge: only overwrite 'unknown' fields
            for field, val in parsed.items():
                if field in all_tags.get(clip_id, {}) and \
                   all_tags[clip_id][field] == "unknown":
                    all_tags[clip_id][field] = val
        except Exception as e:
            print(f"    LLM error on {clip_id}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",     type=int,  default=None)
    parser.add_argument("--llm",       action="store_true",
                        help="Enable LLM fallback for low-coverage clips")
    parser.add_argument("--llm-batch", type=int,  default=50,
                        help="Max clips to send to LLM")
    args = parser.parse_args()
    build(limit=args.limit, use_llm=args.llm, llm_batch=args.llm_batch)
