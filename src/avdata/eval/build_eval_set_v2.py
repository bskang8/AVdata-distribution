"""
EXP-002 Axis A — LLM-based evaluation set builder.

Builds eval_set_v2.json with semantically labeled ground truth.

Candidate pool per query:
  BM25 top-50 + Embedding top-50 + 15 random clips (ceiling-fix)
  → deduplicated → scored by GPT-4o-mini

Relevance thresholds:
  L0/L1/L4 : condition_score >= 2
  L2/L3    : condition_score + causal_score >= 3

Run:
  uv run python -m avdata.eval.build_eval_set_v2 \\
      --queries data/eval/queries_v2.json \\
      --candidate-k 50 \\
      --random-k 15 \\
      --llm-model gpt-4o-mini \\
      --output data/eval/eval_set_v2.json
"""
import argparse
import json
import os
import random
import time
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

from avdata.config import (
    CAPTION_SUFFIX,
    CAPTIONS_DIR,
    CLIP_IDS_PATH,
    EVAL_SET_V2_PATH,
    QUERIES_V2_PATH,
)
from avdata.search.searcher import Searcher

# ── LLM relevance prompt ──────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are an expert autonomous driving data annotator.
Given a search query and a clip caption, score the caption's relevance.
Return ONLY valid JSON with exactly these three keys."""

_USER_TEMPLATE = """\
Query: {query}
Caption: {caption}

Score relevance on two dimensions:
- condition_score (0-2): Does the caption describe the environmental/situational conditions in the query?
  0 = unrelated, 1 = partial match, 2 = full match
- causal_score (0-2): Does the caption capture the causal chain described in the query (cause → reaction → outcome)?
  0 = no causal chain / unrelated, 1 = partial, 2 = full match
- relevant (true/false): Overall relevance judgment

Return JSON:
{{"condition_score": <int>, "causal_score": <int>, "relevant": <bool>}}"""


def _relevance_threshold(level: str, condition: int, causal: int) -> bool:
    if level in ("L2", "L3"):
        return (condition + causal) >= 3
    return condition >= 2


def _load_all_clip_ids() -> list[str]:
    if CLIP_IDS_PATH.exists():
        return json.loads(CLIP_IDS_PATH.read_text())
    # Fallback: enumerate caption files
    return [
        f.name[: -len(CAPTION_SUFFIX)]
        for f in sorted(CAPTIONS_DIR.glob(f"*{CAPTION_SUFFIX}"))
    ]


def _load_caption(clip_id: str) -> str:
    path = CAPTIONS_DIR / f"{clip_id}{CAPTION_SUFFIX}"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[:3000]


def _score_with_llm(
    client,
    model: str,
    query: str,
    caption: str,
    retries: int = 2,
) -> dict:
    for attempt in range(retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": _USER_TEMPLATE.format(
                        query=query, caption=caption[:2000]
                    )},
                ],
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=64,
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            if attempt == retries:
                print(f"      LLM error: {e}")
                return {"condition_score": 0, "causal_score": 0, "relevant": False}
            time.sleep(1.5)
    return {"condition_score": 0, "causal_score": 0, "relevant": False}


def build(
    queries_path: Path = QUERIES_V2_PATH,
    candidate_k: int = 50,
    random_k: int = 15,
    llm_model: str = "gpt-4o-mini",
    output_path: Path = EVAL_SET_V2_PATH,
    dry_run: bool = False,
):
    queries = json.loads(queries_path.read_text())
    all_clip_ids = _load_all_clip_ids()
    rng = random.Random(42)

    searcher = Searcher()

    # LLM client (lazy init — skip in dry-run mode)
    client = None
    if not dry_run:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    # Warmup searcher
    print("Warming up searcher …")
    searcher.search("warmup", method="embedding", top_k=1)
    searcher.search("warmup", method="bm25", top_k=1)

    # ── Resume from checkpoint if exists ──────────────────────────────
    eval_set: dict = {}
    if output_path.exists() and not dry_run:
        try:
            existing = json.loads(output_path.read_text())
            # Only resume entries explicitly marked as LLM-sourced
            eval_set = {
                qid: v for qid, v in existing.items()
                if v.get("source") == "llm"
            }
            if eval_set:
                print(f"  Resuming from checkpoint: {len(eval_set)}/{len(queries)} queries already done")
        except Exception:
            eval_set = {}

    total_llm_calls = 0

    for q in tqdm(queries, desc="Building eval set"):
        qid    = q["id"]
        level  = q["level"]
        qtext  = q["text"]

        # Skip already completed queries
        if qid in eval_set:
            print(f"  {qid} [{level}] → skip (already done, {eval_set[qid]['n_relevant']} relevant)")
            continue

        # ── Build candidate pool ───────────────────────────────────────
        bm25_results, _   = searcher.search(qtext, method="bm25",      top_k=candidate_k)
        emb_results,  _   = searcher.search(qtext, method="embedding",  top_k=candidate_k)

        candidate_ids: set[str] = set()
        candidate_ids.update(r.clip_id for r in bm25_results)
        candidate_ids.update(r.clip_id for r in emb_results)

        # Ceiling fix: add random samples not already in pool
        random_pool = [c for c in all_clip_ids if c not in candidate_ids]
        candidate_ids.update(rng.sample(random_pool, min(random_k, len(random_pool))))

        candidates = list(candidate_ids)

        # ── Score with LLM ─────────────────────────────────────────────
        relevant_ids:  list[str] = []
        scored_details: list[dict] = []

        for clip_id in candidates:
            caption = _load_caption(clip_id)
            if not caption:
                continue

            if dry_run:
                cap_lower = caption.lower()
                long_words = [w for w in qtext.lower().split() if len(w) > 3]
                matched = sum(1 for w in long_words if w in cap_lower)
                ratio = matched / max(len(long_words), 1)
                condition_score = 2 if ratio >= 0.7 else (1 if ratio >= 0.4 else 0)

                # L2/L3: check for causal language in caption
                causal_score = 0
                if level in ("L2", "L3"):
                    causal_kws = [
                        "caus", "trigger", "lead", "result", "forc",
                        "sudden", "emergency", "collision", "avoid",
                        "brak", "swerv", "slip", "skid",
                    ]
                    causal_score = 1 if any(kw in cap_lower for kw in causal_kws) else 0

                score = {
                    "condition_score": condition_score,
                    "causal_score":    causal_score,
                    "relevant": False,
                }
            else:
                score = _score_with_llm(client, llm_model, qtext, caption)
                total_llm_calls += 1

            score["relevant"] = _relevance_threshold(
                level, score["condition_score"], score["causal_score"]
            )
            if score["relevant"]:
                relevant_ids.append(clip_id)
            scored_details.append({"clip_id": clip_id, **score})

        eval_set[qid] = {
            "source": "dry_run" if dry_run else "llm",
            "level": level,
            "text":  qtext,
            "relevant_clip_ids": relevant_ids,
            "n_candidates": len(candidates),
            "n_relevant": len(relevant_ids),
            "scored_details": scored_details,
        }

        # Save checkpoint after every query
        if not dry_run:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(eval_set, indent=2, ensure_ascii=False))

        # Ceiling-fix diagnostic: count random hits
        random_relevant = [
            s for s in scored_details
            if s["clip_id"] not in {r.clip_id for r in bm25_results + emb_results}
            and s["relevant"]
        ]
        print(
            f"  {qid} [{level}] → {len(relevant_ids):3d} relevant "
            f"| random hits: {len(random_relevant)} / {random_k}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(eval_set, indent=2, ensure_ascii=False))
    print(f"\n  → {output_path}")
    print(f"     Queries: {len(eval_set)}")
    print(f"     Total LLM calls: {total_llm_calls:,}")
    total_rel = sum(v["n_relevant"] for v in eval_set.values())
    print(f"     Total relevant labels: {total_rel:,}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries",      type=Path, default=QUERIES_V2_PATH)
    parser.add_argument("--candidate-k",  type=int,  default=50)
    parser.add_argument("--random-k",     type=int,  default=15)
    parser.add_argument("--llm-model",    type=str,  default="gpt-4o-mini")
    parser.add_argument("--output",       type=Path, default=EVAL_SET_V2_PATH)
    parser.add_argument("--dry-run",      action="store_true",
                        help="Skip LLM calls; use keyword heuristic (smoke test)")
    args = parser.parse_args()
    build(
        queries_path=args.queries,
        candidate_k=args.candidate_k,
        random_k=args.random_k,
        llm_model=args.llm_model,
        output_path=args.output,
        dry_run=args.dry_run,
    )
