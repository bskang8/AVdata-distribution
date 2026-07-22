# ADV-0: Closed-Loop Min-Max 적대적 학습 (롱테일 강건성)

## 출처
- **저자**: Tong Nie, Yihong Tang, Junlin He, Yuewen Mei, Jie Sun, Lijun Sun, Wei Ma, Jian Sun
- **연도**: 2026
- **논문**: arXiv:2603.15221, Mar 2026
- **파일**: `literature/papers/adv0-adversarial-training-2026.pdf`

---

## 핵심 아이디어

주행 정책(defender)과 대적 에이전트(attacker)를 zero-sum Markov game으로 모델링하여 롱테일 시나리오에 강건한 E2E AV 정책을 학습.

### 게임 이론 프레임워크

| 플레이어 | 역할 | 목표 |
|---------|------|------|
| Defender (주행 정책) | 안전하게 주행 | 최소 비용으로 목표 도달 |
| Attacker (대적 에이전트) | 최악 상황 생성 | defender의 실패 유발 |

### 핵심 알고리즘 구조

```
Zero-sum Markov Game 정의:
  min_θ max_φ E[cost(defender_θ, attacker_φ)]

1단계: Attacker utility를 defender objective와 직접 정렬
   → attacker_φ* = argmax cost(defender_θ, φ)
   → 최적 대적 분포 도출 (롱테일 = 고비용 시나리오)

2단계: Iterative Preference Learning으로 대적 진화 근사
   → Nash Equilibrium 방향으로 수렴
   → dynamic attacker update를 tractable하게 유지

3단계: Nash Equilibrium 수렴 → 최악 케이스 성능 인증 하한 최대화
```

### 성능 특성

| 특성 | ADV-0 | 기존 방법 |
|------|-------|---------|
| 롱테일 강건성 | Nash Eq. 보장 | 경험적 보강 |
| 대적 진화 | 동적 (iterative preference) | 정적 규칙 기반 |
| 인증 가능성 | 실세계 성능 하한 제공 | 미보장 |
| closed-loop 학습 | 예 | 부분적 |

---

## 장단점

**장점**
- Zero-sum Markov game으로 이론적 Nash Equilibrium 수렴 보장
- Attacker를 defender objective와 정렬 → 가장 해로운 시나리오만 생성
- 실세계 성능 인증 하한(lower bound) 최대화 → 안전 인증에 활용 가능

**단점**
- Min-max 최적화는 학습 불안정성 내포 (attacker-defender 동시 학습)
- Iterative preference learning의 수렴 속도가 느릴 수 있음
- 시뮬레이션 환경에서 학습 → 실세계 도메인 갭 존재

---

## 프로젝트 적용 포인트

### Gap-4: 롱테일 강건성 달성 전략

현재 83k 클립의 분포 편향 문제를 ADV-0 관점에서 재해석:

```python
# ADV-0의 핵심 인사이트: 롱테일 = attacker가 선택하는 고비용 시나리오
# 현재 분포 편향 진단:
# - agent_type effective_n=1.16: attacker는 보행자/자전거 포함 시나리오 선택
# - weather effective_n=1.33: attacker는 야간/비/눈 조건 선택
# - scene_ambiguity effective_n=1.04: attacker는 복잡 씬 선택

# COLLECT_HIGH_PRIORITY 시나리오 = attacker가 생성하는 hard 케이스:
# S4(교차로), S1(보행자), S8(버스/트럭) → 수집 우선순위 정당화

# ADV-0 방식 적용:
# defender_θ: 현재 검색 모델 (EXP-003)
# attacker_φ: 검색이 실패하는 쿼리/시나리오 생성기
# → iterative mining으로 hard negative 시나리오 발굴
```

### Gap-4: 데이터 수집 전략에 min-max 관점 도입

- 현재 수집 데이터 = "쉬운" 시나리오 편향
- ADV-0의 attacker utility 정렬 개념: 수집 우선순위를 "모델이 가장 실패하는 시나리오"에 집중

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-4 | Min-max 프레임워크로 롱테일 = attacker 최적 전략임을 이론적 정당화 |

## 관련 실험
- EXP-003 (Phase 0): 분포 편향 시나리오 = hard case 식별 → ADV-0 attacker 역할
- EXP-004: 롱테일 시나리오 오버샘플링 전략의 이론적 근거
