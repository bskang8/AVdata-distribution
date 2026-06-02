# MOSAIC: 스케일링 인식 데이터 선택 (Data Mixture Optimization)

## 출처
- **저자**: Dimlioglu, Chang, Shen, Mahmood, Alvarez (NYU / NVIDIA)
- **연도**: 2026
- **학술대회**: arXiv:2604.08366
- **파일**: `literature/papers/dimlioglu-2026-scaling-aware-data-selection.pdf`

---

## 핵심 아이디어

대규모 자율주행 데이터 풀에서 **어떤 데이터를 얼마나** 학습에 추가할지를 결정하는 3단계 프레임워크.  
기존 방법들은 단일 메트릭 최적화에 집중했지만, MOSAIC은 **다중 경쟁 메트릭**을 동시 최적화한다.

### 3단계 파이프라인 (MOSAIC)

```
Pool Dataset
    ↓
① Cluster & Rank   : 도메인별 클러스터링 + 중요도 스코어로 랭킹
    ↓
② Estimate Scaling : 각 클러스터의 스케일링 법칙 추정 (pilot run)
    ↓
③ Iterative Mining : 한계 이득(marginal gain)이 최대인 클러스터에서 순차적으로 샘플 추가
```

### 스케일링 법칙 (Saturating Exponential)

```
ΔU_i(n) ≈ a_i(1 - e^(-n/τ_i))
```
- `a_i`: 클러스터 i의 점근적 최대 기여도
- `τ_i`: 포화 속도 (낮을수록 빠르게 포화)

### 실험 결과 (OpenScene / Navtrain)

| Method | EPDMS | BRMR (데이터 효율) |
|--------|-------|-------------------|
| Random | 72.84 | 1.00 (기준) |
| Chameleon | 72.97 | 0.86 |
| **MOSAIC** | **77.38** | **0.15** |

→ MOSAIC은 Random 대비 **80% 적은 데이터**로 동일 성능 달성

### 클러스터 예시 (Caption 기반, Navtrain)

| Cluster | 특성 |
|---------|------|
| 1 | calm day, street, trees, signs |
| 2 | signals, crossing, crosswalks, pedestrians |
| 3 | highway, vehicles, busy urban |
| 6 | precipitation, potential rain, overcast, cloudy |

---

## 장단점

**장점**
- 다중 메트릭(NC, DAC, TLC 등) 동시 최적화
- 클러스터링 방식에 robust (geolocation, caption 모두 유효)
- 80%+ 데이터 효율성 개선

**단점**
- Pilot run 비용 발생 (초기 스케일링 추정)
- 클러스터 간 독립성 가정 (cross-cluster 상호작용 미반영)
- 포화된 클러스터 이후 다른 클러스터로 전환하는 로직 필요

---

## 프로젝트 적용 포인트

### Gap-4 (분포 편향: 정상 과다, 희귀 과소) 핵심 해결책

현재 83k 캡션에서 야간/안개/교차로 등 희귀 클립이 극히 적음.  
MOSAIC 방식으로 **어떤 도메인(클러스터)에서 데이터를 더 수집해야 하는지** 정량화 가능.

**구현 아이디어:**
```python
# Step 1: 현재 캡션을 TF-IDF로 클러스터링
# Step 2: 각 클러스터의 검색 성능(Recall@5)을 메트릭으로
# Step 3: 클러스터별 스케일링 법칙 추정
# Step 4: 가장 한계 이득이 높은 클러스터 우선 수집
```

### Gap-4 보완: 데이터 수집 우선순위 가이드
현재 UMAP 분포(`data/index/distribution.html`) 결과를 MOSAIC 클러스터와 연계:
- density 하위 5% 클립 → 해당 도메인의 `a_i` 추정
- 수집 ROI가 높은 시나리오 유형 식별

### 아이디어: 미니 파일럿 실험
현재 83k 캡션을 6개 클러스터로 나누고, Recall@5를 유틸리티 함수로:
```
U = weighted_sum(Recall@5_cluster_1, ..., Recall@5_cluster_6)
```

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-4 | 핵심 해결책 — 클러스터별 데이터 수집 우선순위 정량화 |

## 관련 실험
- EXP-003 (분포 분석): MOSAIC 클러스터링 결과를 UMAP과 비교
- EXP-004 (Full Scale): 클러스터별 검색 성능 차이 측정 후 MOSAIC 적용 검토
