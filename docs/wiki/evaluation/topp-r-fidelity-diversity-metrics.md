# TopP&R — 임베딩 공간 위상 기반 Fidelity & Diversity 분리 측정

## 출처
- **저자**: P. J. Kim, Y. Jang, J. Kim, J. Yoo
- **연도**: 2023
- **학술대회**: NeurIPS 2023
- **파일**: `literature/papers/R4_TopPR_NeurIPS2023.pdf`

---

## 핵심 아이디어

임베딩 공간에서 **Kernel Density Estimation(KDE)으로 지지도(support)를 추정**하여 생성 모델(또는 데이터셋)의 두 가지 품질을 분리 측정한다.

- **Fidelity (TopP)**: 생성 샘플이 실제 분포를 얼마나 커버하는가 → "빠진 구간이 없는가"
- **Diversity (TopR)**: 실제 분포 내부의 다양성이 얼마나 유지되는가 → "내부가 균등하게 채워졌는가"

### 기존 PR (Precision-Recall) 대비 개선점

| 항목 | 기존 Precision-Recall | TopP&R |
|------|----------------------|--------|
| 지지도 추정 | k-NN 바운더리 (이산적) | KDE 기반 연속 밀도 |
| 위상 민감도 | 낮음 | 위상 구조 보존 |
| 고차원 안정성 | 불안정 | 안정적 |
| 해석 | Precision / Recall | Fidelity / Diversity |

### 수식 개요

```
TopP(데이터셋 A, 기준 B) = ∫ min(p_A(x), p_B(x)) dx  →  Fidelity
TopR(기준 B, 데이터셋 A) = ∫ min(p_B(x), p_A(x)) dx  →  Diversity
```

KDE로 `p(x)`를 추정하고, 두 분포 간 최소값 적분으로 커버리지를 정량화한다.

---

## 장단점

**장점**
- 데이터셋 간 커버리지(fidelity)와 다양성(diversity)을 **독립적**으로 측정
- KDE 기반이라 위상 구조(클러스터, 매니폴드)에 민감하게 반응
- 생성 모델 평가뿐 아니라 **실제 데이터셋 커버리지 분석**에도 직접 적용 가능

**단점**
- KDE bandwidth 설정에 따라 결과가 달라질 수 있음
- 고차원(>50D)에서 KDE 자체의 차원의 저주 문제 — PCA/UMAP 축소 선행 필요
- 두 분포의 임베딩 공간이 같아야 비교 가능

---

## 프로젝트 적용 포인트

### Gap-3 / Gap-4 → EXP-002 Phase A

bge-m3 임베딩(1024-dim)을 PCA(50D) → UMAP(10D) 축소 후 TopP&R 적용:

```python
# 데이터셋 전체(A)와 희귀 시나리오 기준(B)의 커버리지 측정
from sklearn.neighbors import KernelDensity

kde_A = KernelDensity(bandwidth=0.5).fit(embeddings_A)
kde_B = KernelDensity(bandwidth=0.5).fit(embeddings_B)

# Fidelity: B가 A를 얼마나 커버하는가
# Diversity: A 내부의 다양성이 B 기준 대비 어느 수준인가
```

HDBSCAN 클러스터별 Fidelity/Diversity를 계산하여 "포화 클러스터"와 "부족 클러스터"를 구분한다.

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-3 | 임베딩 클러스터별 Fidelity 측정 → 커버리지 부족 구간 식별 |
| Gap-4 | Diversity 점수로 클러스터 내부 균등성 평가 |

## 관련 실험
- EXP-002: Phase A — HDBSCAN 클러스터별 Fidelity/Diversity 계산
