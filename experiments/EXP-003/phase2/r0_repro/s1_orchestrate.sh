#!/usr/bin/env bash
# G-Q1 / S1 자율 오케스트레이터: prep 완료 대기 → 양 GPU 캠페인 자동 시작.
# setsid로 띄우면 Claude 세션 종료와 무관하게 끝까지 자율 진행.
#   setsid bash s1_orchestrate.sh > output/s1_orchestrate.log 2>&1 &
set -uo pipefail
PHASE2="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$PHASE2/r0_repro/output"
PREPLOG="$OUT/s1_prep_full.log"

echo "[orch] prep 완료 대기 시작 $(date +%H:%M:%S)"
until grep -q "leave-out pkl" "$PREPLOG" 2>/dev/null; do
  grep -qE "Traceback|Error:" "$PREPLOG" 2>/dev/null && { echo "[orch] PREP 실패 — 중단 $(date)"; exit 1; }
  sleep 15
done
echo "[orch] prep 완료 확인 $(date +%H:%M:%S)"
grep -E "prep\]" "$PREPLOG" | grep -vE "warn"

# 양 GPU 캠페인 각각 독립 세션(detached)으로 시작. mkdir-claim으로 arm 자동 분배.
setsid bash "$PHASE2/r0_repro/s1_campaign.sh" 1 > "$OUT/campaign_gpu1.log" 2>&1 &
sleep 3   # baseline claim을 GPU1이 먼저 잡도록 소폭 스태거
setsid bash "$PHASE2/r0_repro/s1_campaign.sh" 0 > "$OUT/campaign_gpu0.log" 2>&1 &
echo "[orch] GPU1·GPU0 캠페인 시작 $(date +%H:%M:%S) — 로그: campaign_gpu{0,1}.log"
