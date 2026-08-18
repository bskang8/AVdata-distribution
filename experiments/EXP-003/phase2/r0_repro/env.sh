# source 하세요:  source env.sh   (SparseDrive 환경 활성화 — 매 세션 필요)
# repo /.venv 와 별개인 phase2 전용 venv + userspace CUDA 11.8 툴킷.
# 경로는 스크립트 위치 기준으로 자동 유도. 새 서버서 다르면 아래 env로 override:
#   CUDA_HOME=/path/cuda-11.8  TORCH_CUDA_ARCH_LIST=8.0(A100)/8.6(A6000)/8.9(4090)  source env.sh
PHASE2="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
export CUDA_HOME="${CUDA_HOME:-/Data1/home/bskang/cuda-11.8}"
export PATH="$CUDA_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_HOME/lib64:${LD_LIBRARY_PATH:-}"
export TORCH_CUDA_ARCH_LIST="${TORCH_CUDA_ARCH_LIST:-8.9}"   # RTX 4090 (Ada); 새 GPU면 override
source "${PHASE2}/.venv-sparsedrive/bin/activate"
echo "[env] SparseDrive venv 활성 | CUDA_HOME=$CUDA_HOME | arch=$TORCH_CUDA_ARCH_LIST | $(python --version 2>&1)"
