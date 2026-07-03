# EXP-003 연구 종합 — 패러다임 분석 & 관련 연구

**작성일**: 2026-07-02  
**역할**: EXP-003 design.md의 이론적 배경 문서  
**참조 실험**: EXP-003 ([design.md](design.md))

---

## 1. 패러다임 전환 분석

### 1.1 왜 이 방향인가

EXP-002(SANFlow)까지의 접근은 "D_train에서 어떤 갭이 있는가"를 찾는 수동 탐색이었다. MOSAIC은 여기서 한 걸음 나아가 "D_pool에서 어떤 데이터를 추가하면 성능이 얼마나 오르는가"를 스케일링 법칙으로 정량화한다.

그러나 MOSAIC만으로는 불충분한 지점이 있다. MOSAIC은 D_train이 이미 있다고 가정하고 D_pool 선택만 최적화한다. D_train 자체의 분포가 심하게 편향되어 있다면 — 예를 들어 맑은 날 직진 클립이 70%를 차지한다면 — D_pool을 아무리 잘 선택해도 구조적 한계가 있다.

EXP-003의 DISC(Distribution-Informed Smart Curation) 방향은 이 문제를 해결한다. D_train 분포를 먼저 다차원으로 이해하고, 필요하면 D_train 내부도 재구성(프루닝 + 리밸런싱)하는 것이 핵심이다.

### 1.2 Pool Selection vs. Distribution Curation 비교

| 차원 | Pool Selection (MOSAIC) | Distribution Curation (DISC) |
|------|------------------------|------------------------------|
| 관점 | D_pool에서 무엇을 추가할지 | D_train 분포 자체를 최적화 |
| 전제 | D_train은 주어진 것 (고정) | D_train도 조정 가능한 변수 |
| 갭 정의 | 성능 여지 a_i | 밀도 갭 × 성능 여지 × LID × 수집 가능성 |
| 대표 논문 | MOSAIC (Dimlioglu et al., 2026) | DataComp, Sorscher et al., Domino |
| 프루닝 | 없음 | 중복/저가치 클립 먼저 제거 |
| 시간 복잡도 | M × 파일럿 횟수 | Phase 0 분석 추가 필요 |

### 1.3 Data-Centric AI 패러다임과의 연결

Data-Centric AI는 Andrew Ng이 제안한 개념으로, 모델 아키텍처보다 데이터 품질과 구성에 집중하는 패러다임이다. 핵심 주장은 세 가지다:

1. **모델 성능 병목은 종종 데이터에 있다**: 동일 아키텍처에서 데이터 품질 개선이 모델 개선보다 효율적
2. **데이터 분포가 모델의 일반화를 결정한다**: 희귀 시나리오 부족 = 그 도메인 성능 한계
3. **데이터 검수는 반복적이어야 한다**: 학습 결과를 보고 데이터를 개선하는 루프

EXP-003의 DISC 방향은 이 세 원칙을 구체화한 것이다. Phase 0에서 분포를 이해하고, Phase A~D에서 수집 전략을 최적화하며, EXP-004에서 구성 변화의 효과를 검증하는 전체 루프가 Data-Centric AI의 실천이다.

### 1.4 Phase 0 설계 철학 — 단일 앵커 기반 기하학-의미 이중 분석

Phase 0의 핵심 질문은 단순하다: **"83k 클립이 있다는 것과 83k 클립의 분포를 안다는 것은 다른가?"**

답은 다르다. 카운트(count)는 "얼마나 많은가"만 말한다. 분포(distribution)는 "어떻게 퍼져 있는가", "어디에 밀집되어 있는가", "빈 공간은 어디인가"를 말한다. 같은 83k라도 한 시나리오에 70%가 집중된 분포와 균등 분포는 전혀 다른 학습 데이터다.

Phase 0 v3는 **단일 k-NN 앵커**(0-A) 위에 두 개의 분석 트랙을 독립 공간에서 운영한다:

```
기하학 트랙: 0-A → 0-B(밀도+중복) → 0-C(LID+신뢰도+k-민감도) → 0-D(6분류, GMM BIC K=1~3 brentq)
                                                                         ↓ thresholds.json
                                               [조건부] 0-D-val → "Q3 결정 FLIPD 검증"
                                                                         ↓
의미 트랙:                               0-E-1(TF-IDF KMeans K=12) × 0-D 교차표
                                                                         ↓
수집 전략:                                         0-E-2(mean_lid + gap_ratio → 4분기)
```

기하학 트랙은 임베딩 공간에서 밀도·LID를 측정하고, 의미 트랙은 **TF-IDF 공간**(임베딩과 독립)에서 시나리오를 클러스터링한다. 두 트랙이 서로 다른 공간에서 나오므로 교차표(0-D 사분면 × 0-E-1 시나리오)가 진정한 새 정보를 제공한다. "어떤 시나리오가 Q1(과잉)이고 어떤 시나리오가 Q2(수집 우선)"인지 처음으로 완전하게 파악된다.

**v3 핵심 변경점 세 가지**:
1. **0-D 임계값**: `np.median` 50:50 강제 → GMM BIC K=1~3 brentq 실제 교차점 (`thresholds.json`에 저장, 0-E-2에서 재사용)
2. **0-E-1 클러스터링**: 임베딩 GMM(0-D와 같은 공간) → TF-IDF KMeans(독립 텍스트 공간) + per-scenario Vendi Score 추가
3. **0-E-2 수집 판정**: 3분기 → 4분기 (`COLLECT_HIGH_PRIORITY` 추가 — `gap_in_scenario_ratio > 0.4`일 때 대규모 탐색 트리거)

**왜 Effective N + Vendi Score인가 (0-B)**

Effective N은 "83k 클립이 실질적으로 얼마나 많은 독립 시나리오를 커버하는가"를 정량화한다. 야간 직진 클립 3만 개가 서로 98% 유사하다면 이 3만 개는 사실상 하나의 시나리오를 중복 표현한 것이다. Yao et al. (ACL 2024, SoftDedup)의 아이디어를 따라 uniqueness_weight = 1.0 - soft_commonness로 각 클립을 연속 가중치로 평가하고, 그 합이 Effective N이 된다. 이 값이 38k(soft)라면 83k 클립 중 약 54%가 중복 정보다 — 중복 제거 후 실질 정보량이 절반 수준임을 의미한다.

그러나 Effective N은 한 가지를 놓친다. 유사도가 0.7~0.9인 "비슷하지만 같지는 않은" 클립들 사이의 다양성이다. Vendi Score(Friedman & Dieng, TMLR 2023)는 이를 해결한다. `VS = exp(H(eigenvalues(K/tr(K))))` — 커널 행렬의 전체 고유값 스펙트럼으로 다양성을 계산하므로, 클립 간 유사도 분포 전체를 반영한다.

**v2 변경점**: Effective N(per-clip uniqueness_weight)은 0-D와 0-E-1에 직접 연결된다. 0-D에서 사분면별 `effective_n_contribution`을 계산하고, 0-E-1에서 시나리오별 `internal_redundancy`로 분해한다 — "글로벌 숫자"에서 "시나리오 단위 중복도"로 전환.

**왜 LID + 신뢰도 플래그 + k-민감도인가 (0-C)**

LID(Local Intrinsic Dimensionality, Ma et al. ICLR 2018)는 각 클립 주변의 변동 축 수를 측정한다. LID가 높은 희소 클립 = 다양한 시나리오 변주가 존재하는 갭, LID가 낮은 희소 클립 = 본질적으로 단조로운 자연 희귀.

**v2 신규: LID 신뢰도 플래그**. LID MLE는 k=20 이웃 거리의 로그 비율로 추정된다. 저밀도 영역에서 20번째 이웃까지 거리(r_max)가 크면 log 비율의 분산이 폭발하고 LID 추정치 자체가 노이즈가 된다. `r_max_dist < 0.6` 기준으로 신뢰 가능한 클립만 Q2/Q3로 분류하고, 나머지를 Q4(LID_UNCERTAIN)로 분리한다. Q4 클립은 기하학적 판단 대신 0-E-1의 시나리오 프로파일로 결정한다.

**v12 신규: k-민감도 분석**. 0-C에서 k=15/20/25 세 가지로 LID를 계산한다(`lid_k15.npy`, `lid_k20.npy`, `lid_k25.npy`). k=20 MLE만으로는 "이 추정치가 이웃 수 선택에 얼마나 민감한가"를 모른다. `flip_any_gmm`: k=20 임계값 미만이지만 k=15 또는 k=25에서 임계값 이상인 저차원 신뢰 클립 비율이 `k_sensitive_rate`로 계산된다. 이 값이 > 0.05이면 `flipd_recommended=True` — 경계 구역 클립의 LID 판정이 k 선택에 민감하다는 실증 신호다. 0-D에서 GMM 임계값이 확정된 후 k_sensitive_rate를 GMM 기반으로 재계산해 `lid_stats.json`을 업데이트한다(`k_sensitive_rate_approx`에 원본 중앙값 기준 근사치 보존).

**왜 6-분류 Action Map인가 (0-D)**

v1의 4-사분면(Q0~Q3)은 모든 저밀도 클립의 LID를 신뢰한다고 가정했다. v2는 Q4를 추가해 "저밀도 + LID 불신뢰 케이스"를 명시적으로 분리한다. v9에서 Q5를 추가해 "고밀도 + LID 불신뢰" 케이스도 분리한다:

```
        고밀도                 저밀도
고LID  Q0 KEEP              Q2 COLLECT (저밀도+고LID+신뢰)
저LID  Q1 PRUNE             Q3 → 0-E-2 판정 (저밀도+저LID+신뢰)
—      Q5 PRUNE_UNCERTAIN   Q4 → 0-E-1 의미로 판단 (저밀도+LID 불신뢰)
       (고밀도+LID 불신뢰)
```

**v3 임계값 변경**: `np.median` 사용 시 데이터를 기계적으로 50:50으로 나눠 "절반이 저밀도, 절반이 고밀도"가 되는 아티팩트가 발생한다. 실제 분포는 두 개의 자연 군집(조밀한 시나리오 클러스터 vs. 희소 공간)으로 나뉘는 경우가 많다. GMM BIC로 K=1~3을 비교하고, K=2 이상이면 `brentq`로 인접 성분 간 실제 교차점을 임계값으로 쓴다 — 두 군집 중심의 산술 평균보다 더 정확하게 데이터 자체의 구조를 반영한다. K=1(단봉 분포)이면 median 폴백을 사용하고 `thresholds.json`의 `lid_threshold_unimodal=True` / `density_threshold_unimodal=True` 플래그로 경고한다 — 이 경우 Q2/Q3 구분이 50:50 기계 분할임을 다운스트림에 알린다. 결정된 임계값은 `thresholds.json`에 저장되어 0-E-2에서 재로드된다.

**v12 신규: 경계 구역 정량화**. `lid_margin = |lid_per_clip - lid_threshold| / lid_threshold`를 계산하고, margin ≤ 0.15인 클립을 `lid_boundary_zone`으로 표시한다. `q3_boundary_rate`(Q3 내 경계 클립 비율)가 `thresholds.json`에 저장된다. 이 값이 > 0.3이면 0-D-val FLIPD 검증이 트리거된다.

Q1/Q5는 "많지만 단조로움 → 프루닝 후보"인데, 0-E-1 시나리오 레이블이 부여되므로 "맑은 날 직진이 Q1의 65%"처럼 **무엇을 프루닝하는지 구체적으로 알 수 있다**.

**0-D-val: 조건부 FLIPD 검증 (v12 신규)**

`k_sensitive_rate > 0.05` 또는 `q3_boundary_rate > 0.3`이면 0-D-val가 실행된다. FLIPD(Cresswell et al. NeurIPS 2024)는 Poisson 점 과정 경계 보정을 적용해 경계 클립의 LID를 재추정한다. 0-D에서 Q3로 분류된 클립 중 `lid_boundary_zone=True`인 클립만 선택적으로 재계산(`flipd_per_clip`)하고, 재추정 결과가 다르면(`flipd_per_clip >= lid_threshold`) Q3→Q2로 재분류한다. `flipd_validation.json`은 항상 기록된다 — SKIP 시에는 `flipd_applied=False`와 skip 이유를 저장해 "실행되지 않음"과 "SKIP 결정"을 구별할 수 있게 한다.

**왜 0-E를 두 단계로 분리했는가 (0-E-1 + 0-E-2)**

v1의 0-E는 Q2+Q3(저밀도 클립)에만 GMM을 적용했다. 이 구조에는 두 가지 문제가 있었다:

1. **분석 비대칭**: Q0/Q1(고밀도 50%)의 시나리오 내용을 전혀 알 수 없었다. "무엇이 과잉인가"를 모른 채 프루닝 결정을 내려야 했다.
2. **Q2 비율 순환성**: "슬라이스 내 Q2(고LID) 클립이 많으면 COLLECT"는 0-C/0-D의 LID 정보를 반복하는 것이지 독립적 새 정보가 아니었다.

**0-E-1(전체 83k)**은 Domino(Eyuboglu et al., ICLR 2022)의 아이디어를 "저밀도 조건" 대신 **"전체 데이터셋"**에 적용한다. **TF-IDF KMeans K=12**로 83k 전체를 시나리오 클러스터로 나누고, 각 클러스터의 사분면 분포(Q0~Q4 비율)를 계산한다. 이 교차표가 "멀티차원 분포 프로파일링"의 실제 핵심 결과물이다.

**왜 임베딩 GMM이 아닌 TF-IDF KMeans인가 (v3 변경)**: 0-D가 이미 임베딩 공간에서 밀도·LID를 계산했다. 0-E-1도 임베딩 GMM을 쓰면 같은 공간에서 클러스터링한 것이므로 0-D와 상관관계가 높고 독립적인 새 정보를 제공하지 못한다. TF-IDF는 텍스트 의미를 직접 인코딩하므로 고차원 임베딩 공간에서 인접한 클립이라도 텍스트 의미가 다를 수 있고, 역도 성립한다. 두 공간의 불일치 지점이 가장 흥미로운 분석 결과다.

**per-scenario Vendi Score (v3 신규)**: 전체 Vendi Score(0-B)가 "83k 전체 다양성"을 줬다면, 시나리오별 Vendi Score는 "각 시나리오가 내부적으로 얼마나 다양한가"를 보여준다. Vendi Score가 낮은 시나리오 = 내부 반복이 많은 과잉 시나리오, 높은 시나리오 = 내부 변주가 풍부한 양질 시나리오.

**v12 신규: NMI/ARI 독립성 검증**. TF-IDF 공간(시나리오 레이블)과 임베딩 공간(Q0~Q5 사분면) 간 독립성을 NMI < 0.15 + ARI < 0.1로 검증한다(`two_space_independence_ok` 플래그). 이 조건이 실패하면 두 공간이 예상보다 상관관계가 높다는 의미 — TF-IDF KMeans가 임베딩 기반 사분면을 단순히 복제하고 있을 수 있다. §4.8.2에서 언급한 BERTopic 재시도 트리거 조건의 하나다.

**v12 신규: PRUNE_DOMINANT_THRESHOLD 상대 기준선**. 시나리오별 `prune_signal_pct`(Q1+Q5 비율)가 고정 임계값 40%를 초과하면 `is_prune_dominant=True`였으나, 글로벌 Q1+Q5 기준선이 이미 35%인 데이터셋에서 40% 기준은 의미가 없다. `PRUNE_DOMINANT_THRESHOLD = max(40.0, 1.5 × global_prune_pct)`로 기준선 대비 상대 판정으로 전환한다. 글로벌 기준선보다 50% 이상 높은 시나리오만 PRUNE 우세로 표시된다.

**0-E-2(저밀도 갭 세부 분석)**는 0-E-1 시나리오 레이블을 재사용해(재클러스터링 없이) Q2+Q3+Q4 클립을 시나리오 단위로 그룹화한다. Q2 비율 대신 **mean_lid를 직접 사용**해 순환성을 제거하고, 4분기로 분류한다:

```
lid_rel_ratio < 0.4          → UNCERTAIN_CHECK_SEMANTIC (수동 검토)
mean_lid ≥ lid_threshold
  + gap_in_scenario_ratio > 0.4 → COLLECT_HIGH_PRIORITY  (대규모 탐색 필요)
  + gap_in_scenario_ratio ≤ 0.4 → COLLECT               (표준 탐색)
mean_lid < lid_threshold     → SYNTHETIC_OR_ACCEPT       (데이터 부족 or 수용)
```

`lid_threshold`는 0-D에서 계산한 GMM BIC brentq 값을 `thresholds.json`에서 로드한다. `gap_in_scenario_ratio > 0.4`는 "이 시나리오 전체에서 갭이 차지하는 비율"로, 비율이 높으면 시나리오 자체가 D_train에 부재한다는 의미 — 단순 COLLECT보다 더 적극적인 수집 전략이 필요하다.

**v12 신규: lid_context_caution 플래그**. 갭 슬라이스의 mean_lid ≥ lid_threshold이지만 해당 시나리오 전체의 mean_lid < lid_threshold인 경우 `lid_context_caution=True`를 부여한다. 이는 소수의 고LID 클립이 시나리오 전체의 COLLECT 판정을 끌어올리는 "소수 지배" 케이스다. 갭 내부에는 진짜 탐색 가치가 있지만 시나리오 전체 맥락에서는 LID 상황이 다르다는 경고 신호다. `collect_candidates.json`에 이 플래그가 포함되며, Phase D에서 해당 시나리오 수집 시 더 신중한 접근이 필요하다.

**MIN_GAP_SIZE = 50**: 갭 슬라이스 최소 크기를 50으로 설정한다. LID MLE가 k=20 이웃을 사용하므로 클립 수가 50 미만이면 이웃 관계가 불안정해 mean_lid 자체의 분산이 과도하게 커진다. 30(구 기준)은 분산 폭발 방지에는 충분했지만 안정적인 mean_lid 추정에는 부족했다.

---

## 2. MOSAIC 핵심 공헌 분석

> 이 절은 "캡셔닝 후 클러스터링"이 표면이고, 그 아래 어떤 수학적 구조와 패러다임 전환이 있는지를 설명한다.

### 2.1 공헌 1: 문제 정의 — 다중 경쟁 지표 동시 최적화

기존 데이터 선택 연구들은 이런 가정을 공유한다:

> "좋은 데이터를 골라내면, 모든 평가 지표가 함께 좋아진다."

MOSAIC이 이 가정을 깼다. 현실은 다르다:

> "고속도로 클립을 추가하면 Lane Keeping은 오르지만, No-fault Collision에는 도움이 안 되거나 심지어 떨어질 수 있다. 교차로 클립을 추가하면 반대다."

즉 **지표들은 서로 경쟁한다**. 이 트레이드오프를 모델링하지 않은 채 데이터를 선택하면, 어떤 지표는 좋아지고 어떤 지표는 희생되는 결과가 나온다. 논문 Table 2에서 Uncertainty 방법이 TTC는 올리지만 DAC를 깎는 현상이 정확히 이것이다.

이것을 수식으로 표현하면:

```
max          U  ( { G_r( f(·; D_train ∪ D_sel), D_val ) }^R_{r=1} )
 ↑                ↑    ↑   ↑                              ↑
최적화 목표   집계함수  지표  모델                         R개 지표 전부

조건: D_sel ⊂ D_pool,  |D_sel| = B
       ↑                    ↑
  풀에서만 고를 것        딱 B개만 고를 것
```

#### 기호 해설

**`f(·; D)` — 모델**

```
f(·; D_train)          → 기존 데이터만으로 학습한 모델
f(·; D_train ∪ D_sel)  → 기존 데이터 + 새로 선택한 데이터로 학습한 모델
```

세미콜론 오른쪽은 "무엇으로 학습했는가"다. 새 데이터를 추가하면 모델 자체가 달라진다는 것을 명시한다.

**`G_r(f(·; D), D_val)` — 개별 평가 지표**

"모델 f를 검증셋 D_val에서 돌렸을 때 나오는 r번째 성능 수치". 논문에서 R=9이고, 9개 지표는:

| 기호 | 의미 | 유형 |
|------|------|------|
| NC | No-fault Collision (무과실 충돌 없음) | 패널티 |
| DAC | Drivable Area Compliance (주행 가능 구역 준수) | 패널티 |
| DDC | Driving Direction Compliance (주행 방향 준수) | 패널티 |
| TLC | Traffic Light Compliance (신호 준수) | 패널티 |
| EP | Ego Progress (자차 진행률) | 평균 |
| TTC | Time To Collision (충돌까지 시간) | 평균 |
| LK | Lane Keeping (차선 유지) | 평균 |
| HC | Heading Change (방향 변화) | 평균 |
| EC | Ego Comfort (승차감) | 평균 |

편의상 논문은 `G_r(D)` 로 줄여 쓴다 (검증셋은 고정이라 생략).

**`U(...)` — 집계 함수 (EPDMS)**

U는 9개 수치 벡터를 받아서 숫자 하나로 만드는 함수다. 논문에서는 EPDMS로 정의된다:

```
EPDMS = (NC × DAC × DDC × TLC)  ×  weighted_average(EP, TTC, LK, HC, EC)
         ←──── 패널티: 곱셈 ────→       ←──── 평균 지표 ────→
```

곱셈 구조가 경쟁을 만드는 방식:
- NC=1.0, DAC=0.0 → EPDMS = **0** (DAC 하나가 망하면 전체가 0)
- NC=0.8, DAC=0.8 → EPDMS = **0.64** (균형이 유리)

어느 하나만 올리고 다른 걸 희생하는 전략이 통하지 않는다.

#### 왜 이것이 "R개 지표 동시 최적화"인가

단일 지표 최적화라면:
```
max G_1(D_train ∪ D_sel)   ← NC만 올리면 끝, 다른 지표 무관
```

다중 지표 동시 최적화는:
```
max U(G_1, G_2, ..., G_9)   ← D_sel이 9개 지표 전부에 미치는 영향을 계산해야 함
```

고속도로 클립을 예로 들면:
```
NC↑  DAC↑  LK↑        ← 좋아지는 지표
TLC↔  EP↓              ← 변화 없거나 나빠지는 지표 (도심 신호/진행 경험 희석)
```

단일 지표(LK)만 보면 "이 클립 좋다"지만, U를 최적화하려면 EP·TLC 손실까지 계산해서 **진짜 순이익이 있을 때만** 선택해야 한다.

> 한 문장 요약: `max U(...)` 는 "어떤 데이터 B개를 추가로 학습시키면 9개 지표 종합 점수가 가장 높아지는가"를 찾는 문제이며, U 내부의 곱셈 구조 때문에 하나만 올리고 다른 걸 희생하는 전략은 오히려 U를 낮춘다.

이전 연구 중 다중 경쟁 지표를 이 방식으로 정식화한 것은 없었다.

---

### 2.2 공헌 2: 조합 폭발 해결

위 문제를 직접 풀려면, M개 클러스터 각각에서 몇 개씩 뽑을지 모든 조합을 시험해야 한다. 클러스터가 6개만 되어도 경우의 수가 폭발한다.

논문의 핵심 수학적 기술은 이 문제를 아래 근사로 분해한다:

```
ΔU_mix(n1,...,nM) ≈ ΔU_1(n1) + ΔU_2(n2) + ... + ΔU_M(nM)
      ↑전체 이득                ↑클러스터별 독립 이득의 합
```

"각 클러스터의 기여가 독립적이다"는 가정 하에, **M번의 독립 실험으로 최적 배분을 계산**할 수 있게 된다. 조합 폭발이 선형으로 줄어든다.

저자들도 이 근사가 완벽하지 않음을 안다. 논문 Limitations에 직접 적었다:
> "If the clustering fails to produce well-separated groups, this assumption may be violated."

즉 **클러스터가 잘 분리될수록 이 근사가 정확하다**. 이것이 Q1(클러스터링 알고리즘)과 Q2(K 값) 결정에 직접 영향을 미친다.

#### "M번의 독립 실험"이란 구체적으로 무엇인가

각 클러스터별로 **"이 클러스터 데이터만 n개 추가해서 학습하면 U가 얼마나 오르나"** 를 측정하는 소규모 파일럿 학습이다. 클러스터 3개 예시:

```
[클러스터 1: 야간]
  D_train + 야간 50개  → 모델 재학습 → U 측정 → ΔU_1(50)
  D_train + 야간 100개 → 모델 재학습 → U 측정 → ΔU_1(100)
  D_train + 야간 200개 → 모델 재학습 → U 측정 → ΔU_1(200)
  D_train + 야간 400개 → 모델 재학습 → U 측정 → ΔU_1(400)
  → 4개 점으로 스케일링 곡선 피팅 → (a_1, τ_1) 획득

[클러스터 2: 우천]  ← 야간 클립은 전혀 넣지 않음
  D_train + 우천 50/100/200/400개 → 각각 재학습·측정
  → (a_2, τ_2) 획득

[클러스터 3: 고속도로]  ← 야간·우천 전혀 없음
  D_train + 고속도로 50/100/200/400개 → 각각 재학습·측정
  → (a_3, τ_3) 획득
```

각 실험은 **오직 그 클러스터의 데이터만** 추가한다. 다른 클러스터는 섞지 않는다. 이것이 "독립"의 의미다.

**왜 D_train이 매번 들어가는가**

두 가지 이유가 같은 사실을 다른 각도에서 설명한다.

이유 1 — 이론적: ΔU_i(n)은 절대 성능이 아닌 **변화량**이므로 기준점이 필요하다.

```
ΔU_i(n) = U(D_train ∪ 야간 n개) − U(D_train)
            ↑새 데이터 추가 후 성능    ↑추가 전 성능 (기준)
```

D_train 없이 야간 50개만으로 학습하면 야간 데이터 자체의 절대 성능이 나오는데, 이건 알고 싶은 정보가 아니다. "이미 가진 것(D_train)에서 출발해서, 야간 데이터가 얼마나 더 도움이 되는가"가 목표다.

이유 2 — 실제 구현: 논문 p.8에서 **"through continual training"** 이라고 명시한다. 즉:

```
[이론적 표현]                      [실제 구현]
D_train ∪ 야간 50개로 학습   →   D_train으로 학습된 체크포인트
                                      ↓
                                 야간 50개로 이어서 finetune
                                      ↓
                                 U 측정 → ΔU_1(50)
```

매 파일럿마다 처음부터 전체 재학습하면 비용이 너무 크다. D_train 체크포인트에서 출발해 클러스터 데이터를 추가 학습하는 **pretrain(D_train) → finetune(클러스터 데이터)** 구조가 실제 구현이다.

파라미터가 2개(a_i, τ_i)뿐이므로 2개 점만으로도 피팅 가능하다. 논문 Figure 3의 ★ 표시가 실제 파일럿 포인트로, 2개로도 곡선이 잘 맞음을 보였다.

**실험 비용 비교:**

```
조합 탐색 방식: C(83000, 1000) ≈ 10^2000번 학습 → 불가능
MOSAIC 파일럿:  M(클러스터 수) × 4(포인트) = 6 × 4 = 24번 학습 → 실용적
```

**파일럿 이후 실제 선택은 추가 학습 없이 수식 계산만:**

```python
# (a_i, τ_i)를 모두 얻은 뒤 — 모델 학습 없음
while len(D_sel) < B:
    for i in range(M):
        δ[i] = ΔU_i(b[i]+1) - ΔU_i(b[i])  # 피팅된 수식으로만 계산
    j = argmax(δ)        # 지금 한계 이득이 가장 큰 클러스터
    sample = D_pool[j]   # 그 클러스터에서 중요도 순 1개 선택
    D_sel.add(sample)
    b[j] += 1
```

파일럿으로 얻은 수식이 이후 모든 선택 결정을 대신한다. 이것이 MOSAIC의 계산 효율성의 원천이다.

---

### 2.3 공헌 3: 스케일링 곡선의 오목성 → 탐욕 최적성

각 클러스터의 기여를 포화 지수 함수로 모델링한다:

```
ΔU_i(n) ≈ a_i × (1 - e^{-n/τ_i})

  a_i : 이 클러스터에서 얻을 수 있는 최대 성능 향상
  τ_i : 포화 속도 (낮을수록 빠르게 포화 → 일찍 "다 먹었다")
```

이 함수의 모양은 오목(concave)하다. 즉 처음에 많이 오르다가 점점 덜 오른다. 이 오목성 때문에:

- 한계 기여 δ_i(b) = ΔU_i(b+1) - ΔU_i(b) 는 b가 커질수록 단조 감소
- "지금 가장 한계 기여가 큰 클러스터에서 하나 더 뽑는다"는 탐욕 전략이 수학적으로 최적해와 동일

알고리즘 자체는 단순하지만, **이 단순함이 이론적으로 보장된다**는 점이 핵심이다. 탐욕 알고리즘이 항상 최적인 것은 아니다 — 목적함수가 오목할 때만 그렇다.

실용적으로도 중요하다: 파라미터가 2개(a_i, τ_i)뿐이므로 **파일럿 실험 4포인트만으로 곡선을 피팅**할 수 있다.

---

### 2.4 공헌 4: 최적 전략이 예산에 따라 달라진다 — 정적 랭킹의 한계

논문 Figure 3과 Figure 4가 보여주는 가장 중요한 발견:

```
예산 B = 250일 때   → Boston, Singapore 클러스터 우선
예산 B = 4,000일 때 → Pittsburgh 클러스터 우선
Vegas 클러스터      → 거의 어떤 예산에서도 효과 없음
```

Boston/Singapore는 초반에 가파르게 오르다 빨리 포화한다(τ_i 작음).  
Pittsburgh는 천천히 오르지만 끝까지 꾸준히 기여한다(a_i 크고 τ_i 큼).  

**이 전략은 고정 점수 랭킹으로는 절대 재현할 수 없다.** Uncertainty, Coreset, Chameleon이 실패하는 근본 이유다. 이 방법들은 모두 데이터 포인트에 고정 점수를 부여하는 정적 방식이다. "예산 250일 때와 4,000일 때 최적이 달라진다"는 동적 현상을 포착하지 못한다.

| 기존 패러다임 | MOSAIC 패러다임 |
|-------------|----------------|
| "이 데이터는 얼마나 중요한가?" | "지금 이 클러스터에서 하나 더 추가하면 얼마나 이득인가?" |
| 정적 가치 (한 번 계산, 끝) | 동적 한계 기여 (현재 상태에 따라 매번 재계산) |
| 예산 무관 | 예산에 따라 최적 전략 변화 |

#### 실험 결과 비교 구조 — 무엇과 비교하는가

논문의 비교 구조는 3개의 기준점으로 설계되어 있다.

```
성능
 ↑
 │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  Full Training (D_train + 전체 D_pool)  ← 천장
 │
 │                          ✦ MOSAIC
 │                    ✦ Chameleon
 │              ✦ Coreset
 │        ✦ Random
 │
 │  ■  Base (D_train만)  ← 바닥
 │
 └──────────────────────────────────→ 추가한 클립 수 (예산 B)
```

**기준 1 — Base보다 좋아야 한다 (최소 조건)**

`D_train`만으로 학습한 모델(Base)이 출발점이다. Base EPDMS는 Openscene 72.0, Navtrain 83.97.

**기준 2 — 같은 예산에서 다른 방법보다 좋아야 한다 (핵심 비교)**

```
Budget B=1000 (Openscene)
  Random     : EPDMS 75.84
  Uncertainty: EPDMS 71.12  ← Base보다 나빠짐
  Coreset    : EPDMS 80.46
  Chameleon  : EPDMS 79.08
  MOSAIC     : EPDMS 81.68  ← 최고
```

Uncertainty가 Base보다 낮아진 것에 주목. 불확실성 높은 샘플만 골랐더니 특정 지표는 올랐지만 다른 지표를 깎아 전체 U가 하락했다. 다중 경쟁 지표 문제를 무시했을 때 발생하는 전형적 실패다.

**기준 3 — Full Training에 얼마나 빨리 수렴하는가 (효율 비교)**

```
Navtrain에서 Full Training 성능 도달에 필요한 클립 수:
  전체 데이터 사용 : 4,141개
  MOSAIC          : 2,400개  ← 42% 적은 데이터로 동일 천장 도달
```

**효율 지표: BRMR (Budget Ratio to Match Random)**

```
BRMR = B_k / B

  B_k : 방법 k가 Random의 EPDMS에 도달하는 데 필요한 예산
  B   : Random이 사용한 예산

BRMR = 1.00  → Random과 동일한 효율
BRMR = 0.18  → Random 대비 82% 적은 데이터로 동일 성능 (MOSAIC 달성값)
```

| 비교 대상 | 질문 | MOSAIC 결과 |
|----------|------|------------|
| Base (D_train만) | 추가 데이터가 도움이 되는가? | 항상 Base 이상 |
| 다른 선택 방법들 | 같은 예산에서 더 좋은가? | 모든 예산에서 최고 |
| Full Training | 더 적은 데이터로 천장에 도달하는가? | 42~82% 적은 데이터로 동일 |

---

### 2.5 우리 프로젝트만의 확장

MOSAIC은 성능 이득(a_i)만 본다. 우리는 SANFlow로 **밀도 갭**도 안다.

```
MOSAIC만 쓸 경우: a_i가 높은 클러스터 우선 수집
우리가 할 수 있는 것:
    수집 우선순위_i = a_i × (1 - 현재 밀도_i)
                      ↑MOSAIC        ↑SANFlow
```

이 결합이 의미하는 바:
- 밀도 갭이 있어도 a_i가 낮으면(이미 포화) 수집 효과 없음
- a_i가 높아도 이미 밀도가 충분하면 우선순위 낮음
- **갭도 있고 성능 여지도 있는 클러스터** = 진짜 수집 우선 대상

EXP-003 v3 가설에서는 이를 4차원으로 확장한다:

```
priority_i = a_i × (1 - density_i) × LID_i_normalized × collectability_i
```

- `a_i`: MOSAIC 스케일링 파일럿에서 추정 (Phase B)
- `(1 - density_i)`: k-NN 소프트 밀도 역수 — 저밀도일수록 수집 필요 (0-B)
- `LID_i_normalized`: 지역 내재 차원 정규화값 — 다양성 있는 갭일수록 수집 가치 (0-C × 0-D)
- `collectability_i`: GMM 슬라이스 내 Q2 비율 — 수집 가능한 갭인지 판정 (0-E)

구 공식의 `coverage_gap_i`(크로스탭 셀 희귀도)와 `redundancy_i`(NMF 토픽 중복도)는 서로 다른 집계 단위에 정의되어 클립 수준에서 직접 결합할 수 없었다. 새 공식은 세 항이 모두 클립 수준(per-clip)으로 정의되므로 클러스터 집계가 일관적이다.

---

## 3. E2E AD 학습 패러다임

> MOSAIC 논문은 "어떤 데이터를 추가할 것인가"만 다룬다.
> 실제 E2E 개발에서 데이터가 어떻게 관리되는지 이해해야 MOSAIC의 위치가 명확해진다.

### 핵심: 두 전략은 대립이 아니라 시간 축이 다른 두 레이어

```
시간 →→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→

[단기: 1~4주 주기]  Finetune (D_train 유지)
  체크포인트 → finetune(D_sel + replay 샘플) → 빠른 배포
  목적: 긴급 버그 수정, 새 지역 추가, 빠른 반복

[장기: 분기 주기]  Full Retrain with Rebalancing (D_train 재구성)
  D_train 전체 재구성(리밸런싱) → 처음부터 Full Retrain
  목적: 누적 편향 제거, 구조적 성능 향상, 모델 아키텍처 변경
```

### 3.1 단기: Finetune (Catastrophic Forgetting & Experience Replay)

새 데이터를 체크포인트에 이어 학습하는 방식이다. 수백만 클립을 처음부터 재학습하면 몇 주가 걸리므로, 빠른 배포 주기에는 현실적으로 finetune이 필수다.

**핵심 문제: Catastrophic Forgetting**

새 데이터로만 finetune하면 모델이 기존 시나리오를 잊는다. 야간 데이터를 추가했더니 맑은 날 성능이 떨어지는 현상이 대표적이다.

해결책은 **Experience Replay** — 새 D_sel과 함께 기존 D_train 일부를 섞어 학습한다:

```
잘못된 finetune: 새 D_sel 100%  →  catastrophic forgetting
올바른 finetune: D_sel 70% + D_train replay 30%  →  균형 유지
```

이 때 "D_train replay 30%"에서 어떤 샘플을 고를지가 중요한 문제다. 균등 랜덤 샘플링이 기본이지만, 희귀 시나리오 오버샘플링이 더 효과적이라는 연구가 있다.

### 3.2 장기: Full Retrain with Rebalancing (D_train 진화)

분기 단위로 전체 데이터셋을 재구성하고 처음부터 학습한다. 이 단계에서 D_train 자체가 바뀐다:

```
D_train v1 (Q1) → 신규 수집 + 희귀 오버샘플링 + 품질 필터링 → D_train v2 (Q2)
```

리밸런싱의 핵심 작업:

| 작업 | 내용 |
|------|------|
| 오버샘플링 | 야간·우천·교차로 등 희귀 시나리오를 높은 가중치로 반복 샘플링 |
| 언더샘플링 | 맑은 날 직진 등 과잉 수집 시나리오 비율 축소 |
| 품질 필터링 | 라벨 오류·중복·저품질 클립 제거 |
| 롱테일 보강 | 사고 직전 등 희귀 케이스 집중 추가 |

D_train을 **삭제**하는 것이 아니라 **비율을 조정**하는 것이 핵심이다. 기존 데이터를 지우면 forgetting이 발생하므로, 희귀 시나리오를 오버샘플링해서 모델이 더 자주 학습하게 만드는 방식을 쓴다.

### 3.3 대표 사례

**Tesla — Data Engine**

```
수백만 대 플리트
    ↓ Shadow Mode: 모델이 틀린 순간 자동 감지
hard clip 자동 수집 (개입·판단 오류 장면)
    ↓ Dojo 슈퍼컴퓨터에서 라벨링
D_train에 편입 → 주기적 Full Retrain from scratch
```

Tesla는 D_train을 고정하지 않는다. Shadow Mode가 "모델이 실패한 시나리오"만 골라 D_train에 편입하므로, 이 자체가 **자동 리밸런싱**이다. FSD v12는 수백만 클립 규모를 Dojo에서 처음부터 재학습한다.

**Waymo — Simulation 보강**

희귀 시나리오를 실제로 수집하기 어려우므로, AdvSim·SurfelGAN으로 합성 데이터를 대량 생성해 채운다. 리밸런싱을 "합성 데이터 생성"으로 해결하는 방식이다.

**NVIDIA/MOSAIC — Pool Selection**

MOSAIC이 답하는 질문은 더 좁다:

```
D_train은 이미 있다 (이번 학습 사이클의 기준)
D_pool이 있다 (수집됐지만 아직 미선별 데이터)
→ D_pool에서 무엇을 D_train에 추가할 것인가?
```

"어떻게 학습하는가"가 아니라 **"무엇을 추가할 것인가"** 만 다룬다. Full Retrain vs Finetune의 선택은 MOSAIC 바깥의 문제다.

### 3.4 MOSAIC의 정확한 위치

```
[장기 Full Retrain 사이클]

D_train 현재 버전
      ↓
  D_pool에서 무엇을 추가할지 결정  ← MOSAIC이 여기를 담당
      ↓
D_train 새 버전 (= D_train ∪ D_sel)
      ↓
  Full Retrain from scratch
      ↓
배포 → 단기 finetune 반복
      ↓
다음 Full Retrain 사이클
```

MOSAIC은 장기 재학습 사이클에서 **D_pool 선택에 대한 정량적 근거**를 제공한다. 리밸런싱의 방향("어디에 희귀 데이터가 더 필요한가")을 스케일링 법칙으로 수치화하는 역할이다.

---

## 4. 관련 최신 연구

### 4.1 Data-Centric AI 패러다임

2021년 Andrew Ng이 NeurIPS 워크숍에서 제창한 패러다임 전환이다. 요약:

- **Model-Centric AI (기존)**: 데이터는 고정, 모델·알고리즘 개선에 집중
- **Data-Centric AI (새)**: 모델은 고정, 데이터 품질·구성 개선에 집중

실용적으로는 두 접근이 공존하지만, 현재 대규모 AD 시스템에서 데이터 구성이 성능 병목인 경우가 많다는 인식이 확산됐다. EXP-003의 DISC 방향이 이 흐름에 위치한다.

---

### 4.2 Beyond Neural Scaling Laws (Sorscher et al., NeurIPS 2022)

**핵심 주장**: 데이터를 무작정 늘리는 것보다 **프루닝(저품질·중복 제거) + 핵심 데이터 유지**가 같은 성능에 더 적은 데이터로 도달한다.

**주요 결과**:
- 데이터 프루닝(하위 30% 제거) + 나머지 학습 > 전체 데이터 학습 (동일 클립 수 기준)
- 특히 롱테일 분포에서 효과가 두드러짐
- 프루닝 기준: 모델 훈련 중 "어렵지만 맞추는" 샘플이 가장 가치 있는 샘플

**프로젝트 적용점**:
- EXP-003 Q6 (저가치 클립 프루닝) 결정의 이론적 근거
- "redundant 클립 제거 → 갭 채우기" 순서의 정당화
- 프루닝 기준으로 cosine similarity > 0.95 사용 (Sorscher의 "중복" 기준 응용)

---

### 4.3 Domino: 체계적 오류 자동 발견 (Eyuboglu et al., ICLR 2022)

**핵심 주장**: 모델이 일관되게 실패하는 "코히런트 슬라이스"를 자동으로 찾아낼 수 있다.

**방법**:
1. 모델 오류 임베딩 + 메타데이터를 결합해 슬라이스 발견
2. 슬라이스별 성능 갭 정량화
3. 발견된 슬라이스를 기반으로 수집 방향 결정

**성능 갭 vs 밀도 갭 구분**:
- 밀도 갭 (SANFlow, EXP-002): "이 시나리오가 D_train에 얼마나 없는가"
- 성능 갭 (Domino): "이 슬라이스에서 모델이 얼마나 틀리는가"

두 갭이 항상 일치하지 않는다는 것이 중요하다. 밀도 갭이 있어도 모델이 잘 일반화하면 수집 불필요. 성능 갭이 있어도 밀도가 충분하면 데이터 문제가 아닌 모델 문제일 수 있다.

**프로젝트 적용점**:
- Phase C (다중 메트릭 분리 평가)의 설계 근거
- 도메인별 Recall@5 측정이 단순 aggregate보다 필요한 이유

---

### 4.4 LESS: 영향력 기반 데이터 선택 (Xia et al., ICML 2024)

**핵심 주장**: 어떤 훈련 샘플이 특정 태스크 성능에 얼마나 영향을 미치는지 gradient similarity로 정량화할 수 있다.

**방법**:
```
influence(x_train → x_target) = ∇L(x_train) · ∇L(x_target)
                                  ↑gradient 내적 → 영향력 수치
```

높은 influence 샘플 선택 = target-specific 데이터 선택

**MOSAIC과의 비교**:

| 기준 | MOSAIC | LESS |
|------|--------|------|
| 관점 | 클러스터 단위 | 샘플 단위 |
| 계산 방식 | 스케일링 파일럿 | gradient 내적 |
| 타겟 | Aggregate U | 특정 태스크 |
| 비용 | M × 파일럿 횟수 | 전체 데이터 gradient 계산 |
| 장점 | 예산 동적 최적화 | 개별 샘플 정밀 선택 |

**프로젝트 적용점**:
- EXP-004 Phase A (데이터 가치 평가)에서 LESS 방식 gradient influence 추정 활용
- MOSAIC을 보완하는 샘플 단위 선별 방법으로 사용

---

### 4.5 DataComp: 대규모 데이터 큐레이션 벤치마크 (Gadre et al., NeurIPS 2024)

**핵심 주장**: 대규모 웹 데이터에서 **품질 필터링 → 다양성 확보** 순서가 중요하다. 모든 데이터를 다 쓰는 것보다 잘 필터링된 서브셋이 더 좋다.

**주요 발견**:
1. **필터링 > 다양성**: 품질 필터 적용 후 다양성을 추가하는 것이 효과적
2. **롱테일에서 다양성 필수**: 다수 도메인만 있는 데이터는 희귀 태스크에서 실패
3. **순서 중요성**: 필터링 전에 다양성 샘플링하면 저품질 데이터가 들어옴
4. **CLIP Score 필터**: 이미지-텍스트 정렬 품질 기준 (우리 프로젝트에서는 캡션 품질 기준)

**프로젝트 적용점**:
- Phase 0 ③ (품질 분포 분석)의 설계 근거
- "품질 필터 먼저, 다양성 나중" 원칙 → Q6 (프루닝 먼저) 결정의 지지
- 희귀 도메인 다양성 확보 필요성 (Phase D 근거)

---

### 4.6 DoReMi: 도메인 가중치 최적화 (Xie et al., NeurIPS 2023)

**핵심 주장**: 사전에 도메인 비율을 알 수 없을 때, 최악 도메인의 excess loss를 최소화하는 Minimax 최적화로 도메인 가중치를 자동 추정할 수 있다.

```
min  max_{d} E_{x~p_d}[L(x; θ)]
 θ     d
```

**MOSAIC과의 관계**:
- MOSAIC은 (a_i, τ_i) 파일럿으로 도메인별 기여량을 사후 추정한다 → 최악 케이스 보장 없음
- DoReMi는 Minimax 최적화로 도메인 가중치를 추정 → 희귀 도메인이 희생되지 않음을 보장

**프로젝트 적용점**:
- Phase B 파일럿 후 `a_i` 추정이 불안정하거나 희귀 도메인이 과소 평가될 경우의 대안/보완
- EXP-004에서 리밸런싱 가중치를 DoReMi 방식으로 추정하는 방향 (Waymo Full Retrain 사이클 참조)
- design.md 헤더 등록 논문 — 본문 연결: Phase B의 한계를 보완하는 이론적 대안

---

### 4.7 Dataset Cartography (Swayamditta et al., EMNLP 2020)

**핵심 주장**: 훈련 동역학(training dynamics)으로 데이터를 세 유형으로 분류할 수 있다.

```
Easy-to-learn   : 모델이 일관되게 맞추는 샘플 (중복/과잉 대표 가능성)
Ambiguous       : 에포크마다 맞추기도 틀리기도 하는 샘플 (가장 가치 있음)
Hard-to-learn   : 모델이 일관되게 틀리는 샘플 (노이즈 또는 OOD 가능성)
```

EXP-004에서 LESS 방식 대신 또는 보완으로 사용 가능한 방법이다. 구현이 더 단순하다 (추가 gradient 계산 불필요).

---

### 4.7 기존 프로젝트 문헌과의 연결

| 문헌 | 개념 | EXP-003 연결점 |
|------|------|----------------|
| Coverage Coreset (literature/GUIDE.md) | 커버리지 기반 코어셋 | Phase A TF-IDF 클러스터링의 대안 비교 기준 |
| Zhao et al. (diversity) | 다양성 측정 지표 | 0-B Vendi Score 해석 보완 기준 |
| FEND | 이상 탐지 기반 갭 발견 | SANFlow(EXP-002)의 이론적 배경 |
| WOD-E2E | Waymo E2E 데이터셋 구성 | D_train 목표 분포의 벤치마크 |
| Chodowiec et al. | ODD 커버리지 평가 | 0-E gap_slices의 semantic 해석 — ODD 태그 대조 기준 |

---

### 4.8 Phase 0 설계 범위 밖: 미반영 SoTA 방법론

Phase 0는 의도적으로 캡션 전용 오프라인 분석으로 설계됐다. 아래 세 방향은 기술적으로 더 강력하지만 현재 파이프라인에 통합되지 않았다. 미반영 이유와 그 영향을 명시해 Phase B 이후 보완 가능성을 판단할 수 있도록 한다.

#### 4.8.1 VLM/멀티모달 임베딩 (CLIP, DINOv2)

**무엇인가**: CLIP(Radford et al., OpenAI 2021), DINOv2(Oquab et al., META 2023) 등은 이미지(또는 비디오 프레임)와 텍스트를 공유 임베딩 공간에 매핑한다. 실제 시각 데이터 기반 LID·밀도 계산이 가능해져 캡션 의존성을 탈피할 수 있다.

**미반영 이유**:
- Phase 0는 83k 캡션만 존재하는 시점에 실행 가능하도록 설계됐다. 비디오 프레임 추출·인코딩 파이프라인이 없으면 CLIP/DINOv2를 적용할 수 없다.
- bge-m3 캡션 임베딩은 이미 고품질 언어 표현을 제공하며, Ruppik et al. (NeurIPS 2025)이 언어 모델 임베딩 LID의 일반화 예측력을 실증했다.

**영향 및 한계**:
캡션이 시각 데이터를 충실히 반영하지 않으면(예: 야간·우천 장면이 캡션에서 과소 묘사되는 경우) LID·밀도 분류 전체가 왜곡된다. Phase B 파일럿이 첫 번째 교차 검증 신호다 — 캡션 기반 클러스터와 실제 성능 갭이 불일치하면 bge-m3 임베딩을 CLIP/DINOv2로 교체하는 방향을 검토해야 한다. `thresholds.json`의 `lid_threshold_unimodal=True` 케이스(단봉 LID 분포)는 이 불일치 가능성이 특히 높은 신호다.

> **후속 작업**: Phase B 이후 `caution_scenarios.json`에 있는 CAUTION 시나리오에 대해 CLIP 임베딩 기반 LID를 사후 비교하면 캡션-시각 일치도를 정량화할 수 있다.

#### 4.8.2 BERTopic / 계층적 클러스터링

**무엇인가**: BERTopic(Grootendorst, 2022)은 UMAP 차원 축소 → HDBSCAN 밀도 기반 클러스터링 → c-TF-IDF 토픽 추출을 결합한 현대적 토픽 모델이다. 계층적 클러스터링(Ward linkage + 덴드로그램 기반 K 선택)은 실루엣보다 안정적인 K 결정 방법을 제공한다.

**미반영 이유**:
0-E-1의 TF-IDF KMeans는 구현 단순성과 재현성을 우선한 선택이다. `best_models` dict로 검증 모델을 재사용하고, `flat_fallback K=12`로 불안정한 실루엣 결과를 처리하는 실용적 보완이 이미 적용됐다.

**영향 및 한계**:
TF-IDF silhouette 점수는 고차원 희소 공간(83k × 3000)에서 불안정하다. `flat_fallback=True`(K간 실루엣 차이 < 0.02)가 발생하면 K=12 도메인 지식 폴백을 사용하는데, 이 K 자체가 임의적이다. 또한 KMeans는 구형 클러스터를 가정하므로 비선형 시나리오 경계(예: "교차로 야간 우천" 같은 복합 조건)를 하나의 클러스터로 묶지 못할 수 있다.

`silhouette_scores.json`에서 `flat_fallback=True` + `two_space_independence_ok=False`(scenario_diversity_summary)가 동시에 나타나면 TF-IDF KMeans의 시나리오 분리력이 낮다는 신호 → BERTopic 재시도를 고려.

> **후속 작업**: `flat_fallback=True` 케이스에서 BERTopic을 병렬 실행해 K 선택 및 토픽 일관성(coherence score)을 비교하는 ablation. 구현 비용이 낮고 Phase 0 결과 신��도를 직접 검증하는 효과가 있다.

#### 4.8.3 DoReMi 온라인 재가중치 (Xie et al., NeurIPS 2023)

**무엇인가**: DoReMi는 소규모 proxy 모델을 학습시키면서 도메인별 excess loss를 실시간으로 계산해 학습 데이터 도메인 가중치를 동적으로 최적화한다(Minimax DRO 프레임워크). Phase 0처럼 사전 분석 없이도 학습 중에 희귀 도메인 가중치를 자동으로 높인다.

**미반영 이유**:
Phase 0는 정적(static) 분석으로 D_train 구조를 이해하는 단계다. DoReMi는 proxy 모델 학습 비용이 필요하고, 학습 루프에 통합돼야 한다. 현재 파이프라인에서는 Phase B 파일��(스케일링 법칙 추정)이 유사한 역할을 수행한다.

**영향 및 한계**:
Phase 0의 `priority_i = a_i × (1 - density_i) × LID_i_normalized × collectability_i` 공식은 사전 분석에서 고정된 정적 우선순위다. 실제 학습 중 도메인 간 난이도 변화(특정 시나리오가 예상보다 빠르게 포화되거나 느리게 학습되는 경우)를 포착하지 못한다. Phase B 파일럿이 시나리오별 `a_i`(스케일링 이득)를 추정하지만, 희귀 도메인이 극소 표본이면 `a_i` 추정 자체가 불안정하다.

`collect_candidates`에서 `lid_context_caution=True` 케이스 — 즉 갭 클립이 소수 고LID 클립에 의존하는 시나리오 — 는 특히 DoReMi 방식의 동적 재가중치가 유효할 수 있는 케이스다. Phase B에서 이 시나리오의 `a_i` 신뢰 구간이 넓다면 DoReMi 보완을 검토할 것.

> **후속 작업**: Phase B 파일럿 결과에서 `a_i` 추정 분산이 큰 시나리오(`lid_context_caution=True` 또는 소규모 `healthy_scenarios` 미포함 시나리오)에 대해 DoReMi proxy 학습을 적용하는 하이브리드 전략. Phase 0 정적 분석이 거칠게 방향을 잡고, DoReMi가 해당 시나리오의 가중치를 동적으로 보정하는 2단계 구조.

---

## 5. DISC 통합 프레임워크

각 Phase가 어떤 연구를 이론적 근거로 삼는지 정리한다.

```
Phase 0: D_train 분포 프로파일링 (6+1개 서브 실험 — 기하학·의미 이중 트랙, 0-D-val 조건부 포함)
    0-A FAISS k-NN Foundation (k=50, 단일 앵커)
        ← knn_sim / knn_idx 1회 계산 → 모든 서브 실험 재사용
    0-B Effective N + Vendi Score + k-NN Density
        ← Yao et al. (ACL 2024, SoftDedup) — 연속 uniqueness_weight
        ← Friedman & Dieng (TMLR 2023, Vendi Score) — 고유값 스펙트럼 다양성
        ← uniqueness_weight → 0-D effective_n_contribution, 0-E-1 internal_redundancy로 연결
    0-C LID + 신뢰도 플래그 + k-민감도 (Ma et al. ICLR 2018 MLE) [v12 개정]
        ← Ma et al. (ICLR 2018) — k-NN 거리 MLE 추정 (k=20)
        ← Ruppik et al. (NeurIPS 2025) — LM 임베딩 LID → 일반화 예측
        ← lid_reliable: r_max_dist < 0.6 — 희소 영역 LID 불안정 케이스 명시 [v2 신규]
        ← k=15/20/25 병렬 계산 → k_sensitive_rate (경계 구역 k-민감성) [v12 신규]
        ← flipd_recommended=True if k_sensitive_rate > 0.05 → 0-D-val 트리거 신호 [v12 신규]
        ← 0-D GMM 확정 후 k_sensitive_rate GMM 기반 재계산 (k_sensitive_rate_approx 보존) [v12 신규]
    0-D 6-분류 Action Map (Density × LID × 신뢰도, BIC GMM brentq 임계값 + 경계 구역) [v12 개정]
        ← Sorscher et al. (NeurIPS 2022) — Q1(고밀도·저LID) prune 이론 근거
        ← Q0 KEEP / Q1 PRUNE / Q2 COLLECT / Q3 → 0-E-2 / Q4(저밀도 불신뢰) → 0-E-1 [v2 신규]
        ← Q5 PRUNE_UNCERTAIN (고밀도+저LID 판정이지만 LID 불신뢰) [v9 신규]
        ← BIC K=1~3 비교 + brentq 실제 교차점 (구 means_.mean() 부정확 수정) [v4: K=2고정→BIC선택]
        ← K=1 단봉 시 median 폴백 + lid_threshold_unimodal / density_threshold_unimodal 플래그 [v12 신규]
        ← lid_margin ±15% 경계 구역 → lid_boundary_zone.npy [v12 신규]
        ← thresholds.json: q3_boundary_rate 추가 저장 (> 0.3 → 0-D-val 트리거) [v12 신규]
    0-D-val Targeted FLIPD 검증 (조건부 서브 실험) [v12 신규]
        ← Cresswell et al. (NeurIPS 2024, FLIPD) — Poisson 과정 경계 보정 LID 재추정
        ← 트리거: k_sensitive_rate > 0.05 OR q3_boundary_rate > 0.3
        ← 대상: lid_boundary_zone=True 인 Q3 클립만 선택 (비용 최소화)
        ← 결과: flipd_per_clip으로 Q3→Q2 재분류; flipd_validation.json 항상 기록 (SKIP 포함)
    0-E-1 전체 시나리오 의미 지도 (83k 전체, TF-IDF 독립 공간) [v12 개정]
        ← Eyuboglu et al. (ICLR 2022, Domino) — 전체 데이터 의미 슬라이스 철학
        ← TF-IDF KMeans K=12 (임베딩과 독립 공간) → 시나리오 × 사분면 교차표 [v3: GMM→KMeans]
        ← per-scenario Vendi Score (Friedman & Dieng) — 앵커 200개 고정, 독립 측정 [v4: 500→200 표준화]
        ← Q1 × Vendi 피드백: prune_flag=CAUTION (Q1 우세+고Vendi 불일치 케이스) [v4 신규]
        ← "Q1에 있는 클립 = 어떤 시나리오인가" 처음으로 식별
        ← Effective N을 시나리오 단위 internal_redundancy로 분해
        ← NMI/ARI(NMI < 0.15, ARI < 0.1): two_space_independence_ok — TF-IDF·임베딩 공간 독립성 검증 [v12 신규]
        ← PRUNE_DOMINANT_THRESHOLD = max(40.0, 1.5 × global_prune_pct) — 글로벌 기준선 대비 상대 판정 [v12 신규]
    0-E-2 저밀도 갭 슬라이스 정밀 분석 [v12 개정]
        ← 0-E-1 scenario_labels 재사용 (재클러스터링 없음)
        ← mean_lid 직접 사용 → Q2 비율 순환성 제거
        ← thresholds.json에서 lid_threshold 로드 (0-D BIC GMM brentq 값) [v3 신규]
        ← COLLECT_HIGH_PRIORITY (GAP_RATIO_HIGH_PRIORITY=0.4, 캘리브레이션 파라미터) / COLLECT / SYNTHETIC_OR_ACCEPT / UNCERTAIN_CHECK_SEMANTIC 4분기 [v4: 0.4 상수화]
        ← MIN_GAP_SIZE = 50 (k=20 기반 stable mean_lid 보장; 구 30 → 50 상향) [v12 신규]
        ← lid_context_caution: 갭 mean_lid ≥ threshold + 시나리오 mean_lid < threshold → 소수 고LID 의존 경고 [v12 신규]
        ← collect_candidates.json에 lid_context_caution 전파 → Phase D 수집 전략 조정 신호 [v12 신규]
        ← 명시적 변수 로드 (독립 실행 지원) [v4 신규]

Phase A: TF-IDF 클러스터링
    ← MOSAIC (caption 기반 클러스터링)
    ← Coverage Coreset (커버리지 기반 클러스터 구조)

Phase B: 클러스터별 스케일링 파일럿
    ← MOSAIC (ΔU_i 스케일링 법칙, (a_i, τ_i) 피팅)
    ← LESS (대안: gradient influence 기반 선택)
    ← DoReMi (Xie et al. NeurIPS 2023) — 희귀 도메인 Minimax 가중치 대안

Phase C: 다중 메트릭 분리 평가
    ← Domino (성능 갭 슬라이스 발견)
    ← MOSAIC 공헌1 (다중 경쟁 지표 구조)

Phase D: 타겟 탐색 효율 측정
    ← MOSAIC Q7 스케일링 법칙 역산 (n_target = τ_i × ln(a_i/ε))
    ← Active data collection 연구 (TypiClust 계열)
```

### DISC 원칙 요약

EXP-003의 DISC 방향이 기존 접근과 다른 점을 한 표로 정리:

| 원칙 | 기존 | DISC |
|------|------|------|
| 시작점 | D_pool 선택 바로 시작 | D_train 분포 이해 먼저 |
| 프루닝 | 없음 | 중복·저가치 먼저 제거 |
| 갭 정의 | 단일 신호 (밀도 또는 성능) | 4차원 결합 신호 |
| 수집 종료 | 예산 소진 | 스케일링 법칙 역산 |
| 검증 | Aggregate 메트릭 | 도메인별 분리 메트릭 |

---

## 6. 변경 이력

| 날짜 | 변경 내용 |
|------|---------|
| 2026-07-02 | 신규 파일 생성 — design.md에서 이론 내용 분리 |
| 2026-07-02 | §2 MOSAIC 핵심 공헌 분석 이동 (기존 design.md §2.5) |
| 2026-07-02 | §3 E2E AD 학습 패러다임 이동 (기존 design.md §2.6) |
| 2026-07-02 | §1 패러다임 전환 분석 신규 작성 |
| 2026-07-02 | §4 관련 최신 연구 신규 작성 (Sorscher, Eyuboglu, Xia, Gadre, Swayamditta) |
| 2026-07-02 | §5 DISC 통합 프레임워크 신규 작성 |
| 2026-07-02 | §1.4 Phase 0 설계 철학 신규 추가 (카운트 vs 분포, KDE/NMF/Effective N/α/편향 진단 논증) |
| 2026-07-02 | §2.5 redundancy_i 참조 수정 — 0-C FAISS k-NN으로 명확화 |
| 2026-07-02 | §5 Phase 0 항목 — 5개 서브 실험별 이론 근거로 세분화 |
| 2026-07-02 | §1.4 전면 교체 — k-NN 앵커 체인 설계 철학으로 (KDE/NMF/α 구설 삭제) |
| 2026-07-02 | §2.5 우선순위 공식 v3 — coverage_gap/redundancy → LID_normalized/collectability |
| 2026-07-02 | §5 Phase 0 항목 — 신규 5개 서브 실험(0-A FAISS/0-B Vendi/0-C LID/0-D Quadrant/0-E Domino) 및 논문 참조 교체 |
| 2026-07-02 | 신규 참조 논문 등록: Ma et al. ICLR 2018, Friedman & Dieng TMLR 2023, Yao et al. ACL 2024, Ruppik et al. NeurIPS 2025, Eyuboglu et al. ICLR 2022 (Domino) |
| 2026-07-02 | 최종 검토 수정: §1.2 갭 정의 열 v3 공식 용어로 교체, §4.7 구 Phase 0 번호 → 신규 번호로 교체 |
| 2026-07-02 | §4.6 DoReMi (Xie et al. NeurIPS 2023) 신규 추가 — 헤더 등록 논문 본문 연결 |
| 2026-07-02 | §5 Phase B → DoReMi 참조 추가, §1.4 예시 숫자 31k → 38k로 design.md와 통일 |
| 2026-07-02 | Phase 0 v2 재설계 반영 — §1.4 전면 교체 (기하학·의미 이중 트랙, LID 신뢰도, 0-E 분리 근거) |
| 2026-07-02 | §5 Phase 0 항목 — 6개 서브 실험(0-E-1/0-E-2 분리, Q4 신규, mean_lid 직접 사용)으로 교체 |
| 2026-07-02 | Phase 0 v3 재설계 반영 — §1.4 v3 핵심 변경점 3가지 및 트랙 다이어그램 업데이트 |
| 2026-07-02 | §1.4 0-D: GMM K=2 자연 임계값 이유 및 thresholds.json 설명 추가 |
| 2026-07-02 | §1.4 0-E-1: TF-IDF KMeans 독립 공간 이유, per-scenario Vendi Score 설명 추가 |
| 2026-07-02 | §1.4 0-E-2: 4분기 판정 테이블 (COLLECT_HIGH_PRIORITY 신규, lid_threshold thresholds.json 로드) 추가 |
| 2026-07-02 | §5 Phase 0 0-D/0-E-1/0-E-2 항목 v3 반영 — GMM2/TF-IDF KMeans/4분기/per-scenario Vendi |
| 2026-07-02 | Phase 0 v4 시너지 보강 — §5 Phase 0 항목 v4 반영 |
| 2026-07-02 | §5 0-D: BIC K=1~3 + brentq 교차점 [v4: K=2고정→BIC선택], thresholds.json 검증 정보 확장 |
| 2026-07-02 | §5 0-E-1: Vendi 앵커 200개 표준화 + Q1×Vendi prune_flag 피드백 루프 [v4 신규] |
| 2026-07-02 | §5 0-E-2: GAP_RATIO_HIGH_PRIORITY 상수화 + 명시적 변수 로드 [v4 독립 실행 지원] |
| 2026-07-03 | §4.8 신규 추가 — Phase 0 미반영 SoTA 3개(VLM 임베딩, BERTopic, DoReMi) 분석 및 후속 작업 방향 |
| 2026-07-03 | §1.4 체인 다이어그램: 0-D `5분류/GMM2` → `6분류/GMM BIC K=1~3 brentq`, 0-D-val 조건부 분기 추가 |
| 2026-07-03 | §1.4 v3 핵심 변경점: "GMM K=2 자연 임계값" → "GMM BIC K=1~3 brentq 실제 교차점" 수정 |
| 2026-07-03 | §1.4 0-C: k-민감도 분석 설명 추가 (k=15/20/25, k_sensitive_rate, flipd_recommended, GMM 재계산) [v12] |
| 2026-07-03 | §1.4 0-D 섹션 제목: "5-분류" → "6-분류", Q5 PRUNE_UNCERTAIN 추가, brentq 교차점 설명 수정, K=1 unimodal 플래그, 경계 구역 정량화 추가 [v12] |
| 2026-07-03 | §1.4 0-D-val: Targeted FLIPD 검증 서브 실험 설명 신규 추가 (트리거 조건, 대상 클립, SKIP audit) [v12] |
| 2026-07-03 | §1.4 0-E-1: NMI/ARI 독립성 검증(two_space_independence_ok), PRUNE_DOMINANT_THRESHOLD 상대 기준선 추가 [v12] |
| 2026-07-03 | §1.4 0-E-2: lid_context_caution 플래그, MIN_GAP_SIZE=50 근거, collect_candidates 전파 설명 추가 [v12] |
| 2026-07-03 | §5 0-C: k-민감도 분석 항목 추가 [v12] |
| 2026-07-03 | §5 0-D: 6-분류로 수정, Q5 추가, K=1 unimodal 플래그, lid_margin/boundary_zone, q3_boundary_rate [v12] |
| 2026-07-03 | §5 0-D-val: 신규 항목 추가 (FLIPD 조건부 검증, flipd_validation.json 항상 기록) [v12] |
| 2026-07-03 | §5 0-E-1: NMI/ARI two_space_independence_ok, PRUNE_DOMINANT_THRESHOLD 상대 기준선 추가 [v12] |
| 2026-07-03 | §5 0-E-2: MIN_GAP_SIZE=50, lid_context_caution, collect_candidates 전파 추가 [v12] |
