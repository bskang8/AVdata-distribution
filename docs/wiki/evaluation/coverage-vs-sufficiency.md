# Coverage vs Sufficiency — 중요 ODD 조합 선별과 신뢰성 충분성 판정

## 문서 성격

단일 논문 정리가 아니라, 두 개의 실전 질문에 대한 **문헌 종합 분석 노트**다.

- **Q1**: ODD 조합이 1억+ 개인데 커버리지를 다 채우는 건 무의미하다. 주행에 중요한 조합을 어떻게 효율적으로 구별하나?
- **Q2**: 중요 조합군의 커버리지가 충분해도 실주행 신뢰성이 보장되지 않는다. 신뢰성·다양성이 충분한지, 아니면 어떤 데이터가 필요한지 어떻게 분석하나?

**핵심 명제 두 개**
1. Q1 = "조합 커버리지는 애초에 잘못된 목표다." 목표를 *커버리지 채우기* → *중요도 랭킹*으로 전환해야 한다.
2. Q2 = "커버리지 ≠ 신뢰성." 커버리지는 이진(있다/없다) 신호일 뿐, 충분성(sufficiency)은 셀별 성능 포화 곡선이 판정한다.

관련 갭: Gap-1(평가셋 커버리지), Gap-3(ODD 커버리지 저조), Gap-4(분포 편향). 관련 실험: EXP-003 Phase 0/C, EXP-004.


우리 목적은 **기존데이터(83k~100k 클립) 분포를 진단**하는 것이다. 진단 목적은 직교하는 두 질문으로 분해
된다(논문 서술용 정식화):
> - **Q-cov (커버리지)**: 데이터가 *중요* ODD를 커버하는가?
> - **Q-div (다양성)**: 커버한 셀이 학습 성능을 낼 만큼 *다양한가*?

---

## Q1. 어떤 ODD 조합이 중요한가 — 관측 조합을 중요도로 랭킹

**목적.** ODD는 이미 이산이라 값 조합(격자)은 스키마가 이미 준다 — 새로 만들 게 없다. 하려는 건 **데이터에 실제 나타난 조합을 집계해 ① 의미없는 것 걸러내고 ② 중요한 순으로 줄세워 ③ 중요한데 데이터가 부족한 조합에 수집을 몰아주는 것**이다. 이 진단 목적에는 생성형 문헌(Sensors 2025 등)의 covering array·forbidden tuple·t-wise 차수설계가 대부분 불필요하다(→ 맨 아래 "제외" 참조). 세 스텝이면 된다.

*(커버리지·중요도가 Q1, 학습용 다양성은 Q2 — 직교하며 Q2 섹션에서 다룬다.)*

### Step A — 해상도 정돈 (축 선택 + 값 병합)

격자를 *만드는* 게 아니라, 이미 있는 이산 조합을 **분석 가능한 해상도로 정돈**한다. 손잡이는 둘뿐:
- **축 선택**: 19개 ODD 차원을 다 쓰면 조합이 폭발해 전부 singleton → 분석 불가. AV 성능에 직결된 소수만 축으로 (EXP-003은 11개 선택).
- **값 병합 (frequency-floor)**: 최빈값이 상수인 차원 제거 + 희소 값 병합으로 빈 셀 축소.

**실측 (100,398 클립)** — 병합 전후 "판정 가능한 셀" 수:

| | 관측 셀 | singleton | 추정가능(≥50클립) | 이론 셀 | 커버율 |
|---|---|---|---|---|---|
| 병합 전(11D) | 2,070 | 897 (43%) | **169** | 7.26M | 2.3e-5 |
| 병합 후(9D) | 1,773 | 677 (38%) | **176** | 172.8k | 1.0e-3 |

*(퇴화 차원 2개 제거: `occlusion`·`special_event`; 값<500 병합)*

- 병합은 **표만 깔끔해질 뿐(이론공간 42×↓, 커버율 44×↑) 분석력은 그대로**다: **판정 가능 셀이 거의 안 늘어난다(169→176)**. 병합은 빈 칸·꼬리를 정리할 뿐 새 데이터를 만들지 못하기 때문.
- **데이터 91%가 ~170개 흔한 셀**(urban/rural×clear×cars_only×sparse×dry)에 몰림. 위험 꼬리(pedestrians 268·snow 1,360·high-occlusion 123·dense)는 표본 부족으로 **셀 판정 자체가 불가**.
- → **의미있는 per-cell 분석은 head ~170셀에 한정된다.**

### Step B — 중요도 랭킹 (의미없음 제거 + 우선순위)

판정 가능한 조합을 3축 곱으로 점수화 (EXP-003 우선순위 공식과 동형):

```
priority = criticality × exposure × model_sensitivity
```

| 축 | 측정 대상 | 문헌 근거 |
|----|-----------|-----------|
| **Criticality** | 사고/near-miss 전환 확률·심각도 | de Gelder Criticality Coverage ([coverage-metrics-scenario-database.md](coverage-metrics-scenario-database.md)); Simulating-Unseen crash prior |
| **Exposure** | P(조합\|ODD) — 현실 발생 빈도 | naturalistic 분포; **현실에 없는 조합 → 0 자동 탈락 = 여기가 "의미없음" 필터** |
| **Model sensitivity** | 이 조합에서 모델이 실제로 실패하나 | **Domino** ([domino-systematic-error-discovery.md](../data_distribution/domino-systematic-error-discovery.md)): 오류 슬라이스 자동 발견 |

**의미있는 조합 구별은 이 세 축이 한다** — exposure≈0(현실에 없음)은 탈락, model_sens 낮음(이미 잘함)은 후순위. Domino 2×2로 정리:

```
밀도 낮음 × 성능 낮음  → 최우선 수집     밀도 낮음 × 성능 높음  → 처리 가능, 후순위
밀도 높음 × 성능 낮음  → 품질 문제       밀도 높음 × 성능 높음  → 강점, 수집 불필요
```

**수행 방법 — 중요도 선별은 전체 공간에서, model_sens는 커버 후로.** 목표가 "전체 ODD 공간에서 중요 조합 선별 → 현 데이터가 얼마나 커버했나"이므로, **중요도는 클립 없이 전체 공간에 정의되는 축으로만 매긴다**: `importance(c) = criticality(c) × exposure(c)`. model_sensitivity는 그 조합에 클립이 있어야 측정되므로(수집 데이터에 갇힘) 중요도 선별엔 못 들어가고, **커버된 셀의 충분성 정제** 단계로 미룬다.

> **축이 정의되는 범위가 우선순위를 정한다.** criticality·exposure는 세상/조합의 속성이라 미관측 조합에도 정의되지만, model_sens는 (모델 × 그 셀 데이터)의 속성이라 관측 조합에만 존재한다.

**역할 분담 — "전체를 보는" 능력은 criticality에 있다 (exposure에 과부하 걸지 말 것).**

- **exposure = 빈도 축 하나.** "흔해서 무시 못 할 영역"을 잰다. 편향 없는 표본이면 그 일은 정확히 하지만 **그 이상은 시키면 안 된다.** exposure는 분포 추정이라 전체 조합을 *관측*할 필요는 없으나(대표 표본이면 됨), 안전-critical 조합은 **정의상 희귀**하라 exposure가 0에 가까운 값을 준다 → **exposure 단독 랭킹은 바로 그 위험한 꼬리를 떨어뜨린다.**
- **전체 공간 + 희귀-위험 조합의 부담은 exposure가 아니라 다른 둘이 진다**:
  - **criticality** — 클립 없이 전체 공간에 정의(보행자×눈=위험은 관측 0이어도 계산됨). "전체를 보는" 능력이 여기 있다.
  - **Step C 외삽** — 이웃 실패율로 미관측 조합의 위험도를 추정.
- 따라서 `importance = criticality × exposure`에서 exposure는 곱의 한 인자로 **"흔한 것 중 위험한 것"을 걸러줄 뿐**, 단독으로 중요도를 정하지도 전체를 보지도 않는다. (raw exposure의 기여도 "편향 없는 빈도 축 + 큐레이션 편향 측정"이라는 좁고 확실한 몫이지, 전체 공간 중요도 분석이 아니다.)

| 우선 | 축 | 확립 방법 | 이 순서인 이유 |
|----|----|----|----|
| **1 (최우선)** | Exposure | 외부 naturalistic 분포(공개 AV·교통통계) 확립 — 없으면 존재 여부부터 조사 | **당신이 빠뜨린 유일한 full-space 신호.** 이게 있어야 1억 조합을 현실 빈도로 줄세운다. self빈도는 "수집량 ≠ 현실노출"이라 순환→불가 |
| **2** | Criticality | 손 위험표(도메인, 라벨 불요; 예 pedestrian 1.0…cars 0.2) → *선택적* crash-DB 정밀화 | 클립 없이 전체 공간 즉시 적용. 유일하게 수집과 독립인 **이미 믿을 만한 축**. 지금 확립 가능 |
| **3 (커버리지 확인)** | — | (crit×expo 상위 조합) ∩ 관측 조합 → 개수·다양성 측정 | Step A + effective_n으로 대체로 지금 가능. "중요한데 미관측"은 Step C 외삽 |
| **4 (뒤로: 충분성)** | Model sens | egomotion surrogate: `egomotion_offline` ego궤적을 GT로 "과거→미래 궤적 예측" → 라벨 없이 per-clip ADE/FDE | 세상 중요도가 아니라 **커버된 셀에서 모델이 여전히 실패하나**(Q2 충분성). Q2·Domino·LID검증의 관문이나 그건 충분성 단계 얘기 |

- **주의**: "커버했나"가 단순 개수면 model_sens 불필요, "성능 낼 만큼 제대로 커버"면(학습용 다양성) 4단계에서 필요 — 단 중요조합 선별·커버확인을 마친 뒤의 last-mile이지 첫 수순이 아니다.
- **착수 전 de-risk (egomotion에 투자할 때)**: `egomotion_offline` GT 사용성 확인(클립 커버율·품질·프레임 정합)을 본격 투자 전 10줄로 먼저.

**Exposure 외부-자료 확립 + "무시 못 할 영역" 선별 (전체-공간 축).** 수집 데이터에 의존하면 순환이므로 기관·연구 자료로 구성한다. 두 단계: ① 결합 분포 구성 → ② 빈도 영역 절단.

- **① 결합 구성 — 기관 marginal을 블록 결합** (결합을 직접 주는 소스는 없음 → 분해·조달·곱). *구현 방법론 전문: [EXP-003 Phase 1 design](../../../experiments/EXP-003/phase1/design.md) — VKT-가중 층화 혼합, 매핑표, MC 합성, 검증 프로토콜.*

  | ODD 블록 | 소스(기관) | 주의 |
  |---|---|---|
  | weather·fog·road_surface | 기상청(KMA) 지역·시간별 강수/적설/안개 비율 | 노면은 강수+기온 파생 → weather와 묶음 |
  | road_type | 국가교통DB(KTDB)·국토부 도로등급별 **VKT** | ⚠️ 도로 길이 아닌 **통행량** 가중 |
  | lighting(주/야) | 천문연(KASI) 일출몰 × KTDB 시간대 교통량 | time_of_day 미보유분 복구 |
  | agent_type·traffic_density | 도로교통공단(KoROAD) 보행자·교통량 | ⚠️ **road_type 조건부**(고속→보행자~0) |
  | speed_range | KTDB 도로등급별 속도 | road_type 조건부 |

  결합: `P_ext = P(환경) × P(도로망) × P(agent,density|road_type) × P(lighting)`, forbidden 0. **강한 조건부(agent|road_type, speed|road_type) 2~3개만 손지정**, 나머지 블록 독립 근사.
- **최대 리스크 = 카테고리 매핑**: 기관 분류(KMA "강수 있음", 국토부 도로등급)를 **당신 ODD 값으로 매핑하는 테이블**을 손으로 짜야 하며, 어긋나면 전체가 흔들림.
- **② 영역 절단**: `P_ext` 내림차순 → **누적 exposure가 목표%(95%/99%)에 도달하는 최소 조합집합** = 핵심 운행영역(리포트: "상위 N조합 = 주행의 X%"). 보완으로 per-combo 바닥(예 0.1% 초과).
- **⚠️ 이 빈도영역은 안전-critical 희귀조합을 포함하지 않는다**(저빈도라 누적 상위에 안 듦) → 최종 타겟 = (exposure 누적영역) ∪ (criticality 상위 희귀조합). exposure에 전체를 기대하지 말 것.
- **검증**: 현실 앵커(`맑음×도심×차량만×주간`이 최상위 지배 조합인가) / 교차 소스 일치 / raw 대조(있으면, `P_ext` vs raw 빈도 격차 = 매핑 불량 또는 플릿 도메인 ≠ 전국평균).
- **v1(과잉설계 금지)**: 4블록 각 1소스 + 조건부 2~3개 + 곱 + forbidden 0 → 정렬 → 누적 95% 절단. 조회 테이블 + 곱 + cumsum.

**Criticality 손 위험표 확립 (전체-공간 축, 지금 가능).** 한 덩어리가 아니라 **`crit(c) = P(안전-critical 이벤트|c) × severity(c)`** 로 분리한다 — 각 절반을 다른 통계로 앵커할 수 있어 값이 정당화된다.

- **차원 분류** (모든 차원에 주지 말고 안전 관련만):
  - *Likelihood↑*: weather·fog·lighting·visibility·occlusion(지각 저하) / junction·lane_marking(충돌 기하·경로 모호) / agent_type·traffic_density(충돌점 수)
  - *Severity↑*: speed(운동에너지 ∝ v²) / agent_type=VRU(취약) / road_type=highway(고에너지) / road_surface·gradient(제동거리)
- **값별 배수 = 공개 통계에 앵커** (숫자 지어내기 금지): pedestrian 4·cyclist 3(Rosén&Sander 보행자 치사율 ∝ 속도^4) / poorly_lit 2~3(NHTSA 야간 치사) / snow 2.5·fog 2(FHWA weather-crash) / speed high 4(∝v²) / in_junction 2.
- **결합 = relative-risk 곱** `likelihood = ∏배수_i`, `crit = likelihood × severity`. ⚠️ **상관 요인 이중계산 금지**: `비×젖은노면×저시야`를 다 곱하면 "악천후" 하나를 3중 계산 → **상관 차원을 블록으로 묶어 블록당 배수 하나**(exposure와 동일 블록). 다요인 누적은 cap/log 감쇠, forbidden은 0.
- **검증(손 표는 주관적 → 필수)**: ① 최상위 조합이 알려진 고사고 시나리오(보행자×야간×젖은노면×교차로)와 맞나 ② **민감도**: 가중치 ±30% 흔들어 *순위*가 안정한가(뒤집히면 앵커 보강) ③ 전문가 2인 이상 평균 ④ crash-DB 확보 시 실사고율과 상관 보정(선택적 정밀화).
- **v1(과잉설계 금지)**: 값별 배수 dict(YAML) + 앵커 ~5개 + 상관 블록 묶음 + 곱 + 민감도 스윕. **신뢰도를 가르는 둘 = ① published multiplier 앵커 ② 상관 이중계산 방지.**

### Step C — 부족 진단 → 수집/합성

- **중요도 상위인데 표본 부족(꼬리)** 조합 = 실주행 수집 또는 LTDA 합성 타겟 → [ltda-drive-longtail-augmentation.md](../scenario_generation/ltda-drive-longtail-augmentation.md). 해상도 조절로는 안 풀린다(데이터 부족 문제).
- **중요한데 아예 미관측**인 조합 = 이웃 실패율로 확률 외삽해 위험도 상한 → **Situation Coverage Grid**(arXiv 2507.12158). "실패 0" 가정 대신 통계적 랭킹.

### 이 목적에서 제외한 것 (진단·이산 데이터라 불필요)

- **covering array 생성 / t-wise 차수 설계 / forbidden tuple**: 관측 데이터를 진단하므로 조합은 데이터가 이미 주고(≈2,070개), 물리 불가 조합은 애초에 안 나타난다. t-wise는 *생성형 안전 커버리지 논증*이 목표일 때만 필요 — 그건 별도 목표다(Kuhn NIST SP 800-142).
- **고차 상호작용 안전망(SHAP-interaction 등)**: 오류 신호 확보 후 선택적 정밀화.

**결과**: 관측 ~2,070 조합 → 해상도 정돈으로 판정 가능 ~170셀 → 3축 랭킹으로 상위 수십 셀이 수집 타겟. 단, 위험 꼬리·오류 신호 부재가 현 병목.

---

## Q2. 커버리지가 충분해도 신뢰성은 별개 — 세 가지 충분성 테스트

반드시 분리할 개념:

> **Coverage** = "이 셀에 샘플이 ≥1개 있나?" (이진/카운트)
> **Sufficiency / Reliability** = "신뢰성 있게 동작할 만큼 *충분하고 다양한* 데이터가 있나?"

EXP-003이 계산한 `effective_n = 1.16`(agent_type)이 이 함정의 증거다 — 명목상 여러 조합을 커버했지만 실효 다양성은 1에 가까움(사실상 cars_only). 커버리지 표는 초록불, 신뢰성은 빨간불.

### (A) 다양성 충분성 — 셀 *내부* 다양성 (intra-cell)

같은 셀 안 500개 클립이 전부 같은 교차로·날씨·시각이면 카운트는 500이어도 모델은 한 인스턴스에 과적합.

- **effective_n**(이미 보유) 또는 **Vendi score**, 임베딩 공간 엔트로피/반경으로 측정 → [topp-r-fidelity-diversity-metrics.md](topp-r-fidelity-diversity-metrics.md), [metric-space-magnitude-diversity.md](metric-space-magnitude-diversity.md)
- 임계값 미달 셀 = "커버리지는 채웠지만 다양성 부족" → LTDA-Drive 합성 대상.

### (B) 성능 충분성 — 셀별 오류 + **포화 곡선** (가장 중요)

"충분한가?"의 원리적 답은 **셀별 스케일링 포화 곡선**이다.

**실증 ①: Data Scaling Laws for E2E AD (Naumann/NVIDIA, CVPR 2025 WAD).** 16~8192시간으로 시나리오별 스케일링 측정.

- 파워법칙: `L_val − ε∞ = β·x^c`, c ≈ −0.4
- **시나리오마다 기울기가 다르다**(핵심):
  - Lane keeping: c = −0.413 (가장 빨리 포화 → 더 넣어도 무의미)
  - Lane changing: c = −0.348 (가장 느림, 수확체감)
  - Turning: 8192시간까지 개선 후 plateau
- **타겟 성능당 필요 데이터 외삽** (꼬리의 지수적 폭증):

| 목표 FDE 개선 | 추가 필요 데이터 |
|------|------|
| 1% | +4,000 시간 |
| 3% | +29,000 시간 |
| 5% | +273,000 시간 |

- 이 데이터의 액션 분포 **91.8% 직진 / 5.2% 회전 / 3% 차선변경** — D_train의 71% 편향과 판박이.
- 함의: 평평해진 셀(직진 = 맑음·직진 71%)은 끊고, **아직 가파른 셀에만** 예산 투입.

**실증 ②: MOSAIC = Scaling-Aware Data Selection (arXiv 2604.08366).** EXP-003이 DISC로 전환하기 전 출발점이었던 논문. Q2 메커니즘이 그대로 구현됨:

- 클러스터별 포화 모델: `Δ̂U_i(n) = a_i(1 − e^{−n/τ_i})` (a=점근 상한, τ=포화 속도)
- 한계이득 그리디: `δ_i(b_i) = Δ̂U_i(b_i+1) − Δ̂U_i(b_i)` 최대 클러스터에서 1샘플씩 추가
- 결과: BRMR 0.18 = 랜덤 대비 **18% 예산으로 동등 성능**

> Naumann이 "곡선이 존재한다"를 증명하고, MOSAIC이 "그 곡선으로 어디에 얼마 넣을지 고르는 알고리즘"을 준다. **DISC(분포 분석)와 MOSAIC(스케일링 선택)은 대립이 아니라 Q1/Q2 역할 분담** — DISC로 셀 랭킹(Q1), MOSAIC 포화곡선으로 충분성 판정·정지(Q2).

**저비용 근사**: 재학습 없이 셀별 한계효용을 gradient influence로 추정 → **LESS** ([less-influential-data-selection.md](../data_distribution/less-influential-data-selection.md)). 남은 영향력 크면 아직 부족.

**포화 이론**: easy/redundant 샘플은 이미 포화 → 제거 대상, 희귀 셀은 가파른 구간 → 수집 타겟 → **Sorscher** ([beyond-neural-scaling-laws.md](../data_distribution/beyond-neural-scaling-laws.md)).

### (C) 분포 정합 충분성 — 셀 vs 실제 ODD 분포

셀 안 샘플 수가 많아도 **현실의 셀 내부 분포와 어긋나면**(covariate shift) 신뢰성 미보장. 예: "주간·맑음·교차로" 셀이 전부 4거리인데 현실엔 T자로가 절반.

- 수집 셀 분포 vs naturalistic 레퍼런스 간 **MMD / FID / KL** 또는 geometric coverage radius(de Gelder의 분포적 커버 비율).
- 어긋난 방향 = 부족한 하위 영역.

### 방향 진단 — "어떤 데이터가 필요한가"

세 테스트가 "부족"을 알려주면, *어느 방향*으로 부족한지는 **반사실·적대적 프로빙**으로 찾는다.

- **Simulating-Unseen** (counterfactual) / adversarial: 커버된 셀의 그럴듯한 near-miss 변형을 생성해 모델을 흔든다. 무너지는 방향 = 실효 커버 부족 방향 → [simulating-unseen-crash.md](../data_distribution/simulating-unseen-crash.md)
- 그 방향을 **LTDA-Drive**(LLM 명세 → diffusion 합성)로 타겟 합성하거나 실주행 수집 → [ltda-drive-longtail-augmentation.md](../scenario_generation/ltda-drive-longtail-augmentation.md)

---

## 종합 — 하나의 루프

```
A. 해상도 정돈: 축 선택 + 값 병합 (관측 ~2,070조합 → 판정가능 ~170셀)
B. criticality × exposure × model_sens 랭킹  [de Gelder, Domino] → 상위 수십 셀
     ※ 미관측 중요 조합은 확률외삽으로 플래그 [Situation Grid]
3. 상위 셀마다 3-충분성 테스트:
     (A) effective_n / Vendi           (intra-cell 다양성)
     (B) Domino 오류 + 포화곡선/LESS    [Naumann CVPR 2025, MOSAIC]  ← 정지 판정
     (C) MMD 분포 정합                  (셀 vs naturalistic)
4. 불충분 셀 → counterfactual/adversarial로 부족 '방향' 진단
5. LTDA-Drive 합성 or 타겟 실수집 → 2로 복귀
```

| 단계 | 방법 | 핵심 근거 |
|------|------|-----------|
| 해상도 정돈 (Q1-A) | 축 선택 + 값 병합 (판정가능 ~170셀) | 실측 100,398 클립 |
| 셀 랭킹 (Q1-B) | criticality×exposure×model-sens + 미관측 확률외삽 | Situation Coverage Grid 2025, de Gelder 2025, Domino |
| 충분성 판정 (Q2) | 셀별 포화곡선 `a(1−e^{−n/τ})`, 한계효용 정지 | Naumann CVPR 2025, MOSAIC 2604.08366 |
| 방향 진단 | counterfactual/adversarial → 타겟 합성 | Simulating-Unseen, LTDA-Drive |

**가장 강한 한 문장**: Naumann의 "5% 개선 = +273,000시간"이 "커버리지 다 채우는 건 무의미"의 정량적 증명이다. **커버리지는 어디를 볼지만 정하고, 충분/정지는 셀별 스케일링 곡선의 포화 여부로만 판정**한다.

---

## 참고문헌

| 저자/연도 | 기여 | 링크 |
|-----------|------|------|
| Naumann et al. (CVPR 2025 WAD, NVIDIA) | E2E AD 데이터 스케일링 법칙; 시나리오별 지수 상이, 타겟 개선당 데이터 외삽 | [arXiv 2504.04338](https://arxiv.org/html/2504.04338v1) |
| Scaling-Aware Data Selection / MOSAIC (2026) | 클러스터별 포화 스케일링 + 한계이득 그리디 선택 (BRMR 0.18) | [arXiv 2604.08366](https://arxiv.org/html/2604.08366v1) |
| Kuhn, Kacker, Lei (NIST SP 800-142, 2010) | interaction rule / FTFI: 결함 대부분 저차(≤3-way), ≤6-way 사실상 100%; CCM 측정 프레임 | [NIST SP 800-142](https://csrc.nist.gov/pubs/sp/800/142/final) |
| Full Coverage Testing (Sensors 2025) | t-wise 86.5% vs full-coverage 100%; 482개로 96% 비용 절감 | [PMC12473291](https://pmc.ncbi.nlm.nih.gov/articles/PMC12473291/) |
| Situation Coverage Grid (2025) | 커버리지 + 확률적 실패율 외삽으로 미관측 영역 안전 논증 | [arXiv 2507.12158](https://arxiv.org/pdf/2507.12158) |
| de Gelder et al. (2025) | ODD Coverage + Criticality Coverage 두 메트릭 | [coverage-metrics-scenario-database.md](coverage-metrics-scenario-database.md) |
| Eyuboglu et al. (ICLR 2022) — Domino | 오류 슬라이스 자동 발견 (밀도×성능 2×2) | [domino-systematic-error-discovery.md](../data_distribution/domino-systematic-error-discovery.md) |
| Xia et al. (ICML 2024) — LESS | gradient influence로 재학습 없이 셀 한계효용 근사 | [less-influential-data-selection.md](../data_distribution/less-influential-data-selection.md) |
| Sorscher et al. (NeurIPS 2022) | 기하학적 프루닝: easy 포화 / hard 유지 | [beyond-neural-scaling-laws.md](../data_distribution/beyond-neural-scaling-laws.md) |
| Li et al. (2025) — Simulating Unseen | counterfactual near-miss로 방향 진단 | [simulating-unseen-crash.md](../data_distribution/simulating-unseen-crash.md) |
| Yurt et al. (2025) — LTDA-Drive | LLM 명세 → diffusion 롱테일 합성 | [ltda-drive-longtail-augmentation.md](../scenario_generation/ltda-drive-longtail-augmentation.md) |
