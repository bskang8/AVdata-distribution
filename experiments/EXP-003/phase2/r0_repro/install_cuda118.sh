#!/usr/bin/env bash
set -euo pipefail
export TMPDIR=/Data1/home/bskang/tmp
URL=https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_520.61.05_linux.run
RUN=/Data1/home/bskang/downloads/cuda_11.8.0.run
DEST=/Data1/home/bskang/cuda-11.8
echo "== 다운로드 (4.3GB) =="; [ -s "$RUN" ] || wget -q "$URL" -O "$RUN"; ls -lh "$RUN"
echo "== userspace 툴킷 설치 → $DEST =="
sh "$RUN" --silent --toolkit --toolkitpath="$DEST" --tmpdir="$TMPDIR" --no-man-page --override
echo "== 검증 =="; "$DEST/bin/nvcc" --version | tail -3
