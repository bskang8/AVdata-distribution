# Experiment Log

## Format
Each experiment entry records: hypothesis → setup → result → next action.

---

## EXP-001 · BM25 vs Embedding vs Hybrid Baseline
**Date**: TBD  
**Status**: 🔲 Not started

**Hypothesis**: Embedding-based search will outperform BM25 for semantic queries (e.g. "pedestrian suddenly enters road"), while BM25 will be faster.

**Setup**:
- Dataset: 83,612 captions (English narrative)
- Eval set: `data/eval/eval_set.json` (20 queries, auto-labelled)
- Metrics: Recall@5, MRR@5, Latency (ms)

**Run**:
```bash
uv run python -m avdata.phase1.build_bm25
uv run python -m avdata.phase2.build_embeddings --limit 10000  # pilot
uv run python -m avdata.eval.build_eval_set
uv run python -m avdata.eval.evaluate
```

**Results**: _(fill after running)_

| Method     | Recall@5 | MRR@5 | Avg Latency (ms) |
|------------|----------|-------|-----------------|
| BM25       |          |       |                 |
| Embedding  |          |       |                 |
| Hybrid     |          |       |                 |

**Analysis**: _(fill after running)_

**Next**: EXP-002 — ODD tag filter ablation

---

## EXP-002 · ODD Tag Filter Ablation (Hybrid Level-1)
**Date**: TBD  
**Status**: 🔲 Not started

**Hypothesis**: Adding ODD tag pre-filter will improve Recall@5 for specific scenario queries while reducing latency.

**Setup**:
- Run Phase 3 ODD tag extraction on full 83k captions
- Test hybrid search with/without `odd_filter` for night & hazard queries

**Run**:
```bash
uv run python -m avdata.phase3.extract_odd_tags
uv run python -m avdata.eval.evaluate  # hybrid with odd_filter
```

**Results**: _(fill after running)_

---

## EXP-003 · Distribution Analysis — Long-tail Discovery
**Date**: TBD  
**Status**: 🔲 Not started

**Hypothesis**: Bottom 5% density clips represent genuinely rare/OOD scenarios.

**Setup**:
```bash
uv run python -m avdata.phase2.build_embeddings        # full 83k
uv run python -m avdata.phase4.distribution_analysis   # UMAP + KDE
```

**Output**: `data/index/distribution.html`, `data/index/longtail_clips.json`

**Analysis**: _(manual review of long-tail clips)_

---

## EXP-004 · Full Scale BM25 (83k clips)
**Date**: TBD  
**Status**: 🔲 Not started

---

## Notes / Lessons Learned
_(append observations here as experiments run)_
