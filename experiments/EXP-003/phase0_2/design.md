# EXP-003 Phase 1 — Exposure 분포 구축: 외부자료 조달 계획 → 주요 ODD 조합 선정

> **📎 개념 근거 (항상 참조)**: [coverage-vs-sufficiency.md](../../../docs/wiki/evaluation/coverage-vs-sufficiency.md) — 이 Phase의 상위 프레임(Q1 중요조합 선별 / Q2 충분성, Exposure=우선 1순위 축). Phase 1 작업 중 수시로 대조할 것. (같은 폴더 `_ref_coverage-vs-sufficiency.md` 심링크로도 접근 가능.)
>
> **위치**: `experiments/EXP-003/phase0_2/` — Phase 0(self 분포 프로파일링)의 산출물 `P_self`를 소비해 현실 앵커 `P_ext`와 대조. 구현 시 `strata.py`·`compose.py`·`output/` 합류.

## 문서 성격

[coverage-vs-sufficiency.md](../../../docs/wiki/evaluation/coverage-vs-sufficiency.md) Q1-B의 **우선 1순위 축 = Exposure**를 실제로 어떻게 구축·활용하는지 정식화한 **방법론 노트**(문헌 정리 아님). 두 부로 구성:

- **1부. 데이터 조달 계획** — 어떤 외부자료를 어느 포털에서·어떻게 끌어와 파이프라인 입력(CSV)으로 만드나.
- **2부. 주요 ODD 조합 선정** — 그 자료를 조립해 `P_ext`를 만들고, 이를 근거로 핵심 운행영역·수집 편향·수집 타겟을 뽑아내나.

**해결 대상**: 어떤 공개 소스도 ODD 조합의 *결합* 분포를 직접 주지 않는다(marginal·저차 조건부만). self 플릿 빈도는 "수집량 ≠ 현실노출"이라 순환. → 기관 marginal을 분해·조달·조립해 외부 naturalistic 노출분포 `P_ext(c)`를 만들고, 이걸로 주요 조합을 랭킹한다.

관련 갭: Gap-4(분포 편향 정량화). 관련 실험: EXP-003 Phase 0(self 분포와 대조).

---
---

# 1부 · 데이터 조달 계획

**목표**: 아래 2부 조립식에 넣을 **블록별 조건부 확률표(CSV 세트)** 를 외부 기관자료로 채운다. 순서: 무엇을·왜(§1) → 조립 구조 미리보기(§2) → 소스별 조달 레시피(§3) → **소스 정찰·게이팅(§3-R, recon)** → 층화 결정(§4) → 카테고리 매핑(§5) → 산출물(§6).

## 1. 무엇을·왜 조달하나 — exposure = VKT 질량의 분포

self 빈도로 노출을 재면 순환이다. 그래서 **가중치를 우리 플릿이 아니라 전국 통행량(VKT)** 에서 가져온다.

> 현실 노출은 면적도 도로길이도 시간도 아닌 **차량이 실제 굴러간 거리(VKT=주행거리)의 분포**다. 모든 것을 VKT로 가중한 (지역 × 시간 × 도로유형) **층(stratum)** 위의 혼합분포로 조립한다.

**"VKT 질량의 분포"란**: 전국 총 주행거리(예 3,500억 km)를 하나의 질량으로 보고 조건별로 100%를 나눠 담은 것 = `P_ext`. 저울추가 면적·도로길이·시간이 아니라 **굴러간 거리**인 이유: 골목길은 도로*길이*로는 대로의 절반이어도 실제 굴러간 *거리*는 1/10 미만 — AV가 마주치는 빈도는 길이가 아니라 주행거리에 비례한다.

**우리 ODD와의 관계**: `P_ext(c)`는 우리가 클립에서 만든 것과 **동일한 ODD 조합 격자** 위에 산다(현실의 모든 1km도 조합 c 하나에 떨어짐). 우리 데이터 `P_self(c)`=클립수 비율, 현실 `P_ext(c)`=VKT 비율 → 같은 축이라 **나눠서** 과/소수집 진단(§9). 즉 VKT는 *우리 분포를 재는 현실의 자*다.

> ⚠️ **단위 주의**: 우리 클립은 고정길이 영상(≈시간 조각)이라 엄밀히는 **차량·시간(VHT=VKT/평균속도)** 이 맞는 짝. v1은 VKT 그대로 쓰고 속도 보정(÷평균속도)은 노브로 남긴다 — 편향 *방향*은 잘 안 뒤집히나, 고속도로 계열 셀 해석 시 이 과대평가를 기억.

이 프레임이 조달 대상을 정한다: ① 층 가중치용 **VKT**, ② 층 조건부 **블록 marginal**들. 단, 기관은 지각·장면 축을 못 재므로 **조달 대상 축을 미리 가른다**:

| 그룹 | 축 | 조달 여부 |
|---|---|---|
| **A. exposure-supported** | road_type, weather, fog, road_surface, lighting, agent_type, traffic_density, speed_range | **조달 O** — P_ext 정식 구성 |
| **B. 파생/약함** | lanes, road_divider, gradient, curvature | road_type 조건부로 약하게 or 생략 |
| **C. 측정 불가**(지각·장면) | occlusion, scene_ambiguity, visibility, lane_marking, junction, unexpected_element | **조달 X** — exposure 침묵 → 2부에서 criticality가 담당 |

> [coverage-vs-sufficiency.md](../../../docs/wiki/evaluation/coverage-vs-sufficiency.md) L74-80의 "전체를 보는 능력은 exposure가 아니라 criticality"와 일치. **P_ext는 A그룹(≈8축)에서만** 정의하고 조달도 A그룹만 한다. C축 위험 꼬리는 2부에서 criticality가 잡는다.

## 2. 조립 구조 미리보기 — 어떤 표를 채워야 하나

> **쉬운 설명 — 왜 이 단계가 필요한가**
>
> **알고 싶은 것**: 현실 주행의 모든 순간을 늘어놓으면 각 장면 조합이 몇 %냐(맑은 도심 주간 30%, 비 오는 고속 야간 0.5%…). 이게 있어야 우리 데이터가 현실보다 뭘 많이/적게 담았는지 잰다. **근데 이 통짜 표를 주는 데가 없다.** 있는 건 조각난 단순 통계뿐("1월 눈 20%", "주행의 28%가 고속도로").
>
> **순진한 방법이 망하는 이유**: 그냥 곱하면(`고속 28% × 보행자 5% = 고속에 보행자 1.4%`) **현실에 없는 유령 조합**이 생긴다(고속엔 보행자 0, 한여름엔 눈 0). 축들이 서로 얽혀 있는데 곱셈이 그 얽힘을 무시하기 때문.
>
> **해결 — "무엇이 무엇을 정하나" 지도**: 얽힘엔 주도권이 있다. **도로유형이 무대감독**(고속→차만·빠름·야간 어둠 / 도심→보행자 섞임·느림·가로등)이고, **언제·어디가 날씨를 정한다**(1월 강원→눈). 신경 쓸 얽힘은 딱 3개(도로→참여자, 도로+날씨→속도, 도로+시각→밝기), 나머지는 독립으로 단순화.
>
> **상관을 공짜로 얻는 트릭(핵심)**: 상관("눈은 겨울에")을 일일이 재지 않는다. 주행을 `(계절·시간·도로)` **바구니**로 나눠 담고 각 바구니를 **실제 주행량(VKT)만큼 무겁게** 치면, 눈은 겨울 산간 바구니에 몰려 있으므로 "눈∧지방도∧저속"이 **알아서** 흔해지고 "눈∧한여름"은 애초에 안 생긴다. 즉 **장면을 통째로 상상하지 말고 "상황을 먼저 뽑고 그 안을 채우는" 순서**로 만들면 얽힘이 저절로 지켜진다(→ §7 시뮬레이션).
>
> **그래서 이 단계 = 통짜 표를 못 사니, 살 수 있는 작은 조각들을 현실적으로 이어붙일 설계도를 그리는 것.** 설계도의 화살표 하나가 곧 조달할 표 하나다.

조달 목표(=어떤 조건부 CSV가 필요한가)는 조립식의 구조에서 나온다. 층 $s=(r,m,h,k)$ 안에서:

```
road_type k  ──┬─▶ agent_type, traffic_density   (P₃: k, h 조건부)   ← 강한 조건부
               ├─▶ speed_range                    (P₄: k, weather 조건부) ← 강한 조건부
               └─▶ lighting                        (P₅: h, k 조건부)   ← 강한 조건부
(r,m,h) ──────────▶ weather, fog, road_surface     (P₁: 기후값 조건부)
```

- **손지정 조건부 3개**: (agent,density|k), (speed|k,weather), (lighting|h,k). 나머지 블록 독립.
- **forbidden = 조건부 표의 0**(예 `P₃(pedestrians|highway)=0`). 별도 리스트 안 만듦.

→ **채워야 할 표**: $w(s)$(VKT), $P_1$(weather·fog·road_surface), $P_3$(agent·density), $P_4$(speed), $P_5$(lighting). road_type $P_2$는 VKT 비율이 곧 marginal이라 $w$에 흡수. 조립·수식은 2부(§7).

### 이 구조는 어떻게 세우나 — 명시→반증→방어 (데이터 '도출' 아님)

> **핵심**: 위 화살표(의존 그래프)는 **데이터에서 도출하는 게 아니라 메커니즘으로 명시(specify)하고, 데이터로 반증·추정(constrain)하고, 민감도로 방어(defend)**한다. 데이터가 못 하는 건 "구조 생성"뿐이다.

**왜 데이터로 못 세우나 (세 겹의 벽)**: ① 노출=VKT라 8축이 동시에 찍힌 결합표본이 없음, ② marginal만으론 일관된 결합(DAG)이 무수히 많음(비식별), ③ 관측만으론 방향이 Markov 동치류까지만 결정. → 구조학습(PC·GES·NOTEARS) 적용 불가. **§2 조건부 3개가 "손지정"인 이유가 이것.**

**구조를 나눠 봐야**: (a) **그래프 골격**(어느 부모가 어느 블록을 조건화)=정성적 인과, 데이터로 도출 ❌ / (b) **조건부 수치** P_b(·|부모)=지지 소스면 추정 ✅. 못 하는 건 (a)뿐.

**(a)를 세우는 4개 비-데이터 근거**:

| 근거 | 정하는 것 | 예 |
|---|---|---|
| 인과 메커니즘·물리·법 | 화살표와 **방향** | `road_type→agent`(고속 보행금지=법), `road_type,weather→speed`(제동물리+규제) |
| 표준 taxonomy | 층 분해 | PEGASUS 6-layer / ASAM OpenODD (§14) |
| 구조적 0(hard rule) | forbidden | `highway 보행자=0` — 학습 아닌 법적 사실 |
| 전문가 elicitation | 모호 엣지 | 문서화된 가정 |

방향(orientation)은 **개입논증**이 준다: "고속도로를 지으면 참여자 구성이 바뀌지만(→), 보행자를 늘려도 도로가 고속도로가 되진 않는다(←아님)." 데이터가 못 주는 방향을 메커니즘이 고정.

**데이터의 정당한 역할 (생성 아님)**: ① 엣지 **반증** — 2-way marginal이 있으면 독립검정, 독립이면 엣지 삭제(§3-R recon `edge_max_tv`), ② 조건부 **추정**(골격 가정 후), ③ 조립 결과 **정합성 검증**(§11).

**수행 절차**:
```
1. 메커니즘·법·PEGASUS로 DAG 초안(부모→블록, 방향)   ← 사람(데이터 아님)
2. 구조적 0(forbidden) 하드룰 인코딩                ← 법·물리
3. recon 엣지-반증: 2-way 있는 곳만 독립검정→불필요 엣지 삭제  ← 데이터(§3-R)
4. 골격 고정 → SUPPORTED 소스로 조건부 추정, 나머지 손앵커   ← 데이터+전문가
5. P_ext 조립(§7)
6. 앵커 정합성 검증(§11.1) → 실패 시 2로 복귀           ← 데이터
7. 민감도 스윕(§11.2): 랭킹 강건→수용 / 불안정→데이터 보강  ← 방어
```
코드가 하는 건 3·4·5·6·7(recon·loader·§7·§11). **1·2만 도메인 판단.**

**담보는 진리값 아닌 강건성**: 구조를 "맞혔다"는 증명 불가 → 목표를 "구조 오차가 top-N 결정을 바꾸지 않는다"로 전환. §11 민감도가 안정이면 정확한 구조는 결정에 무관 → 충분. 불안정이면 그 엣지가 load-bearing → 데이터 보강 or 주장 축소. *구조는 발견이 아니라 명시하고 방어하는 대상.*

## 3. 소스별 조달 레시피 — 외부자료를 실제로 어떻게 끌어오나

> **왜 이 네 소스인가 — 임의 목록이 아니다.** 주행 장면 하나는 **서로 독립적으로 작동하는 네 물리 시스템**이 겹쳐 만들어지고, 각 시스템을 재는 **권위 기관이 하나씩** 대응한다(그래서 §2의 블록 독립 근사가 성립하고 따로 조달 가능):
>
> | 물리 시스템 | 정하는 것 | 기관 | 블록 · 없으면 깨지는 것 |
> |---|---|---|---|
> | **도로망** | 어디서·얼마나·얼마나 빠르게 | 국토부/KTDB | $w$·$P_2$·$P_4$ — **현실 눈금**(VKT 없으면 self-순환)·**심각도**(속도=에너지) |
> | **대기** | 맑음/비/눈/안개/노면 | 기상청 | $P_1$ — **악조건 꼬리**(눈·안개 과소수집 여부를 잴 기준) |
> | **도로 위 사람** | 누가·얼마나 붐비나 | 도로교통공단 | $P_3$ — **충돌위험 1순위 축**(VRU 노출); 제일 중요한데 데이터 제일 약함 |
> | **태양 위치** | 낮/밤 → 밝기 | 천문연 | $P_5$ — **지각저하 축 + 데이터 구멍 메우기**(`time_of_day` 전량 미관측을 천문 계산으로 복구) |
>
> 즉 각 블록은 "합치면 완전한 `P_ext(c)`가 되도록" 현실을 도메인별로 쪼갠 조각이고, 하나라도 빠지면 그 축의 과/소수집 진단이 불가능해진다.

각 블록: **① 데이터셋·포털 → ② 접근수단 → ③ 뽑을 컬럼 → ④ 집계 → ⑤ 산출 CSV(= compose.py 입력)**. 두 경로 택1:
- **자동(API)**: 대표 1년 원자료를 REST로 받아 pandas 집계. 갱신 쉬움. `data.go.kr` 무료 serviceKey 필요.
- **손전사(v0 권장)**: 각 기관 **연보 표**를 20~50행 옮겨적기. 반나절, 감사 명확. **v0는 손전사로 시작**하고 갱신 부담 생기면 API로.

한눈 지도:

| 블록 | 데이터셋(포털) | 접근수단 | 산출 CSV |
|---|---|---|---|
| $P_1$ weather·fog | 기상청 ASOS 시간자료 (data.kma.go.kr / data.go.kr) | CSV 다운로드 or `AsosHourlyInfoService` | `weather_P1.csv`, `fog_P1.csv` |
| $w(s)$·$P_2$·$P_4$ | 도로교통량 통계연보 (KTDB·통계누리 stat.molit.go.kr) | 연보 Excel/PDF (손전사) | `vkt_weight.csv`, `hourly_profile.csv`, `speed_P4.csv` |
| $P_3$ agent·density | 보행교통량조사(국가교통DB)+TAAS 보정 (taas.koroad.or.kr) | 연보 표 + 손앵커 | `agent_P3.csv`, `density_P3.csv` |
| $P_5$ lighting | 한국천문연 출몰시각 (data.go.kr) | `RiseSetInfoService` API | `lighting_P5.csv` |

> ⚠️ 아래 엔드포인트·파라미터는 대표 예시다. **serviceKey 발급·정확한 파라미터명은 포털 신청 후 확인.**

### $P_1$ — KMA weather·fog·road_surface
- **데이터셋**: 기상자료개방포털 `data.kma.go.kr` → 데이터 → *종관기상관측(ASOS) 시간자료*. 또는 API `apis.data.go.kr/1360000/AsosHourlyInfoService/getWthrDataList`.
- **접근**: 대표연도(예 2023) 전 지점(또는 대표 17지점) 시간자료. params `stnIds`(서울=108…), `startDt/endDt`(YYYYMMDD), `startHh/endHh`, `dataType=JSON`.
- **뽑을 컬럼**: `tm`(일시), `ta`(기온℃), `rn`(강수량mm), `vs`(시정m), 필요시 현상코드.
- **집계**: `(월 m, 시 h)`로 groupby → `rn>0 & ta>0 → rain` / `적설 or ta≤0 & rn>0 → snow` / `else clear`. fog = `mean(vs < 1000)`.
- **산출**:
```
# sources/weather_P1.csv          # sources/fog_P1.csv
month,hour,weather,prob           month,hour,fog_present_prob
1,8,clear,0.71                    1,8,0.03
1,8,rain,0.05                     7,6,0.11
1,8,snow,0.24
```
- **함정**: `rn` 결측(-9)·미소강수 처리. road_surface는 여기서 안 나옴 → §5-2에서 weather로 파생.

### $w(s)$·$P_2$·$P_4$ — KTDB/국토부
- **데이터셋**: 국토부 *도로교통량 통계연보*(상시·수시 교통량조사), 등급별 통행속도. 통계누리 `stat.molit.go.kr`, KOSIS, KTDB 자료실.
- **접근**: 연보 Excel 표 **손전사**(등급 5행이면 충분). 시간 프로파일은 상시조사지점 24h 시간교통량비.
- **뽑을 값**: 등급별 연장(km)·평균일교통량(AADT)·등급별 시간교통량비·등급별 평균속도(±표준편차).
- **집계**: `VKT(k) = 연장 × AADT × 365` → 정규화(= road_type marginal, $w$에 흡수). 속도는 정규근사로 `low/mid/high` 구간 확률, 강수 시 −10~15% 하향(계수 손지정).
- **산출**:
```
# vkt_weight.csv    # hourly_profile.csv        # speed_P4.csv
road_type,vkt_share road_type,hour,traffic_share road_type,weather,speed,prob
highway,0.28        highway,8,0.058              highway,clear,high,0.62
urban,0.41          urban,8,0.071               highway,rain,high,0.40
```
- **함정**: **연장 아닌 VKT(통행량) 가중** 필수. 터널은 등급 통계에 없음(§5-3).

### $P_3$ — KoROAD/보행량 (가장 약함, 솔직히 표기)
- **데이터셋**: 보행 *노출*은 TAAS 사고통계로 못 구함(사고≠노출). 국가교통DB 보행교통량조사·도시교통 실태조사·지자체 보행량이 원천. 부족하면 **손앵커 + TAAS 도로유형별 사고분포로 보정**.
- **접근**: v0 = 도로유형×시간대 보행자 등장확률 손지정(urban 주간↑, highway=0), density는 V/C비(교통량/용량) 또는 AADT 등급 매핑.
- **산출**:
```
# sources/agent_P3.csv                # sources/density_P3.csv
road_type,hour,agent_type,prob        road_type,hour,density,prob
urban,8,cars_only,0.55                urban,8,dense,0.45
urban,8,mixed,0.30                    highway,8,sparse,0.20
urban,8,pedestrians,0.12
highway,8,pedestrians,0.00            # forbidden = 0
```
- **함정**: 값이 손앵커라 §8 **민감도 스윕 필수**. 여기가 랭킹을 가장 크게 흔든다.

### $P_5$ — KASI lighting (출몰 → 밝기)
- **데이터셋**: 공공데이터포털 *한국천문연구원 출몰시각 정보* `apis.data.go.kr/B090041/openapi/service/RiseSetInfoService/getAreaRiseSetInfo`.
- **접근**: 월 대표일 × 지역 → `sunrise`,`sunset`. params `locdate`(YYYYMMDD), `location`(지역명).
- **집계**: `day = sunrise~sunset`, `dusk_dawn = ±30분`, `night = else` → §5-4 `(time,road_type)→밝기` 표를 곱해 최종 $P_5$.
- **산출**:
```
# sources/lighting_P5.csv  (출몰 × §5-4 매핑 합성)
road_type,hour,lighting,prob
urban,2,moderate,1.0        # 야간 도심 = 가로등
rural,2,poorly_lit,1.0
urban,13,well_lit,1.0
```
- **함정**: 일출몰은 계절 이동 → `month`도 조건에 넣거나 월중값 사용.

### End-to-end 한 흐름 (weather 블록)
```
ASOS 원자료 CSV(수백만행)
  └─ pandas groupby(month,hour) + 분류함수 → prob 정규화
     └─ sources/weather_P1.csv (수백행)          ← 감사 가능 원장
        └─ compose.py 로드: P1[(m,h)] = {clear:.7, rain:.05, snow:.24}
           └─ MC: np.random.choice(['clear','rain','snow'], p=[...])
```

## 3-R. 소스 정찰(recon) — 대량 조달 전 블록 게이팅

> **왜 먼저인가**: §2 조립 구조(어떤 조건부가 존재하나)는 **데이터가 못 주는 prior**다. 공개 소스는 marginal·저차 조건부만 주므로 결합에서 의존 그래프를 *학습*하는 건 비식별(non-identifiable) — §2 손지정 조건부 3개가 애초에 손지정인 이유. 그래서 recon은 구조를 **만들지 않고**, 각 소스 샘플을 프로파일링해 §2 블록이 실제로 채워지는지 **게이팅·반증**만 한다. 대량 손전사(§6) 이전에 스키마 착오를 잡는 값싼 단계.

- **입력**: `raw/<source>/*.csv|json` — 각 소스에서 손수 export한 대표 샘플 1개(어차피 §3에서 만질 자료). 스크래핑·PDF파싱 안 함.
- **처리**: 컬럼·granularity·카테고리 어휘 추출 → `loader.BLOCKS`(=§2 prior)와 대조.
- **출력**: `recon/availability.json`(기계) + `recon/recon_report.md`(감사 매트릭스).
- **게이트 5종**:

| 게이트 | 뜻 | 다음 조치 |
|---|---|---|
| `SUPPORTED` | 소스가 needs_key 해상도로 지지 | §6 실값 전사 |
| `LOW_RES` | 소스가 더 거침(예: 월만·시 없음) | 조건키 trim or 상위 집계 |
| `HAND_ANCHOR` | 축 자체가 데이터에 없음(P₃ 보행노출·P₄ weather차원·P₅ 밝기) | §11 민감도 스윕 대상 |
| `INSUFFICIENT` | 컬럼 미검출 | 컬럼명 확인 |
| `NOT_OBTAINED` | 샘플 없음 | 소스 확보 |

- **엣지 반증(옵션)**: 소스가 (부모, 축) 2-way 표를 주면 부모별 조건부 분포의 max Total-Variation을 재서 `<ε(=0.05)` 이면 그 조건부를 **삭제 후보**(marginal 단순화)로 표기. *구성이 아니라 falsify* — §2 손지정 조건부를 데이터로 흔드는 유일 지점.
- **순서**: §3 소스 확인 → **recon 게이트** → (구조 trim) → §6 값 전사 → `loader.py` 계약 검증.
- **self-check**: `python3 recon.py`(합성 픽스처로 게이트 분기 검증). 근거: §14 "코어를 소스-네이티브 해상도로", [coverage-vs-sufficiency.md](../../../docs/wiki/evaluation/coverage-vs-sufficiency.md) L74-80(축 부재는 exposure 아닌 criticality).

## 4. 층화 결정 — v0는 전국, region은 검증 후

**region×season 층화를 v1에서 즉시 하지 말 것.** 17지역×4계절×24시×5도로 ≈ 8,160층은 대부분 전국 marginal을 지역으로 쪼갠 가짜 해상도. **v0 = `(계절 m × 시간 h × 도로 k)` = 4×24×5 = 480층.** region은 *weather 앵커가 검증에서 틀릴 때만* 추가($P_1$만 지역화; 영동 폭설·해안 안개는 전국평균으로 못 잡음).

→ 이 결정이 위 §3 조달량을 정한다: v0에선 KMA를 대표지점 월×시 집계, region 컬럼 생략.

## 5. 카테고리 매핑 — 최대 리스크, 표를 명시

전체를 흔드는 지점(coverage-vs-sufficiency.md L105). `mapping.yaml` 하나에 몰고 **사람이 편집·검토**. 자동화 금지(감사 불가). 값은 [odd_schema.md](../odd_schema.md) 기준.

**5-1. weather / fog** (KMA → ODD)
```
강수없음         → weather=clear
비·이슬비·소나기  → weather=rain
눈·진눈깨비      → weather=snow
안개(시정<1km)   → fog=present     # 독립 축, weather와 병존 가능
```

**5-2. road_surface — 날씨 파생 + 지속성 (계산값)**
weather-파생 가능한 건 {dry,wet,snow}뿐. unpaved·gravel·dirt는 도로 속성(road_type=rural 비포장 지분). v0는 {dry,wet,snow}로 병합.
```
snow   if precip=snow  or (T≤0 & precip>0)
wet    if precip=rain
dry    otherwise
wet_fraction(h) ≈ min(1, rain_freq(h) × ρ)   # ρ = 젖음 지속계수
# ρ=1.7 초기값. 노면 건조시간은 물리 튜닝 노브 —
# 검증에서 wet 비중이 self와 어긋나면 여기 먼저 조정.
```

**5-3. road_type** (국토부 등급 → ODD)
```
고속국도                     → highway
일반국도                     → national_road
특별·광역시도, 시군도(도심)   → urban
지방도·군도(시외)            → rural
터널구간                     → tunnel   # ⚠️ KTDB에 터널 태그 없음
```
⚠️ **tunnel이 매핑 최대 구멍**: 등급 통계로 안 나옴. v0는 터널 연장 통계로 상수 주입하거나 `unknown`으로 두고 self 비교에서 제외. 억지 매핑 금지.

**5-4. lighting — day/night을 밝기로 재매핑** (가장 미묘)
KASI는 day/dusk/night만, 우리 축은 밝기(`well_lit/moderate/poorly_lit`). 조명 인프라 차이로 $(time,road\_type)$ 조건부:
```
day        × any             → well_lit
dusk_dawn  × any             → moderate
night      × urban(가로등)    → moderate
night      × highway(부분조명) → 0.5 moderate / 0.5 poorly_lit
night      × national/rural   → poorly_lit
```
이게 **미관측 `time_of_day`(전체 101,741 파일에서 없음)를 밝기로 복구**하는 핵심. 검증은 §8에서 self VLM `lighting` marginal과 직접 대조(같은 축).

**5-5. agent·density / speed**: KoROAD 유형별 보행자비 → `cars_only/mixed/pedestrians/cyclists`; V/C비 → `sparse/moderate/dense`; 등급 속도분포 → `low/mid/high`. 고속=보행자 0은 표의 0으로.

## 6. 조달 산출물 & CSV 계약

1부의 결과물 = 아래 CSV 세트 + 매핑. **각각은 "조합"이 아니라 축 하나짜리 낱개 분포**(=재료)다. 조합은 §7에서 이것들을 엮어야 나온다. 이게 2부 파이프라인의 유일한 입력.
```
exposure/
  sources/weather_P1.csv  fog_P1.csv
          vkt_weight.csv   hourly_profile.csv  speed_P4.csv
          agent_P3.csv     density_P3.csv      lighting_P5.csv
  mapping.yaml            # 기관 카테고리 → ODD 값 (리스크 표면, 사람 편집)
```

### 재료 8장 — 채워진 예시 (v0, 전국·480층 가정)

각 표를 "이 조건이면 값이 이 확률"로 읽는다. 숫자는 형식 예시(실제 조달값 아님).

**① `weather_P1.csv`** — (월,시)마다 맑음/비/눈 (합=1). 기상청 ASOS 집계.
```
month,hour,weather,prob
1,8,clear,0.71     # 1월 아침: 눈 비중 큼
1,8,rain,0.05
1,8,snow,0.24
7,8,clear,0.82     # 7월 아침: 눈 0, 비 늘어남
7,8,rain,0.18
7,8,snow,0.00
```

**② `fog_P1.csv`** — (월,시)마다 안개 있을 확률 (독립 축, 합 제약 없음). 시정<1km 비율.
```
month,hour,fog_present_prob
1,7,0.06           # 겨울 새벽 안개
7,6,0.11           # 여름 새벽 복사안개 최다
13,14,0.01         # 한낮 거의 없음
```

**③ `vkt_weight.csv`** — 도로유형별 연 주행거리 지분 (합=1). = road_type marginal. 국토부 VKT.
```
road_type,vkt_share
highway,0.28
national_road,0.16
urban,0.41         # 도심이 주행 최다
rural,0.13
tunnel,0.02        # ⚠️ 별도 조달, 없으면 제외
```

**④ `hourly_profile.csv`** — 도로유형별 24시간 교통량 분포 (도로별 합=1). 상시조사지점.
```
road_type,hour,traffic_share
urban,8,0.071      # 도심 출근 피크
urban,3,0.008      # 새벽 한산
highway,18,0.065   # 고속 퇴근 피크
```
> ③×④ = 층 가중 $w(m,h,k)$의 뼈대(§7 strata.py). 계절 m은 ①의 월별 편차로 흡수하거나 별도 계수.

**⑤ `speed_P4.csv`** — (도로,날씨)마다 저/중/고속 (조건별 합=1). 강수 시 하향. 등급별 속도조사.
```
road_type,weather,speed,prob
highway,clear,high,0.62
highway,clear,mid,0.35
highway,clear,low,0.03
highway,rain,high,0.40    # 비 오면 고속 비중↓
highway,rain,mid,0.52
highway,rain,low,0.08
urban,clear,low,0.55      # 도심은 원래 저속 우세
```

**⑥ `agent_P3.csv`** — (도로,시)마다 참여자 유형 (조건별 합=1). KoROAD+보행량. **forbidden=0**.
```
road_type,hour,agent_type,prob
urban,8,cars_only,0.55
urban,8,mixed,0.30
urban,8,pedestrians,0.12
urban,8,cyclists,0.03
urban,3,pedestrians,0.02   # 심야 보행자 급감
highway,8,cars_only,1.00
highway,8,pedestrians,0.00 # 고속 보행자 금지 = 0
```

**⑦ `density_P3.csv`** — (도로,시)마다 sparse/moderate/dense (조건별 합=1). V/C비.
```
road_type,hour,density,prob
urban,8,dense,0.45         # 출근 정체
urban,3,sparse,0.80
highway,8,moderate,0.50
```

**⑧ `lighting_P5.csv`** — (도로,시)마다 밝기 (조건별 합=1). KASI 출몰 × §5-4 재매핑 결과.
```
road_type,hour,lighting,prob
urban,13,well_lit,1.00     # 주간
urban,2,moderate,1.00      # 야간 도심=가로등
rural,2,poorly_lit,1.00    # 야간 시골=암흑
highway,2,moderate,0.50    # 야간 고속=부분조명
highway,2,poorly_lit,0.50
```

`mapping.yaml`은 위 값들이 어떻게 나왔는지의 규칙(§5): `강수없음→clear`, `고속국도→highway`, `night×rural→poorly_lit` 등. **표는 결과, yaml은 근거·감사용.**

### CSV 계약
- 모든 블록 파일 = **long tidy, 마지막 컬럼 `prob`**, 같은 condition_key 그룹 내 `prob` 합 = 1(②만 독립축이라 예외).
- compose.py는 *파일명 → 블록·조건키 매핑*만 앎. **소스 갈아끼우기 = CSV 교체 한 번**(코드 무변경). 자동/손전사/버전갱신을 같은 인터페이스로 흡수.
- **이 8장만으로는 "고속∧눈∧야간 몇 %"를 못 답한다** — 낱개 분포라서. 엮는 건 §7.

---
---

# 2부 · 주요 ODD 조합 선정

**목표**: 1부 CSV로 `P_ext`를 조립하고, 이를 근거로 ① 핵심 운행영역, ② 수집 편향, ③ 수집 타겟을 뽑는다.

## 7. P_ext 조립 — VKT-가중 층화 혼합 (정확 enumerate)

$$
P_{\text{ext}}(c) \;=\; \sum_{s} w(s)\;\prod_{b\in\text{blocks}} P_b\big(c_b \mid \text{pa}(b),\,s\big)
$$

- $s=(m,h,k)$(v0), $w(s)\propto\text{VKT}(s)$. 층이 조건을 고정하므로 블록끼리 층 내부 독립 근사해도 상관이 산다(상관은 $w$가 나른다).
- **MC 아님 — 정확 enumerate.** 조합공간이 ~7,776셀(축 cardinality 곱)뿐이라 표본추출할 이유가 없다. 층×블록 곱을 닫힌형으로 합산 → MC 표본오차(§13-R 게이트 C) 원천 제거. PGM 라이브러리 금지, dict 곱셈만:
```
w(s) 정규화                              # 480개 층 = vkt_weight × hourly_profile
for s in 480층:
  for c in 조합공간:                      # 곱분포를 직접 합산
    P_ext[c] += w(s) · P₁(weather,fog|m,h) · P₄(speed|k,weather)
                     · P₃(agent,density|k,h) · P₅(lighting|h,k)
                     · [road_surface = derive(weather,T,ρ)]   # §5-2 결정적
```
> **신뢰 스코프(§13-R):** speed·agent·lighting은 HAND_ANCHOR라 이 축을 고정한 full 조합의 P_ext는 손앵커 prior를 문다. **selection에 쓰는 신뢰 P_ext는 손앵커 3축을 marginalize out 한 5축 부분공간** `{road_type, weather, fog, road_surface, density}` 위에서 정의한다. 조건부 표만 갈면 구조 불변.

## 8. 선정① — Exposure 누적 절단 (핵심 운행영역)

`P_ext` 내림차순 → **누적 95%/99% 도달 최소 조합집합** = 핵심 운행영역. 리포트: **"상위 N조합 = 주행의 X%."**
- 이게 "1억 조합을 현실 빈도로 줄세운다"의 실행. self와 무관하게 *세상*이 어디에 몰려있나를 먼저 확정.

## 9. 선정② — self 대조 편향맵 (Gap-4 수치화, 헤드라인)

$P_{\text{self}}$ **소유자 = EXP-003 phase0 `output/odd_coverage.json`**(10만 클립 관측분포, crosswalk `_to_compat_v2` 포함). phase0_2은 이걸 조달만, 재집계 금지(§12-R 재사용).

**과수집과 시급을 같은 지표로 재지 않는다** — 신뢰영역이 정반대라(§13-R). 둘로 분리:

**(a) 과수집/충분 판정 — 머리, 신뢰 O.** 고질량 조합에서 비율이 안정:
$$
r(c)=\frac{P_{\text{self}}(c)}{P_{\text{ext}}(c)},\qquad \mathrm{KL}(P_{\text{self}}\Vert P_{\text{ext}})
$$
$r(c)\gg1$ → **과수집**(중복·예산낭비, 예: 맑음×도심×주간). KL 한 숫자 = 전체 편향 크기.

**(b) 과소수집/시급 순위 — 꼬리, 나눗셈 금지.** $r=P_{\text{self}}/P_{\text{ext}}$는 꼬리에서 $P_{\text{self}}{\approx}0$으로 나눠 노이즈/노이즈가 된다(§13-R). 대신:
$$
\text{urgency}(c) = P_{\text{ext}}(c)\ \ \text{s.t. }P_{\text{self}}(c)<\epsilon\quad(\text{분자 단독, 분모 floor})
$$
"노출 크고 + 우리가 거의 없음"을 P_ext 질량 순으로. **해상도도 낮춘다** — full 8조합이 아니라 2~3필드 marginal/pairwise에서 순위(개별 고차원 셀은 카운트≈1이라 방어 불가).

- 적용 범위: 위 (a)(b) 모두 **§13-R 신뢰 부분공간(5축)** 안에서만. 밖은 §10 criticality·§11 스윕으로.
- "정상 과다 71%" 주관 진술 → **현실 앵커 대비 셀별 과/소 표집 배수**로 치환.

## 10. 선정③ — 희귀-위험 보강 (exposure의 사각지대)

⚠️ **exposure 누적영역은 안전-critical 희귀조합을 포함하지 않는다**(저빈도라 상위에 안 듦). exposure에 전체를 기대하면 안 됨.
$$
\text{최종 타겟} = (\text{§8 exposure 누적영역}) \;\cup\; (\text{criticality 상위 희귀조합})
$$
- criticality는 클립 없이 전체 공간에 정의 → [coverage-vs-sufficiency.md](../../../docs/wiki/evaluation/coverage-vs-sufficiency.md) L111-119 손 위험표. 미관측 위험조합은 [situation-coverage-grid.md](../../../docs/wiki/evaluation/situation-coverage-grid.md) 확률 외삽.

## 11. 검증 프로토콜 (손표는 주관적 → 필수)

1. **현실 앵커**: `clear×urban×cars_only×day`가 최상위? snow 비중이 전국 적설일수와 일치? highway 보행자≈0? night 밝기 분포가 self VLM `lighting` marginal과 정합(§5-4 직접 검증)?
2. **민감도**: 손지정 조건부 3개 ±30% 흔들어 **top-N 랭킹 Spearman 안정성**. 뒤집히면 앵커 보강.
3. **교차 소스**: KTDB·KoROAD 교통량 겹침 구간 일치.
4. **불확실성(lazy)**: 각 조건부에 Dirichlet 두고 MC로 매핑 오차 전파 → 랭크 CI. v0는 ±30% 스윕으로 대체.

## 12. 구현 스켈레톤 (파일 6개)

```
exposure/
  raw/<source>/*     # 1부: recon 입력 — 소스 대표 샘플 (사람 export)
  recon.py           # 1부: §3-R 소스 정찰·블록 게이팅 → recon/*  (조달 전 실행)
  sources/*.csv      # 1부 조달 원장 (감사 가능)
  mapping.yaml       # 기관 카테고리 → ODD 값 (사람 편집)
  loader.py          # 1부: §6 CSV 계약 로더·검증  (2부 진입점 load_all)  [구현됨]
  strata.py          # §7 w(s)   (480층)
  compose.py         # §7 정확 enumerate → P_ext (5축 부분공간)  [미구현]
  analyze.py         # §8·§9 누적절단 + (a)과수집비율 (b)시급 P_ext순  [미구현]
  validate.py        # §11 앵커+민감도  ← 런타임 self-check  [미구현]
```
runnable check = `validate.py`: 앵커 3개를 `assert`(clear×urban×day 최상위 / highway 보행자<ε / snow비중 KMA±20%). 손표가 깨지면 여기서 터짐.

## 12-R. 구현 gap & 축 정합 — 목표(중요조합 선별) 대비 현 스코프

목표 파이프라인 = **① 외부API→P_ext 중요조합 → ② 보유 P_self 조합구성 → ③ 충분/시급 순위.** 현 상태 대비 gap:

| 단계 | 필요 | 현재 | 보완 |
|---|---|---|---|
| ① P_ext | §7 compose | design만, 입력 CSV placeholder(전 블록 NOT_OBTAINED) | **[P0] raw/ 조달→sources 실전사** ▸ [P2] `compose.py`(enumerate) |
| ② P_self | 10만 클립 집계+crosswalk | **phase0 `odd_coverage.json`에 구현됨** (단 top100만 저장, 꼬리 없음) | [P1] **phase0 crosswalk 함수 import**(`_to_compat_v2`·`_flatten_final`)해 phase0_2이 카운트 — phase0 무수정 |
| ③ 비교·순위 | §8/§9/§10 | design만 | [P2] `analyze.py`(§9 (a)비율·(b)P_ext분자, §13-R 스코프) |

**손대지 마 (역할 완결):** `loader.py`·`recon.py`·`mapping.yaml`, **그리고 phase0 전체.**

**진짜 1순위는 코드가 아니라 데이터(P0).** 전 블록 미확보라, ①③를 지어도 placeholder 위에서 돈다.

**② P_self 무침습 재사용 (phase0 무수정).** `odd_coverage.json`은 top100만 저장 → 시급(꼬리) 조합이 없다. 하지만 phase0를 고칠 필요 없음: `step_a_odd_coverage.py`는 `__main__` 가드가 있어 **import해도 파이프라인이 안 돌고**, crosswalk가 모듈 레벨 함수라 그대로 재사용 가능.
```python
from phase0.step_a_odd_coverage import _to_compat_v2, _flatten_final   # 위험 로직 단일 출처
P_self = Counter()
for f in ODD_DIR/*.json:
    rec = _to_compat_v2(_flatten_final(json.load(f)['odd_final']))
    P_self[tuple(rec[k] for k in AXES)] += 1        # phase0_2 5축으로 카운트
```
이건 "재집계 금지"에 안 걸린다 — 금지 대상은 *crosswalk 복붙 재구현*(발산 위험). **같은 함수 호출은 복제가 아니라 재사용**: 위험한 매핑은 phase0에 단일 출처로 남고, phase0_2은 자기 축으로 카운트만(축 정합도 여기서 처리).

### 축 정합 — 가장 미묘한 함정 (P_ext ↔ P_self가 다른 crosswalk에서 옴)

P_ext는 `mapping.yaml`(기관→ODD), P_self는 phase0 `_to_compat_v2`(태거→공통축). **두 crosswalk가 동일 축·값 집합에 착지해야** 비교가 성립. 어긋나면 "충분/시급"이 조용히 틀린다:

| 축 | 불일치 | 처리 |
|---|---|---|
| fog | P_ext=독립축 / phase0 v2=weather에 병합{clear,rain,snow,fog} | **독립축으로 통일**(fog_P1이 독립이라 더 정확) |
| road_surface | P_ext=weather에서 ρ=1.7 규칙 *유도* / P_self=태거 *독립 관측* | 생성과정 상이 → 비교 시 "규칙 vs 관측" 혼입, **한계로 표기** |
| speed | P_ext=P4_speed 축 존재 / phase0 compat 스키마에 speed 없음(연속) | P_self측 **binning(low/mid/high) 추가** 필요 |
| unknown | phase0=값으로 보존 / P_ext=unknown 질량 없음 | 비교 전 **unknown 클립 제외 후 재정규화** |

## 13. v1 최소 vs 확장 트리거

| 요소 | v1 (지금) | 확장 조건 |
|---|---|---|
| 층화 | 전국 (m×h×k), 480층 | weather 앵커 실패 → region 추가($P_1$만) |
| road_surface | {dry,wet,snow} | unpaved 비중 필요 → rural 세분 |
| tunnel | unknown/제외 | 터널 연장 통계 확보 시 |
| 불확실성 | ±30% 스윕 | 랭크 뒤집힘 → Dirichlet MC |
| ρ(젖음 지속) | 1.7 고정 | wet 비중 self와 어긋남 → 튜닝 |

## 13-R. P_ext 신뢰구간 — 어떤 조합을 믿을 수 있나 (스코프)

**핵심**: `P_ext(c)`를 조합 전체에 대해 균일하게 신뢰하면 안 된다. 편향맵(§9)·시급 순위가 표본잡음에 지배되는 구간이 있다. "신뢰"는 단일 임계가 아니라 **서로 독립적인 3개 게이트의 교집합**으로 정의한다 — 각각이 다른 불확실성 원천을 막기 때문.

$$P_{\text{ext}}(c)=\sum_s \underbrace{w(s)}_{}\;\underbrace{\textstyle\prod_b P_b(c_b\mid \text{pa}(b),s)}_{\text{B: 입력표 오차}}\quad(\text{C: MC 추정오차})$$

| 게이트 | 막는 원천 | 정의 | 표본↑로 감소 |
|---|---|---|---|
| **C. MC** | 표본오차 | 곱 분포를 **정확 enumerate**(공간 ~7,776셀뿐 → MC 불필요)로 **제거**. 굳이 MC면 기대카운트 $N\cdot P_{\text{ext}}(c)\ge 50$ | ✅ (제거 가능) |
| **A. 축** | 손앵커·독립근사 편향 | c가 **손앵커 축(P4_speed·P3_agent·P5_lighting)을 고정하지 않을 것** | ❌ 안 줄어듦 |
| **B. 해상도** | 입력 셀 추정오차 | 블록표에 **Dirichlet 사후** 얹어 조합별 신뢰구간 산출 → **상대폭 $CI/P_{\text{ext}}<\tau$**(예 0.3) | △ 소스 표본 의존 |

**게이트 A의 냉정한 귀결 — full 조합엔 완전신뢰구간이 없다.** 8블록 중 3개가 HAND_ANCHOR(데이터가 원리적으로 못 주는 손값)이고, **모든 8필드 full 조합은 speed·agent·lighting을 반드시 하나씩 포함**한다. 즉 full 해상도 P_ext는 예외 없이 손앵커 prior를 물고 있다. 신뢰 가능한 건 **손앵커 축을 marginalize out 한 부분공간뿐**:

- ✅ 데이터 방어 가능: `{road_type, weather, fog, road_surface, density}` 상의 조합
- ❌ 손저작 오염: speed / agent / lighting 을 고정하는 순간 (값은 나오되 근거는 손 — §11 스윕 대상)

**조작적 정의**:
> `P_ext(c)` 신뢰 ⟺ (A) c가 손앵커 축을 고정 안 함 ∧ (B) Dirichlet 전파 상대 신뢰폭 $<\tau$ ∧ (C) 정확 enumerate(또는 기대카운트 ≥ 50).

**절차**: ① MC 버리고 곱 분포 정확 enumerate → ② 블록표 Dirichlet로 조합별 CI(§13 "랭크 뒤집힘→Dirichlet MC" 트리거의 상시화) → ③ 손앵커 3축 marginalize → ④ CI 상대폭 $<\tau$ 인 조합만 "신뢰 P_ext" 라벨. 꼬리는 CI가 넓어 자동 탈락.

**스코프 결론**: 이 소스·이 데이터 구성에서 P_ext가 정직하게 지지하는 최대 범위 = **손앵커 3축을 뺀 5축 부분공간의 고질량 조합**. → §8 누적절단·§9 편향맵의 **과잉/충분 판정은 이 구간에서 신뢰**, 그 밖(특히 고차원 꼬리의 "시급" 순위)은 스윕·criticality로 넘긴다. 시급 신호는 $R=P_{\text{ext}}/P_{\text{self}}$의 나눗셈(꼬리에서 노이즈/노이즈) 대신 `P_self<임계`에서 **P_ext 분자 단독**을 우선순위로.

## 14. 범용화 — 기준스키마 R* + crosswalk 아키텍처

**동기**: 이상적으로는 외부자료로 만든 노출·중요도를 *특정 ODD에 종속되지 않게* 한 번 만들고, 목표 ODD가 무엇이든 **연결고리(crosswalk)**로 갈아끼우고 싶다. 이건 표준 "canonical model + adapter" 패턴(통계 crosswalk: ISCO·ICD 버전변환 / AV: PEGASUS 6-layer·ASAM OpenODD)이고 **타당하다 — 단 한 개념을 바로잡고 세 한계를 받아들이는 조건에서.**

**바로잡을 개념 — 재사용 단위는 "주요 조합 리스트"가 아니다.** 중요도 `P_ext×criticality`는 축·값 구간에 *상대적*으로만 정의된다(좌표계 없는 조합은 없음). 값을 병합하면 순위가 승격/강등되므로 **top-N은 스키마 불변이 아니다.** → **재사용 불변량은 최대해상도 기준스키마 $R^*$ 위의 `P_ext(R*)`·`crit(R*)`(분포·장 그 자체)**, "주요 조합"은 목표 $T$로 투영 후 *재랭킹*한 파생물이다.

```
L0  sources → mapping.yaml(institution→R*) → P_ext(R*)·crit(R*)   # 재사용 코어 (비싼 부분, 1회)
L1  crosswalk_T.yaml : R*→T  (결정적 coarsening, 값 그룹핑)        # 목표 스키마당 한 장
L2  project(marginalize) + re-rank → T의 주요 조합                 # 함수 하나
```
투영은 확률 합산: $P^{T}_{\text{ext}}(c)=\sum_{r\in\text{preimage}(c)} P^{R^*}_{\text{ext}}(r)$. **성립 조건: $T$가 $R^*$의 coarsening(더 거칠거나 같음)일 때만.**

**이득(정직)**: 진짜 위험한 건 institution→R* 매핑(§5). 이걸 $R^*$에서 **한 번** 하면 이후 어떤 ODD가 와도 R*→T crosswalk(순수 ODD-side, 결정적) 한 장이면 끝 — **위험한 매핑은 amortize, 새 스키마 비용은 값-그룹핑 표 한 장.**

**원리적 한계 (엔지니어링으로 못 넘음)**:

| 한계 | 내용 |
|---|---|
| 해상도 상한 | $R^*$보다 세밀한 $T$는 불가(정보가 R*에 없음 → 재조달만이 답) |
| 축 부재(C그룹) | occlusion·scene_ambiguity 등은 어떤 기관도 안 잼 → R*에 없음, 어댑터로 못 만듦(→ criticality 담당) |
| 비-중첩 구간 | $T$ 경계가 R* 경계를 가로지르면 "구간 내 균등" 가정 필요 → 근사오차. 무손실은 *중첩 구간*만 |
| 시간 drift | 노출은 연·지역별 변동 → R* 주기적 재조달 필요 |

→ **"범용"은 $R^*$의 해상도·보유축 안에서만 참.** 그 밖은 어댑터가 아니라 새 조달.

**실전 권고 (지금 뭘 지을지 — YAGNI)**: ODD가 하나뿐이라 완전한 어댑터 *프레임워크*는 speculative. 대신 거의 공짜인 laziest 경로 —
1. **P_ext를 소스-네이티브 해상도(=$R^*$)로 유지**, 우리 ODD로 *미리 병합하지 말 것*(병합은 마지막에; 오히려 작업 덜 듦).
2. ODD 접속을 **명시적 crosswalk 파일**로(어차피 §5에서 필요 — 공짜).
3. 어댑터 엔진 = marginalization 함수 하나(수십 줄). 프레임워크 금지.
4. **두 번째 스키마가 실제 나타날 때** 일반화(crosswalk 한 장 추가).

즉 *"어댑터블하게 설계하되 어댑터 레이어는 아직 짓지 않는다."* P_ext를 이름있는 축·값의 결합객체로만 두면 투영은 나중에 trivial.

> **판정**: 개념 타당 ★★★★★ / 범용 실현도 ★★★★☆(exposure 부분공간+R* 해상도 내) / 지금 착수가치 ★★★☆☆(코어를 소스-네이티브로 두는 것만 즉시, 어댑터 일반화는 2번째 스키마까지 보류). 최대 오해: "주요 조합을 먼저 고정" → 실제 불변량은 **분포·criticality 장**, 주요 조합은 투영 후 재랭킹 산물.

---

**한 줄 요약**: **1부**에서 KMA·KTDB·KoROAD·KASI 연보/API를 블록별 CSV로 조달하고(가중치는 VKT), **2부**에서 VKT-가중 층화 혼합을 **정확 enumerate**해 `P_ext`를 (손앵커 3축 뺀 5축 부분공간에서) 조립 — ① 핵심 운행영역 누적절단, ② P_self(phase0 `odd_coverage.json`) 대조로 **(a) 과수집=비율 / (b) 시급=P_ext 분자** 분리 산출, ③ 희귀-위험 union으로 주요 ODD 조합을 선정한다. 최대 리스크는 `mapping.yaml`(핫스팟 tunnel·lighting 재매핑)과 **P_ext↔P_self 축 정합**(§12-R), 가장 약한 블록은 $P_3$(보행 노출).

## 관련 문서
- [coverage-vs-sufficiency.md](../../../docs/wiki/evaluation/coverage-vs-sufficiency.md) — 상위 프레임(Q1-B Exposure 축, criticality 손 위험표)
- [coverage-metrics-scenario-database.md](../../../docs/wiki/evaluation/coverage-metrics-scenario-database.md) — de Gelder ODD/Criticality Coverage
- [situation-coverage-grid.md](../../../docs/wiki/evaluation/situation-coverage-grid.md) — 미관측 조합 확률 외삽
