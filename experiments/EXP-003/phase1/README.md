# EXP-003 Phase 1 — per-clip 성능 대리지표 (egomotion ADE/FDE)

> **역할**: 방법론(`../phase0/output/methodology_direction_analysis.md`)의 마지막 병목이던 **model_error 신호**를 공급한다. 라벨 없이 ego 궤적 자체를 GT로 "과거→미래" 궤적을 예측해 per-clip 예측난이도(ADE/FDE)를 산출 → §2 획득함수 `model_error` 인자 + §5 leave-out 검증층의 성능 신호.
>
> **전신(前身)**: 기존 phase1(exposure P_ext 구축)은 **`../phase0_2/`로 이동**. 이 phase1은 성능 축을 담당한다.

## 왜 이게 linchpin인가
- **#1(수집)**: `low-density × high-error` 셀 = 최우선 수집 (Domino 완성)
- **#2(충분성)**: 셀별 ADE/FDE를 데이터량에 대해 그리면 포화곡선 → 정지판정
- **#3(성능시연)**: 수집/큐레이션 전후 ADE/FDE 그대로 성능 지표

## de-risk (완료 · GO)
`../phase0/derisk_egomotion.py` — GT 사용성 확인: 커버율 **97.4%**(97,820/100,398) · 스키마 6-DoF 포즈(`timestamp, x y z, qx qy qz qw`) · **~10Hz·20s** · 2+3s 지평 100% 확보.

## 방법 (compute_surrogate.py)
- 각 클립 egomotion 궤적(x,y)에서 **과거 OBS_S=2s 관측 → 미래 FUT_S=3s를 등속(CV) 예측** → 예측오차.
- 클립 전체를 STRIDE_S=2.5s로 슬라이딩해 창별 오차 평균 → per-clip **ADE**(평균변위오차)·**FDE**(최종변위오차).
- **직관**: CV(단순 운동prior)가 크게 틀림 = 정지·회전·가감속 등 **복잡 기동** = "예측이 어려운 조건" 대리. 작으면 = 단조 직진.
- CV는 **첫 베이스라인(가장 lazy)** — 절대난이도 근사. §5 leave-out에선 실제 학습 예측기로 교체해 '특정 모델의 실패'로 격상.

## 산출물 (output/)
- `ade_per_clip.npy` · `fde_per_clip.npy` — phase0 `clip_ids.npy` 순서 정렬(길이 100,398, egomotion 없는 클립=NaN) → ODD·임베딩 분석과 바로 join.
- `surrogate_summary.json` — 유효 수·분포(mean/p50/p90).

## 실행
```bash
# 반드시 .venv (phase0 산출물이 numpy2 · parquet 리더 pyarrow 필요)
../../../.venv/bin/python compute_surrogate.py --demo        # 자기검증
../../../.venv/bin/python compute_surrogate.py --limit 500   # 표본
../../../.venv/bin/python compute_surrogate.py               # 전체 97,820
```

## 표본 결과 (n=500, 참고)
ADE p50 **2.20m** · p90 4.21m · max 8.60m / FDE p50 **4.99m** · p90 9.47m (3s 지평). 분포에 폭이 있어 난이도 변별력 확인.

## 다음 → **완료. 결과는 [RESULTS.md](RESULTS.md)**
1. ~~전체 실행 → `ade/fde_per_clip.npy` 확정.~~ ✓
2. ~~ODD 셀별·임베딩 사분면별 집계 → `model_error(c)` + Domino.~~ ✓ (`aggregate_error.py`)
3. ~~Priority(c) 통합 랭킹~~ ✓ (`priority.py`) · ~~CV→학습형(`learned_surrogate.py`)~~ ✓ · ~~exposure urban/rural 확장(`extend_exposure.py`)~~ ✓
4. ~~leave-out 재현실험(§5)~~ ✓ (`leaveout.py`) — **G4 미성립**: egomotion은 실패가 기동축이라 ODD-조건 가중 guided가 구조적으로 오조준. **두-렌즈 G4는 condition-sensitive 다운스트림(perception)으로 이관.** 상세 [RESULTS.md](RESULTS.md).
