# TrimFlow — NF 기반 AV 희귀 사건 중요도 샘플링

## 출처
- **저자**: (arXiv 2024)
- **연도**: 2024
- **학술대회/저널**: arXiv preprint
- **논문**: arXiv:2407.07320
- **파일**: `literature/papers/trimflow-2024-normalizing-flow-rare-event-av.pdf`

---

## 핵심 아이디어

Normalizing Flow + Temporal Importance Sampling을 결합하여 자율주행 검증에서 희귀 위험 사건(rare hazardous event)을 효율적으로 샘플링한다. 자연발생적 분포(naturalistic driving distribution)에서 샘플링하는 대신, NF로 학습한 위험 사건 분포에서 직접 샘플링하여 **86.1% 적은 테스트로 동일 검증 수준** 달성.

### 핵심 개념: Temporal Importance Sampling

배경 차량 행동을 naturalistic 분포 대신 위험 상태로 진화하는 분포에서 샘플링:

```
q*(a_t) ∝ p(a_t) × w(a_t)   # w: 위험 상태 도달 가중치
NF: p(a_t) → q*(a_t)          # NF가 목표 분포 학습
```

### 작동 방식

1. **Phase 1**: 자연발생적 주행 데이터에서 NF 사전 학습
2. **Phase 2**: 위험 상태(충돌 직전, TTC < 1s 등)를 보상으로 NF fine-tuning
3. **Phase 3**: fine-tuned NF에서 배경 차량 행동 샘플링 → 시뮬레이션 실행
4. **결과**: hazardous state 도달 확률 대폭 증가, 동일 테스트 예산으로 더 많은 엣지 케이스 커버

### 주요 결과

- naturalistic 분포 대비 86.1% 적은 시뮬레이션으로 동일한 검증 수준
- 희귀 충돌 사건 발견율: 기존 방법 대비 5.8× 향상

---

## 장단점

**장점**
- 테스트 예산 대비 희귀 사건 커버리지 극적 향상
- NF의 가역성으로 중요도 가중치 정확 계산
- 시뮬레이션 환경과 무관하게 적용 가능

**단점**
- 위험 상태 정의(reward function) 설계가 결과에 민감
- NF fine-tuning에 충분한 희귀 사건 데이터 필요
- 시뮬레이션 기반 접근 → 실제 데이터 분포와 gap 존재 가능

---

## 프로젝트 적용 포인트

### Gap-4 (분포 편향) 연결 → EXP-002 Axis C

gap_score 상위 구간 클립을 Importance Sampling으로 재샘플링하여 평가 쿼리 집중:

```python
# phase5/detect_gaps.py (설계안)
# 1. NF로 5D ODD 밀도 추정
log_prob = flow.log_prob(odd_vectors)

# 2. 희소 + 고위험 구간 가중치 계산
importance_weight = exp(-log_prob) * hazard_proximity

# 3. 가중 샘플링 → 취약 구간 클립 집중 선정
sampled_clips = weighted_sample(clips, weights=importance_weight, n=1000)

# 4. 이 클립들로 EXP-002 평가 쿼리 후보 생성
```

EXP-001 longtail(bottom 5% KDE density, 14,959개)과 달리, TrimFlow 방식은 **밀도 + 위험도** 두 축으로 우선순위화하여 실제 위험한 희귀 구간만 선별.

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-4 | 분포 편향 → 위험 희귀 시나리오 중심으로 데이터 재샘플링 |
| Gap-6 | 쿼리 다양성 → 취약 구간 클립 기반으로 평가 쿼리 자동 생성 |

## 관련 실험
- EXP-002: Axis C — 갭 탐지 후 Importance Sampling으로 쿼리 집중
