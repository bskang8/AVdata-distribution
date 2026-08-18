#!/usr/bin/env bash
# userspace CUDA 11.8 툴킷 설치. 새 서버서 경로 다르면 CUDA_HOME/TMPDIR override:
#   CUDA_HOME=$HOME/cuda-11.8 bash install_cuda118.sh   (env.sh와 반드시 동일 경로)
set -euo pipefail
export TMPDIR="${TMPDIR:-$HOME/tmp}"; mkdir -p "$TMPDIR"
URL=https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_520.61.05_linux.run
DEST="${CUDA_HOME:-/Data1/home/bskang/cuda-11.8}"
RUN="${TMPDIR}/cuda_11.8.0.run"
echo "== 다운로드 (4.3GB) =="; [ -s "$RUN" ] || wget -q "$URL" -O "$RUN"; ls -lh "$RUN"
echo "== userspace 툴킷 설치 → $DEST =="
sh "$RUN" --silent --toolkit --toolkitpath="$DEST" --tmpdir="$TMPDIR" --no-man-page --override
echo "== 검증 =="; "$DEST/bin/nvcc" --version | tail -3
