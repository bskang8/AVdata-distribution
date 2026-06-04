"""
EXP-002 evaluation harness — Recall@K, MRR@K, latency with warmup.

Features:
  - Warmup dummy queries excluded from latency measurement
  - Per-level metrics (L0, L1, L2, L3, L4)
  - Per-method per-level breakdown CSV
  - Gap-2 fix: Hybrid uses ODD hint extracted from query text

Run:
  uv run python -m avdata.eval.evaluate_v2
  uv run python -m avdata.eval.evaluate_v2 --top-k 10
"""
import csv
import json
import re
import statistics
import time
from pathlib import Path

from avdata.config import EVAL_SET_V2_PATH, EXP002_RESULTS_DIR
from avdata.search.searcher import Searcher

# ── ODD hint extraction (Gap-2 fix) ──────────────────────────────────────────
# keyword → (field, value) 매핑: 쿼리 텍스트에서 ODD 조건을 추출해 Hybrid 필터로 전달
_ODD_PATTERNS: list[tuple[list[str], str, str]] = [
    # (keywords, field, value)
    # time_of_day
    (["night", "nighttime", "after dark", "poorly lit", "dark"],    "time_of_day", "night"),
    (["dawn", "sunrise"],                                            "time_of_day", "dawn"),
    (["dusk", "sunset", "twilight"],                                 "time_of_day", "dusk"),
    # weather
    (["fog", "foggy", "mist", "misty", "atmospheric condition"],     "weather", "fog"),
    (["rain", "rainy", "wet road", "heavy rain", "aquaplaning",
      "slippery surface"],                                           "weather", "rain"),
    (["snow", "snowy", "icy", "ice", "slippery", "winter", "frost"], "weather", "snow"),
    # road_type
    (["highway", "motorway", "freeway", "on-ramp"],                  "road_type", "highway"),
    (["intersection", "crossroads", "crosswalk"],                    "road_type", "intersection"),
    (["parking lot", "parking"],                                     "road_type", "parking_lot"),
    (["tunnel"],                                                     "road_type", "tunnel"),
    (["urban", "city street"],                                       "road_type", "urban"),
    # agent_type
    (["pedestrian", "person walking", "walker", "child", "children",
      "passenger stepping"],                                         "agent_type", "pedestrian"),
    (["cyclist", "bicycle", "bike", "two-wheeler"],                  "agent_type", "cyclist"),
    (["truck", "freight vehicle", "lorry"],                          "agent_type", "truck"),
    (["bus"],                                                        "agent_type", "bus"),
    (["animal", "wildlife"],                                         "agent_type", "animal"),
    # traffic_density
    (["congested", "congestion", "standstill", "heavy traffic",
      "traffic jam"],                                                "traffic_density", "congested"),
    # hazard_level
    (["emergency braking", "near-miss", "near miss", "collision",
      "hard braking", "sudden braking"],                             "hazard_level", "high"),
]


def extract_odd_hint(query: str) -> dict[str, str] | None:
    """쿼리 텍스트에서 ODD 조건을 추출해 Hybrid odd_filter dict로 반환한다.

    각 field는 가장 먼저 매칭된 값 하나만 사용한다 (중복 방지).
    아무 조건도 감지되지 않으면 None을 반환한다.
    """
    q = query.lower()
    hint: dict[str, str] = {}
    for keywords, field, value in _ODD_PATTERNS:
        if field in hint:
            continue  # 이미 이 field에서 값을 찾았으면 스킵
        if any(kw in q for kw in keywords):
            hint[field] = value
    return hint if hint else None


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
    eval_set_path: Path = EVAL_SET_V2_PATH,
    top_k: int = 5,
    experiment_id: str = "002",
):
    if not eval_set_path.exists():
        print(f"[ERROR] eval_set not found: {eval_set_path}")
        print("  Run first: uv run python -m avdata.eval.build_eval_set_v2")
        return

    eval_set: dict = json.loads(eval_set_path.read_text())
    # Filter out queries with no relevant clips
    eval_set = {
        qid: v for qid, v in eval_set.items() if v["n_relevant"] > 0
    }
    if not eval_set:
        print("[ERROR] eval_set has no queries with relevant clips.")
        return

    searcher = Searcher()

    # ── Warmup (excluded from timing) ─────────────────────────────────
    print("Warming up …")
    for method in ("bm25", "embedding", "hybrid"):
        searcher.search("warmup query autonomous driving", method=method, top_k=1)
    print("  done.\n")

    methods  = ["bm25", "embedding", "hybrid"]
    levels   = sorted({v["level"] for v in eval_set.values()})
    rows:    list[dict] = []
    summary: dict[str, dict] = {}  # method → {overall, per_level}
    all_retrieved: dict[tuple[str, str], list[str]] = {}  # (method, qid) → clip_ids

    for method in methods:
        method_rows: list[dict] = []
        latencies: list[float] = []
        hint_count = 0
        print(f"[{method.upper()}]")

        for qid, qdata in eval_set.items():
            qtext    = qdata["text"]
            level    = qdata["level"]
            relevant = qdata["relevant_clip_ids"]

            # Gap-2 fix: extract ODD hint from query text for hybrid searches
            odd_hint = extract_odd_hint(qtext) if method == "hybrid" else None
            if method == "hybrid" and odd_hint:
                hint_count += 1

            results, latency_ms = searcher.search(
                qtext, method=method, top_k=top_k, odd_filter=odd_hint
            )
            retrieved = [r.clip_id for r in results]
            all_retrieved[(method, qid)] = retrieved

            r_at_k = recall_at_k(retrieved, relevant, top_k)
            mrr    = mrr_at_k(retrieved,   relevant, top_k)
            latencies.append(latency_ms)

            row = {
                "experiment_id":   experiment_id,
                "method":          method,
                "level":           level,
                "query_id":        qid,
                "query":           qtext,
                f"recall@{top_k}": round(r_at_k, 4),
                f"mrr@{top_k}":    round(mrr,    4),
                "latency_ms":      round(latency_ms, 2),
                "n_relevant":      len(relevant),
            }
            rows.append(row)
            method_rows.append(row)

        # ── Per-method summary ─────────────────────────────────────────
        all_recalls = [r[f"recall@{top_k}"] for r in method_rows]
        all_mrrs    = [r[f"mrr@{top_k}"]    for r in method_rows]

        print(f"  Overall  Recall@{top_k}={statistics.mean(all_recalls):.4f}  "
              f"MRR@{top_k}={statistics.mean(all_mrrs):.4f}  "
              f"latency_median={statistics.median(latencies):.1f}ms")

        per_level: dict[str, dict] = {}
        for lv in levels:
            lv_rows = [r for r in method_rows if r["level"] == lv]
            if not lv_rows:
                continue
            lv_recalls = [r[f"recall@{top_k}"] for r in lv_rows]
            lv_mrrs    = [r[f"mrr@{top_k}"]    for r in lv_rows]
            per_level[lv] = {
                f"recall@{top_k}": round(statistics.mean(lv_recalls), 4),
                f"mrr@{top_k}":    round(statistics.mean(lv_mrrs),    4),
                "n_queries":       len(lv_rows),
            }
            print(f"  [{lv}]    Recall@{top_k}={per_level[lv][f'recall@{top_k}']:.4f}  "
                  f"MRR@{top_k}={per_level[lv][f'mrr@{top_k}']:.4f}  "
                  f"({per_level[lv]['n_queries']} queries)")

        summary[method] = {
            "overall": {
                f"recall@{top_k}":   round(statistics.mean(all_recalls), 4),
                f"mrr@{top_k}":      round(statistics.mean(all_mrrs),    4),
                "latency_mean_ms":   round(statistics.mean(latencies),   2),
                "latency_median_ms": round(statistics.median(latencies),  2),
                "n_queries":         len(method_rows),
            },
            "per_level": per_level,
        }
        print()

    # ── Axis A key check: L2 gap Embedding vs BM25 ────────────────────
    if "L2" in (summary.get("embedding", {}).get("per_level", {})):
        emb_l2  = summary["embedding"]["per_level"]["L2"][f"recall@{top_k}"]
        bm25_l2 = summary["bm25"]["per_level"]["L2"][f"recall@{top_k}"]
        emb_l0  = summary["embedding"]["per_level"].get("L0", {}).get(f"recall@{top_k}", 0)
        bm25_l0 = summary["bm25"]["per_level"].get("L0", {}).get(f"recall@{top_k}", 0)
        gap_l2  = emb_l2  - bm25_l2
        gap_l0  = emb_l0  - bm25_l0
        print("── Axis A Hypothesis Check ───────────────────────────────────")
        print(f"  Embedding - BM25 Recall@{top_k} gap:")
        print(f"    L0 : {gap_l0:+.4f}  (Emb={emb_l0:.4f}, BM25={bm25_l0:.4f})")
        print(f"    L2 : {gap_l2:+.4f}  (Emb={emb_l2:.4f}, BM25={bm25_l2:.4f})")
        if gap_l2 > gap_l0:
            print("  ✓ PASS: L2 gap > L0 gap (causal queries benefit Embedding more)")
        else:
            print("  ✗ FAIL: L2 gap NOT > L0 gap — revisit hypothesis")
        print()

    # ── Gap-2 verification: Hybrid ≠ Embedding count ──────────────────
    q_ids = list(eval_set.keys())
    hints_with_diff = 0
    hints_same      = 0
    no_hint_diff    = 0
    for qid in q_ids:
        emb_r = all_retrieved.get(("embedding", qid), [])
        hyb_r = all_retrieved.get(("hybrid",    qid), [])
        odd_h = extract_odd_hint(eval_set[qid]["text"])
        if odd_h:
            if emb_r != hyb_r:
                hints_with_diff += 1
            else:
                hints_same += 1
        else:
            if emb_r != hyb_r:
                no_hint_diff += 1
    total_hinted = hints_with_diff + hints_same
    print("── Gap-2 Fix Verification ────────────────────────────────────")
    print(f"  Queries with ODD hint : {total_hinted} / {len(q_ids)}")
    if total_hinted:
        print(f"    Hybrid ≠ Embedding  : {hints_with_diff}  ({hints_with_diff/total_hinted:.1%})")
        print(f"    Hybrid == Embedding : {hints_same}  (fallback — no matching clips)")
    print(f"  Queries without hint  : {len(q_ids) - total_hinted}")
    if hints_with_diff > 0:
        print("  ✓ Gap-2 FIXED: Hybrid now diverges from Embedding for hinted queries")
    elif total_hinted == 0:
        print("  ⚠ No ODD hints detected in this eval set — Gap-2 fix had no effect")
    else:
        print("  ⚠ Hybrid == Embedding for all hinted queries (ODD filter found no candidates)")
    print()

    # ── Save outputs ───────────────────────────────────────────────────
    EXP002_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = EXP002_RESULTS_DIR / f"experiment_{experiment_id}_results.csv"
    fieldnames = list(rows[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    summary_path = EXP002_RESULTS_DIR / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    print(f"  → CSV    : {csv_path}")
    print(f"  → Summary: {summary_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-set", type=Path, default=EVAL_SET_V2_PATH)
    parser.add_argument("--top-k",   type=int,  default=5)
    args = parser.parse_args()
    run_evaluation(eval_set_path=args.eval_set, top_k=args.top_k)
