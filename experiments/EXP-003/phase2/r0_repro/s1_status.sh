#!/usr/bin/env bash
# G-Q1 / S1 캠페인 진행상황 한눈에. 그냥 실행: bash r0_repro/s1_status.sh
PHASE2="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$PHASE2/r0_repro/output"; OV="$PHASE2/r1_gates/output_val"; STATE="$OUT/s1_claims"
ARMS="baseline c0 c1 c2 c7 c8 c9 c10 c11 c12 c13 c14 c15 c16 c17 c18 c19"
PER_ARM_H=7.8   # 실측 2-GPU 병렬 기준

done=0; running=0; pending=0; run_list=""
for a in $ARMS; do
  if [ -f "$OV/tail_${a}.json" ]; then done=$((done+1))
  elif [ -d "$STATE/claim_${a}" ]; then running=$((running+1)); run_list="$run_list $a"
  else pending=$((pending+1)); fi
done
total=$(echo $ARMS | wc -w)

echo "==================== S1 캠페인 진행 ===================="
echo "완료 $done / $total   |   진행중 $running   |   대기 $pending"
echo "-------------------------------------------------------"
echo "[완료된 arm]"; ls "$OV"/tail_*.json 2>/dev/null | sed 's#.*/tail_##;s#.json##' | tr '\n' ' '; echo
echo "-------------------------------------------------------"
echo "[진행중 arm — 현재 iter / ETA / loss]"
for a in $run_list; do
  full=$(grep "Iter \[" "$OUT/s1_${a}.log" 2>/dev/null | tail -1)
  if [ -z "$full" ]; then echo "  $a : (로그 대기중/모델 빌드중)"; continue; fi
  head=$(echo "$full" | grep -oE "Iter \[[0-9]+/[0-9]+\].*time: [0-9.]+")
  # 핵심 loss만: 총 loss·grad_norm + nan 취약 브랜치(motion/planning). nan이면 그대로 노출됨.
  loss=$(echo "$full" | grep -oE "(loss|grad_norm|motion_loss_reg_0|planning_loss_reg_0): [0-9.na]+" | tr '\n' ' ')
  echo "  $a : $head"
  echo "       $loss"
done
echo "-------------------------------------------------------"
echo "[GPU]"; nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
echo "-------------------------------------------------------"
# 남은 벽시계 추정: (대기+진행중) arm을 2 GPU로 나눠서
remain_arms=$((pending + running))
remain_h=$(python3 -c "import math;print(round(math.ceil($remain_arms/2)*$PER_ARM_H,1))" 2>/dev/null)
echo "예상 잔여: 약 ${remain_h}시간 (남은 arm $remain_arms개 ÷ 2GPU × ${PER_ARM_H}h)"
echo "[러너 살아있나]"
if pgrep -f "s1_campaign.sh" >/dev/null; then
  echo "  캠페인 러너 실행중 ✔"
else
  echo "  ⚠ 캠페인 러너 없음. 전체 재개(재부팅 등) 절차:"
  echo "     rm -rf $STATE   # 죽은 러너의 오래된 claim 정리(안 하면 미완 arm이 막힘)"
  echo "     setsid bash $PHASE2/r0_repro/s1_campaign.sh 1 > $OUT/campaign_gpu1.log 2>&1 &"
  echo "     setsid bash $PHASE2/r0_repro/s1_campaign.sh 0 > $OUT/campaign_gpu0.log 2>&1 &"
  echo "  (완료 arm은 skip, 부분학습 arm은 latest.pth부터 자동 재개)"
fi
echo "======================================================="
