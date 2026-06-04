# Metric Space Magnitude — 잠재 표현 다양성의 위상수학적 측정

## 출처
- **저자**: K. Limbeck, R. Andreeva, R. Sarkar, B. Rieck
- **연도**: 2024
- **학술대회**: NeurIPS 2024
- **파일**: `literature/papers/R5_MetricSpaceMagnitude_NeurIPS2024.pdf`

---

## 핵심 아이디어

위상수학(topology)의 **Magnitude** 개념을 latent representation의 다양성 측정에 적용한다. Vendi Score 대비 **수학적으로 provably stable**하며, 단일 스칼라가 아닌 **multi-scale 다양성 프로파일**을 제공한다.

### Magnitude란

유한 metric space `(X, d)`의 Magnitude는 "공간이 효과적으로 몇 개의 독립적 포인트로 구성되는가"를 스케일 파라미터 `t`에 따라 연속적으로 측정한다.

```
Mag(X, t) = Σ_i w_i(t)
여기서 w_i(t)는 포인트 x_i의 t-스케일에서의 가중치
```

- `t → 0`: 모든 포인트가 독립 → Mag = |X|
- `t → ∞`: 전체 공간이 하나의 포인트 → Mag = 1
- **Magnitude function**: t에 따른 변화가 공간의 다양성 구조를 드러냄

### Vendi Score 대비 장점

| 항목 | Vendi Score | Metric Space Magnitude |
|------|-------------|------------------------|
| 이론적 보장 | 없음 | Provably stable (perturbation에 안정) |
| 스케일 | 단일 스칼라 | Multi-scale 프로파일 |
| 해석 | 엔트로피 기반 다양성 | 위상 기반 유효 독립 포인트 수 |
| 계산 복잡도 | O(n²) | O(n²) (동일) |

---

## 장단점

**장점**
- 수학적 안정성 보장 — 소규모 perturbation에 불변
- 클러스터 크기뿐 아니라 내부 구조(밀집/분산 여부)를 포착
- 기존 임베딩(numpy array)에 바로 적용 가능

**단점**
- n×n 유사도 행렬 계산 필요 → 대규모(>10k) 클러스터에서 메모리 제약
- 클러스터별 분할 후 적용 필요 (전체 299k에 직접 적용 불가)
- 구현 라이브러리가 성숙하지 않아 직접 구현 필요할 수 있음

---

## 프로젝트 적용 포인트

### Gap-3 / Gap-4 → EXP-002 Phase A

HDBSCAN 클러스터별 Magnitude를 계산하여 클러스터 내부 다양성 점수를 산출:

```python
import numpy as np
from scipy.spatial.distance import cdist

def magnitude(embeddings, t=1.0):
    """클러스터 임베딩의 Magnitude 계산"""
    D = cdist(embeddings, embeddings, metric='euclidean')
    Z = np.exp(-t * D)          # similarity matrix
    w = np.linalg.solve(Z, np.ones(len(embeddings)))
    return w.sum()

# 클러스터별 diversity 점수
for cluster_id, embs in cluster_embeddings.items():
    mag = magnitude(embs, t=1.0)
    print(f"클러스터 {cluster_id}: Magnitude={mag:.1f} (클립 수={len(embs)})")
```

**수집 우선순위 기준**:
- Magnitude / 클립수 비율이 낮은 클러스터 = 내부가 균일하게 포화 → 추가 수집 불필요
- Magnitude / 클립수 비율이 높은 클러스터 = 내부가 다양하지 않음 → 다양성 보완 필요

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-3 | 클러스터별 diversity 점수 → ODD 커버리지 품질 측정 |
| Gap-4 | 수집 우선순위 근거 수치 제공 (Magnitude 기반) |

## 관련 실험
- EXP-002: Phase A — HDBSCAN 클러스터별 Metric Space Magnitude 계산 (수집 우선순위 도출)
