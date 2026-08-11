#!/usr/bin/env bash
# R0 baseline: released ckpt로 SparseDrive-S eval → L2/collision을 공개수치와 대조.
# 학습 없이 재현 baseline 확보 + KatechBridge/converter 데이터경로 검증.
# 결과 로그: r0_repro/output/eval_baseline_<stage>.log  →  sparsedrive_baseline.json 채우기.
# NOTE: config의 data 경로가 sparsedrive 레포 루트 기준 상대경로라 반드시 거기서 실행.
set -euo pipefail

PHASE2="$(cd "$(dirname "$0")/.." && pwd)"
SD="$PHASE2/third_party/sparsedrive"
PY="$PHASE2/.venv-sparsedrive/bin/python"
OUT="$PHASE2/r0_repro/output"
STAGE=${1:-stage2}                   # stage2=planning(L2/collision), stage1=det/map/track/motion
# 재추론 스킵: RESULT_FILE=work_dirs/sparsedrive_small_stage2/results.pkl 로 전달
RESULT_FILE=${RESULT_FILE:-}

mkdir -p "$OUT"
CKPT="ckpt/sparsedrive_${STAGE}.pth"
CFG="projects/configs/sparsedrive_small_${STAGE}.py"
[ -f "$SD/$CKPT" ] || { echo "MISSING $SD/$CKPT"; exit 1; }

cd "$SD"                              # config의 data/ 상대경로 해석 기준
# 비분산 단일 GPU(--launcher none). torchrun 분산 모드는 motion eval에서 데드락하므로 금지.
# GPU1은 타 사용자 상주 가능 → CUDA_VISIBLE_DEVICES=0 기본. detach 시 stdout 버퍼링 해제 필수.
CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0} \
PYTHONUNBUFFERED=1 PYTHONPATH="$SD":${PYTHONPATH:-} \
stdbuf -oL -eL "$PY" tools/test.py "$CFG" "$CKPT" \
  --launcher none --eval bbox --deterministic \
  ${RESULT_FILE:+--result_file "$RESULT_FILE"} \
  2>&1 | tee "$OUT/eval_baseline_${STAGE}.log"
