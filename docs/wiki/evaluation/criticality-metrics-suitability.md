# Criticality Metrics for Automated Driving — 리뷰 + 적합성 분석

## 출처
- **저자**: Lukas Westhofen, Christian Neurohr, Tjark Koopmann, Martin Butz, Barbara Schütt, Fabian Utesch, Birte Neurohr, Christian Gutenkunst, Eckard Böde (DLR, Bosch, FZI, AVL)
- **연도**: 2022 (Received 2021-07)
- **저널**: Archives of Computational Methods in Engineering (Review Article)
- **논문**: DOI 10.1007/s11831-022-09788-7
- **보충 웹**: http://purl.org/criticality-metrics
- **파일**: `literature/papers/Criticality Metrics for Automated Driving.pdf`

---

## 핵심 아이디어

**criticality = "교통 상황이 계속될 때 관련 행위자들의 결합 위험"**. 이 논문은 (1) 약 **40개 criticality 지표**를 통일된 표기로 리뷰하고, (2) 주어진 응용에 **어떤 지표가 적합한지 고르는 5단계 적합성 분석(suitability analysis)** 을 제시한다.

### 지표 카탈로그 (Sect 5.2, ~40종)
- **시간형**: TTC, MTTC/CrI, PTTC, TTZ, TTCE, WTTC, TET, TIT, TTM(TTB/TTS/TTK), TTR, THW, ET, PET, PrET/TA/SPrET
- **가속/거리형**: PSD, a_long,req(DRAC), a_lat,req, a_req, DST, BTN, STN, LatJ/LongJ, SOI, PRI, RSS-DS, Δv, CS
- **확률/최적화형**: CPI, ACI, CI, TCI, P-MC, P-SRS, P-SMH, PF, SP(SFF), AM
- Fig 5: 지표 간 상호관계 그래프(A가 B를 계산에 사용/집계/의미유사 등)

### 지표의 8개 속성 (Sect 4.1) — 적합성 판단 축
run-time capability, target values, **subject type**(사람 vs 자동차), **scenario type**(타당성이 시나리오 유형에 구속 — TTC는 차량추종엔 유효, 교차로선 ∞로 무의미, Fig 1), inputs, output scale(nominal/ordinal/interval/ratio), reliability, validity, **sensitivity/specificity**(GT 대비 혼동행렬), prediction model.

### 적합성 분석 (Sect 6) — 5단계 전문가 프로세스
```
입력: 응용 A, 가용 지표집합 K, 모델집합 M
(1) A에 필요한 지표 속성 P → 요구사항 R 도출 (Table 4 참조)
(2) R을 중요도순 정렬 (부분순서)
(3) 각 지표의 속성 평가 (Sect 5.3)
(4) 최중요 요구 r부터 불충족 지표 제거, r 제거
(5) R 빌 때까지 반복 → 남은 K = 적합 지표집합
```
예시(비보호 좌회전/교차로): 43지표 → subject/scenario type·validity 요구로 필터 → 물리기반 회귀모델용 지표 셋으로 수렴.

### 응용 분류 (Sect 3, V-model 배치)
A.1 목적함수 / A.2 런타임 모니터링 / A.3 위험저감상태 식별 / B.1 pass-fail / B.2 **시나리오 분류·인스턴스화·데이터기반 시나리오 발굴**(B.2.c: **선택적 데이터 기록 + 데이터 필터링**) / B.3 테스팅 / B.4 안전논증.

---

## 장단점

**장점**
- criticality 지표의 **가장 포괄적 통일 카탈로그**(수식·속성·상호관계) — 위험도 정량화 시 단일 참조점
- **적합성 분석**이 "어느 지표를 쓸까"를 속성 요구로 형식화 (Table 4 = 응용별 요구 매핑, 재사용 템플릿)
- 지표 타당성이 **시나리오 유형에 구속**됨을 명시 → 셀별(ODD별) 지표 선택 근거

**단점 / 한계 (논문 자인)**
- 속성 평가 다수가 **전문가 가설**(추적 가능 근거 부족) — 정량 연구 필요
- 불확실성 정량화·측정오차 전파 미해결(향후과제: interval arithmetic)
- **대부분 지표가 인과연쇄 끝단(물리 증상: 근접·고속·급감속)만 측정** → 상류 인과요인(환경조건·도로망 복잡도·규칙위반)은 미포착. 저자도 "더 예방적 접근 = 상류요인 식별"을 향후방향으로 지목.

---

## 프로젝트 적용 포인트

### EXP-003 Phase 1 §10 (희귀-위험 union)의 정량 엔진

Phase 1 §10은 "criticality 상위 희귀조합"을 **손 위험표**(coverage-vs-sufficiency L111-119)로 정의한다. 이 논문이 그 손표를 **계산 가능한 지표**로 치환·보강한다.

1. **§10 손 위험표 → 지표 카탈로그**: ODD 셀별 criticality를 주관 손값 대신 적합 지표(TTC/THW/PET/BTN/PRI 등)로 산정. exposure가 침묵하는 C그룹 축(occlusion·visibility)의 위험 꼬리를 계산값으로.
2. **적합성 분석 = 셀별 지표 선택 절차**: 지표 타당성이 시나리오 유형 구속(TTC=차량추종, 교차로 무의미)이므로 **셀마다 다른 지표**가 필요. Sect 6의 5단계·Table 4 속성요구 매핑을 §10 지표 선택 템플릿으로.
3. **Phase 1의 위치 = 상류 예방층**: 이 논문이 "미흡"으로 지목한 **상류 인과요인(환경조건·도로망 복잡도)** 이 곧 Phase 1의 ODD-조합 criticality다. 즉 Phase 1(상류 조건 위험) + 이 카탈로그(하류 운동학 증상) = **2층 criticality**. Phase 1의 기여 포지셔닝 근거.
4. **지표 union**: 단일 지표가 전체 criticality를 못 덮음(논문 반복 강조) → §10의 "union" 구성은 여러 지표 조합이어야 함을 뒷받침.
5. **응용 B.2.c 직접 대응**: 선택적 데이터 기록 + 데이터 필터링 = EXP-003 데이터 큐레이션 목표 그 자체. criticality 지표로 대규모 naturalistic 데이터에서 안전관련 희귀샘플을 거르는 것이 리뷰의 명시 응용.

### ⚠️ 주의
- 지표 대부분이 **행위자 궤적·상태(운동학) 입력**을 요구 → 클립 캡션/ODD 태그만으론 직접 계산 불가. Phase 1 §10은 조합 수준 위험(exposure 부재 + 손/외삽 위험표)에 머물고, 지표 카탈로그는 **원신호가 있는 경우의 정량화 로드맵**으로 참조.
- 속성평가가 전문가 가설 → 특정 지표 채택 시 보충웹(purl.org/criticality-metrics)에서 근거·GT 확인.

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-4 | ODD 셀 위험도 정량화 → 희귀-위험 조합 우선순위 (분포 편향의 위험축) |
| Gap-1 | 평가셋 위험 시나리오 선별에 지표 기반 sensitivity/specificity |
| Gap-3 | 시나리오 유형별 지표 타당성 → 셀별 커버리지 위험 가중 |

## 관련 실험
- EXP-003 Phase 1 §10: 희귀-위험 union의 criticality 정량 엔진 + 지표 선택 절차
- EXP-002: 위험 시나리오 발굴(밀도 갭)의 위험도 지표 보강
- EXP-004: 위험도 가중 데이터 큐레이션

## 관련 문서
- [coverage-vs-sufficiency.md](coverage-vs-sufficiency.md) — criticality 손 위험표(L111-119)를 이 카탈로그로 치환
- [dbca-combinatorial-odd-reduction.md](dbca-combinatorial-odd-reduction.md) — 조합 커버리지(위험도의 조합 축)
- [ttc-scenario-distribution.md](../data_distribution/ttc-scenario-distribution.md) — TTC 기반 시나리오 분포
- [situation-coverage-grid.md](situation-coverage-grid.md) — 미관측 위험조합 확률 외삽
- [EXP-003 Phase 1 design](../../../experiments/EXP-003/phase1/design.md) §10 — 희귀-위험 union
