#!/usr/bin/env bash
# EXP-002 Phase A: Gap-2 fix → ODD Coverage → Embedding Cluster
# Run from repo root: bash scripts/run_phase_a.sh
# Options:
#   --no-llm   skip LLM labeling (saves ~$0.004, OPENAI_API_KEY required)
#   --top-k N  Recall@K for evaluation (default 5)
set -euo pipefail

# .env 파일이 있으면 환경변수로 로드
[ -f .env ] && export $(grep -v '^#' .env | xargs)

NO_LLM=""
TOP_K=5
for arg in "$@"; do
  case $arg in
    --no-llm) NO_LLM="--no-llm" ;;
    --top-k=*) TOP_K="${arg#*=}" ;;
  esac
done

echo "════════════════════════════════════════════"
echo " EXP-002 Phase A"
echo "════════════════════════════════════════════"

echo ""
echo "── Step 1: Hybrid re-evaluation (Gap-2 fix) ──"
uv run python -m avdata.eval.evaluate_v2 --top-k "$TOP_K"

echo ""
echo "── Step 2: ODD Coverage Matrix ──"
uv run python -m avdata.phase6.odd_coverage_matrix

echo ""
echo "── Step 3: Embedding Clustering + Magnitude + LLM labels ──"
uv run python -m avdata.phase6.embedding_cluster $NO_LLM

echo ""
echo "════════════════════════════════════════════"
echo " Phase A complete. Results in experiments/EXP-002/results/"
echo "════════════════════════════════════════════"
