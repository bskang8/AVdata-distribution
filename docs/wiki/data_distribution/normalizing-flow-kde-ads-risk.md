# Normalizing Flow vs KDE — ADS 리스크 정량화

## 출처
- **저자**: (SYNERGIES 프로젝트, Horizon Europe 101146542)
- **연도**: 2025
- **학술대회/저널**: IEEE International Automated Vehicle Validation Conference (IAVVC 2025)
- **논문**: arXiv:2507.22429
- **파일**: `literature/papers/comparing-2025-normalizing-flows-kde-ads-risk.pdf`

---

## 핵심 아이디어

고차원 파라미터 공간에서 자율주행 시스템(ADS)의 리스크 PDF를 추정할 때, Normalizing Flow(NF)가 Kernel Density Estimation(KDE)보다 정밀한 불확실성 추정을 제공한다. 특히 데이터가 희소한 고차원 영역에서 KDE는 차원의 저주로 인해 bandwidth 불안정 및 0 수렴 문제가 발생하지만, NF는 학습된 역변환으로 이를 극복한다.

### Normalizing Flow 작동 원리

단순한 기저 분포(보통 가우시안)를 일련의 가역적·미분 가능한 변환으로 복잡한 분포로 변환한다.

```
z ~ N(0, I)  →  x = f_θ(z)
log p(x) = log p(z) - log |det J_{f_θ}(z)|
```

대표 아키텍처:
- **MAF (Masked Autoregressive Flow)**: autoregressive 구조로 고차원 밀도 추정에 강건
- **RealNVP**: coupling layer 기반, 역변환이 병렬 계산 가능
- **Flow Matching**: simulation-free 학습, ICLR 2024에서 효율성 검증

### KDE와의 비교

| 항목 | KDE | MAF (NF) |
|------|-----|---------|
| 고차원 성능 | 차원의 저주, bandwidth 불안정 | 차원 증가에 강건 |
| 희소 구간 표현 | 0으로 수렴 | 확률 추정 가능 |
| 계산 비용 | 낮음 | 높음 (GPU 학습 필요) |
| 분포 가정 | 없음 (non-parametric) | 없음 (implicit) |
| ADS 리스크 추정 | 저차원(≤3D) 적합 | 고차원(5D+) 적합 |

### 주요 결과

NF가 고차원 ADS 리스크 공간에서 KDE보다 리스크 불확실성 추정 정밀도가 향상됨을 확인. 계산 비용이 더 높지만, 고차원에서의 신뢰도 차이로 NF 사용이 정당화됨.

---

## 장단점

**장점**
- 고차원(5D+) ODD 공간에서 안정적인 밀도 추정
- 조건부 밀도 `p(x | condition)` 직접 학습 가능
- 희소 구간(rare scenario)에서도 확률 값 반환

**단점**
- 학습 시간이 KDE 대비 수십 배 소요
- 하이퍼파라미터(레이어 수, 은닉 차원) 튜닝 필요
- 학습 데이터 부족 시 과적합 위험

---

## 프로젝트 적용 포인트

### Gap-3 / Gap-4 (ODD 커버리지 + 분포 편향) 연결 → EXP-002 Axis C

EXP-001의 UMAP + KDE(2D)를 5D 연속 ODD 공간 + MAF로 교체:

```python
# phase5/fit_normalizing_flow.py (설계안)
from nflows.flows import MaskedAutoregressiveFlow

# odd_vectors: (N, 5) — [visibility, precipitation, traffic, hazard, agent]
flow = MaskedAutoregressiveFlow(features=5, hidden_features=64, num_layers=8)
flow.fit(odd_vectors)

# 조건부 갭 탐지
log_prob = flow.log_prob(grid_points)  # 5D 그리드
gap_score = (1 / exp(log_prob)) * hazard_weight
```

갭 탐지 파이프라인:
1. 5D ODD 벡터 학습 → `p(ODD)` 추정
2. `hazard_proximity > 0.7` 조건부 밀도 계산
3. gap_score 상위 5% 구간 = "취약 시나리오 구간"

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-3 | ODD 커버리지 저조 → NF로 커버되지 않는 ODD 구간 탐지 |
| Gap-4 | 분포 편향 → NF로 희소 고위험 시나리오 정밀 탐지 |

## 관련 실험
- EXP-002: Axis C — 조건부 밀도 갭 탐지 (MAF 적용)
