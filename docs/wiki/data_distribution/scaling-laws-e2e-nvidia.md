# 데이터 스케일링 법칙 — End-to-End AV (NVIDIA)

## 출처
- **저자**: Naumann, Gu, Dimlioglu, Bojarski, Degirmenci, Popov, Bisla, Ivanovic, Müller, Pavone (NVIDIA / Toronto / NYU / Stanford)
- **연도**: 2025
- **학술대회**: CVPR Workshop
- **파일**: `literature/papers/naumann-2025-data-scaling-laws-end-to-end.pdf`

---

## 핵심 아이디어

E2E 자율주행 모델의 성능이 훈련 데이터 크기에 따라 **멱함수(power-law)** 로 향상됨을 체계적으로 분석.  
16h → 8192h 규모 내부 데이터셋으로 실험, open-loop와 closed-loop 성능 괴리를 최초로 정량 비교.

### 스케일링 법칙 모델 (M1~M4)

| 모델 | 수식 | 특징 |
|------|------|------|
| M1 | `y = βx^c` | 단순 멱함수 |
| M2 | `y - ε_∞ = βx^c` | 점근 최솟값 포함 |
| M3 | `y = β(x^{-1} + γ)^c` | 소/대규모 데이터 모두 적합 |
| M4 | `y - ε_∞ = (ε_0 - y)^α βx^c` | 복잡 적응형 |

→ **M2가 전체적으로 가장 우수한 적합**

### 주요 실험 결과

| 액션 유형 | 필요 추가 데이터 (FDE 1% 개선) |
|-----------|-------------------------------|
| 전체 | ~4,000h |
| Lane keeping | ~4,031h |
| Lane change | ~2,879h |
| Turning | ~1,961h |

- ResNet-50 사용 시 ResNet-18 대비 **63% 적은 데이터**로 동일 성능
- **Closed-loop 성능은 256h에서 포화** → open-loop 개선이 closed-loop로 이어지지 않음

### ODD 분포 (학습 데이터)

| 도로 유형 | 비율 |
|-----------|------|
| Motorway | 36% |
| Urban | 52% |
| Residential | 8% |
| Rural | 4% |

---

## 장단점

**장점**
- 데이터 수집 투자 대비 성능 향상을 사전 예측 가능
- 액션 유형별 스케일링 계수 차이 → 시나리오별 우선순위 결정
- 모델 크기(ResNet-18 vs 50)의 효과도 정량화

**단점**
- Open-loop → Closed-loop 전이가 불완전 (covariate shift)
- 내부 데이터셋 의존 (공개 재현 어려움)
- Highway 중심 실험 → 복잡한 도시 교차로 분석 미흡

---

## 프로젝트 적용 포인트

### Gap-4 (분포 편향) 직결

현재 83k 클립의 ODD 분포가 알려져 있지 않음.  
**동일한 스케일링 법칙 분석**으로 어떤 도로/시나리오 유형에서 데이터가 부족한지 판단 가능.

```python
# 시나리오 유형별 검색 성능 스케일링 측정
# x: 해당 유형 클립 수, y: Recall@5
# M2 피팅으로 포화점 추정
from scipy.optimize import curve_fit

def M2(x, beta, c, eps_inf):
    return eps_inf + beta * x**c

popt, _ = curve_fit(M2, x_data, y_data)
```

### 아이디어: 시나리오 유형별 스케일링 분석
- Lane keeping / Lane change / Turning 구분 → Recall@5 스케일링 비교
- Motorway vs Urban vs Rural 클립 수 vs 검색 성능 플롯

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-4 | 데이터 스케일링 법칙으로 부족한 시나리오 유형 정량화 |

## 관련 실험
- EXP-003 (분포 분석): ODD별 클립 수와 검색 성능 스케일링 관계 분석
