"""
Phase 1 — Data Exploration
Run:  uv run python -m avdata.phase1.explore
"""
import json
import random
from collections import Counter
from pathlib import Path

from avdata.config import CAPTIONS_DIR, CAPTION_SUFFIX, VIDEOS_DIR, VIDEO_SUFFIX


def get_clip_id(path: Path) -> str:
    """Strip suffix to get bare UUID clip ID."""
    name = path.name
    for suffix in (CAPTION_SUFFIX, VIDEO_SUFFIX):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


def explore():
    caption_files = sorted(CAPTIONS_DIR.glob(f"*{CAPTION_SUFFIX}"))
    video_files   = sorted(VIDEOS_DIR.glob(f"*{VIDEO_SUFFIX}"))

    caption_ids = {get_clip_id(f) for f in caption_files}
    video_ids   = {get_clip_id(f) for f in video_files}

    matched     = caption_ids & video_ids
    caps_only   = caption_ids - video_ids
    videos_only = video_ids   - caption_ids

    print("=" * 60)
    print("DATA OVERVIEW")
    print("=" * 60)
    print(f"  Total video  files : {len(video_files):>8,}")
    print(f"  Total caption files: {len(caption_files):>8,}")
    print(f"  Matched (both)     : {len(matched):>8,}")
    print(f"  Caption only       : {len(caps_only):>8,}")
    print(f"  Video only         : {len(videos_only):>8,}")

    # ── Text length distribution ──────────────────────────────────────
    sample_n   = min(1000, len(caption_files))
    sample_files = random.sample(caption_files, sample_n)
    lengths    = [len(f.read_text(encoding="utf-8").split()) for f in sample_files]

    print(f"\nCAPTION LENGTH (words, n={sample_n} sample)")
    print(f"  min={min(lengths)}  max={max(lengths)}")
    print(f"  mean={sum(lengths)/len(lengths):.1f}")
    buckets = Counter(l // 50 * 50 for l in lengths)
    for bucket in sorted(buckets):
        bar = "█" * (buckets[bucket] * 40 // max(buckets.values()))
        print(f"  {bucket:4d}-{bucket+49:4d} words  {bar} ({buckets[bucket]})")

    # ── Keyword frequency (quick ODD signal) ─────────────────────────
    print("\nKEYWORD FREQUENCY (top-30, from 1000 sample captions)")
    keywords = [
        "night", "nighttime", "day", "daytime", "highway", "intersection",
        "urban", "rural", "rain", "fog", "snow", "pedestrian", "cyclist",
        "truck", "bus", "emergency", "animal", "braking", "stopping",
        "turning", "lane change", "parking", "tunnel", "bridge",
        "congested", "moderate traffic", "hazard", "warning", "accident",
    ]
    text_corpus = " ".join(
        f.read_text(encoding="utf-8").lower() for f in sample_files
    )
    counts = {kw: text_corpus.count(kw) for kw in keywords}
    for kw, cnt in sorted(counts.items(), key=lambda x: -x[1]):
        bar = "█" * (cnt * 30 // max(counts.values(), default=1))
        print(f"  {kw:<20} {bar} ({cnt})")

    # ── Save summary ──────────────────────────────────────────────────
    summary = {
        "total_videos":   len(video_files),
        "total_captions": len(caption_files),
        "matched":        len(matched),
        "sample_lengths": {"min": min(lengths), "max": max(lengths),
                           "mean": round(sum(lengths)/len(lengths), 1)},
        "keyword_counts": counts,
    }
    out_path = Path("data/eval/exploration_summary.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\n  → Summary saved to {out_path}")


if __name__ == "__main__":
    explore()
