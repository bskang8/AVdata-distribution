# Scenario Dreamer — 벡터화 잠재 확산 모델 기반 주행 시나리오 생성

## 출처
- **저자**: L. Rowe, R. Girgis, A. Gosselin, L. Paull, C. Pal, F. Heide
- **연도**: 2025
- **학술대회**: CVPR 2025
- **파일**: `literature/papers/R15_ScenarioDreamer_CVPR2025.pdf`

---

## 핵심 아이디어

**벡터화된 씬 요소**(차선 그래프 + 에이전트 바운딩 박스)를 잠재 확산 모델(Latent Diffusion Model)로 생성한다. 잠재 공간의 각 차원이 씬 구성 요소에 **직접 대응**하므로 역변환이 가능하고, 원하는 시나리오 특성을 잠재 공간에서 직접 조작할 수 있다.

### 기존 방법 대비 차별점

| 항목 | 기존 NF 방식 | Scenario Dreamer |
|------|------------|-----------------|
| 표현 | 연속 스칼라 ODD 벡터 | 벡터화 씬 그래프 |
| 역변환 | 불가 (좌표 → 시나리오 불명) | 가능 (잠재 차원 → 씬 요소) |
| 다양성 | 제한적 | 확산 모델 샘플링으로 무한 다양 |
| 물리 일관성 | 낮음 | 벡터 표현으로 구조적 일관성 유지 |

### 잠재 공간 구조

```
잠재 벡터 z = [z_road | z_agents | z_conditions]
  z_road:       차선 그래프 구조 (교차로, 직선, 곡선)
  z_agents:     에이전트 위치/속도/유형 배열
  z_conditions: 날씨, 시간대, 도로 조건

갭 탐지:
  NF 또는 클러스터링으로 z 공간의 저밀도 영역 탐지
  → z_conditions 조작으로 "안개 + 야간 + 역주행" 시나리오 생성
  → 확산 모델 샘플링으로 현실적인 씬 생성
```

### 생성 프로세스

1. 목표 시나리오 특성을 잠재 공간에서 지정
2. Latent Diffusion으로 벡터 씬 샘플링
3. 벡터 씬 → 시뮬레이터 입력 변환

---

## 장단점

**장점**
- 잠재 공간 조작으로 **원하는 특성의 시나리오를 정밀 생성**
- 역변환 가능 — 생성된 씬이 어떤 조건인지 명확
- 벡터 표현으로 물리 일관성 유지
- 확산 모델 다양성 → 동일 조건에서 다양한 변형 생성

**단점**
- 벡터화된 맵 데이터 필요 (HD Map)
- 학습 비용이 높음 (대규모 확산 모델)
- 현재는 씬 레벨 생성 — 센서 데이터(이미지/LiDAR)는 별도 렌더러 필요

---

## 프로젝트 적용 포인트

### Gap-4 / Gap-6 → EXP-002 Phase D

Phase A에서 식별된 갭의 잠재 공간 좌표를 지정하여 시나리오 생성:

```python
# SANFlow Phase B 결과 → Scenario Dreamer 입력
gap_latent = {
    "z_conditions": {
        "weather": "fog",       # 안개
        "time": "night",        # 야간
        "road": "highway",      # 고속도로
    },
    "z_agents": {
        "count": 3,
        "behaviors": ["following", "emergency_brake", "overtaking"],
    }
}

# Scenario Dreamer로 시나리오 생성
generated_scene = scenario_dreamer.sample(gap_latent, n_samples=50)
```

UniSim, ChatScene과 함께 Phase D 합성 파이프라인의 핵심 구성 요소.

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-4 | 잠재 공간 제어로 정확한 희귀 시나리오 생성 |
| Gap-6 | 다양한 시나리오 변형으로 쿼리 다양성 확보 |

## 관련 실험
- EXP-002: Phase D [Month 2-3] — Scenario Dreamer로 벡터 잠재 확산 시나리오 생성
