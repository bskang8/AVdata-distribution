# R0 — SparseDrive 재현 셋업 (2×RTX4090)

> 목표: SparseDrive-S를 2×4090에서 재현 → baseline L2/collision 확인 + stage1/2 시간·메모리 실측 + stage2-only leave-out 타당성.
> repo: `../third_party/sparsedrive/` (clone 완료). 공식: `docs/quick_start.md`, `requirement.txt`.

## 🔁 다른 서버에서 third_party 재구성 (로컬 패치 자동 적용)
`third_party/`는 gitignore(외부 fork)라 clone에 없다. 새 서버에서:
```bash
cd experiments/EXP-003/phase2/third_party
git clone https://github.com/swc-17/SparseDrive.git sparsedrive
cd sparsedrive && git checkout ec0225d          # 패치 기준 커밋
git apply ../../r0_repro/sparsedrive_local.patch # 로컬 수정 7건 일괄 적용
```
패치 내용(수동 재타이핑 불필요): converter shapely import 순서, train.py `--local_rank` alias,
`np.int→np.int64`, stage1/2 config, 신규 `s1_leaveout_stage2.py`. 아래 §의 개별 패치 설명은 참고용.

## 머신 실측 (2026-08-10)
- GPU: 2× RTX 4090 24GB, 드라이버 580.173.02(최신 — 어떤 CUDA 런타임도 지원).
- conda ❌ · nvcc ❌(시스템 CUDA 없음) · uv ✅(0.11.14) · 디스크 75T 여유 · nuScenes ❌(다운로드 필요).

## 🚫 repo `.venv` 재사용 불가 (확인 완료)
repo 메인 env `/Data1/home/bskang/AVdata-distirbution/.venv`(uv, **py3.12·torch2.12+cu130·numpy2.4**)는 SparseDrive(**py3.8·torch1.13~2.0·mmcv_full1.7.1·numpy1.23**)와 **호환 0/4**. 게다가 이 `.venv`는 분포분석 파이프라인의 메인 env라 **여기에 설치하면 기존 파이프라인이 깨짐**. → **반드시 분리된 별도 env.** 아래 `setup_env.sh`는 **uv로 `.venv`와 다른 경로(`phase2/.venv-sparsedrive`)에 py3.8 전용 venv**를 새로 만든다(기존 `.venv` 무손상).

## 🔴 핵심 난관 2개 (R0에서 먼저 해결 — 학습보다 이게 먼저)
1. **4090 = Ada(sm_89)**. SparseDrive quick_start 기본은 **torch1.13+CUDA11.6** → **CUDA 11.6 nvcc는 sm_89 미지원** → custom op(`projects/mmdet3d_plugin/ops`, deformable aggregation) 컴파일 실패 가능.
   - 해결: **CUDA 11.8 툴킷으로 op 컴파일** + `export TORCH_CUDA_ARCH_LIST="8.9"`(nvcc≥11.8 필요). nvcc가 11.7 이하면 `"8.6+PTX"`로 두고 PTX JIT에 의존.
   - 논문이 8×4090서 돌렸으니 가능은 함 — **repo Issues에서 "4090/3090/CUDA11.8" 확인된 조합**을 먼저 찾을 것.
2. **flash-attn==2.3.2** 빌드. Ada 지원하나 CUDA/torch 매칭 까다로움 → CUDA 11.8 환경에서 빌드 권장. 실패 시 flash-attn 없는 config 경로 확인.

## requirement.txt (verbatim, mmdet3d 없음 = UniAD보다 수월)
```
numpy==1.23.5  mmcv_full==1.7.1  mmdet==2.28.2  nuscenes-devkit==1.1.10
flash-attn==2.3.2  pandas==1.1.5  scikit-learn==1.3.0  tensorboard==2.14.0
motmetrics==1.1.3  pyquaternion==0.9.9  opencv-python==4.8.1.78  prettytable==3.7.0  yapf==0.33.0
```

## 셋업 순서

> ⚡ **자동화 초안**: §0~2·4~7(환경·op 컴파일)은 **`bash r0_repro/setup_env.sh`** 로 한 번에 시도 가능(uv 기반, `phase2/.venv-sparsedrive` 생성, conda 불요). nuScenes(§3)만 수동. **초안이므로 실패 단계는 STOP·폴백 주석 참고 후 조합 확정** — 확정본을 정본으로 갱신할 것.

### (대안) conda 경로 — pip nvcc 실패 시
```
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/mc.sh
bash /tmp/mc.sh -b -p /Data1/home/bskang/miniconda3
eval "$(/Data1/home/bskang/miniconda3/bin/conda shell.bash hook)"
```

### 1) 환경 (4090 조정판 — 기본 cu116 대신 cu118 권장)
```
conda create -n sparsedrive python=3.8 -y && conda activate sparsedrive
# 4090(sm_89)용: torch 1.13.0 + cu117(공식 최고) 또는 torch 2.0.1+cu118. mmcv_full 1.7.1 휠 매칭되는 쪽 선택.
# 1순위 시도: torch 2.0.1 + cu118 (sm_89 네이티브)
pip install torch==2.0.1 torchvision==0.15.2 --index-url https://download.pytorch.org/whl/cu118
# op 컴파일용 CUDA 11.8 툴킷(nvcc)
conda install -c nvidia cuda-toolkit=11.8 -y
pip install -r ../third_party/sparsedrive/requirement.txt   # mmcv_full 1.7.1 휠이 torch/cu 조합에 있어야 함(없으면 mim 사용)
```
⚠️ mmcv_full 1.7.1 × (torch2.0.1+cu118) 휠이 없으면: torch를 1.13.0+cu117로 낮추고 op는 cu118 nvcc로 arch=8.9 강제 컴파일하는 혼합 경로로 폴백. **이 조합 확정이 R0의 첫 산출.**

### 2) custom op 컴파일
```
cd ../third_party/sparsedrive/projects/mmdet3d_plugin/ops
export TORCH_CUDA_ARCH_LIST="8.9"
python3 setup.py develop
```

### 3) nuScenes + CAN bus (repo 밖, 관례 위치)
```
# nuScenes 계정 로그인 후 trainval(+ CAN bus expansion) 다운로드 → /Data1/home/bskang/cds-data/nuscenes/
# SparseDrive 데이터 폴더에 심볼릭 링크 후:
cd ../third_party/sparsedrive
ln -s /Data1/home/bskang/cds-data/nuscenes data/nuscenes
sh scripts/create_data.sh     # data/infos/*.pkl 생성 (map ROI 기본 (30,60))
sh scripts/kmeans.sh          # ★필수★ K-means 앵커 생성 → data/kmeans (학습 전 반드시)
```

### 4) 백본 가중치
```
mkdir -p ckpt && wget https://download.pytorch.org/models/resnet50-19c8e357.pth -O ckpt/resnet50-19c8e357.pth
```

### 5) 학습 (2×4090로 수정)
- 공식 `scripts/train.sh`는 다중 GPU 가정 → **`--nproc_per_node=2`로, 배치는 config에서 유지(장당 6, 15.2GB)**.
- 2-stage config(확정): `projects/configs/sparsedrive_small_stage1.py`(지각) → `sparsedrive_small_stage2.py`(플래닝). **stage2는 stage1 체크포인트를 로드** → leave-out은 stage2만 재실행하는 §1-5 전략의 근거.
- 실측 기록: stage1/stage2 wall-clock·peak mem → `output/r0_cost.json`.

### 6) 평가
```
sh scripts/test.sh   # L2 / collision → output/sparsedrive_baseline.json 로 공개 수치 대조
```
⚠️ 개방루프 L2는 ego-status shortcut 오염 → **collision 중심 해석**, 이후 NAVSIM 병행 검토(EXECUTION_PLAN §1-1).

## ✅ 진행 상태 (2026-08-10) — 환경 구축 완료, 데이터/학습 남음
- **환경 DONE**: `.venv-sparsedrive`(py3.8)·CUDA11.8(userspace)·torch2.0.1+cu118·mmcv1.7.1(_ext OK)·mmdet2.28.2·flash-attn2.3.2·**custom op(deformable_aggregation_ext) 컴파일 OK**. `setup_env.sh` 재실행 불필요.
- **남음**: nuScenes 데이터(§3) → create_data → kmeans → 백본 → SparseDrive-S 재현 학습·비용 실측(§5~6).

## ✅ 데이터 셋업 (2026-08-11)
- **nuScenes 재다운로드 불필요**: 풀 trainval+test가 이미 `/Data1/home/bskang/KatechBridgeAD/data/nuscenes`에 존재(samples 40157장·can_bus·maps expansion 추출됨, sweeps는 빔 — SparseDrive는 카메라 sparse라 sweep 이미지 로드 안 함, create_data는 메타만 읽음).
- 배선: `data/nuscenes/{samples,sweeps,maps,can_bus}` → KatechBridge로 **심볼릭 링크**(원본 무변경). 메타 JSON은 `v1.0-trainval_meta.tar`/`v1.0-test_meta.tar`에서 `v1.0-trainval/`·`v1.0-test/` **subdir만** 로컬 추출(maps/ 는 심볼릭 오염 방지 위해 제외).
- ⚠️ **`scripts/create_data.sh` 그대로 쓰지 말 것**: 맨 앞 `v1.0-mini` 단계가 여기 mini 데이터 없어서 실패. **컨버터를 직접 호출**(`--version v1.0` = trainval+test):
  ```
  python tools/data_converter/nuscenes_converter.py nuscenes \
    --root-path ./data/nuscenes --canbus ./data/nuscenes \
    --out-dir ./data/infos/ --extra-tag nuscenes --version v1.0
  ```
- 🔧 **근본원인 패치(적용됨)**: `tools/data_converter/nuscenes_converter.py`가 `from shapely.geometry import ...`를 plugin(map_utils, 내부 `shapely.strtree`/GEOS 초기화) import보다 **먼저** 하면 `std::runtime_error: random_device could not be read`로 100% abort. → plugin import를 shapely보다 앞으로 이동해 해결. (GEOS 정적 초기화 순서 충돌)
- **백본 DONE**: `ckpt/resnet50-19c8e357.pth`.

## 🔧 학습 착수 시 env 호환 수정 3건 (2026-08-11, 스모크런서 발견·적용)
설치 패키지가 requirement.txt 핀보다 신버전이라 학습 파이프라인에서 터짐. 적용 완료:
1. **torch 2.0 DDP**: `torch.distributed.launch`가 `--local-rank`(하이픈) 주입 → `tools/train.py`가 `--local_rank`만 받아 argparse 거부(exitcode 2). → `parser.add_argument("--local_rank","--local-rank",...)` alias 추가.
2. **yapf**: 설치 0.43.0(‘verify’ 인자 제거)인데 mmcv 1.7.1 Config가 `FormatCode(...,verify=True)` 호출 → `TypeError`. → `uv pip install yapf==0.33.0`(핀 복원, ‘yanked’이나 설치·작동 정상).
3. **numpy 1.24**: `np.int` 제거됨 → `projects/mmdet3d_plugin/datasets/nuscenes_3d_dataset.py:392` `dtype=np.int` → `np.int64`. (numpy 다운그레이드는 mmcv `_ext` ABI 위험이라 코드 1줄 수정 선택.)
- **스모크런 검증 DONE**: stage1 1GPU 15iter 완주(det/map/depth loss 하강·custom op·fp16·NaN無, batch2=4469MiB). 명령: `bash tools/dist_train.sh <cfg> <ngpu> --no-validate --deterministic --work-dir work_dirs/_smoke_stage1 --cfg-options data.samples_per_gpu=2 data.workers_per_gpu=2 runner.max_iters=15 log_config.interval=2 checkpoint_config.interval=100000`.

## ▶ 내일 이어서 (새 세션 resume)
```bash
cd /Data1/home/bskang/AVdata-distirbution/experiments/EXP-003/phase2/r0_repro
source env.sh                       # venv + CUDA_HOME 활성 (매 세션 필수)
# 환경 정상 확인(선택):
python -c "import torch,mmcv,mmdet,flash_attn; from mmcv.ops import nms; print('env OK', torch.cuda.get_device_capability(0))"
```
그다음 §3부터: nuScenes+CANbus 다운로드(계정 필요) → `data/nuscenes` 링크 → `sh scripts/create_data.sh` → `sh scripts/kmeans.sh` → 백본 → 학습.

## R0 완료 기준 (go/no-go)
- [ ] 환경/op 컴파일 성공(sm_89) — 4090 조합 확정
- [ ] SparseDrive-S 재현 L2/collision ≈ 공개 수치
- [ ] stage1/stage2 시간·메모리 실측 → `output/r0_cost.json`
- [ ] **stage2-only leave-out 프로토타입**(결핍1개, stage1 동결) 회복 측정 타당 → R1 예산 산정
