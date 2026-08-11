#!/usr/bin/env bash
# ============================================================================
# R0 SparseDrive 환경 구축 v2 — uv 파이썬 + userspace CUDA 11.8 툴킷(경로 C)
#   venv: phase2/.venv-sparsedrive (py3.8, repo /.venv와 완전 분리)
#   CUDA: /Data1/home/bskang/cuda-11.8 (runfile 설치, install_cuda118.sh 선행)
#   대상: 2×RTX4090(sm_89) → torch2.0.1+cu118 · mmcv_full1.7.1(CUDA ops) · arch=8.9
#
#   v1→v2 수정: (1) uv venv에 setuptools/wheel/ninja 명시 설치(op·flash 빌드용),
#               (2) flash-attn을 requirement.txt에서 분리(전체 -r 롤백 방지),
#               (3) CUDA_HOME=userspace 툴킷 지정(pip-nvcc 조각 문제 해소).
#   실행:  bash setup_env.sh   (install_cuda118.sh 완료 후)
# ============================================================================
set -euo pipefail

PHASE2="/Data1/home/bskang/AVdata-distirbution/experiments/EXP-003/phase2"
VENV="${PHASE2}/.venv-sparsedrive"
SD="${PHASE2}/third_party/sparsedrive"
PYVER="3.8"
export CUDA_HOME="/Data1/home/bskang/cuda-11.8"
export PATH="${CUDA_HOME}/bin:${PATH}"
export LD_LIBRARY_PATH="${CUDA_HOME}/lib64:${LD_LIBRARY_PATH:-}"
export TORCH_CUDA_ARCH_LIST="8.9"   # 4090 Ada
export FORCE_CUDA=1 MMCV_WITH_OPS=1
export MAX_JOBS="${MAX_JOBS:-8}"

# ---- 가드 ------------------------------------------------------------------
[[ "${VIRTUAL_ENV:-}" == *"/AVdata-distirbution/.venv" ]] && { echo "[STOP] repo .venv 활성"; exit 1; }
command -v uv >/dev/null || { echo "[STOP] uv 없음"; exit 1; }
[[ -d "$SD" ]] || { echo "[STOP] SparseDrive repo 없음: $SD"; exit 1; }
[[ -x "${CUDA_HOME}/bin/nvcc" ]] || { echo "[STOP] CUDA 툴킷 없음: ${CUDA_HOME} (install_cuda118.sh 먼저)"; exit 1; }
"${CUDA_HOME}/bin/nvcc" --version | tail -2

# ---- 1) uv venv (py3.8) ----------------------------------------------------
echo "== [1] uv venv (py${PYVER}) =="
uv python install "${PYVER}"
uv venv --python "${PYVER}" "${VENV}"
VPY="${VENV}/bin/python"
UVPIP=(uv pip install --python "${VPY}")
export PATH="${VENV}/bin:${PATH}"   # ninja 등 venv 도구를 빌드 서브프로세스가 찾도록
"${VPY}" -c "import sys; assert sys.version_info[:2]==(3,8), sys.version; print('venv OK', sys.executable)"

# ---- 1.5) 빌드 툴 (uv venv는 bare → 필수) ----------------------------------
echo "== [1.5] build tools (setuptools/wheel/ninja) =="
"${UVPIP[@]}" "setuptools<70" wheel ninja packaging

# ---- 2) torch (cu118, sm_89) ----------------------------------------------
echo "== [2] torch 2.0.1 + cu118 =="
"${UVPIP[@]}" torch==2.0.1 torchvision==0.15.2 \
  --index-url https://download.pytorch.org/whl/cu118
"${VPY}" -c "import torch;print('torch',torch.__version__,'cuda',torch.version.cuda,'avail',torch.cuda.is_available())"

# ---- 3) mmcv-full 1.7.1 (소스 빌드, CUDA ops 포함) -------------------------
#  ⚠️ cp38+cu118+torch2.0 프리빌트 휠 없음 → 반드시 소스빌드.
#     --no-cache: ops 없이 캐시된 빌드 재사용 방지(v1 함정). --no-build-isolation: venv의 torch/ninja 사용.
echo "== [3] mmcv-full 1.7.1 (+CUDA ops, 소스빌드 ~10-20분) =="
"${UVPIP[@]}" mmcv-full==1.7.1 --reinstall --no-cache --no-binary mmcv-full --no-build-isolation
"${UVPIP[@]}" mmdet==2.28.2

# ---- 4) requirement.txt (flash-attn 제외 → -r 롤백 방지) -------------------
echo "== [4] requirement (flash-attn 제외) =="
grep -viE 'flash[-_]attn' "${SD}/requirement.txt" > /tmp/req_noflash.txt
"${UVPIP[@]}" -r /tmp/req_noflash.txt \
  -f https://download.openmmlab.com/mmcv/dist/cu118/torch2.0/index.html

# ---- 5) flash-attn 2.3.2 (별도, 빌드 툴·torch·CUDA 준비된 뒤) ---------------
echo "== [5] flash-attn 2.3.2 (--no-build-isolation) =="
"${UVPIP[@]}" flash-attn==2.3.2 --no-build-isolation || \
  echo "[WARN] flash-attn 빌드 실패 → config에서 flash-attn 미사용 경로 확인(비치명)"

# ---- 6) deformable_aggregation CUDA op 컴파일 (sm_89) ----------------------
echo "== [6] custom op 컴파일 (arch=8.9) =="
( cd "${SD}/projects/mmdet3d_plugin/ops" && "${VPY}" setup.py develop )

# ---- 검증 ------------------------------------------------------------------
echo ""; echo "== 검증 =="
"${VPY}" - <<'PY'
import torch, mmcv, mmdet
print('torch', torch.__version__, '| mmcv', mmcv.__version__, '| mmdet', mmdet.__version__)
print('cuda cap', torch.cuda.get_device_capability(), '| device', torch.cuda.get_device_name(0))
try:
    from mmcv.ops import nms; print('mmcv CUDA ops: OK')
except Exception as e:
    print('mmcv CUDA ops: FAIL', e)
try:
    import flash_attn; print('flash_attn', flash_attn.__version__)
except Exception as e:
    print('flash_attn: 미설치(비치명)', type(e).__name__)
PY
echo "다음: nuScenes+CANbus → data 링크 → create_data.sh → kmeans.sh → 백본 → 학습 (SETUP.md §3~5)"
