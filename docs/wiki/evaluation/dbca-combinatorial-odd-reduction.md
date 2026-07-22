# DBCA — 의존성 기반 조합 접근으로 ODD 시나리오 분석 부담 축소

## 출처
- **저자**: Kaushik Madala, Hyunsook Do (Univ. of North Texas), Carlos Avalos-Gonzalez (kVA by UL)
- **연도**: 2021
- **학술대회**: VEHITS 2021 (7th Int. Conf. on Vehicle Technology and Intelligent Transport Systems), pp. 235–246
- **논문**: DOI 10.5220/0010495022350246 — *A Dependency-based Combinatorial Approach for Reducing Effort for Scenario-based Safety Analysis of Autonomous Vehicles*
- **파일**: `literature/papers/Combinatorial Approach for Reducing.pdf`

---

## 핵심 아이디어

ISO 21448(SOTIF) Table B.3의 12개 ODD 요소를 완전 열거하면 **169,554,739,200 조합**(운행환경 OE). DBCA는 요소 간 **의존성(dependency)** 을 사람이 명시한 뒤, 의존 차수만큼만 t-way 조합을 생성해(IPOG/ACTS) 폭발을 붕괴시킨다 — 의존성을 빠뜨리지 않으면서.

### 2단계 조합 구조 (핵심)

DBCA는 조합을 **두 층위**로 나눈다:

| 층위 | 대상 | 조합 방식 | 예 |
|---|---|---|---|
| **운행환경 (OE)** | ODD **요소**(weather, road condition, time…) | **t-way** (요소 간 의존성 = t) | 169B → 266(2-way)/4032(3-way)/55075(4-way) |
| **시나리오 인스턴스** | 요소의 **속성/파라미터**(강수량, puddle 밀도, 속도범위) | **p-way** (속성 간 의존성 = p) | 1760 → 176(2-way) |

- **의존성이 t/p 값을 정한다**: weather↔road condition은 의존(비→젖은 노면) → 이 둘은 반드시 함께 커버(t≥2). weather와 time-of-day는 독립 → 낮은 차수로 충분. **forbidden**(예: 고속도로 보행자=0)은 의존성 표의 0으로 인코딩.
- 결과(cut-in 시나리오, level-2): OE 266 vs 완전열거 169B, 테스트케이스 80 vs 640(**87.5%↓**), 클라우드 시뮬 시간 104분 vs 225분(**~51%↓**). **충돌 근본원인(root cause)은 2개로 동일** → 축소가 안전분석력을 훼손 안 함.

### 조합 폭발 대응 원리
```
완전 열거:  모든 ODD 요소·속성 동시 조합 → 169B (실행 불가)
DBCA:      1. 요소 간 의존성을 사람이 명시 (자동학습 불가 — 논문도 인정)
           2. 최대 의존 차수 = t → IPOG로 t-way OE 생성
           3. 속성 간 의존 차수 = p → p-way 인스턴스 생성
           4. forbidden = 의존성 표의 0
```

---

## 장단점

**장점**
- ODD **요소 vs 속성** 2단계 분리 — 이산 조합(OE)과 연속 파라미터(instance)를 다른 축소기로 다룸
- 의존성 명시가 곧 **감사 근거**(왜 이 조합을 뺐나) — 안전분석 문서화에 유리
- t-value 실증(SW 테스팅 문헌): 2-way 62~97%, 3-way 87~99%, 4-way 96~100% 결함 노출

**단점 / 한계 (논문 자인)**
- **의존성 식별이 수작업** — 자동 구조학습 없음. 향후과제로 "property relation tables" 언급
- 시나리오 goal/objective 정의 절차 부재(recommender system 향후과제)
- 단일 cut-in 시나리오·Metamoto 단일 툴 검증 — 일반화 별도
- 시뮬 툴이 요소 누락 시 조합해도 미검증(툴이 ODD 속성을 못 세팅)
- **비가중(unweighted) 커버리지** — 모든 t-way 조합을 동등 취급. 현실 노출빈도 개념 없음

---

## 프로젝트 적용 포인트

### EXP-003 Phase 1 §2 (의존 그래프)와 직접 대응

Phase 1 §2의 손지정 조건부 3개(`road_type→agent`, `road+weather→speed`, `time+road→lighting`)는 DBCA의 "의존성이 t를 정한다"의 **분포판**이다. DBCA는 같은 문제(ODD 조합 폭발)를 **커버리지 관점**에서 형식화하고, Phase 1은 **노출가중 관점**에서 형식화한다 — 상호보완.

1. **§2 손지정 스탠스의 독립 근거**: DBCA도 "의존성 자동학습 불가 → 수작업 + forbidden 제약"에 도달. Phase 1 §2 "구조는 데이터로 못 세운다(명시→반증→방어)"를 독립 논문이 동일 결론으로 뒷받침.
2. **2단계 분리 채택 검토**: Phase 1의 이산 축(road_type, weather…) = DBCA의 OE(t-way), 연속 파라미터(speed range, density, ρ) = 인스턴스(p-way). Phase 1은 이미 축/파라미터를 나누지만 DBCA의 t/p 형식화·IPOG 툴체인이 명시적 참조.
3. **커버리지 보완 지표(향후)**: §8 exposure 누적절단(95%) 집합이 **의존 그래프의 t-way를 전부 커버하는가?** 미커버 t-way 조합 = §10 희귀-위험 union 후보. → coverage(DBCA) ⟂ exposure(Phase 1)의 교차 검증.
4. **Table 1 = ODD 축/값 대조표**: ISO 21448 B.3 기준 12요소·값 목록은 Phase 1 `odd_schema.md`·`mapping.yaml`의 값 인벤토리·forbidden 규칙 크로스체크용.

### ⚠️ 도입 시 주의 (coverage ≠ exposure)
DBCA는 **비가중 t-way 커버리지**다. t-wise를 그대로 가져오면 희귀 조합과 흔한 조합을 동등 취급 → Phase 1 §1이 반박하는 "self빈도=노출" 오류와 같은 함정. **DBCA로는 셀 집합/의존구조를 정의**하고, **랭킹은 Phase 1 `P_ext`(VKT 가중)** 로 — 역할 분리 유지.

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-3 | 의존성 기반 t-way로 ODD 조합 폭발 축소 → 수집/검증 대상 셀 정의 |
| Gap-4 | forbidden·의존 구조로 유령조합 제거 (Phase 1 §2 유령조합 방지와 동일) |

## 관련 실험
- EXP-003 Phase 1: §2 의존 그래프의 커버리지 대응물 + Table 1 축/값 대조
- EXP-003 Phase 0: ODD 셀을 t-way 의존 커버 집합으로 정의
- EXP-004: 위험도 가중 조합 설계

## 관련 문서
- [combinatorial-full-coverage-testing.md](combinatorial-full-coverage-testing.md) — t-wise 커버리지 실측(비가중), heat+GA 대표점
- [coverage-vs-sufficiency.md](coverage-vs-sufficiency.md) — Q1 조합 축소(커버리지) vs 노출/충분성
- [criticality-metrics-suitability.md](criticality-metrics-suitability.md) — 조합의 위험도(criticality) 정량화
- [graph-based-coverage-analysis.md](graph-based-coverage-analysis.md) — 상호작용 인자 archetype
- [EXP-003 Phase 1 design](../../../experiments/EXP-003/phase1/design.md) §2 — 손지정 의존 조건부
