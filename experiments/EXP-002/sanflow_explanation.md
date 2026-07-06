# SANFlow 학습 설명서

**작성일**: 2026-06-04 (최종 업데이트: 2026-06-18)  
**대상 파일**: `src/avdata/phase6/fit_sanflow.py`  
**실행 명령**: `uv run python -m avdata.phase6.fit_sanflow --epochs 100`  
**버그 수정**: 2026-06-05 nearest_cluster 라벨 오류 수정 (UMAP 공간 기반 역추적)

---

## 1. 이 학습의 목적

한 문장으로 요약하면:

> **"자율주행 데이터셋에서 어떤 시나리오가 부족한지(갭)를 찾고, 그 갭이 구체적으로 어떤 운전 상황인지 이름을 붙이기 위해"**

### 왜 갭을 찾아야 하는가

자율주행 시스템은 다양한 상황을 경험한 데이터로 학습할수록 안전합니다.
문제는 데이터셋이 겉보기엔 29만 개로 방대해 보여도 실제로는 편향되어 있습니다.

```
현실 데이터 분포 (예상)          실제 데이터 분포 (측정)
─────────────────────────        ─────────────────────────
맑은 날 도심 주행     30%   →    맑은 날 도심 주행    71%  ← 과잉 수집
야간 고속도로         15%   →    야간 고속도로         8%
안개 + 교차로          5%   →    안개 + 교차로         0.3% ← 극히 희박
폭우 + 보행자 돌출     3%   →    폭우 + 보행자 돌출   없음  ← 갭
```

이런 갭 시나리오는 AI 모델이 실제 도로에서 마주칠 수 있는 **위험한 상황**임에도 불구하고 학습 데이터에 없어서 모델이 대응 방법을 모릅니다. SANFlow는 이 갭을 **자동으로, 구체적인 시나리오 이름과 함께** 찾아냅니다.

### 기존 방법의 한계

| 방법 | 문제 |
|------|------|
| ODD 태그 집계 (Phase A Coverage Matrix) | "fog + highway 조합이 0개"는 알지만, 실제로 fog가 어느 정도인지, highway 어떤 상황인지 디테일 없음 |
| 표준 Normalizing Flow (기존 phase5) | 밀도 낮은 구역은 찾지만 "그 구역이 어떤 시나리오인가?" 역추적 불가 |
| **SANFlow (현재)** | 밀도 낮은 구역 + "야간 고속도로 안개 상황" 이름까지 출력 ✓ |

---

## 2. 전체 파이프라인 한눈에 보기

```
[Phase A 결과물]                    [Phase B SANFlow]
─────────────────                   ──────────────────────────────────────────
umap_10d.npy                        Step 1: 데이터 로드 + 정규화
(299,180 × 10)    ──────────────→   Step 2: 클러스터별 Gaussian 초기화
                                    Step 3: MAF 학습 (100 epoch)
cluster_labels.npy                  Step 4: 전체 데이터 밀도 계산
(299,180,)        ──────────────→   Step 5: 최저 밀도 200개 = 갭 후보
                                    Step 6: 클러스터 역추적 → 시나리오 이름
cluster_analysis.json               Step 7: sanflow_gaps.json 저장
(LLM 레이블)      ──────────────→
```

---

## 3. 입력 데이터 이해

### 10D UMAP 좌표란?

각 클립(동영상 한 장면)은 1024차원의 임베딩 벡터로 표현됩니다. 이를 UMAP으로 10차원으로 압축한 것이 입력입니다.

```
클립 "3f8a2b" (안개 낀 고속도로 새벽)
  원본 임베딩: [0.023, -0.14, 0.87, ...] (1024차원)
      ↓ UMAP
  10D 좌표: [9.91, 0.47, 2.74, 3.45, 4.67, 3.89, 3.55, 5.48, 6.50, 3.77]
```

의미론적으로 비슷한 장면들은 이 10D 공간에서 가까이 위치합니다.

### 클러스터 레이블

Phase A에서 HDBSCAN 알고리즘이 10D UMAP 공간을 분석해 비슷한 클립들을 그룹화했습니다.

```
클러스터 91: "Morning traffic navigating around a stalled vehicle"
  → 클립 수: ~200개
  → 이 클립들의 10D UMAP 좌표가 서로 가까이 모여 있음

클러스터 19: "Highway merging in foggy conditions"
  → 클립 수: ~150개

노이즈(-1): 어느 클러스터에도 속하지 못한 클립들
  → 클립 수: 65,893개 (22%)
  → 이 클립들이 가장 희귀하고 다양한 시나리오일 가능성이 높음
```

---

## 4. 학습 방법 (SANFlow 원리)

### 4-1. 핵심 아이디어

일반적인 밀도 추정(Normalizing Flow)은 모든 데이터를 **하나의 표준 정규분포**로 매핑하려 합니다.

```
[표준 NF]
  클립 x  →  flow  →  z  ~  N(0, I)
  
  문제: 클러스터 A의 z 와 클러스터 B의 z 가 같은 분포에 섞임
        → 갭을 찾아도 "어떤 클러스터의 갭인지" 알 수 없음
```

SANFlow는 **클러스터마다 별도의 Gaussian**을 목표 분포로 사용합니다.

```
[SANFlow]
  클러스터 k 소속 클립 x  →  flow  →  z  ~  N(μ_k, Σ_k)

  클러스터 91의 클립 → flow → z → N(μ_91, σ_91) 근처에 위치
  클러스터 19의 클립 → flow → z → N(μ_19, σ_19) 근처에 위치
  
  갭 = z 가 어느 Gaussian 에서도 멀리 있는 점
    → 가장 가까운 클러스터 k 를 찾으면 시나리오 이름을 알 수 있음
```

### 4-2. ClusterGaussianBase (클러스터 Gaussian 사전)

```
K_total = 125개 Gaussian
  ├─ 클러스터  0 ~ 123 : HDBSCAN 클러스터 (124개)
  └─ 클러스터 124      : noise bucket (65,893개 noise 클립)

각 k에 대해:
  μ_k     = 클러스터 k 클립들의 10D UMAP 평균   (10차원 벡터)
  log σ_k = 클러스터 k 클립들의 10D UMAP 분산   (10차원 벡터)

초기화 예시 (클러스터 91, "stalled vehicle morning traffic"):
  μ_91    = [ 0.23, -0.81,  1.44,  0.07, -0.33,  1.12, -0.88,  0.45,  0.91, -0.20]
  log σ_91= [-2.12, -2.45, -2.08, -2.31, -2.19, -2.37, -2.03, -2.27, -2.44, -2.15]
  (σ = exp(log σ) ≈ 0.12 ~ 0.17 → 클러스터가 상당히 타이트하게 모여있음)

중요: μ_k 와 log σ_k 는 고정값이 아닌 학습 파라미터
→ NF 학습 중 flow 와 함께 jointly 업데이트됨
```

### 4-3. MAF (Masked Autoregressive Flow) 구조

Flow는 데이터 x를 latent z로 변환하는 함수입니다. 12개 레이어로 구성됩니다:

```
flow_list = [MAF₁, LU₁, MAF₂, LU₂, MAF₃, LU₃, MAF₄, LU₄, MAF₅, LU₅, MAF₆, LU₆]
             ──────────────────────────────────────────────────────────────────────
             총 6 블록 × 2 레이어 = 12개 레이어
```

**MAF 레이어 (핵심):**
```
입력: x = [x₁, x₂, ..., x₁₀]

각 차원 i에 대해:
  z_i = (x_i - μ̂_i) / σ̂_i

  여기서 μ̂_i, σ̂_i 는 앞 차원들 x₁,...,x_{i-1} 로부터 신경망이 예측
  (masked MLP, hidden=128)

x₁ → z₁ (앞 차원 없음, μ̂=0, σ̂=1)
x₂ → z₂ (x₁ 참조)
x₃ → z₃ (x₁, x₂ 참조)
...
x₁₀ → z₁₀ (x₁~x₉ 참조)

장점: 역변환(z→x)은 순차 계산 필요하지만, 순변환(x→z)은 병렬 계산 가능
→ 학습(evaluation 방향)이 빠름
```

**LULinearPermute 레이어:**
```
MAF 후에 차원 순서를 LU 분해 기반으로 섞음
→ MAF가 항상 같은 차원 순서에 의존하지 않도록 방지
→ 더 풍부한 표현력 확보
```

### 4-4. 학습 목표 (Loss 함수)

**변수 변환 공식 (Change of Variables):**

$$\log p(x) = \log p_z(f^{-1}(x)) + \log \left|\det \frac{\partial f^{-1}}{\partial x}\right|$$

```
log p(x) = [클러스터 k의 Gaussian에서 z의 확률] + [변환의 야코비안 행렬식]
         = log N(z; μ_k, σ_k)                    + log|det J⁻¹|
```

**학습 루프 (epoch당 batch_size=1024):**

```python
for (batch_x, batch_cids) in DataLoader:

    # Step 1: x → z  (평가 방향, flow.inverse() 역순 적용)
    z = batch_x
    log_det = 0
    for flow in [LU₆, MAF₆, LU₅, MAF₅, ..., LU₁, MAF₁]:
        z, ld = flow.inverse(z)   # x → z 방향
        log_det += ld

    # Step 2: 클러스터별 log p(z) 계산
    μ_k  = base.means[batch_cids]          # 각 클립의 소속 클러스터 평균
    σ_k  = base.log_stds[batch_cids].exp()
    log_p_z = N(μ_k, σ_k).log_prob(z).sum(-1)   # (batch_size,)

    # Step 3: SANFlow Loss = 음의 로그우도
    loss = -(log_p_z + log_det).mean()
    #          ↑           ↑
    #    클러스터 Gaussian  야코비안 (변환 왜곡 보정)

    # Step 4: 파라미터 업데이트
    # → flow 파라미터 (MAF masked MLP 가중치)
    # → base.means (μ_k, 클러스터 중심)
    # → base.log_stds (log σ_k, 클러스터 분산)
```

**학습이 수렴한다는 의미:**
- flow가 클러스터 k의 클립들을 N(μ_k, σ_k) 근처로 잘 매핑하도록 학습됨
- 동시에 μ_k, σ_k도 이 매핑에 맞게 조정됨
- loss 감소 = 각 클립이 자신의 클러스터 Gaussian에 더 잘 들어맞음

### 4-5. 학습 설정 (현재 실행 중)

| 항목 | 값 | 이유 |
|------|-----|------|
| 입력 차원 | 10 | UMAP 10D |
| 클러스터 수 | 125 | 124 + noise |
| MAF 블록 수 | 6 | 표현력 vs 학습 속도 균형 |
| Hidden units | 128 | 10D 공간에 충분한 용량 |
| Epochs | 100 | loss 수렴 확인 기준 |
| Batch size | 1024 | GPU 메모리 효율 |
| Optimizer | Adam (lr=1e-3) + CosineAnnealing | 안정적 수렴 |
| 훈련 데이터 | 284,221개 (전체 95%) | |
| 테스트 데이터 | 14,959개 (전체 5%) | 과적합 감지 |

---

## 5. 갭 탐지: 학습 완료 후

### 밀도 계산

```
모든 299,180개 클립에 대해:
  z_i    = flow.inverse(x_i)         학습된 flow로 latent 변환
  k_i    = argmin ||z_i - μ_k||      가장 가까운 클러스터 찾기
  log p(x_i) = log N(z_i; μ_{k_i}, σ_{k_i}) + log|det J⁻¹|

→ log p 가 낮다 = 이 클립은 어느 클러스터에도 잘 속하지 않는다
                = 데이터셋에서 희귀한 시나리오
```

### 역추적 (Backtracking)

```
갭 후보 클립 (log p 하위 200개)
  ↓
nearest cluster k_i 조회
  ↓
cluster_analysis.json에서 LLM 레이블 조회
  ↓
출력:
  rank 1 | log_density: -64614 | cluster: 91
          → "Morning traffic navigating around a stalled vehicle"

  rank 7 | log_density: -10735 | cluster: 19
          → "Highway merging in foggy conditions with low visibility"
```

**gap_type 해석:**
- `is_noise=True` (cluster=-1): 원래 어느 클러스터에도 속하지 않은 클립 → 완전히 새로운 시나리오 유형
- `is_noise=False`: 기존 클러스터 근방이지만 분포 가장자리 → 해당 시나리오의 극단적 케이스

---

## 6. 최종 출력물

```
experiments/EXP-002/results/
  sanflow_model.pkl     ← 학습된 모델 (flow 가중치 + μ_k + σ_k)
  sanflow_gaps.json     ← 갭 후보 200개 + 시나리오 이름
  sanflow_eval.json     ← SANFlow vs KDE 테스트 로그우도 비교
  sanflow_train.log     ← 학습 진행 로그
```

`sanflow_gaps.json` 구조:
```json
[
  {
    "rank": 1,
    "clip_id": "3f8a2b...",
    "log_density": -64614.047,
    "nearest_cluster": 91,
    "scenario_name": "Morning traffic navigating around a stalled vehicle",
    "original_cluster": -1,
    "is_noise": true
  },
  ...
]
```

**필드 의미:**
- `rank`: 희귀도 순위 (1=가장 희귀)
- `log_density`: 로그 확률 밀도 (낮을수록 희귀)
- `is_noise`: `true`=완전히 새로운 시나리오 유형, `false`=기존 클러스터의 극단적 케이스
- `nearest_cluster`: 가장 유사한 클러스터 번호 (UMAP 공간 기준)
- `original_cluster`: HDBSCAN 원본 레이블 (-1=noise)

**통계 (200개 갭):**
- noise 갭: 162개 (81%)
- cluster-edge 갭: 38개 (19%)
- SANFlow vs KDE: +1.42 nats 개선 (확률 스케일 4.2배)

---

## 7. 전체 실험 흐름에서의 위치

```
Phase A (완료)                          Phase B (현재)
──────────────────────────────          ──────────────────────────────
EXP-001: BM25 + 임베딩 검색             SANFlow 학습 (진행 중)
   ↓                                       ↓ 완료 후
Gap-2 버그 수정                         sanflow_gaps.json
   ↓                                       ↓
ODD Coverage Matrix                     Phase C (예정)
  - 560개 조합 중 222개 갭              T2SG 씬 그래프 기반 토폴로지 커버리지
   ↓
HDBSCAN 클러스터링 (124개)
  - 22% noise
  - Metric Space Magnitude
   ↓
임베딩 클러스터 → SANFlow 입력 ──────→
```

SANFlow는 Phase A의 **정성적 발견**(어떤 클러스터가 작다)을 **정량적 갭 점수**(log-density)로 바꾸고, **시나리오 이름**(LLM 레이블)까지 붙여주는 것이 핵심 기여입니다.

---

## 8. UMAP 공간 vs SANFlow latent 공간

**버그 이해의 핵심:** 두 공간은 서로 다른 목적과 특성을 가집니다.

### 8-1. UMAP 공간 (원본 입력 공간)

```
클립 영상
  ↓  BGE-M3 임베딩 모델
1024차원 벡터  (클립의 의미론적 내용 표현)
  ↓  UMAP 차원 축소
10차원 벡터  ← 이것이 "UMAP 공간"의 한 점
```

**UMAP 공간에서 두 점이 가깝다 = 두 클립의 시각적·의미론적 내용이 유사하다.**

- 축: 의미론적 유사성을 보존하도록 학습된 10개의 추상 차원
- 거리: 실제 시나리오 유사도를 반영
- HDBSCAN이 이 공간에서 클러스터를 만들었음

```
UMAP 공간 (10D) 개념도

  cluster 63 ●●●        cluster 2 ■■■■■■■■■
  (rural stalled)  ...  (rural night)    ← 공간적으로 구분된 클러스터들
       ●
      noise ×  ← noise 클립: cluster 63 근방 (거리 ~0.1)
                  cluster 2까지 거리 ~11
```

### 8-2. SANFlow latent 공간 (flow 변환 후 공간)

SANFlow는 UMAP 공간의 점 `x`를 **Normalizing Flow(MAF)**로 다른 공간의 점 `z`로 변환합니다.

```
x (UMAP 10D)  →  flow (MAF 6블록)  →  z (latent 10D)
```

**학습 목표**: cluster k 소속 클립은 flow 후 z가 N(μ_k, σ_k) 근방에 모이도록

```
UMAP 공간              SANFlow latent 공간

cluster 2 ■■■■   →   z ≈ N(μ₂, σ₂) ●●●   ← cluster 2 클립들이 μ₂ 근방으로 모임
cluster 63 ●●●  →   z ≈ N(μ₆₃, σ₆₃) ▲▲▲  ← cluster 63 클립들이 μ₆₃ 근방으로 모임
noise ×          →   z ≈ ?              ← 학습 신호 없어 예측 불가
```

**latent 공간에서 두 점이 가깝다 = flow가 같은 Gaussian 근방으로 매핑했다.**  
이는 원본 시나리오 유사도가 아니라 **flow가 학습한 변환 구조**에 의해 결정됩니다.

### 8-3. 왜 두 공간이 다른가 — noise 포인트의 경우

```
                      UMAP 공간               SANFlow latent 공간
                      ─────────────────────   ──────────────────────────
cluster 2 클립        μ₂_umap 근방            μ₂_latent 근방  (flow가 여기로 보냄)
cluster 63 클립       μ₆₃_umap 근방           μ₆₃_latent 근방 (flow가 여기로 보냄)
noise 클립            μ₆₃_umap 근방 (거리 0.1)  ??? (flow가 어디로 보낼지 예측 불가)
                                              ↑ 학습 신호가 없어서 임의의 위치로 이동
```

flow는 **cluster 소속 클립들만 제대로 훈련된 변환**입니다.  
noise 클립(-1)은 학습 시 noise bucket으로 배정되지만, 이 변환이 반드시 UMAP 공간의 이웃 구조를 보존하지 않습니다.

### 8-4. 역할 분담 (최종 설계)

```
                         log_density 계산    nearest_cluster 역추적
                         (갭 심각도)          (시나리오 이름)
─────────────────────────────────────────────────────────────────────
SANFlow latent 공간        ✅ 강점              ❌ noise 포인트에서 오류
UMAP 원본 공간             △ (KDE 필요)        ✅ 의미론적으로 정확
```

**최적 설계**: SANFlow latent 공간은 **밀도 계산**에 사용하고,  
역추적은 **UMAP 원본 공간**에서 수행하는 것이 정확합니다.

---

## 9. SANFlow latent 공간을 사용하는 이유

"UMAP 공간에서 바로 밀도를 계산하면 되는데 왜 굳이 flow로 변환하는가?"  
이 선택에는 명확한 이유가 있습니다.

### 9-1. 정확한 로그우도 계산

**UMAP 공간에서 KDE(Kernel Density Estimation)를 쓰면:**

```
p_KDE(x) = (1/N) Σᵢ K((x - xᵢ)/h)    ← 모든 N개 데이터 포인트 기준 근사값
                                          bandwidth h 선택에 민감
                                          10D에서 계산 비용 O(N)
```

**SANFlow를 쓰면:**

```
log p(x) = log p_z(f⁻¹(x)) + log|det J⁻¹|    ← 변수 변환 공식 (수학적으로 정확)
                ↑                   ↑
       클러스터 Gaussian에서     flow의 부피 왜곡
       z의 정확한 확률         보정항 (야코비안)
```

NF는 학습 후 한 번의 forward pass로 **정확한** log p(x)를 계산합니다.  
KDE는 본질적으로 근사이며 고차원에서 bandwidth 선택이 어렵습니다.

**실제 측정 (테스트 셋 로그우도):**

| 방법 | 테스트 셋 log-likelihood | 비고 |
|------|---------------------:|------|
| SANFlow | **-3.5848** | 정확한 변수 변환 |
| KDE (baseline) | -5.0082 | 10D Gaussian 커널 근사 |
| 차이 | **+1.42 nats** | 확률 스케일로 **4.2배** 더 정확 |

### 9-2. 클러스터 크기 불균형 문제 해결

이 데이터셋의 클러스터 크기 분포:

```
최대 cluster (cluster 7):   61,909개
최소 cluster (cluster 12):      146개
크기 비율:                  1,238×
noise 포인트:               65,893개 (22%)
```

**UMAP KDE의 문제:**

```
전역 KDE에서 밀도는 "얼마나 많은 데이터 포인트가 주변에 있는가"

  cluster 7 경계 근처 포인트  → 주변에 많은 점 → 밀도 높음  (갭이 아님으로 판정)
  cluster 12 내부 포인트      → 주변에 적은 점 → 밀도 낮음  (갭으로 판정) ← 오탐
  
  cluster 12가 소수인 것은 '희귀한 시나리오'이기 때문일 수도 있지만,
  단순히 '수집량이 적은 것'일 수도 있다.
  전역 KDE는 이 둘을 구분하지 못한다.
```

**SANFlow의 해결:**

```
클러스터 k마다 독립적인 Gaussian N(μ_k, σ_k)을 기준으로 밀도 계산

  "이 포인트는 cluster k의 분포에서 얼마나 전형적인가?"
  
  → cluster 7 (61,909개)의 이상한 포인트  → 해당 Gaussian에서 멀리 있으면 → 갭
  → cluster 12 (146개)의 전형적인 포인트 → 해당 Gaussian에서 가까우면  → 갭 아님
```

클러스터 크기에 관계없이 **클러스터 내에서의 이상도**를 측정하므로 크기 편향이 없습니다.

### 9-3. 비선형 밀도 구조 포착

UMAP 공간의 클러스터들은 구형(spherical)이 아닙니다:

```
클러스터별 내부 퍼짐(spread) 비교 — 형태가 제각각

  타이트한 클러스터 (spread ≈ 0.03):
    cluster 12: Parking lot navigation in heavy rain       → 매우 동질적
    cluster 10: Nighttime parking lot navigation in heavy rain

  넓고 복잡한 클러스터 (spread ≈ 1.0):
    cluster 3:  Nighttime driving in narrow urban streets  → 다양한 서브 시나리오 혼재
    cluster 7:  Lane merging near intersection with parked cars
```

KDE는 각 포인트 주변에 동일한 구형 커널을 씌우므로 비구형·비균질 분포에서 밀도를 과소/과대 추정합니다.

Flow의 비선형 변환은 이런 복잡한 형태의 클러스터도 latent 공간에서 단순한 Gaussian으로 "펼쳐" 더 정확한 밀도를 추정할 수 있습니다.

### 9-4. 시나리오 역추적 (가장 핵심적인 동기)

이것이 SANFlow를 **표준 Normalizing Flow**와 구분짓는 핵심입니다.

```
방법                    갭 탐지     "이 갭이 어떤 시나리오인가?" 역추적
──────────────────────  ──────────  ──────────────────────────────────────
UMAP KDE                ✅ 가능      ❌ 불가 (전역 밀도만 있고 클러스터 정보 없음)
표준 NF (phase5)        ✅ 가능      ❌ 불가 (단일 Gaussian 목표, 클러스터 구분 없음)
SANFlow                 ✅ 가능      ✅ 가능 (클러스터별 Gaussian → nearest 역추적)
```

---

## 10. 버그 수정 히스토리 (2026-06-05)

### 10-1. 발견 경위

클립 `ef742bb7-c767-4848-a15b-7d39c565b45e`의 캡션:

> *"Early in the morning, the road is bustling with activity … a vehicle stalls on the left side … two pedestrians are crossing."*

하지만 초기 `sanflow_gaps.json`에 기록된 `scenario_name`:

> `"Rural night driving with limited visibility conditions."` ❌

**캡션(아침 도심 정체, 정차 차량, 보행자)과 라벨(야간 농촌 시야 제한)이 완전히 다름.**

### 10-2. 버그 원인

**초기 구현**: SANFlow latent 공간에서 `base.nearest(z)`로 nearest cluster 계산

```python
# 초기 구현 (버그 있음)
z, ld = _eval_direction(flow_list, X_sc)
nearest_k = base.nearest(z)  # latent 공간에서 계산 ← 문제
```

**문제점**:
- 162개 noise 갭 중 **158개가 cluster 2로 편향** (97.5%)
- UMAP 공간에서는 cluster 63 근방(거리 0.1)이지만, latent에서는 cluster 2로 밀려남(거리 ~11)
- **영향 범위**: 200개 갭 중 200개 전수 (100%) 불일치

### 10-3. 수정 방법 (후보 C 채택)

**`detect_gaps()` 함수 수정** (src/avdata/phase6/fit_sanflow.py, line 258):

```python
# 역추적 전략 (후보 C — HDBSCAN 우선 + UMAP nearest 보완):
#   - original_cluster != -1 → HDBSCAN 레이블 직접 사용 (재학습 불필요)
#   - original_cluster == -1 → UMAP(X_sc) 공간 nearest cluster 탐색
# log_density 계산은 latent z 공간 (SANFlow 본래 목적) 그대로 유지.

# UMAP 공간 클러스터 중심 계산
cluster_means_umap = np.stack([
    X_sc[labels_mapped == k].mean(axis=0)
    for k in range(K_clusters)
])

# noise 갭 포인트에 대해 UMAP-space nearest cluster 계산
noise_positions = X_sc[gap_idx[noise_mask]]
dists = np.linalg.norm(
    noise_positions[:, None, :] - cluster_means_umap[None, :, :],
    axis=-1,
)
umap_nearest = dists.argmin(axis=1)
```

**핵심:**
- **밀도 계산**: SANFlow latent 공간 (정확한 log-likelihood) ✅
- **시나리오 역추적**: UMAP 원본 공간 (의미론적 유사도) ✅

---

## 11. 최종 결과 및 통계

### 11-1. sanflow_gaps.json 필드 의미

```json
[
  {
    "rank": 1,                          // 희귀도 순위 (1=가장 희귀)
    "clip_id": "e73225e5-9341-...",     // 클립 고유 ID
    "log_density": -100551.1484,        // 로그 밀도 (낮을수록 희귀)
    "nearest_cluster": 16,              // 할당된 클러스터 번호
    "scenario_name": "Narrow winding road with railway crossing warning",
    "original_cluster": -1,             // HDBSCAN 원본 레이블 (-1=noise)
    "is_noise": true                    // noise 포인트 여부
  }
]
```

| 필드 | 의미 | 해석 |
|------|------|------|
| `rank` | 희귀도 순위 | 1~200, 낮을수록 더 희귀한 시나리오 |
| `log_density` | 로그 확률 밀도 | -100551 = 극도로 희귀 vs -40000 = 상대적으로 덜 희귀 |
| `is_noise` | noise 포인트 여부 | `true`: 완전히 새로운 시나리오 유형<br>`false`: 기존 클러스터의 극단적 케이스 |
| `nearest_cluster` | 가장 유사한 클러스터 | 시나리오 이름 결정에 사용 (UMAP 공간 기준) |
| `original_cluster` | HDBSCAN 원본 레이블 | `-1`: 어느 클러스터에도 속하지 않음<br>`0~123`: 해당 클러스터 소속이지만 가장자리 |

### 11-2. 갭 분포 통계 (200개)

| 항목 | 수량 | 비율 | 의미 |
|------|-----:|-----:|------|
| **noise 갭** (`is_noise=true`) | 162 | 81% | 완전히 새로운 시나리오 유형 |
| **cluster-edge 갭** (`is_noise=false`) | 38 | 19% | 기존 클러스터의 극단적 케이스 |
| **log_density 범위** | -100551 ~ -40783 | - | 약 2.5배 차이 |
| **커버 클러스터** | 다양 (16, 70, 110, 119, 120, 121 등) | - | 여러 시나리오 타입에 걸쳐 분산 |

### 11-3. 모델 성능 (test set, 14,959개)

| 지표 | 값 | 의미 |
|------|-----|------|
| SANFlow log-likelihood | **-3.5848** | 정확한 변수 변환 기반 |
| KDE baseline log-likelihood | -5.0082 | 10D Gaussian 커널 근사 |
| **개선 폭** | **+1.42 nats** | 확률 스케일로 **4.2배** 더 정확 |
| 학습 데이터 | 284,221개 (95%) | 전체 데이터의 95% |
| 테스트 데이터 | 14,959개 (5%) | 과적합 감지용 |

---

## 12. 파일 활용처

### 12-1. 시각화

**파일**: `scripts/visualize_phase_a.py` (line 483)

```python
SANFLOW_GAPS_PATH = RESULTS_DIR / "sanflow_gaps.json"
gaps = json.loads(SANFLOW_GAPS_PATH.read_text())

# viz_sanflow_gaps.html 생성
# - 갭 분포 차트
# - 클러스터별 갭 통계
# - log_density 히스토그램
```

### 12-2. 캡션 정제

**파일**: `src/caption_refine/batch_runner.py` (line 64)

```python
from caption_refine.config import SANFLOW_GAP_PATH

gaps = json.loads(SANFLOW_GAP_PATH.read_text())

# 200개 갭 클립에 대해 LLM으로 상세 캡션 재생성
# - 희귀 시나리오의 디테일 보강
# - 평가셋 구성 시 검색 쿼리 생성에 활용
```

### 12-3. 평가셋 구성

- 희귀 시나리오 위주 테스트 케이스 선정
- Embedding vs BM25 검색 성능 비교
- 특히 L2 인과 체인 쿼리에서 격차 측정

### 12-4. 데이터 수집 우선순위

```
sanflow_gaps.json (rank 1~50)
  → 가장 희귀한 50개 시나리오
  → 추가 데이터 수집 시 우선 대상
  → "이런 상황의 클립을 더 수집해야 함"
```

---

## 13. 정리: SANFlow가 해결한 문제들

| 문제 | 기존 방법의 한계 | SANFlow 해결 |
|------|------------------|--------------|
| **갭 탐지 정확도** | KDE는 근사치, bandwidth 민감 | 정확한 log-likelihood (4.2배 개선) |
| **클러스터 불균형** | 전역 밀도는 크기 편향 | 클러스터별 Gaussian으로 공정 평가 |
| **시나리오 역추적** | 표준 NF는 역추적 불가 | UMAP 공간 nearest로 정확한 레이블 |
| **비선형 분포** | 구형 커널로 과소/과대 추정 | Flow가 복잡한 형태를 Gaussian으로 펼침 |
| **자동화** | 수동 분석 필요 | 200개 갭 + 시나리오 이름 자동 생성 |

**핵심 인사이트**: 
- SANFlow latent 공간 = **밀도 계산**의 정확성
- UMAP 원본 공간 = **시나리오 역추적**의 정확성
- 두 공간을 적절히 분담하여 사용하는 것이 최적 설계
