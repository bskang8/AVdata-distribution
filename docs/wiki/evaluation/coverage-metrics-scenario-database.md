# Coverage Metrics for Scenario Database (de Gelder et al., TNO)

## 출처
- **저자**: Erwin de Gelder, Maren Buermann, Olaf Op den Camp (TNO, Netherlands)
- **연도**: 2025
- **논문**: arXiv:2409.01139v2, Jul 2025
- **파일**: `literature/papers/coverage-metrics-scenario-database-2025.pdf`

---

## 핵심 아이디어

시나리오 기반 ADS 평가에서 "수집된 시나리오가 충분한가?"를 정량적으로 답하는 두 가지 커버리지 메트릭 제안.

### 두 가지 커버리지 질문

| 질문 | 메트릭 | 의미 |
|------|--------|------|
| Q1: ODD를 충분히 커버하는가? | ODD Coverage | 정의된 운영 설계 도메인 내 파라미터 공간에 대한 시나리오 집합의 분포적 커버 비율 |
| Q2: 중요 상황을 놓치지 않는가? | Criticality Coverage | 실제 주행 데이터에서 발생하는 고위험(critical) 상황이 시나리오 DB에 얼마나 표현되는가 |

### 검증 설정

| 항목 | 값 |
|------|-----|
| 데이터셋 | HighD (독일 고속도로 자연주행 데이터) |
| 시나리오 수 | 200,000개 |
| 목표 커버리지 | 100% 달성 가능 조건 식별 |
| 인증 연계 | Safety Assessment Framework (SAF) |

### 핵심 알고리즘 구조

```
실제 주행 로그
    ↓ 파라미터 추출 (속도, 가속도, 차간거리, 상대속도 등)
시나리오 파라미터 분포 D_log
    ↓ ODD 정의와 교차 비교
ODD Coverage = Vol(D_log ∩ ODD) / Vol(ODD)
    ↓ Criticality 가중 적용
Criticality Coverage = Σ w_i × coverage_i (위험도 가중 합산)
```

### SAF 인증 연계

- Safety Assessment Framework(SAF)는 ADS 인증에서 시나리오 충분성을 요건으로 포함
- 두 메트릭이 인증 프로세스에서 요구하는 정량적 근거 제공
- 100% 커버리지 달성 조건: 파라미터 해상도 vs 시나리오 수 트레이드오프 식별

---

## 장단점

**장점**
- 두 질문(ODD 커버리지 vs 임계 상황 커버리지)을 명확히 분리하여 정의
- HighD 200k 시나리오로 실증 검증
- SAF 인증 프로세스와 직접 연계 가능한 정량 근거

**단점**
- HighD는 독일 고속도로 데이터 — 도심·교차로·야간 등 다양한 시나리오 타입 커버 미흡
- ODD 파라미터 정의가 도메인 전문가 판단에 의존
- 복잡한 상호작용 시나리오(다중 에이전트)에서 커버리지 계산 비용 높음

---

## 프로젝트 적용 포인트

### Gap-1: 평가셋 커버리지 정량화

현재 EXP-003 phase0 결과 기반으로 두 질문을 직접 적용:

```python
# Q1: ODD Coverage — 83k 클립이 정의한 ODD를 얼마나 커버하는가?
# 현재 ODD 파라미터: agent_type, weather, scene_type, time_of_day
# effective_n: agent_type=1.16(cars_only), weather=1.33, scene_ambiguity=1.04
# → ODD 커버리지 = 관측된 조합 수 / 정의된 전체 ODD 조합 수

# Q2: Criticality Coverage — 위험 시나리오가 DB에 충분히 있는가?
# COLLECT_HIGH_PRIORITY: S4(교차로), S1(보행자), S11, S5(램프), S8(버스/트럭)
# → 이 시나리오들이 83k 중 몇 %인지 측정 → 목표 비율 대비 갭 계산
```

### Gap-3: 수집 우선순위 정당화

두 메트릭으로 COLLECT_HIGH_PRIORITY 시나리오 선정 근거를 SAF 수준에서 정당화:
- S4(회전/교차로): ODD 내 파라미터 공간에서 현재 커버 부족 → Criticality Coverage 낮음
- S1(보행자): agent_type effective_n=1.16은 사실상 cars_only → ODD 파라미터 커버리지 저조

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-1 | Q1/Q2 메트릭으로 평가셋 커버리지 불충분 여부 정량화 |
| Gap-3 | ODD 파라미터별 커버리지 측정으로 수집 갭 식별 |

## 관련 실험
- EXP-003 (Phase 0): ODD Coverage 계산 — 현재 effective_n 값과 연계
- EXP-004 (Full Scale): 전체 83k 대상 Q1/Q2 메트릭 계산
