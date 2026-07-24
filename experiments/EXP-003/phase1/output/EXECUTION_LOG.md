# EXP-003 Phase 1 — 실행 과정·결과 상세 로그

> 작성 2026-07-24. 획득함수 `Priority(c)` end-to-end 조립 + §5 leave-out 검증의 전 실행 기록.
> 실행 인터프리터: **`../../../.venv/bin/python`** (phase0 산출물 numpy2 · pyarrow 필요, 시스템 python 불가).
> 상위 요약은 [`../RESULTS.md`](../RESULTS.md), 이 파일은 단계별 명령·입출력·수치·판단의 전체 로그.

---

## 0. 파이프라인 개요

```
compute_surrogate.py ─ CV 대리지표(per-clip ADE/FDE)
        │
aggregate_error.py ─ ODD셀·사분면 집계 → model_error(c) + Domino
        │
priority.py ─ Priority(c) 5인자 통합 랭킹
        ├── learned_surrogate.py ─ CV→학습형 예측기(model_error 격상)
        ├── extend_exposure.py ─ exposure urban/rural 손앵커 확장 + 스윕
        └── leaveout.py ─ §5 leave-out 재현실험(정책 5종 × 시나리오 2 × seed 5)
```

---

## 1. CV 대리지표 (베이스라인) — `compute_surrogate.py`

- **방법**: 각 클립 egomotion 궤적에서 관측 2s → 미래 3s를 등속(CV) 예측, 2.5s stride 슬라이딩 창 평균 → per-clip ADE/FDE.
- **실행**: `compute_surrogate.py` (전체), 백그라운드.
- **결과** (`surrogate_summary.json`, `ade/fde_per_clip.npy`):
  - 처리 100,398 · valid **97,820** (커버 97.4%) · NaN 2,578(egomotion parquet 없음).
  - ADE: mean 2.369 · p50 **2.160** · p90 4.346 · max 19.123
  - FDE: mean 5.268 · p50 **4.817** · p90 9.664
  - npy 독립 재검산 = summary 일치 (finite 97,820 / NaN 2,578). 로그 에러 0건.

## 2. 집계 → model_error(c) — `aggregate_error.py`

- **셀 정의**: ODD 11-tuple(`odd_codes_compat_v2`) 유니크 = ODD 셀. n≥20 셀만(추정 안정).
- **model_error(c)**: 셀 mean ADE의 **클립수 가중 경험 CDF** ∈[0,1] (max 아웃라이어에 강건).
- **결과**:
  - ODD 셀 **282개** (valid 클립의 94.4%, 92,376 커버).
  - 임베딩 사분면별 ADE p50: Q1(high-dens×low-LID) 1.98 < Q0 2.16 < Q2 2.53 ≈ Q3 2.54
    → **저밀도 사분면(Q2/Q3)이 예측 어려움** = density-deficit와 같은 방향.
  - Domino(low-density × high-error) 최우선 수집 후보 13셀.

## 3. Priority(c) 통합 랭킹 — `priority.py`

- **공통 셀** = coarse `road_type|weather|fog` (exposure 결정공간·이름주소화 가능).
- `Priority = criticality × exposure × deficit × model_error × headroom`, 각 인자 min-max[0,1] 후 곱.
- `priority_core` = crit×ME×headroom (관측 셀 전부) / `priority_full` = ×exposure×deficit.
- **첫 산출(CV model_error 기준)**: priority_full이 6/17셀만 정의(exposure 한계①) + exposure×ME 충돌로 퇴화.
  → 이 진단이 4·5단계(학습형 교체, exposure 확장)를 촉발.

## 4. CV → 학습형 예측기 — `learned_surrogate.py`

- **동기**: CV는 클립별 자기적합 → 오차=기동 절대복잡도. **전역 학습모델**은 fleet 평균 동역학에
  맞춰져 오차=**"fleet 기준 비전형성"**(분포 의존). same-clip 누수 없는 **GroupKFold OOF**.
- **모델**: canonical frame(분기점 원점·관측 heading +x 회전) 미래 6지평 변위 회귀, MLP(64,32).
- **실행 주의 — 캐싱 버그 1건 잡음**: smoke(`--limit 2000`)가 저장한 2000클립 `windows.npz`를
  full run이 재사용 → 실제 1,949클립만 처리. `do_cache=(limit is None)`으로 수정 후 재실행.
- **결과** (`learned_surrogate_summary.json`, `learned_ade/fde_per_clip.npy`):
  - valid **97,820** · 창 **676,624**.
  - 학습 ADE: mean 1.081 · p50 **0.939** · p90 1.946 · max 26.817 (CV p50 2.16 대비 크게 개선 = 진짜 학습).
  - 학습 FDE: mean 2.487 · p50 2.169 · p90 4.487
- **검증**: 학습형 vs CV model_error 셀별 **Spearman 0.885** — 대체로 일치하나 소수 셀(n~25)에서
  +0.5~0.67 급등(CV는 클립별 적응이라 저평가) → 분포 의존 신호로 격상 성공.

## 5. exposure urban/rural 손앵커 확장 — `extend_exposure.py`

- **문제**: P_ext(KTDB itmsh)가 highway·national_road **2/4등급만**(rural 502·urban 미조사, COVERAGE.md).
  → priority_full 6셀만 정의(한계①). 저자는 "보완 안 함"으로 남겨둠.
- **결정(사용자 승인)**: **손앵커 + 민감도 스윕**으로 갱신. 관측 hw:nr(0.41465:0.58535, KTDB)은
  **보존**, {trunk, urban, rural} total-VKT 구성만 손앵커(통계연보 근사, 관측 아님). urban/rural
  hourly = national proxy. `compose.compose` **무수정 재사용**.
- **스윕 결과** (`exposure_sweep.json`) — road_type 과/소수집 deficit logr(부호<0=과대수집=프루닝, >0=과소=수집):

  | anchor | highway | national_road | urban | rural |
  |---|---|---|---|---|
  | central | +0.18 | +4.69 | −0.10 | −0.98 |
  | urban_heavy | −0.07 | +4.44 | +0.02 | −0.70 |
  | trunk_heavy | +0.38 | +4.89 | −0.38 | −0.98 |
  | rural_heavy | +0.18 | +4.69 | −0.38 | −0.47 |
  | rural_light | +0.28 | +4.79 | −0.10 | −1.39 |

  - **부호 안정**: national_road=**True(강건히 과소수집→수집)**, rural=**True(강건히 과대수집→프루닝)**,
    highway·urban=False(near-balanced, 앵커 민감 → 결론 보류).
  - **랭킹 견고성**: priority_full Spearman vs central **0.971~1.0**, top5 Jaccard 0.67~1.0.
- **효과**: priority_full **6→17셀 전부** 정의.

### 최종 Priority 랭킹 (학습형 ME × 확장 exposure, `learned_ext_priority_ranking.json`)

**priority_core top5** (crit × ME × headroom):

| cell | core | crit | ME |
|---|---|---|---|
| rural\|snow\|present | 0.763 | 6.0 | 1.00 |
| rural\|clear\|present | 0.107 | 2.4 | 0.64 |
| urban\|clear\|present | 0.083 | 2.0 | 0.63 |
| urban\|snow\|none | 0.056 | 2.5 | 0.19 |
| rural\|rain\|present | 0.050 | 3.6 | 0.16 |

**priority_full top5** (× exposure × deficit):

| cell | full | ME | deficit logr |
|---|---|---|---|
| urban\|clear\|present | 0.0109 | 0.63 | 3.47 |
| rural\|clear\|present | 0.0031 | 0.64 | 0.94 |
| national_road\|clear\|none | 0.0023 | 0.16 | 4.50 |
| rural\|clear\|none | 0.0012 | 0.82 | −1.12 |
| urban\|rain\|none | 0.0004 | 0.17 | 0.23 |

- 설계 긴장: `rural|snow|present`(core 1위)는 exposure 희소라 full에선 내려감 — ΔRisk=빈도×심각도×오차 가중이 의도대로 작동.

## 6. §5 leave-out 재현실험 — `leaveout.py`

### 설계 진화 (3차 반복)
1. **초기 smoke**: 전 정책 음(−) 회복 → 진단 = 입력이 kinematics 6차원뿐이라 모델이 날씨 조건축을
   학습할 통로 없음. **→ 장면 feature 추가**: 입력 = kinematics(6) + **PCA(임베딩,16)**.
2. **2 결핍시나리오 + 다중seed**: adverse(snow/fog, ODD축)·kinematic(고yaw). guided per-clip 재정의
   = `cell_context(exposure×crit×deficit×headroom) × per-clip raw ADE`. → 정책차가 std에 잠김.
3. **mixed candidate pool + 5seed**: candidate = tail(유용) + 잉여 common(3×, 무용) → 정책 **변별력**
   시험. `tail_picked` = 각 정책이 실제로 tail을 집은 비율(핵심 진단).

### 최종 결과 (`leaveout_results.json`, mixed pool · 5 seed · budget 800)

**kinematic** (baseline tail ADE 0.984, candidate 11,740):

| 정책 | 회복 mean±std | tail_picked |
|---|---|---|
| diversity_only | **+0.0598 ± 0.0148** | 33% |
| coverage_only | +0.0592 ± 0.0300 | 50% |
| random | +0.0437 ± 0.0274 | 25% |
| uncertainty_only | +0.0185 ± 0.0190 | 29% |
| **guided** | **+0.0074 ± 0.0189** | **23%** |

**adverse** (baseline tail ADE 0.916, candidate 9,684): random +0.004 > 나머지 ≈0 (결핍 자체 없음).

### 판정
- **G4(guided > 단일렌즈) 미성립**. kinematic에서 diversity/coverage가 guided를 이기고 **guided 꼴찌**.
- **결정적 진단** (`tail_picked`): guided가 유용 kinematic 클립을 **23%만** 집음(random 25%보다도 낮음).
  이유: guided = ODD-조건 Priority × per-clip 오차인데, 고yaw 급기동은 **평범한 ODD조건**(urban/highway·clear)에
  살아 cell_context 낮음 → guided가 회피 → 예산 낭비.
- **원인 = task 부적합**: egomotion의 실패는 **기동축**, Priority는 **ODD-조건축** → 구조적 오조준.
  adverse(ODD축)엔 애초 성능결핍 없음(baseline_tail 0.916 < overall).

---

## 7. 최종 결론

1. 획득함수 `Priority(c)`는 다섯 인자로 **완전히 조립·작동**(exposure 스윕 견고: national 수집 / rural 프루닝).
2. **egomotion 대리지표는 두-렌즈 G4 검증에 부적합** — downstream·기계적으로 증명됨(guided 오조준).
3. egomotion은 uncertainty/kinematic 축·exposure 과소수집 검증엔 유효.
   **ODD 두-렌즈 G4는 condition-sensitive 다운스트림(perception/detection)으로 이관** 필요.

## 산출물 목록 (이 디렉토리)
- `ade/fde_per_clip.npy`, `surrogate_summary.json` — CV 대리지표
- `learned_ade/fde_per_clip.npy`, `learned_surrogate_summary.json`, `windows.npz` — 학습형
- `{learned_,}model_error_by_odd_cell.json`, `{learned_,}model_error_per_clip.npy`, `{learned_,}domino_density_x_error.json`, `{learned_,}error_by_quadrant.json`
- `{learned_,learned_ext_}priority_ranking.json` — Priority 랭킹
- `coarse_cell_per_clip.npy` — per-clip coarse 라벨 캐시
- `exposure_sweep.json` — exposure 손앵커 스윕 (+ `../../phase0_2/exposure/output/P_ext_extended.json`)
- `leaveout_results.json` — §5 leave-out (최종=mixed pool 5seed)
- 실행 로그: `full_run.log`, `learned_full_run.log`, `leaveout_full.log`, `leaveout_mixed.log`
