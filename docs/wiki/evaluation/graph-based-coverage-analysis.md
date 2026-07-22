# Graph-based Coverage Analysis for Autonomous Driving (Mühlenstädt & Bause)

## 출처
- **저자**: Thomas Mühlenstädt, Marius Bause
- **연도**: 2026
- **논문**: arXiv:2602.00903, Jan 2026
- **파일**: `literature/papers/graph-based-coverage-2026.pdf`

---

## 핵심 아이디어

교통 씬을 계층적 그래프로 표현하고, 서브그래프 동형성 또는 GINE 임베딩으로 커버리지를 분석하는 프레임워크.

### 계층적 그래프 구조

| 레이어 | 표현 내용 | 노드 유형 |
|--------|-----------|-----------|
| 맵 레이어 | 차선·교차로 토폴로지 | 차선 노드, 연결 엣지 |
| 에이전트 레이어 | 차량·보행자·자전거 관계 | 에이전트 노드 |
| 상호작용 엣지 | 선행/후행/인접/대향 관계 | 방향성 엣지 |

### 2단계 그래프 구성 알고리즘

```
Step 1: 맵 그래프 구성
  - 차선 중심선을 노드로 변환
  - 연결 관계(merge, split, intersection) → 엣지

Step 2: 에이전트-맵 통합
  - 에이전트를 맵 위에 투영
  - 선행(leading) / 후행(following) / 인접(adjacent) / 대향(opposing) 관계 포착
  → 최종 씬 그래프 G = (V_map ∪ V_agent, E_map ∪ E_spatial)
```

### 두 가지 분석 방법

| 방법 | 동작 방식 | 적합한 경우 |
|------|-----------|-------------|
| 서브그래프 동형성 | 수동 정의 archetype 패턴과 씬 그래프 매칭 | 특정 시나리오 타입 검색 |
| GINE 임베딩 | 자기지도 대조 학습으로 씬 벡터화 | 유사도 기반 클러스터링, 새로운 패턴 발견 |

### 검증 데이터셋

| 데이터셋 | 용도 |
|---------|------|
| Argoverse 2.0 | 실제 자율주행 씬 그래프 검증 |
| CARLA | 생성된 시뮬레이션 씬 커버리지 검증 |

---

## 장단점

**장점**
- 맵 토폴로지 + 에이전트 관계를 단일 그래프에 통합 → 구조적 커버리지 측정 가능
- 서브그래프 동형성으로 특정 archetype(교차로 좌회전, 끼어들기 등) 직접 카운팅
- GINE 임베딩으로 미리 정의하지 않은 새로운 패턴도 발견 가능

**단점**
- 그래프 구성 비용: 씬당 O(V²) 엣지 계산 → 대규모 데이터셋에서 느림
- 서브그래프 동형성(NP-hard) → 대규모 적용 시 근사 알고리즘 필요
- GINE 임베딩 학습에 도메인 특화 대조 학습 데이터 필요

---

## 프로젝트 적용 포인트

### Gap-1: 구조적 커버리지 측정

현재 83k 클립의 캡션/태그 기반 분류 한계를 그래프 구조로 보완:

```python
# 현재: 캡션 키워드로 시나리오 분류 (교차로, 보행자 등)
# 그래프 방식: 씬 그래프 archetype 매칭으로 정확한 인터랙션 패턴 파악

# COLLECT_HIGH_PRIORITY 시나리오와 archetype 대응:
# S4(회전/교차로) → archetype: intersection + turning_agent
# S1(보행자)      → archetype: ped_crossing + vehicle_stopping
# S8(버스/트럭)   → archetype: large_vehicle + following_gap

# GINE 임베딩 활용:
# 기존 bge-m3 임베딩 + 씬 그래프 임베딩 결합
# → 커버리지 갭 탐지 정밀도 향상
```

### Gap-3: ODD 구조적 커버리지 갭 탐지

- effective_n이 낮은 속성(agent_type=1.16, scene_ambiguity=1.04)의 원인을 그래프 구조에서 진단
- "cars_only" 편향의 구조적 원인: 보행자/자전거 에이전트가 포함된 서브그래프 archetype 부재

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-1 | 씬 그래프 archetype으로 평가셋 구조적 커버리지 측정 |
| Gap-3 | GINE 임베딩으로 ODD 파라미터 조합 커버리지 시각화 |

## 관련 실험
- EXP-003 (Phase 0): 씬 그래프 기반 시나리오 분류 보완 — T2SG와 비교
- EXP-002 Phase B: ScenarioNet 26-카테고리 + 그래프 archetype 병행 분석
