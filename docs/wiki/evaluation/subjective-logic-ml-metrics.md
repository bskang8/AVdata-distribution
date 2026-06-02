# Subjective Logic 기반 ML 메트릭 불확실성 정량화

## 출처
- **저자**: Benjamin Herd, Simon Burton (Fraunhofer IKS, Munich)
- **연도**: 2024
- **학술대회**: ACM SAC '24
- **파일**: `literature/papers/herd-2024-can-you-trust-your.pdf`

---

## 핵심 아이디어

**"98% Recall"은 실제로 얼마나 믿을 수 있는가?**

단일 포인트 추정(point estimate)인 ML 메트릭은 안전 주장(safety argument)으로 사용하기 부족.  
Subjective Logic(SL) 프레임워크로 메트릭을 **확률 분포**(Beta distribution)로 표현하고  
표본 크기·모델 캘리브레이션·데이터 커버리지 불확실성을 전파한다.

### Subjective Logic 핵심 개념

**Binomial Opinion** = (belief `b`, disbelief `d`, uncertainty `u`, base rate `a`)  
조건: `b + d + u = 1`

**Recall을 SL Opinion으로 변환:**
```
b_rec = TP / (TP + FN + W)
d_rec = FN / (TP + FN + W)
u_rec = W / (TP + FN + W)    # W=2: 비정보적 사전 가중치
```

**Trust Discounting:** 상위 계층 불확실성을 하위 추정에 전파
```
ω^{B:A} = ω^B ⊗ ω^A   # B의 신뢰도로 A의 추정값 할인
```

### 실험 예시 (교통 표지판 분류)

- 측정 Recall = 98%, 500 테스트 샘플
- Step 1 (recall 단독): CI [95.6%, 99.4%]
- Step 2 (+calibration): CI [94.0%, 99.4%]  
- Step 3 (+data coverage 99%): CI [94.0%, 99.1%] → 보수적 추정 **94%**

→ "98%가 아닌 실제 안전 추정치는 94%"

### 3단계 불확실성 계층

| 계층 | 불확실성 원천 |
|------|------------|
| Model layer | 캘리브레이션, 모델 복잡도 |
| Data layer | 표본 크기, 대표성 |
| Input space & Task | ODD 커버리지, 분포 가정 |

---

## 장단점

**장점**
- 단일 숫자 메트릭의 숨겨진 불확실성을 명시적으로 정량화
- Beta 분포로 자연스럽게 신뢰 구간(CI) 계산
- 계층 간 불확실성 전파 (trust chain)

**단점**
- 정성적 불확실성(explainability, fairness)은 별도 처리 필요
- W(사전 가중치) 선택이 결과에 민감
- 다중 메트릭 조합 시 복잡도 증가

---

## 프로젝트 적용 포인트

### Gap-1 (평가셋 편향 — 키워드 기반 레이블) 직결

현재 `keyword_relevance` 기반 평가는 단일 포인트 Recall@5.  
Herd의 방법으로 **Recall@5의 실제 불확실성 범위**를 계산 가능.

```python
import scipy.stats as stats

TP = relevant_retrieved
FN = relevant_not_retrieved
W = 2  # non-informative prior

b_rec = TP / (TP + FN + W)
u_rec = W / (TP + FN + W)

alpha = TP + W * 0.5
beta = FN + W * 0.5
ci_lower, ci_upper = stats.beta.interval(0.95, alpha, beta)
```

### Gap-1 보완: LLM relevance labeling의 신뢰도 검증
LLM 레이블이 human annotation과 다를 경우:
- `ω^{LLM} ⊗ ω^{recall}` 로 trust discounting 적용
- LLM 레이블 신뢰도 = Brier Score로 캘리브레이션 추정

### 아이디어: 평가셋 품질 CI 리포트
```
현재 Recall@5 = 0.72
95% CI (w/ calibration + coverage): [0.61, 0.82]
→ "실제 성능은 72%가 아닌 61~82% 범위"
```

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-1 | 평가 메트릭의 불확실성 정량화 → 더 신뢰 가능한 평가셋 구축 |

## 관련 실험
- EXP-002 (LLM-based relevance labeling): LLM 레이블의 trust discounting 적용 검토
