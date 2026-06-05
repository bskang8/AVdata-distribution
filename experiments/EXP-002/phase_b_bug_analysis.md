# Phase B 버그 분석: SANFlow `nearest_cluster` 라벨 오류

**작성일**: 2026-06-05  
**발견 계기**: 클립 `ef742bb7-c767-4848-a15b-7d39c565b45e` 캡션 ↔ `scenario_name` 불일치  
**영향 범위**: `sanflow_gaps.json` 내 noise 갭 162개 전수 + cluster-edge 갭 38개 전수

---

## 1. 발견 경위

클립 `ef742bb7`의 캡션:

> *"Early in the morning, the road is bustling with activity … a vehicle stalls on the left side … two pedestrians are crossing."*

하지만 `sanflow_gaps.json`에 기록된 `scenario_name`:

> `"Rural night driving with limited visibility conditions."`

**캡션(아침 도심 정체, 정차 차량, 보행자)과 라벨(야간 농촌 시야 제한)이 완전히 다름.**

---

## 2. 정량적 규모

### 2-1. UMAP 공간 vs SANFlow latent 공간 nearest cluster 비교

| 대상 | 수 | UMAP 공간 기준 일치 | latent 공간 편향 |
|------|---:|---:|---|
| noise 갭 (is_noise=True) | 162 | **0개 (0%)** | 158개(97.5%)가 cluster 2 단일 수렴 |
| cluster-edge 갭 (is_noise=False) | 38 | **0개 (0%)** | 분산되어 있으나 전량 불일치 |
| **전체 갭** | **200** | **0개 (0%)** | |

### 2-2. 불일치 거리 비율

noise 갭 162개 각각에 대해:  
- **UMAP 실제 최근접** 클러스터까지의 거리: 평균 0.28, 중앙값 0.27  
- **SANFlow가 선택한** 클러스터(cluster 2)까지의 UMAP 거리: 평균 ~11

```
불일치 거리 비율 (SANFlow 선택 / UMAP 최근접)
  중앙값:  31.6×
  평균:    38.7×
  최대:   118.2×
```

SANFlow가 선택한 클러스터는 UMAP 공간 기준으로 **실제 최근접 클러스터보다 평균 38배 멀리** 있음.

### 2-3. noise 갭의 실제 UMAP nearest cluster 분포 (상위)

| cluster | 개수 | 시나리오 |
|---------|-----:|---------|
| 63 | 31 | Rural driving on two-way road with stalled vehicle |
| 104 | 30 | Rural driving on a clear sunny day |
| 93 | 26 | rural morning drive with low traffic |
| 105 | 12 | Rural two-way road driving with merging traffic |
| 121 | 5 | morning urban traffic with unexpected stalled vehicles |
| … | … | 총 34개 클러스터에 분포 |

→ 실제로는 **34개 시나리오**에 걸쳐 다양하게 분포하지만,  
SANFlow는 **158개(97.5%)를 단일 cluster 2**("Rural night driving")로 잘못 라벨링.

---

## 3. 근본 원인 분석

### 3-1. 코드 흐름 재현

`fit_sanflow.py` `detect_gaps()`:

```python
# Step 1: 원본 UMAP 좌표 x → latent z (flow 변환)
z, ld = _eval_direction(flow_list, bx)

# Step 2: latent z 공간에서 nearest cluster μ_k 탐색
nk = base.nearest(z)           # argmin ||z - μ_k||  ← 이 공간이 문제

# Step 3: latent z 에서의 log_density 계산
lp = base.log_prob(z, nk)
log_dens = lp + ld             # 이 값은 올바름
```

```python
# base.nearest() 내부
dists = torch.cdist(z.cpu(), self.means.cpu())  # μ_k 도 latent 공간 값
return dists.argmin(dim=1)
```

**`nearest_cluster`는 원본 UMAP 공간이 아닌 flow 변환 후 latent z 공간에서 계산된다.**

### 3-2. 왜 latent 공간과 UMAP 공간이 다른가

SANFlow의 학습 구조:

```
cluster k 소속 클립  →  flow  →  z  ≈  N(μ_k, σ_k)   ← 명확한 학습 목표 존재
noise 포인트 (-1)    →  flow  →  z  ≈  N(μ_noise, σ_noise)  ← noise bucket(cluster 124)에 배정
```

**noise 포인트는 학습 시 전용 noise Gaussian에 매핑되도록 훈련됨.**  
이로 인해 flow는 noise 포인트를 UMAP 원본 이웃과 무관하게 latent 공간에서 noise bucket 근방으로 밀어내는 방향으로 학습됨.

역추적 단계에서:

```python
# noise bucket(k==124)이면 display_k를 -1로 처리하려 했으나
display_k = -1 if k == K_clusters else k
```

noise 포인트의 latent z가 noise bucket으로 매핑되지 않고 **cluster 2의 μ₂ 쪽으로 흘러들어가는 현상**이 전체의 97.5%에서 발생.  
→ cluster 2는 가장 큰 클러스터(11,459개)로, latent 공간에서 μ₂가 noise 포인트들이 흘러가는 "중력 중심" 역할을 하고 있음.

### 3-3. log_density는 올바른가

**예, log_density 자체는 올바릅니다.**

noise 포인트들은 latent 공간에서 어느 cluster Gaussian에도 잘 속하지 않으므로  
log p(z) 값이 매우 낮게 나오는 것이 SANFlow의 의도된 동작.  
즉, **갭 탐지(어떤 클립이 희귀한가) 결과는 유효하다.**  
잘못된 것은 **역추적(그 갭이 어떤 시나리오인가) 결과**다.

### 3-4. 오류 요약

| 항목 | 상태 | 설명 |
|------|------|------|
| 갭 후보 200개 선정 | ✅ 올바름 | log_density 하위 200개 → 진짜 희귀 클립 |
| log_density 수치 | ✅ 올바름 | latent 공간 밀도 추정 정확 |
| noise vs cluster-edge 분류 | ✅ 올바름 | HDBSCAN original_cluster 기반 |
| noise 갭의 scenario_name | ❌ **전량 오류** | latent 공간 artifact, 의미론적 불일치 |
| cluster-edge 갭의 scenario_name | ❌ **전량 오류** | 동일 원인 |

---

## 4. 해결 방향 후보

### 후보 A — UMAP 공간 기반 nearest cluster 역추적 (단순 교체)

**방법**: 역추적 단계에서 latent z 대신 **원본 UMAP 10D 좌표를 기준**으로 nearest cluster 탐색

```python
# 현재 (latent 공간)
nk = base.nearest(z)                             # argmin ||z - μ_k(latent)||

# 후보 A
nk = find_nearest_in_umap(x_original, cluster_centers_umap)  # argmin ||x - center_k(umap)||
```

- **장점**: 구현 단순, HDBSCAN이 구성한 원래 공간 그대로 사용, 결과 직관적
- **단점**: flow를 통한 의미론적 정렬을 완전히 무시 / cluster-edge 케이스에서도 UMAP center 기준이 최선인지 불확실
- **예상 효과**: noise 갭 162개의 scenario_name이 의미론적으로 정확해짐 (클립 ef742bb7 → cluster 121 "morning urban traffic with unexpected stalled vehicles")

### 후보 B — UMAP + latent 앙상블 (가중 평균 거리)

**방법**: 두 공간의 nearest 거리를 정규화 후 가중 합산

```python
# 각 공간 거리를 z-score 정규화 후 합산
score_k = α * dist_umap(x, center_k) + (1-α) * dist_latent(z, μ_k)
nearest_k = argmin(score_k)
```

- **장점**: 두 공간 정보를 모두 활용 / α 튜닝으로 균형 조정 가능
- **단점**: α 하이퍼파라미터 결정 근거 부족 / 복잡성 증가
- **예상 효과**: noise 포인트에서 A보다 약하지만 cluster-edge에서 더 안정적일 가능성

### 후보 C — 원본 HDBSCAN 클러스터 레이블을 직접 우선 활용

**방법**: `original_cluster != -1`인 클립은 해당 클러스터를 `nearest_cluster`로 사용,  
`original_cluster == -1`인 noise 포인트만 UMAP nearest로 보완

```python
if original_cluster != -1:
    display_k = original_cluster          # HDBSCAN 레이블 신뢰
else:
    display_k = find_nearest_in_umap(x)  # noise → UMAP nearest
```

- **장점**: cluster-edge 포인트의 정확도 확실 보장 / noise 포인트에 합리적 대안
- **단점**: SANFlow의 latent 공간 정보를 완전히 버림 / original_cluster가 border 클립에서 불안정할 수 있음
- **예상 효과**: cluster-edge 38개는 완벽히 수정, noise 162개는 후보 A와 동일 효과

### 후보 D — nearest cluster 재정의: UMAP + 클러스터 크기 보정

**방법**: 단순 거리가 아니라 클러스터 크기로 보정한 마할라노비스 거리 사용

```python
# 클러스터 내부 분산을 고려한 거리 (Mahalanobis)
dist_k = mahalanobis(x, center_k, cov_k)   # cov_k = 클러스터 k 내 UMAP 분산
nearest_k = argmin(dist_k)
```

- **장점**: 분산이 큰 클러스터(cluster 2: 11,459개)가 과도하게 선택되는 문제 구조적 해결
- **단점**: 클러스터별 공분산 행렬 계산 필요 (10×10, 124개) / 비용↑
- **예상 효과**: 크기 편향 제거 + 의미론적 정확도 향상

---

## 5. 후보 평가 기준

| 기준 | 가중치 | 설명 |
|------|--------|------|
| **의미론적 정확도** | ★★★ | 캡션 내용과 scenario_name 일치율 |
| **구현 단순성** | ★★☆ | 기존 파이프라인 변경 최소화 |
| **재학습 불필요** | ★★☆ | 저장된 sanflow_model.pkl 재사용 가능 여부 |
| **cluster-edge 커버** | ★★☆ | noise뿐 아니라 cluster-edge 38개도 개선 |
| **검증 용이성** | ★★☆ | 캡션 비교로 정량 검증 가능 여부 |

| 후보 | 의미론적 정확도 | 구현 단순성 | 재학습 | cluster-edge 커버 |
|------|:---------:|:---------:|:------:|:-------:|
| A (UMAP nearest) | ★★★ | ★★★ | 불필요 | ★★☆ |
| B (앙상블) | ★★☆ | ★★☆ | 불필요 | ★★★ |
| C (HDBSCAN 우선) | ★★★ | ★★★ | 불필요 | ★★★ |
| D (마할라노비스) | ★★★ | ★☆☆ | 불필요 | ★★★ |

---

## 6. 권고 방향

**1순위: 후보 C** (HDBSCAN 우선 + UMAP nearest 보완)

- `original_cluster != -1` → HDBSCAN 레이블이 곧 정답 (재학습 없이 즉시 수정 가능)
- `original_cluster == -1` → UMAP 공간 nearest cluster (후보 A 효과)
- 두 경우 모두 이미 계산된 데이터(`cluster_labels.npy`, `umap_10d.npy`)만 사용 → **`sanflow_gaps.json` 재생성만으로 완료**

**2순위: 후보 A** (구현이 더 단순하고 결과가 후보 C와 noise 포인트에서 동일)

**보류: 후보 D** — Phase C 이후 전체 파이프라인 재설계 시점에서 재검토

---

## 7. 다음 스텝 (수정 구현 전 확인 사항)

- [ ] 후보 C 방식으로 `sanflow_gaps.json` 재생성 스크립트 작성
- [ ] 재생성 전/후 캡션 매칭 정확도 정량 비교 (샘플 20개 수동 검증)
- [ ] `fit_sanflow.py`의 `detect_gaps()` 함수 수정 또는 별도 후처리 스크립트 결정
- [ ] `viz_sanflow_gaps.html` 및 Streamlit UI 재생성 결과로 업데이트
- [ ] 수정된 `scenario_name` 기준 갭 우선순위 재해석 문서 작성

---

*참조 파일*:  
- `src/avdata/phase6/fit_sanflow.py` — `detect_gaps()` L243–298, `ClusterGaussianBase.nearest()` L67–70  
- `experiments/EXP-002/results/sanflow_gaps.json` — 수정 대상  
- `experiments/EXP-002/results/umap_10d.npy` — UMAP 좌표 (후보 A/C에서 사용)  
- `experiments/EXP-002/results/cluster_labels.npy` — HDBSCAN 레이블 (후보 C에서 사용)
