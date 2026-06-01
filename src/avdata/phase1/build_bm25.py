"""
Phase 1 — Build BM25 index over all caption files (using bm25s — 10-30× faster).

Run:  uv run python -m avdata.phase1.build_bm25
      uv run python -m avdata.phase1.build_bm25 --limit 1000   # quick test

Produces:  data/index/bm25s_index/   (directory)
           data/index/clip_ids.json  (shared with Phase 2)
"""
import argparse
import json
from pathlib import Path

import bm25s
from tqdm import tqdm

from avdata.config import (
    BM25_INDEX_DIR,
    CAPTION_SUFFIX,
    CAPTIONS_DIR,
    CLIP_IDS_PATH,
)


def build(limit: int | None = None):
    caption_files = sorted(CAPTIONS_DIR.glob(f"*{CAPTION_SUFFIX}"))
    if limit:
        caption_files = caption_files[:limit]

    print(f"Reading {len(caption_files):,} captions …")
    clip_ids: list[str] = []
    texts:    list[str] = []
    for txt_file in tqdm(caption_files, desc="Reading"):
        clip_ids.append(txt_file.name[: -len(CAPTION_SUFFIX)])
        texts.append(txt_file.read_text(encoding="utf-8", errors="replace"))

    # bm25s built-in English tokeniser (stopword removal + stemming)
    print("Tokenising …")
    corpus_tokens = bm25s.tokenize(texts, stopwords="en", show_progress=True)

    print(f"Building bm25s index over {len(texts):,} documents …")
    retriever = bm25s.BM25()
    retriever.index(corpus_tokens)

    BM25_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    retriever.save(str(BM25_INDEX_DIR))
    CLIP_IDS_PATH.write_text(json.dumps(clip_ids, ensure_ascii=False))

    print(f"  bm25s index → {BM25_INDEX_DIR}")
    print(f"  Clip ID list→ {CLIP_IDS_PATH}")
    print(f"  Total docs  : {len(clip_ids):,}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None,
                        help="Process only first N captions (for testing)")
    args = parser.parse_args()
    build(limit=args.limit)
