# source 하세요:  source env.sh   (SparseDrive 환경 활성화 — 매 세션 필요)
# repo /.venv 와 별개인 phase2 전용 venv + userspace CUDA 11.8 툴킷.
export CUDA_HOME=/Data1/home/bskang/cuda-11.8
export PATH="$CUDA_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_HOME/lib64:${LD_LIBRARY_PATH:-}"
export TORCH_CUDA_ARCH_LIST=8.9        # RTX 4090 (Ada)
source /Data1/home/bskang/AVdata-distirbution/experiments/EXP-003/phase2/.venv-sparsedrive/bin/activate
echo "[env] SparseDrive venv 활성 | CUDA_HOME=$CUDA_HOME | $(python --version 2>&1)"
