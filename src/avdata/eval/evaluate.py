"""
Evaluation harness — Recall@K, MRR@K, latency for all three search methods.

Run:
  # First build eval_set.json (see build_eval_set.py), then:
  uv run python -m avdata.eval.evaluate

Output: experiments/experiment_001_results.csv
"""
import csv
import json
import time
from pathlib import Path

from avdata.config import EVAL_SET_PATH, EXPERIMENTS_DIR
from avdata.search.searcher import Searcher


def recall_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    if not relevant:
        return 0.0
    return len(set(retrieved[:k]) & set(relevant)) / min(k, len(relevant))


def mrr_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    relevant_set = set(relevant)
    for rank, cid in enumerate(retrieved[:k], start=1):
        if cid in relevant_set:
            return 1.0 / rank
    return 0.0


def run_evaluation(
    eval_set_path: Path = EVAL_SET_PATH,
    top_k: int = 5,
    experiment_id: str = "001",
):
    eval_set: dict[str, list[str]] = json.loads(eval_set_path.read_text())
    searcher = Searcher()

    methods = ["bm25", "embedding", "hybrid"]
    rows: list[dict] = []

    for method in methods:
        recalls, mrrs, latencies = [], [], []
        print(f"\n[{method.upper()}]")

        for query, relevant in eval_set.items():
            results, latency_ms = searcher.search(query, method=method, top_k=top_k)
            retrieved = [r.clip_id for r in results]

            r_at_k = recall_at_k(retrieved, relevant, top_k)
            mrr    = mrr_at_k(retrieved, relevant, top_k)
            recalls.append(r_at_k)
            mrrs.append(mrr)
            latencies.append(latency_ms)

            rows.append({
                "experiment_id": experiment_id,
                "method":        method,
                "query":         query,
                f"recall@{top_k}": round(r_at_k, 4),
                f"mrr@{top_k}":    round(mrr,    4),
                "latency_ms":    round(latency_ms, 2),
            })

        avg_recall  = sum(recalls)  / len(recalls)
        avg_mrr     = sum(mrrs)     / len(mrrs)
        avg_latency = sum(latencies)/ len(latencies)
        print(f"  Recall@{top_k} = {avg_recall:.4f}")
        print(f"  MRR@{top_k}    = {avg_mrr:.4f}")
        print(f"  Latency avg= {avg_latency:.1f} ms")

    # ── Save CSV ───────────────────────────────────────────────────────
    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = EXPERIMENTS_DIR / f"experiment_{experiment_id}_results.csv"
    fieldnames = list(rows[0].keys())
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n  → Results: {out_csv}")


if __name__ == "__main__":
    run_evaluation()
