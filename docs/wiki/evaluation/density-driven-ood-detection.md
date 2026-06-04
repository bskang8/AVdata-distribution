# Density-driven Regularization — OOD 탐지를 위한 밀도 기반 정규화

## 출처
- **저자**: W. Huang, H. Wang, J. Xia, C. Wang, J. Zhang
- **연도**: 2022
- **학술대회**: NeurIPS 2022
- **파일**: `literature/papers/R9_DensityDrivenReg_NeurIPS2022.pdf`

---

## 핵심 아이디어

In-distribution(ID) 데이터의 **밀도 구조를 정규화 신호로 활용**하여 OOD 탐지 성능을 향상시킨다. 기존 OOD 탐지가 모델 출력(softmax confidence)에만 의존하는 한계를 극복한다.

### 핵심 메커니즘

```
기존 OOD 탐지:
  입력 x → 모델 → softmax 신뢰도 → threshold → ID/OOD

Density-driven 방식:
  입력 x → 임베딩 → 밀도 추정 p(z) → 밀도 기반 정규화 → OOD 스코어
```

### 밀도 정규화 적용 방식

1. ID 데이터의 잠재 공간에서 Gaussian Mixture Model(GMM) 또는 KDE로 밀도 추정
2. 학습 중 저밀도 영역의 임베딩에 패널티 부여 (밀도 기반 정규화 항 추가)
3. 추론 시 임베딩의 밀도 스코어를 OOD 판정 기준으로 활용

### 기존 방법 대비 성능

| 방법 | AUROC (CIFAR-10 vs SVHN) |
|------|--------------------------|
| MSP (Hendrycks 2017) | 91.2% |
| Energy Score | 93.1% |
| Density-driven (본 논문) | **95.8%** |

---

## 장단점

**장점**
- 사전학습 모델 수정 없이 적용 가능 (post-hoc)
- 임베딩 공간의 밀도 구조를 활용하여 의미론적으로 일관된 OOD 탐지
- 기존 OOD 방법과 앙상블 가능

**단점**
- GMM 컴포넌트 수, KDE bandwidth 등 하이퍼파라미터 설정 필요
- 고차원 임베딩에서 밀도 추정 비용 증가
- 분류 모델(classification head) 필요 — 현재 프로젝트의 검색 모델과 구조가 다름

---

## 프로젝트 적용 포인트

### Gap-3 → EXP-002 Phase A (참고)

현재 bge-m3 임베딩에서 **저밀도 영역 = 희귀 시나리오 구간**으로 직접 해석 가능:

```python
from sklearn.mixture import GaussianMixture

# bge-m3 임베딩(PCA 50D 축소)에서 밀도 추정
gmm = GaussianMixture(n_components=50, covariance_type='full')
gmm.fit(embeddings_pca)

# 각 클립의 밀도 스코어
log_density = gmm.score_samples(embeddings_pca)
rare_mask = log_density < np.percentile(log_density, 10)  # 하위 10%
```

저밀도 클립 = 현재 데이터셋에서 희귀한 시나리오 → **수집 우선순위 후보**로 활용.

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-3 | 임베딩 밀도 기반 희귀 시나리오 탐지 → ODD 커버리지 갭 식별 |

## 관련 실험
- EXP-002: Phase A 참고 자료 — GMM 밀도 추정으로 희귀 씬 식별
