#!/usr/bin/env bash
# G-Q1 / S1 병렬 캠페인 러너 — 한 GPU에서 미청구 arm을 하나씩 집어 순차 실행.
# 두 인스턴스를 각 GPU에 띄우면 mkdir(원자적) 청구로 자동 로드밸런싱.
#   setsid bash s1_campaign.sh 1 > output/campaign_gpu1.log 2>&1 &   # GPU1
#   setsid bash s1_campaign.sh 0 > output/campaign_gpu0.log 2>&1 &   # GPU0(Carla 공유)
# 재개 가능: tail_<arm>.json 있으면 skip. 크래시 arm은 claim_<arm> 수동 삭제 후 재개.
# 모든 arm bs4 통일(ΔTail 정합). arm 순서: baseline 먼저(공유 기준).
set -uo pipefail

GPU=${1:?gpu 인자 필요 (0|1)}
PHASE2="$(cd "$(dirname "$0")/.." && pwd)"
R1="$PHASE2/r1_gates"
OUT="$R1/output_val"
STATE="$PHASE2/r0_repro/output/s1_claims"
mkdir -p "$STATE"

# val 슬라이스 ≥30 클러스터 + baseline. 균질(~7h/arm)이라 정적 리스트로 충분, 청구는 동적.
ARMS="baseline c0 c1 c2 c7 c8 c9 c10 c11 c12 c13 c14 c15 c16 c17 c18 c19"

export S1_EPOCHS=10 S1_BATCH=4 PYTHONUNBUFFERED=1

for arm in $ARMS; do
  [ -f "$OUT/tail_${arm}.json" ] && { echo "[gpu$GPU] skip $arm (완료됨)"; continue; }
  mkdir "$STATE/claim_${arm}" 2>/dev/null || { echo "[gpu$GPU] skip $arm (타 GPU 청구)"; continue; }
  echo "[gpu$GPU] ▶ $arm 시작 $(date +%H:%M:%S)"
  bash "$PHASE2/r0_repro/s1_run.sh" "$arm" "$GPU" \
    && echo "[gpu$GPU] ✔ $arm 완료 $(date +%H:%M:%S)" \
    || echo "[gpu$GPU] XX $arm 실패 — claim 남김(재개시 claim_${arm} 삭제)"
done
echo "[gpu$GPU] 큐 소진, 종료 $(date +%H:%M:%S)"
