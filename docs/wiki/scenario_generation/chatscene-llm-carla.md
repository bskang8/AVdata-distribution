# ChatScene — LLM 기반 안전 위험 시나리오 자동 생성 (CARLA)

## 출처
- **저자**: J. Zhang, C. Xu, B. Li
- **연도**: 2024
- **학술대회**: CVPR 2024
- **파일**: `literature/papers/R14_ChatScene_CVPR2024.pdf`

---

## 핵심 아이디어

**자연어 시나리오 기술**을 LLM이 자동으로 **CARLA 시뮬레이션 코드**로 변환한다. 전문 엔지니어 없이도 임의의 희귀 시나리오를 시뮬레이션으로 구현할 수 있다.

### 파이프라인

```
자연어 시나리오 기술
"안개가 짙은 야간 고속도로에서 앞차가 급정거하고
 뒤차가 반응하지 못해 추돌 직전 상황"
    │
    ▼  LLM (GPT-4o)
시나리오 파싱:
  - 환경: fog, night, highway
  - 에이전트: ego_vehicle, leading_car
  - 이벤트: leading_car → emergency_brake at t=5s
  - 초기 조건: 거리 15m, 속도 90km/h
    │
    ▼  Knowledge Base (CARLA API 지식)
CARLA Python 코드 생성:
  carla.WeatherParameters(fog_density=80, sun_altitude=-30)
  leading_car.apply_control(brake=1.0) at t=5
    │
    ▼  CARLA 시뮬레이션 실행
리얼리스틱 센서 데이터 + 에이전트 궤적
```

### Knowledge-Enabled 이유

LLM에게 CARLA API 지식을 주입하여:
- CARLA 내장 날씨/조명 파라미터 정확히 매핑
- 에이전트 제어 API 정확히 호출
- 물리적으로 실행 가능한 시나리오만 생성

---

## 장단점

**장점**
- 자연어만으로 임의의 시나리오 생성 → 전문 엔지니어 불필요
- Phase A에서 식별된 갭 시나리오를 바로 입력으로 사용 가능
- CARLA 기반이라 리얼리스틱 센서 데이터 생성

**단점**
- CARLA 환경 구축 필요 (GPU 서버, CARLA 설치)
- LLM이 생성한 코드가 실행 오류를 일으킬 수 있음 (검증 루프 필요)
- 복잡한 다중 에이전트 상호작용은 코드 생성 품질이 저하됨

---

## 프로젝트 적용 포인트

### Gap-4 / Gap-6 → EXP-002 Phase D

Phase A/B 분석 결과에서 "수집 필요"로 분류된 시나리오를 자연어로 기술 → ChatScene 입력:

```python
# Phase A 결과 → ChatScene 입력 자동화
gap_scenarios = [
    "안개 + 야간 + 고속도로 후방 추돌 회피 시나리오 (fog_density=80, night, 3-lane highway)",
    "적설 노면 + 보행자 무단 횡단 + 교차로 (snow=True, pedestrian crossing at red light)",
    "교량 위 결빙 노면 + 다중 차량 연쇄 충돌 (bridge, ice=True, 3 vehicles chain collision)",
]

for scenario in gap_scenarios:
    carla_code = chatscene_llm(scenario)
    execute_in_carla(carla_code)
```

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-4 | 희귀 시나리오 합성 생성 → 분포 편향 보완 |
| Gap-6 | 자연어 갭 시나리오 기술 → 시뮬레이션 자동화 |

## 관련 실험
- EXP-002: Phase D [Month 1] — ChatScene으로 갭 시나리오 CARLA 시뮬레이션 자동화
