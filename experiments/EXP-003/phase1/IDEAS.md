# EXP-003 Phase 1 — 접목 후보 backlog (deferred)

> 설계 미반영 아이디어를 **쌓아두고 훑는** 곳. design.md는 편입 결정 시에만 수정.
> 상태: `후보` → `검토중` → `편입` / `기각`. 편입 시 design.md 콜아웃 추가 + 이 행 갱신.
> 자동 재부상용 트리거는 메모리 `exp003_phase1_refs`가 담당 — 여기는 인간용 목록.

## 후보 목록

| # | 아이디어 | 붙는 곳 | 검토 트리거 | 상태 |
|---|---|---|---|---|
| 1 | **DBCA** 의존성 기반 t/p-way 조합 축소 | §2 의존그래프 | §2 구현·검증 시. exposure 95% 집합이 의존 t-way를 다 커버하나? 미커버=§10 후보 | 후보 |
| 2 | **Criticality Metrics** ~40지표 카탈로그 + 적합성 분석 | §10 희귀-위험 union | §10 정량화 시. 지표가 궤적/운동학 입력 요구 → 원신호 있을 때만 | 후보 |

## 상세

### 1. DBCA (Madala 2021, VEHITS) — §2 커버리지판
- wiki: [dbca-combinatorial-odd-reduction](../../../docs/wiki/evaluation/dbca-combinatorial-odd-reduction.md)
- 왜: §2 손지정 의존조건부 3개의 커버리지 대응물. "의존성이 t 차수를 정한다", forbidden=의존표 0.
- 실용성 체크포인트: DBCA는 **비가중 커버리지** → 셀집합·구조 정의용으로만. 랭킹은 P_ext(VKT) 유지.
- 편입 조건: §2 의존그래프가 코드로 서고, t-way 커버 점검이 exposure 절단과 상보적으로 유용하다고 확인될 때.

### 2. Criticality Metrics 리뷰 (Westhofen 2022) — §10 정량 엔진
- wiki: [criticality-metrics-suitability](../../../docs/wiki/evaluation/criticality-metrics-suitability.md)
- 왜: §10 손 위험표를 계산가능 지표(TTC/THW/PET/BTN/PRI…)로 치환. Sect6 적합성분석=셀별 지표선택.
- 실용성 체크포인트: 지표 대부분 궤적/운동학 입력 필요 → 클립 캡션·ODD 태그만으론 계산 불가. 원신호 확보 여부가 관문.
- 편입 조건: §10 착수 시 원신호(궤적) 접근 가능하면 손표 일부를 지표로 대체 검토.

## 관련
- 메모리: `exp003_phase1_refs` (자동 recall 트리거)
- [design.md](design.md) §2·§10 — 편입 시 콜아웃 추가 지점
