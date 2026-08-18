#!/usr/bin/env bash
# G-Q1 / S1 한 arm(baseline 또는 leave-out cK) 학습→eval→tail. stage2-only(stage1 동결), 단일 GPU.
# 사용: bash s1_run.sh <arm> [gpu]      arm = baseline | c<K>   (예: c5)
# detach: setsid PYTHONUNBUFFERED=1 로 호출측에서 감쌀 것(아래 nohup 아님, 호출측 setsid 권장).
# 학습/eval 모두 --launcher none(비분산). GPU0은 타 사용자 Carla 상주 가능 → gpu 인자로 1 지정 권장.
set -euo pipefail

ARM=${1:?arm 필요: baseline | c<K>}
GPU=${2:-1}
PHASE2="$(cd "$(dirname "$0")/.." && pwd)"
SD="$PHASE2/third_party/sparsedrive"
R1="$PHASE2/r1_gates"
PY="$PHASE2/.venv-sparsedrive/bin/python"
CFG="projects/configs/s1_leaveout_stage2.py"
WORK="work_dirs/s1_${ARM}"
OUTLOG="$PHASE2/r0_repro/output/s1_${ARM}.log"

if [ "$ARM" = "baseline" ]; then
  export S1_LEAVEOUT=""
else
  K="${ARM#c}"
  export S1_LEAVEOUT="data/infos/leaveout/train_minus_c${K}.pkl"
  [ -f "$SD/$S1_LEAVEOUT" ] || { echo "MISSING leave-out pkl: $SD/$S1_LEAVEOUT (먼저 s1_leaveout.py prep)"; exit 1; }
fi

source "$PHASE2/r0_repro/env.sh"
cd "$SD"
export CUDA_VISIBLE_DEVICES="$GPU" PYTHONUNBUFFERED=1 PYTHONPATH="$SD:${PYTHONPATH:-}"
export S1_EPOCHS="${S1_EPOCHS:-6}" S1_BATCH="${S1_BATCH:-4}"

echo "[s1_run] arm=$ARM gpu=$GPU epochs=$S1_EPOCHS batch=$S1_BATCH leaveout=${S1_LEAVEOUT:-<full>}" | tee "$OUTLOG"

# 1) 학습(stage2-only, stage1 동결) — leave-out ann_file은 config가 env에서 읽음
# 부분 체크포인트 있으면 그 지점부터 재개(중간 크래시 복구). 없으면 처음부터.
RESUME=""
[ -f "$WORK/latest.pth" ] && { RESUME="--resume-from $WORK/latest.pth"; echo "[s1_run] 재개: $WORK/latest.pth 발견" | tee -a "$OUTLOG"; }
stdbuf -oL -eL "$PY" tools/train.py "$CFG" --work-dir "$WORK" --launcher none --deterministic $RESUME \
  2>&1 | tee -a "$OUTLOG"

# 2) eval → results.pkl (map eval 데드락 회피 위해 --out만, --eval 생략)
CKPT="$WORK/latest.pth"
[ -f "$CKPT" ] || { echo "학습 산출 ckpt 없음: $CKPT"; exit 1; }
RES="$WORK/results.pkl"
stdbuf -oL -eL "$PY" tools/test.py "$CFG" "$CKPT" --launcher none --out "$RES" \
  2>&1 | tee -a "$OUTLOG"

# 3) per-cluster tail
"$PY" "$R1/s1_leaveout.py" tail --results "$RES" --arm "$ARM" 2>&1 | tee -a "$OUTLOG"
echo "[s1_run] done arm=$ARM → $R1/output_val/tail_${ARM}.json"
