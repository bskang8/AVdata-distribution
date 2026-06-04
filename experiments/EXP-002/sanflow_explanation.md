# SANFlow 학습 설명서

**작성일**: 2026-06-04  
**대상 파일**: `src/avdata/phase6/fit_sanflow.py`  
**실행 명령**: `uv run python -m avdata.phase6.fit_sanflow --epochs 100`

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
