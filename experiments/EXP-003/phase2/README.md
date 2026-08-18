# EXP-003 phase2 — 실 타깃(Paper C): 실 E2E 자율주행 (SparseDrive)

> **다른 서버서 처음 돌리면 → `QUICKSTART.md`** (clone→nuScenes→실행→결과회수 한 흐름).
> 방향=`../PAPER_DIRECTION.md`(Paper C), 실행=`../EXECUTION_PLAN.md`(실 E2E·SparseDrive·2×4090).
> phase1=egomotion 써로게이트(파일럿). **phase2=실 E2E(nuScenes, SparseDrive)에서 크로스-아키텍처 전이·headroom 검증.**
> M0=**SparseDrive-S**(ICRA 2025, 8×RTX4090 24GB·장당 15.2GB로 개발 → 2×4090 실현). 예측-모듈(경로 B)은 폐기(모듈러라 E2E 아님).

## 디렉토리 규약
```
phase2/
  r0_repro/          # R0: SparseDrive-S 재현 + 비용 실측 + stage2-only leave-out 타당성  ← 지금 여기
    output/          # 로그·메트릭·체크포인트(*.pt는 gitignore)
  common/            # 공유: 결핍 클러스터링·feature 추출·recoverability estimator·metric
  third_party/       # sparsedrive/·VAD/ 클론 (gitignore, 커밋 안 함)
  r1_gates/          # R1(G0 headroom + G1 baseline 위생검사) — 필요 시 생성
  r2_transfer_probe/ # R2(G2 값싼 전이) — 필요 시 생성
  r3_transfer_matrix/# R3(G3 전이행렬) — 필요 시 생성
```
- **대용량 외부 데이터는 repo 밖**: nuScenes = `/Data1/home/bskang/cds-data/nuscenes/`(관례 준수).
- 체크포인트·데이터·third_party는 gitignore. **코드·설정·메트릭 JSON·README만 추적.**

## 환경 (재현성 — 채우기)
- python: `../../../.venv/bin/python` (repo venv; SparseDrive는 별도 mmcv/mmdet3d 의존 → third_party에 전용 env 가능)
- nuScenes 버전: (준비 후 기입)
- SparseDrive commit / config: (클론 후 기입)
- GPU: 2×RTX4090 (24GB, NVLink無)

## R0 체크리스트 (`../EXECUTION_PLAN.md` §7)
1. [ ] SparseDrive repo 클론 → `third_party/sparsedrive/`, 의존성·nuScenes 준비
2. [ ] SparseDrive-S 재현 학습(2×4090) → baseline L2/collision 확인(원문/최신 config 대조)
3. [ ] **stage1/stage2 학습 시간·메모리 실측** → `output/r0_cost.json`
4. [ ] **stage2-only leave-out 프로토타입**(결핍 1개, stage1 동결) → 타당성 확인
5. [ ] 결핍 클러스터링(nuScenes 시나리오 메타) → 후보 결핍 5개
6. [ ] R0 go/no-go(비용·타당성) → R1 진입 판단

## 산출물
- `output/r0_cost.json` — stage1/stage2 시간·메모리, leave-out 1회(stage2) 비용(R1 예산 산정).
- `output/sparsedrive_baseline.json` — 재현 L2/collision vs 공개 수치.
