# SANFlow — 의미론적 Normalizing Flow 기반 이상 탐지

## 출처
- **저자**: D. Kim, S. Baik, T. H. Kim
- **연도**: 2023
- **학술대회**: NeurIPS 2023
- **파일**: `literature/papers/R6_SANFlow_NeurIPS2023.pdf`

---

## 핵심 아이디어

표준 Normalizing Flow가 **모든 임베딩 위치에 동일한 단위 정규분포를 강제 적용**하여 의미론적 정보가 소실되는 문제를 해결한다. SANFlow는 위치(시나리오 속성)별로 **다른 base distribution을 부여**하여 semantic-aware 밀도 추정을 실현한다.

### 표준 NF vs SANFlow

```
표준 NF:
  모든 ODD 속성 → 단일 N(0, I)
  fog 클러스터와 rain 클러스터가 같은 기저 분포를 공유
  → 갭 위치가 어떤 속성과 연결되는지 추적 불가

SANFlow:
  fog 클러스터   → N(μ_fog, Σ_fog)
  rain 클러스터  → N(μ_rain, Σ_rain)
  night 클러스터 → N(μ_night, Σ_night)
  → 갭 위치 → 가장 가까운 속성 분포 → 시나리오 설명 역추적 가능
```

### 구조

1. 임베딩 공간을 의미론적 영역으로 분할 (클러스터 = 시나리오 레이블)
2. 각 영역에 별도의 Gaussian `N(μ_k, Σ_k)` 할당
3. NF 변환 시 영역별 base distribution 사용 → 역변환 시 시나리오 이름 복원 가능

---

## 장단점

**장점**
- 갭 탐지 결과를 **시나리오 이름**으로 역변환 가능 (현재 파이프라인의 가장 큰 한계 해결)
- 클러스터 기반 base distribution → HDBSCAN 결과를 직접 재활용
- 기존 NF 구조를 크게 바꾸지 않고 적용 가능

**단점**
- 클러스터링 품질에 의존 — HDBSCAN 결과가 나쁘면 base distribution도 부정확
- 클러스터 경계가 모호한 경우 어느 base distribution을 사용할지 불명확
- 원본 논문은 이미지 이상 탐지 대상 → 텍스트 임베딩에 직접 적용 시 조정 필요

---

## 프로젝트 적용 포인트

### Gap-3 / Gap-4 → EXP-002 Phase B (표준 NF 교체)

Phase A HDBSCAN 클러스터 결과를 base distribution 사전으로 활용:

```python
# 각 클러스터의 Gaussian 파라미터 추정
cluster_gaussians = {}
for cluster_id, embs in cluster_embeddings.items():
    mu = embs.mean(axis=0)
    sigma = np.cov(embs.T)
    cluster_gaussians[cluster_id] = (mu, sigma)

# SANFlow NF 학습 시 클러스터 할당에 따라 base distribution 선택
def get_base_dist(embedding, cluster_gaussians):
    # 가장 가까운 클러스터 찾기
    dists = {cid: mahalanobis(embedding, mu, sigma)
             for cid, (mu, sigma) in cluster_gaussians.items()}
    return min(dists, key=dists.get)

# 갭 탐지 후 역변환
gap_point = detect_gap(flow_model)     # 7D 좌표
nearest_cluster = get_base_dist(gap_point, cluster_gaussians)
scenario_name = cluster_labels[nearest_cluster]  # "안개 + 야간 + 고속도로"
print(f"갭 시나리오: {scenario_name} → 수집 필요")
```

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-3 | NF 갭 탐지 결과를 시나리오 이름으로 역변환 → 커버리지 처방 가능 |
| Gap-4 | 의미론적 영역별 밀도 측정 → 분포 편향 진단 정확도 향상 |

## 관련 실험
- EXP-002: Phase B — 표준 NF를 SANFlow 방식으로 교체 (역변환 가능성 확보)
