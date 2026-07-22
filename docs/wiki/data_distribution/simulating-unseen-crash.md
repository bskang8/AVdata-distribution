# Simulating the Unseen: Counterfactual Safety Learning (Texas A&M 외)

## 출처
- **저자**: Zihao Li, Xinyuan Cao, Xiangbo Gao, Kexin Tian, Keshu Wu, Mohammad Anis, Hao Zhang, Keke Long, Jiwan Jiang, Xiaopeng Li, Yunlong Zhang, Tianbao Yang, Dominique Lord, Zhengzhong Tu, Yang Zhou (Texas A&M, Georgia Tech, UW-Madison)
- **연도**: 2025
- **논문**: arXiv:2505.21743, May 2025
- **파일**: `literature/papers/simulating-unseen-crash-2025.pdf`

---

## 핵심 아이디어

교통 안전의 근본 패러독스 해결: 방지하고 싶은 사고일수록 데이터가 희소하기 때문에, 발생하지 않은 위험 상황(near-miss)에서도 학습하는 counterfactual safety learning 프레임워크.

### 패러다임 전환

| 기존 방식 | 제안 방식 |
|-----------|-----------|
| Crash-only learning | Counterfactual safety learning |
| 발생한 사고에서만 학습 | near-miss + 합성 위험 상황에서도 학습 |
| 희소 라벨 문제 | 생성 모델로 라벨 부족 해소 |
| 상관관계 기반 예측 | 인과적 위험 요인 학습 |

### 프레임워크 구성 요소

| 컴포넌트 | 역할 |
|---------|------|
| Crash-rate prior | 사전 사고 확률 분포 (Poisson/Negative Binomial) |
| Generative scene engine | near-miss → 반사실적 위험 씬 합성 |
| Causal learning | 인과 구조를 활용한 위험 요인 디센탱글링 |
| Vision Zero 연계 | 교통 사망사고 제로 목표와 정책 정합 |

### 시스템 흐름

```
실제 near-miss 데이터 (발생했지만 사고로 이어지지 않은 상황)
    ↓ Crash-rate prior로 사고 전환 확률 추정
반사실적 질문: "이 상황이 사고였다면?"
    ↓ Generative scene engine으로 합성
    ↓ 인과 학습으로 spurious correlation 제거
위험 요인 모델: 사고 발생의 실제 인과 요인 식별
    ↓ Vision Zero 정책 연계
```

### 데이터 비대칭 문제 수치

| 데이터 유형 | 상대적 빈도 |
|------------|------------|
| 정상 주행 | 99.9%+ |
| Near-miss | ~0.1% |
| 실제 사고 | ~0.001% |

---

## 장단점

**장점**
- 교통 안전의 근본 패러독스(방지하려는 사고 = 데이터 희소)를 인과적으로 해결
- Near-miss 데이터 활용으로 사고 데이터 없이도 안전 학습 가능
- Vision Zero 등 정책 목표와 직접 연계 가능

**단점**
- Generative scene engine의 반사실적 합성 품질에 의존
- 인과 구조 가정이 도메인 전문 지식 필요
- Near-miss 레이블링 자체가 주관적이고 비용 높음

---

## 프로젝트 적용 포인트

### Gap-4: 희귀 사고 시나리오 학습 전략

현재 83k 클립의 사고/위험 시나리오 희소 문제에 직접 적용:

```python
# 현재 상황:
# - 83k 클립 중 사고/위험 상황 비율 극히 낮음
# - COLLECT_HIGH_PRIORITY 시나리오도 실제 사고는 아님 (near-miss 수준)

# Counterfactual safety learning 적용:
# 1. Near-miss 식별: S4(교차로 아찔한 상황), S1(보행자 급제동)
# 2. Crash-rate prior: 도심/교차로/야간별 사고율 통계 적용
# 3. 반사실적 생성: "이 교차로 씬이 사고였다면?" → 합성 시나리오 생성

# SYNTHETIC 후보 연결:
# S3(야간): crash-rate prior 높음 → 반사실적 생성 우선순위 높음
# S6(교차로): near-miss 많음 → counterfactual에 적합
```

### Gap-6: 희귀 시나리오 쿼리 보완

- Near-miss에서 생성된 반사실적 씬 = 검색 쿼리 다양성 확보 수단
- 사고 데이터 없이도 위험 시나리오 쿼리 앵커 생성 가능

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-4 | Near-miss 기반 counterfactual 학습으로 희귀 사고 시나리오 분포 편향 해소 |
| Gap-6 | 반사실적 씬 생성으로 희귀 ODD 쿼리 다양성 확보 |

## 관련 실험
- EXP-003 (Phase 0): 위험 시나리오 분류에 near-miss 개념 도입
- EXP-004: 합성 사고 시나리오를 학습 데이터에 포함 시 성능 변화 측정
