# S1 캠페인 서버 이전 가이드 (연속 재개)

목적: 전원 재부팅이 반복되는 현재 서버에서 **다른 서버로 S1 캠페인을 이식**하되,
학습을 처음부터가 아니라 **끊긴 지점(iter_12500)에서 연속**으로 이어가기.

> **확정 경로(2026-08-14):** ① nuScenes 원본은 새 서버에 **없음 → rsync 전송 필요**
> (최장 병목, §3·백그라운드로 **먼저** 시작). ② GPU 아키 미확인 → 환경은 **재빌드
> 경로(§4-B)** 기본. 새 서버가 4090/Ada + 같은 홈경로로 밝혀지면 §4-A(tar 이식)로 전환.

## 0. 왜 git clone만으로는 안 되나

`git clone`이 가져오는 phase2 자산은 **오케스트레이션 스크립트/문서 12개뿐**이다.
`.gitignore`가 아래를 전부 제외한다:

- `third_party/`  ← SparseDrive 코드 **전체** (로컬 패치 포함: plugin import 순서, s1 config, tools)
- 체크포인트(`*.pth`), 데이터(`data/`), 로그, phase2 전용 venv

따라서 **git clone + 아래 번들 scp** 두 단계가 필요하다. 재개 메커니즘 자체는
이미 스크립트에 있으므로, 우리가 할 일은 "상태를 그대로 옮기는 것"뿐이다.

## 1. 현재 진행 상태 (이식 대상 확정)

| arm | 상태 | 옮길 것 |
|---|---|---|
| `s1_baseline` | iter **12500/70320** (~18%) 부분 학습 | `work_dirs/s1_baseline/latest.pth` **필수** |
| 나머지 arm (c0,c1,…) | 미시작 (완료 `tail_*.json` 0개) | 없음 — 새 서버에서 처음부터 |
| `s1_probe_bs8`, `_smoke*`, `_probe*` | 코스트 프로브 잔재 | **옮기지 말 것** |

즉 연속성의 핵심 파일은 `s1_baseline/latest.pth`(=iter_12500) **하나**다.

## 2. 이전 대상 자산 목록

경로는 모두 `experiments/EXP-003/phase2/` 기준. 크기는 실측.

| # | 자산 | 경로 | 크기 | git | 방법 |
|---|---|---|---|---|---|
| 1 | SparseDrive 코드(로컬패치) | `third_party/sparsedrive/` (단, `work_dirs`·`data` 제외) | ~2G | ✗ | tar+scp |
| 2 | 사전학습 가중치 | `third_party/sparsedrive/ckpt/` (resnet50·stage1·stage2) | ~2G | ✗ | scp |
| 3 | nuScenes infos(기본) | `…/data/infos/*.pkl` (train/val/test) | ~0.9G | ✗ | scp |
| 3b | leaveout pkl(재생성) | `…/data/infos/leaveout/*.pkl` (16개, 12G) | 12G | ✗ | **이송 안 함 → §6-5 재생성** |
| 4 | kmeans 앵커 | `…/data/kmeans/*.npy` | 123K | ✗ | scp |
| 5 | **연속 체크포인트** | `…/work_dirs/s1_baseline/latest.pth` | 429M | ✗ | scp |
| 6 | nuScenes 원본 | `…/data/nuscenes/{samples,sweeps,maps,can_bus}`(심볼릭)+`v1.0-*` | **수백 GB** | ✗ | ↓ §3 |
| 7 | 환경(CUDA+venv) | `/Data1/home/bskang/cuda-11.8` + `phase2/.venv-sparsedrive` | ~5.3G | ✗ | ↓ §4 |

**옮기지 말 것:** `output/s1_claims/`(GPU 청구 상태 — 새 서버에서 재생성),
`work_dirs/{s1_probe_bs8,_smoke*,_probe*}`, 로그.

## 3. nuScenes 원본 (최대 관건)

`data/nuscenes/{samples,sweeps,maps,can_bus}`는 심볼릭 링크다:

```
samples -> /Data1/home/bskang/KatechBridgeAD/data/nuscenes/samples
sweeps  -> /Data1/home/bskang/KatechBridgeAD/data/nuscenes/sweeps
maps    -> /Data1/home/bskang/KatechBridgeAD/data/nuscenes/maps
can_bus -> /Data1/home/bskang/KatechBridgeAD/data/nuscenes/can_bus
```

- **새 서버에 nuScenes 원본이 이미 있으면** → 그 경로로 심볼릭만 다시 만든다(가장 좋음).
- 없으면 수백 GB 전송이 필요. rsync 권장(재개 가능):
  `rsync -aP /Data1/home/bskang/KatechBridgeAD/data/nuscenes/ NEWHOST:/DATA/nuscenes/`
- `v1.0-trainval/`, `v1.0-test/`(메타 dir, 심볼릭 아님)는 tar 번들(#2~5)에 포함시키거나 함께 rsync.

**infos(#3)를 그대로 옮기는 이유:** `nuscenes_infos_train.pkl`은 절대경로가 아닌
상대 참조라 재생성 없이 재사용 가능. 원본만 같은 상대구조면 됨. (재생성하려면
`tools/create_data.py` 재실행 — 수십 분~시간, 굳이 불필요.)

## 4. 환경(CUDA 11.8 + venv) — 두 갈래

venv와 userspace CUDA는 **절대경로가 박혀** 있다(`env.sh` 참조:
`CUDA_HOME=/Data1/home/bskang/cuda-11.8`, venv activate 절대경로).

- **A. 새 서버가 같은 GPU 아키(RTX 4090/Ada, arch 8.9) + 같은 홈경로**(`/Data1/home/bskang`)
  → **통째로 tar 이식**이 제일 빠르고 확실:
  ```
  tar czf env.tgz -C / Data1/home/bskang/cuda-11.8
  tar czf venv.tgz -C experiments/EXP-003/phase2 .venv-sparsedrive
  # 새 서버에서 동일 절대경로에 풀기
  ```
  mmcv 재빌드(까다로움)를 피할 수 있다.

- **B. GPU 아키가 다르거나 홈경로가 다름**
  → 재빌드가 안전. `install_cuda118.sh` → `setup_env.sh` 순서 실행,
  `env.sh`의 `TORCH_CUDA_ARCH_LIST`를 새 GPU에 맞게 수정
  (예: A100=8.0, A6000=8.6, 4090=8.9). mmcv가 이 arch로 빌드됨.

> 재개 자체는 GPU 아키와 무관(가중치는 arch-agnostic). B에서도 iter_12500에서 이어진다.

## 5. 번들 만들기 (현재 서버에서)

```bash
cd /Data1/home/bskang/AVdata-distirbution/experiments/EXP-003/phase2
tar czf /tmp/s1_bundle.tgz \
  --exclude='third_party/sparsedrive/work_dirs' \
  --exclude='third_party/sparsedrive/data/infos/leaveout' \
  --exclude='third_party/sparsedrive/data/nuscenes/samples' \
  --exclude='third_party/sparsedrive/data/nuscenes/sweeps' \
  --exclude='third_party/sparsedrive/data/nuscenes/maps' \
  --exclude='third_party/sparsedrive/data/nuscenes/can_bus' \
  third_party/sparsedrive
# = 코드(#1)+ckpt(#2)+infos기본(#3)+kmeans(#4)+v1.0메타.
#   leaveout 12G(중복,재생성)·심볼릭 수백GB·work_dirs 는 제외 → 압축전 ~5G(.tgz ~3G)

# 연속 체크포인트만 별도(작음)
tar czf /tmp/s1_baseline_ckpt.tgz \
  -C third_party/sparsedrive work_dirs/s1_baseline/latest.pth
```

scp: `scp /tmp/s1_bundle.tgz /tmp/s1_baseline_ckpt.tgz NEWHOST:/tmp/`

## 6. 새 서버 셋업 절차

```bash
# 1) repo
git clone <REPO_URL> AVdata-distirbution
cd AVdata-distirbution
git checkout exp003/phase1-expAB-derisk

# 2) 번들 전개
mkdir -p experiments/EXP-003/phase2/third_party
tar xzf /tmp/s1_bundle.tgz     -C experiments/EXP-003/phase2
tar xzf /tmp/s1_baseline_ckpt.tgz -C experiments/EXP-003/phase2/third_party/sparsedrive

# 3) 환경 (§4-A 이식 또는 §4-B 재빌드)

# 4) nuScenes 심볼릭 재생성 (§3의 실제 경로로)
cd experiments/EXP-003/phase2/third_party/sparsedrive/data/nuscenes
ln -sf /DATA/nuscenes/samples  samples
ln -sf /DATA/nuscenes/sweeps   sweeps
ln -sf /DATA/nuscenes/maps     maps
ln -sf /DATA/nuscenes/can_bus  can_bus

# 5) leaveout pkl 16개 재생성 (§3b, 이송 안 한 12G) — CPU offline, 몇 분.
#    입력: base train pkl(#3, 이송됨) + gq1_s0_perclip.npz(6.7M, git추적) + git코드.
#    결정론적(centroid 재현 일치율=1.0) → 원본과 비트 동일.
cd experiments/EXP-003/phase2/r0_repro
source env.sh
python ../r1_gates/s1_leaveout.py prep
ls ../third_party/sparsedrive/data/infos/leaveout/*.pkl | wc -l   # 16 이어야 함
```

> baseline 재개만 급하면 5)는 건너뛰어도 된다(leaveout은 c* arm 전용).
> baseline은 full train pkl만 쓰므로 §3b 없이 바로 iter_12500 재개 가능.

## 7. 검증 (재개 전 필수 스모크)

```bash
cd experiments/EXP-003/phase2/r0_repro
source env.sh
python -c "import torch, mmcv; print('cuda', torch.cuda.is_available(), 'arch', torch.cuda.get_device_name(0))"
ls -l ../third_party/sparsedrive/work_dirs/s1_baseline/latest.pth   # 429M 있어야 함
ls ../third_party/sparsedrive/data/nuscenes/samples/ | head          # 심볼릭 살아있는지
```

## 8. 연속 재개 실행

`s1_orchestrate.sh`는 prep 로그(`s1_prep_full.log`)의 특정 문자열을 기다리므로
새 서버에서는 멈춘다 → **쓰지 말고 캠페인 러너를 직접** 띄운다(prep는 §2에서 이미 이식됨):

```bash
cd experiments/EXP-003/phase2/r0_repro
# GPU 1개면:
setsid bash s1_campaign.sh 0 > output/campaign_gpu0.log 2>&1 &
# GPU 2개면 (자동 로드밸런싱):
setsid bash s1_campaign.sh 1 > output/campaign_gpu1.log 2>&1 &
sleep 3
setsid bash s1_campaign.sh 0 > output/campaign_gpu0.log 2>&1 &
```

`s1_baseline`은 `latest.pth`를 감지해 **iter_12500부터 재개**된다. 로그로 확인:

```bash
grep "재개" output/s1_baseline.log     # "[s1_run] 재개: …/latest.pth 발견"
tail -f output/s1_baseline.log         # Iter [125xx/70320] 부터 시작하는지
```

나머지 arm은 자동으로 처음부터 청구·실행된다.

## 9. 연속성 보장·주의점

- `--resume-from`(mmcv)은 **옵티마이저·iter·lr 스케줄까지 복원** → 진짜 연속.
- `--deterministic`+동일 seed로 데이터 순서도 이어짐.
- **동일 config**(`s1_leaveout_stage2.py`)와 **동일 env**(`S1_EPOCHS=10 S1_BATCH=4`,
  `s1_campaign.sh`가 자동 설정) 유지 필수 — 바꾸면 스케줄 어긋남.
- 재부팅 재발 대비는 그대로 유효: 500 iter 체크포인트 → 손실 상한 500 iter.
- 이전 후엔 현재 서버 `s1_claims/`·미완 work_dir는 신경 쓸 것 없음(새 서버가 진실원).
