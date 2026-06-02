# Safety-aware Causal Transformer (CEWM) — 신뢰성 자율주행 인과 표현

## 출처
- **저자**: Lu et al.
- **연도**: 2024
- **학술대회/저널**: arXiv preprint (cs.LG / cs.AI)
- **논문**: arXiv:2311.10747
- **파일**: `literature/papers/lu-2024-safety-aware-causal-representation.pdf`

---

## 핵심 아이디어

Offline Reinforcement Learning 기반 자율주행에서 허위 상관(spurious correlation)을 제거하고 안전한 의사결정을 위해 **FUSION** 시스템을 제안한다. 핵심은 **CEWM(Causal Exploration with World Model)** — state ↔ reward ↔ cost 간 인과 관계를 Transformer로 모델링하는 Safety-aware Causal Transformer다.

### FUSION 시스템 구조

```
Observation → Causal Encoder → Causal State Representation
                                        ↓
                               CEWM (Causal Transformer)
                               ├── state → reward 인과 경로
                               └── state → cost 인과 경로
                                        ↓
                               Safe Policy (reward↑, cost↓)
```

### CEWM: Safety-aware Causal Transformer

다른 타임스텝의 state, reward, cost 간 인과 관계를 causal mask로 모델링:

```
Causal Mask:
  s_t → r_t  (현재 상태 → 현재 보상: O)
  s_t → c_t  (현재 상태 → 현재 비용: O)
  s_t → s_{t+1} (현재 상태 → 다음 상태: O)
  r_t → s_t  (보상 → 상태: X, 인과 방향 아님)
  c_t → s_t  (비용 → 상태: X, 인과 방향 아님)
```

Causal mask를 통해 attention이 시간적·인과적으로 타당한 관계만 학습.

### 핵심 기여

- **Causal Disentanglement**: 상태에서 보상 관련 피처와 비용 관련 피처를 분리
- **Safety Constraint**: cost 인과 경로를 별도로 모델링하여 안전 제약 위반 예측
- **Offline RL 안정성**: spurious correlation 제거로 분포 외(out-of-distribution) 행동 방지

---

## 장단점

**장점**
- 안전 제약(cost)과 성능 목표(reward) 인과 경로 명시적 분리
- Offline 데이터에서 spurious correlation 제거 → 더 안전한 정책
- Causal mask로 시간적 인과 구조 내장 → 해석 가능

**단점**
- Offline RL 프레임워크에 최적화 → 검색 시스템에 직접 적용 어려움
- State-reward-cost 삼중 구조가 필요 → 클립 캡션만 있는 경우 cost 정의 필요
- 학습에 reward/cost 레이블 필요

---

## 프로젝트 적용 포인트

### Gap-1 (평가셋 편향) + Gap-2 (Hybrid 필터) → EXP-002 Axis A / EXP-004

**인과 관련성 스코어 설계 참조 (EXP-002 Axis A)**

CEWM의 state→cost 인과 경로 개념을 LLM 레이블링 스코어에 적용:

```json
{
  "condition_score": 0~2,  // state 조건 일치 (환경/상황)
  "causal_score": 0~2,     // state→cost 인과 연결 (위험 결과까지 포착)
  "relevant": true/false
}
```

`causal_score`가 CEWM의 cost 인과 경로에 대응: 캡션이 단순히 조건을 언급하는 것을 넘어 인과적 결과(hazard)까지 묘사하는지 평가.

**Hazard 예측 필터 설계 참조 (EXP-004)**

ODD 소프트 필터 재설계 시 state→cost 경로를 클립 검색에 적용:
- state = ODD 조건 (날씨, 도로, 시간대)
- cost = hazard 수준
- 필터: 쿼리의 hazard 수준과 클립의 hazard 수준 간 인과 매칭

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-1 | 인과 관련성 스코어(causal_score) 설계 원칙 제공 |
| Gap-2 | Hybrid ODD 소프트 필터 재설계 시 state→cost 인과 구조 참조 |

## 관련 실험
- EXP-002: Axis A — LLM 인과 관련성 스코어 설계 참조
- EXP-004: Hybrid ODD 소프트 필터 재설계 (백로그)
