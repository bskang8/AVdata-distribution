# phase2 이식 QUICKSTART — 새 서버 fresh 실행

> 목적: **git clone → nuScenes 다운로드 → 바로 실험 → 결과 회수** 한 흐름.
> 상세 근거는 `r0_repro/SETUP.md`, 부분학습 이어달리기(resume)는 `r0_repro/MIGRATION.md`.
> git이 주는 건 코드·스크립트·문서뿐 — 아래 3·4는 clone에 없어 새로 만든다(설계상 정상).

## 0. 현재(원본) 서버에서 먼저: IP 번들 scp
`_handoff/`는 커밋 금지(미출판). 새 서버로 직접 전송:
```bash
scp -r experiments/EXP-003/phase2/_handoff NEWHOST:/tmp/handoff   # 새 서버서 같은 위치로 이동
```

## 1. repo clone
```bash
git clone https://github.com/<계정>/AVdata-distirbution.git   # 새 서버는 SSH alias 없음 → https
cd AVdata-distirbution && git checkout exp003/phase1-expAB-derisk
mv /tmp/handoff experiments/EXP-003/phase2/_handoff             # 0에서 받은 번들
```

## 2. third_party 재구성 (로컬 패치 자동 적용)
```bash
cd experiments/EXP-003/phase2/third_party
git clone https://github.com/swc-17/SparseDrive.git sparsedrive
cd sparsedrive && git checkout ec0225d
git apply ../../r0_repro/sparsedrive_local.patch    # 로컬 수정 7건 일괄
mkdir -p ckpt && wget https://download.pytorch.org/models/resnet50-19c8e357.pth -O ckpt/resnet50-19c8e357.pth
```

## 3. 환경 (CUDA 11.8 + venv) — 새 GPU면 override
```bash
cd ../../r0_repro
# 홈경로/GPU 다르면 override (arch: A100=8.0 · A6000=8.6 · 4090=8.9):
#   export CUDA_HOME=$HOME/cuda-11.8 TORCH_CUDA_ARCH_LIST=8.9
bash install_cuda118.sh          # userspace CUDA 11.8 (nvcc)
bash setup_env.sh                # .venv-sparsedrive + torch/mmcv/flash + custom op 빌드
```
> 원본과 GPU 아키·홈경로가 같으면 재빌드 대신 tar 이식이 더 빠름 → `MIGRATION.md §4-A`.

## 4. nuScenes (이 서버에 별도 다운로드) → 배선
```bash
# nuScenes trainval(+CAN bus, +meta) 를 원하는 위치에 받은 뒤 그 경로를 지정:
export NUSCENES_ROOT=/DATA/nuscenes          # ← 다운로드 위치로 교체 (단일 knob)

cd ../third_party/sparsedrive && mkdir -p data/nuscenes
for d in samples sweeps maps can_bus; do ln -sf "$NUSCENES_ROOT/$d" "data/nuscenes/$d"; done
ln -sf "$NUSCENES_ROOT/v1.0-trainval" data/nuscenes/v1.0-trainval   # 메타 dir(심볼릭 아닌 실체면 그대로)
ln -sf "$NUSCENES_ROOT/v1.0-test"     data/nuscenes/v1.0-test

# infos 생성 (create_data.sh는 v1.0-mini 단계서 실패 → 컨버터 직접호출: SETUP.md §데이터셋업)
source ../../r0_repro/env.sh
python tools/data_converter/nuscenes_converter.py nuscenes \
  --root-path ./data/nuscenes --canbus ./data/nuscenes \
  --out-dir ./data/infos/ --extra-tag nuscenes --version v1.0
sh scripts/kmeans.sh             # ★필수★ K-means 앵커 (학습 전 반드시)
```

## 5. 검증 스모크 (실행 전 필수)
```bash
cd ../../r0_repro && source env.sh
python -c "import torch,mmcv,mmdet,flash_attn; from mmcv.ops import nms; print('env OK', torch.cuda.get_device_name(0))"
ls ../third_party/sparsedrive/data/nuscenes/samples/ | head    # 심볼릭 살아있나
ls ../third_party/sparsedrive/data/infos/*.pkl                 # infos 생성됐나
bash eval_baseline.sh stage2   # (stage2 ckpt 있을 때) baseline L2/CR ≈ sparsedrive_baseline.json 이면 환경 정상
```

## 6. 실험 실행
- **재현/baseline·비용**: `r0_repro/SETUP.md §5~6`.
- **G-Q1 leave-out 캠페인**:
  ```bash
  python ../r1_gates/s1_leaveout.py prep          # leaveout pkl 재생성(시드=output/gq1_s0_perclip.npz, git추적)
  setsid bash s1_campaign.sh 0 > output/campaign_gpu0.log 2>&1 &   # GPU 2개면 gpu1도 (MIGRATION §8)
  bash s1_status.sh                                # 진행 확인
  ```

## 7. 결과 회수 → 원본 서버서 분석
분석에 필요한 **가벼운 산출물만** 회수(대용량 ckpt/데이터 제외):
```bash
# 새 서버에서:
tar czf /tmp/phase2_results.tgz \
  experiments/EXP-003/phase2/r0_repro/output/*.json \
  experiments/EXP-003/phase2/r0_repro/sparsedrive_baseline.json \
  experiments/EXP-003/phase2/r1_gates/output*/*.json \
  experiments/EXP-003/phase2/**/output/*.log
scp /tmp/phase2_results.tgz ORIGINHOST:/tmp/
```
원본 서버서 풀어 `r1_gates/RESULTS.md`·메모리와 대조해 분석 계속.

---
**막히면**: 환경/패치=`SETUP.md`, resume/서버이전=`MIGRATION.md`, 크래시=`CRASH_RECOVERY.md`, 연구맥락=`_handoff/MEMORY_HANDOFF.md`.
