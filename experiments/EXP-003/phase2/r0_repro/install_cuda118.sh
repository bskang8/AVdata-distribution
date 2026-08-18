#!/usr/bin/env bash
# userspace CUDA 11.8 툴킷 설치. 새 서버서 경로 다르면 CUDA_DEST/TMPDIR override:
#   CUDA_DEST=$HOME/cuda-11.8 bash install_cuda118.sh   (env.sh의 CUDA_HOME과 동일 경로로)
# NOTE: 설치 대상은 CUDA_DEST로 받음. 표준변수 CUDA_HOME은 시스템 CUDA(/usr/local/cuda)를
#       가리키는 경우가 많아 그대로 쓰면 환경이 대상 경로를 하이재킹함(심링크 루프 사고).
set -euo pipefail
export TMPDIR="${TMPDIR:-$HOME/tmp}"; mkdir -p "$TMPDIR"
URL=https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_520.61.05_linux.run
DEST="${CUDA_DEST:-$HOME/cuda-11.8}"
RUN="${TMPDIR}/cuda_11.8.0.run"
echo "== 다운로드 (4.3GB) =="; [ -s "$RUN" ] || wget -q "$URL" -O "$RUN"; ls -lh "$RUN"
echo "== userspace 툴킷 설치 → $DEST =="
sh "$RUN" --silent --toolkit --toolkitpath="$DEST" --tmpdir="$TMPDIR" --no-man-page --override
echo "== 검증 =="; "$DEST/bin/nvcc" --version | tail -3
