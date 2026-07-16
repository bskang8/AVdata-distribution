# EXP-003 Phase 1 — Exposure 조달 실행기록 (RESULTS.md)

> **이 문서의 성격:** design.md(=계획)·README.md(=스크립트 작동법)와 별개로, **실제로 뭘
> 돌렸고 API가 뭘 뱉었고 지금 어디까지 왔나**를 담는 실행기록·현황 대장. 생성물(recon_report,
> availability.json, loader 출력)은 베끼지 않고 **참조**한다 — 최신값은 항상 그 파일이 정답.
> 매 조달 후 갱신할 곳은 §0 현황표·§3 한계대장·§4 결정로그 뿐.
>
> **마지막 실행:** 2026-07-16 · 1부(recon 8블록·loader 계약 통과) + 2부 골격 전 체인 구축
> (compose→pself→analyze→validate→criticality→sweep, `run_all.py`).

---

## 0. 현황 한눈에 — 블록 × 파이프라인 단계

파이프라인: **fetch(API)** → `raw/` → **recon(게이팅)** → **transcribe(전사)** → `sources/` → **loader(계약검증)**

| 블록 | 소스 | recon 게이트 | raw 조달 | sources 전사 | loader |
|---|---|---|---|---|---|
| P1_weather | KMA ASOS | SUPPORTED | ✅ 대량(asos_hourly 82MB) | ✅ **실전사**(288칸, 겨울 80칸 상속) | ✅ 통과 |
| P1_fog | KMA ASOS | SUPPORTED | ✅ 대량(위와 동일) | ✅ **실전사**(288칸) | ✅ 통과 |
| w_vkt | KTDB itmsh | SUPPORTED ⚠️2/4 | ✅ 실데이터(2등급) | ✅ **실전사** | ✅ 통과 |
| w_hourly | KTDB itmsh | SUPPORTED ⚠️2/4 | ✅ 실데이터(2등급) | ✅ **실전사** | ✅ 통과 |
| P4_speed | KTDB(손앵커) | HAND_ANCHOR | — | 손앵커 예시 | ✅ 통과 |
| P3_agent | KoROAD(손앵커) | HAND_ANCHOR | — | 손앵커 예시 | ✅ 통과 |
| P3_density | KTDB(손앵커) | HAND_ANCHOR | — | 손앵커 예시 | ✅ 통과 |
| P5_lighting | KASI(손앵커) | HAND_ANCHOR | — | 손앵커 예시 | ✅ 통과 |

**요약:** 데이터 블록 4개(KTDB w_vkt·w_hourly, KMA P1_weather·P1_fog) **모두 실데이터 전사
완료**. 단 KTDB는 2/4 등급(한계 ①), KMA는 겨울 비종관시각 80칸을 종관값에서 상속(한계 ⑤).
손앵커 4개는 애초 데이터로 못 얻는 축(→ §11 민감도 스윕).

> 생성물 원본: [`recon/recon_report.md`](recon/recon_report.md) · [`recon/availability.json`](recon/availability.json) · loader 검증은 `python3 loader.py`.

---

## 1. 조달 파이프라인 (작동 상세는 README로)

독립 실행형 스크립트 체인(1부 조달 4단계 + 2부 조립·선정). 메커니즘은 [`README.md`](README.md),
계획·CSV 계약은 [`design.md`](../design.md) §3·§6 참조. 여기선 **실행 순서만**:

```
fetch_*.py        # API → raw/<source>/*   (사람이 키 세팅 후 실행)
recon.py          # raw 샘플 게이팅 → recon/{availability.json, recon_report.md}
transcribe_*.py   # raw 실값 → sources/*.csv (SUPPORTED 블록만)
loader.py         # sources 8장 계약검증(합=1) → {block: 확률표}  (2부 진입점)
compose→pself→analyze→validate→criticality→sweep   # 2부 조립·선정 (output/*.json)
```

**전체 실행 엔트리:** `python3 run_all.py` — 위 체인을 의존순서로 순차 실행(외부 raw/클립
읽는 느린 단계는 산출물 있으면 캐시 스킵, 조립은 항상 재실행). `--force [단계]` 강제 재실행,
`--fetch` 1부 API 조달부터. 각 스크립트는 단독 실행형이기도 함.

인증키(.env): `KMA_API_KEY`(KMA), `DATAGO_API_KEY`(KTDB=공공데이터포털). 실행 전
`set -a; . <project>/.env; set +a`.

---

## 2. 소스별 추출 실적 — API로 무엇을 어떻게 뽑았나

### 2-1. KMA ASOS — P1_weather · P1_fog  ✅ 실전사(288칸)
- **엔드포인트:** `apihub.kma.go.kr/.../kma_sfctm2.php` (시간자료). CSV 아님 — 고정폭
  텍스트(주석 EUC-KR), 46토큰 고정. 컬럼 인덱스 TM=0·STN=1·TA=11(기온)·RN=15(강수)·VS=32(시정).
- **뽑은 것 (2단계):**
  - `fetch_kma.py` → `raw/kma/asos_sample.csv` — 대표샘플(2022 각 월 15일 08·19시). recon 게이팅용.
  - `fetch_kma_full.py` → `raw/kma/asos_hourly.csv` (**82MB**) — 2022~2024 전일·전시간(≈26k콜,
    재개·스트리밍). weather_P1/fog_P1 **집계**용 실데이터.
- **결과:** recon **SUPPORTED** → `transcribe_weather.py`가 (월,시) 288칸 집계·전사 완료.
  weather=P(clear/rain/snow|월,시), fog=P(시정<1km|월,시). loader 계약 통과.
- **분류 판정(실측 검증):** rn `-9`=건조(clear). -9를 미측정으로 빼면 강수율이 겨울 54%·여름 74%로
  폭증 → 비현실 → `-9=건조`가 맞음(1월 6%·7월 16%로 현실적). ta `-99`=결측→rain 보수처리.
- **한계 ⑤:** 겨울 비종관시각(h%3≠0)은 rn>0 미보고 → **80/288칸을 가장 가까운 종관시각에서
  상속**(강수 자기상관 근사). fog는 시정 전시각 측정이라 288칸 직접. 상세 §3-⑤ / COVERAGE.md.

### 2-2. KTDB 상시교통량 — w_vkt · w_hourly  ✅ 실전사(2/4 등급)
- **엔드포인트:** `apis.data.go.kr/1613000/KictTmsStat/itmsh_yearly` (지점·방향별 시간대별 연간
  교통량). 필수파라미터 serviceKey·spot_id=all·year·dtype·numOfRows≤100·pageNo.
- **뽑은 것:** `fetch_ktdb.py`가 dtype별 페이지네이션 수집 → 레코드의 `time_type1..24`·
  `total_count` 사용. 두 산출물:
  - `raw/ktdb/itmsh_sample.csv` (grade,hour,share) — 시간대 형상 → **w_hourly**
  - `raw/ktdb/vkt_sample.csv` (grade,share) — dtype별 total_count 정규화 = 구성비 → **w_vkt = P(road_type)**
- **API 응답 실적:** dtype 1(고속도로) 176지점·합계 18.1억 ✅ / dtype 2(일반도로) 1026지점·
  25.5억 ✅ / **dtype 3(지방도)·5(국가지원지방도) 즉시 502** (§3-①).
- **전사:** `transcribe_vkt.py`·`transcribe_hourly.py`가 grade→road_type(mapping.yaml §5-3)
  변환 → `sources/vkt_weight.csv`={highway:0.415, national_road:0.585}, `hourly_profile.csv`=2종×24시.
- **주의(대표성):** w_vkt는 **상시지점 관측교통량 구성비**이지 연장가중 VKT 아님(§3-④).

### 2-3. KASI(P5_lighting) · KoROAD(P3_agent) · 손앵커(P4_speed·P3_density) — API 미사용
데이터로 못 얻는 축이라 **의도적으로 API를 호출하지 않음**:
- **P5_lighting:** KASI는 일출·일몰 *시각*만 줌. 밝기(well_lit/poorly_lit)는 어떤 기관도 측정
  안 함 → 시각×도로등급 손매핑(mapping.yaml §5-4).
- **P3_agent:** 보행 노출은 최약 소스. 손앵커 후 §11 스윕.
- **P4_speed:** 등급별 속도조사=맑음만 존재, weather 차원은 손계수.
- **P3_density:** V/C는 「도로용량편람(KHCM 2013)」 방법론 산출값 → API 부재 확정(§3-①과
  별개, 재조사 완료). 손입력/파생만 가능.

---

## 3. 한계 대장 (Limitations register)

| # | 블록 | 한계 | 성격 | 해소 트리거 |
|---|---|---|---|---|
| ① | w_vkt·w_hourly | 지방도·국지도(dtype 3·5) **502 백엔드 미제공**; urban·tunnel은 itmsh 대상 아님 → **2/6 road_type만** | **구조적**(재시도 무효) | dtype 3·5 서버 복구 / urban·tunnel은 통계연보 별도조달 |
| ② | P1_weather·P1_fog | ~~sources 예시값(집계기 미구현)~~ → **해소**: `transcribe_weather.py`로 288칸 실전사 완료 | ✅ 완료(2026-07-16) | — |
| ③ | P4_speed·P3_agent·P3_density·P5_lighting | 데이터 부재 축 = **손앵커** | 설계상(불가피) | §11 민감도 스윕으로 방어 |
| ④ | w_vkt | 관측교통량 구성비 ≠ 연장가중 VKT | 근사(문서화됨) | 15107170 등급별 연장 조인(선택) |
| ⑤ | P1_weather | 겨울 비종관시각(h%3≠0) rn>0 미보고 → **80/288칸 종관시각 상속**(비종관 겨울 실질 3h 해상도) | 소스 구조(근사 방어) | region/계절 층화 시 재검토 |

한계 ①의 상세·함의(합=1이어도 전체분포 아님)는 [`sources/COVERAGE.md`](sources/COVERAGE.md).
①은 recon `vocab_missing` 필드 및 report `⚠ 등급 부분커버` 줄과 **교차 일치**해야 한다.

---

## 4. 결정 로그 (Decision log)

| 날짜 | 결정 | 근거 |
|---|---|---|
| 2026-07-16 | w_vkt 소스 = itmsh `total_count` 구성비로 확정 | 연장·AADT '수치'는 API 밖이나, 구성비는 관측교통량으로 산출 가능 |
| 2026-07-16 | 지방도·국지도 **타 소스로 보완하지 않음**(방침) | 한계를 메우지 않고 그대로 노출하기로. 필요 시 통계연보 별도조달 |
| 2026-07-16 | P3_density `INSUFFICIENT → HAND_ANCHOR` 재분류 | V/C=용량편람(문서) 산출값, 공공데이터 API 부재 재조사 확정 |
| 2026-07-16 | dtype 3·5 502 = **구조적 미제공** 판정 | 연도·포맷·numOfRows 무관 즉시 502, dtype 누락 시 417 정상검증 → 백엔드 미적재 |
| 2026-07-16 | KMA rn `-9` = **건조(clear)** 로 확정 | 미측정 처리 시 강수율 겨울 54%·여름 74%로 비현실 → -9=건조가 실측 정합 |
| 2026-07-16 | 겨울 강수-맹점 80칸 **종관시각 상속** | 비종관시각 rn>0 미보고(측정 0건). 강수 시간자기상관 → 최근접 종관값이 최선 근사 |
| 2026-07-16 | 신뢰 P_ext = **4축**(design §13-R 5축에서 density 제외) | P3_density를 HAND_ANCHOR로 재분류 → 게이트 A(손앵커 축 고정 금지)상 density도 marginalize. {road_type,weather,fog,road_surface}만 SUPPORTED 지지 |
| 2026-07-16 | §9 self대조 **marginal v0**로 시작 | phase0가 필드 marginal만 저장(joint 꼬리 없음). full-joint는 crosswalk 재집계=[P1] |
| 2026-07-16 | **full-joint P_self 배선 완료**(`pself.py`) | 10만 클립 재집계. §9가 결합단위로 상승 → national_road×* 심각 과소, highway×악천후 과수집이 조합해상도로 드러남 |
| 2026-07-16 | **§10 criticality 완료**(`criticality.py`) | published 배수 손위험모델. 최상위 고위험(VRU×겨울밤×저시야)이 전부 미관측 → 수집·합성 타겟 623개 도출 |
| 2026-07-16 | **§11 sweep 실행**(`sweep.py`) — 스윕 대상 §6노브→crit배수로 정정 | compose가 손앵커 marginalize → 소스 스윕은 exposure에 무의미(불변 assert로 증명). 손값이 무는 곳은 crit 배수뿐 → 그걸 스윕(전부 주의, Fragile 없음) |

---

## 5. 향후 — 연속성 (다음 액션 + 발동 조건)

**완료:**
- [x] **KMA 집계기 구현**(2026-07-16) — `transcribe_weather.py`가 asos_hourly 2.5M행 →
  (월,시) 288칸 weather/fog 실전사. 예시값 대체·loader 통과. (한계 ② 해소, ⑤ 발생·문서화)

**트리거 대기:**
- [ ] dtype 3·5 **서버 복구 시** → `fetch_ktdb.py` → `transcribe_vkt.py`/`transcribe_hourly.py`
  재실행만으로 rural 반영(한계 ① 부분해소). *urban·tunnel은 여전히 별도*.
- [ ] **통계연보 조달 결정 시** → urban·tunnel·지방도 연장/구성비 별도 전사(한계 ①·방침 재검토).

**2부(선정) — 골격 구현됨(2026-07-16):**
- [x] `compose.py` — §7 P_ext 정확 enumerate. **신뢰 4축** {road_type,weather,fog,road_surface}
  (density도 HAND_ANCHOR라 §13-R 5축→4축). strata(w(s)) 흡수. → `output/P_ext.json`(12셀).
- [x] `pself.py` — **[P1] full-joint P_self 배선 완료**. phase0 `_flatten_final`·`_SURFACE_MAP`
  import(무수정), weather는 fog 병합 없이 독립계산(§12-R). 100,398클립 재집계 → `output/P_self.json`
  (결합 {road_type,weather,fog} 24셀 + marginal).
- [x] `analyze.py` — §8 누적절단(상위 5/12=95%) + §9 **결합단위** self대조(과수집/시급). → `output/analysis.json`.
- [x] `validate.py` — §11.1 앵커 assert(highway 보행자 0 / clear·dry 최빈 / snow 0.5% / 합=1). 통과.
- [x] `criticality.py` — **§10 완료**. crit=likelihood×severity, published 배수 앵커(보행자4·
  자전거3·야간2.5·눈2.5·안개2), 상관블록 묶음·forbidden 0. 972조합 랭킹 + P_self coverage 교차.
  → `output/criticality.json`. 최상위=`national_road×snow×fog×poorly_lit×보행자×dense`(crit120,미관측).
- [x] `sweep.py` — **§11 스윕 실행 완료**. (A) 손앵커 소스 교란→P_ext 불변 assert(게이트 A 증명).
  (B) criticality 배수 ±30% OAT → Spearman~0.99(순위 안정)·Top-30 Jaccard 0.82~0.88(주의, Fragile 없음).
  → `output/sweep.json`. **설계 정정**: 손앵커 소스는 exposure에 Robust by construction이라 실제
  스윕 대상은 §6 노브가 아니라 §10 crit 배수였음.
- [x] 손앵커 4블록 **민감도 스윕 설계** → §6 부록.
- [ ] criticality v2 — speed축(현 미관측→고속 severity 과소)·이웃 확률외삽(situation-coverage-grid).
- [ ] region/계절 층화, Dirichlet CI(§13-R 게이트 B) 등 정밀화(트리거 시).
- [ ] road_type 2/4 한계(①)로 P_ext에 urban·rural 부재 → self는 urban/rural이 다수(축 커버 갭).

**연속성 유지 규칙:** 매 조달·전사 후 이 문서의 §0 표 한 줄 + §3 한계대장 + §4 결정로그만
갱신. 수치 스냅샷은 절대 여기 베끼지 말고 recon/loader 재실행으로 확인.

---

## 6. 부록 — §11 민감도 스윕 설계 (손앵커 검증) · **초안(정정됨)**

> ⚠️ **이 §6은 compose/analyze/sweep가 미구현이던 시점의 원설계 초안이다.** 실제 구현에서
> compose가 손앵커 블록을 **marginalize out** 하는 게 확정되어, 아래 6-3의 "손앵커 소스값
> 스윕"은 **exposure 선정을 바꾸지 못함**이 판명됐다(sweep.py Part A가 불변 assert로 증명).
> **실제 스윕 대상은 §10 criticality의 published 배수**로 정정됨 → 실행·결과는 §5의 `sweep.py`
> 항목 및 `output/sweep.json` 참조. 아래는 그 정정 맥락을 남기기 위한 **설계 이력**이며, 본문의
> "미구현/신설 예정"은 **작성 시점 기준**(현재는 전부 구현·실행 완료).

design.md §11("손표는 주관적 → 검증 필수")의 실행 설계. 손앵커 값을 흔들어 **최종 선정(중요
ODD 조합)이 그 추측에 얼마나 의존하는지** 측정한다.

### 6-1. 손앵커란 (요약)
**데이터로 못 재서 사람이 손으로 박아둔 값.** SUPPORTED(weather·교통량)=실측 / HAND_ANCHOR=
추정. 4블록: **P5_lighting**(밝기 — KASI는 출몰 *시각*만), **P4_speed**(우천 속도 — 조사는
맑음만), **P3_agent**(보행 노출 — 최약), **P3_density**(혼잡 V/C — 용량편람 문서). 정직히
라벨 달아 격리 후 스윕으로 관리.

### 6-2. 스윕 목적 (요약)
**"추측했다"보다 "그 추측이 답을 바꾸느냐"가 문제 — 그걸 가려낸다.** 손앵커 값을 그럴듯한
범위로 쓸어보며 파이프라인을 반복 실행 → 최종 선정 변화 관찰 → 4개 추측을 **안심/위험으로 분류**.

| 결과 | 의미 | 행동 |
|---|---|---|
| **Robust(안 흔들림)** | 값 바꿔도 선정 그대로 | ✅ 손앵커 유지, 조치 불필요 |
| **Fragile(확 흔들림)** | 값 조금 바꿔도 선정 뒤집힘 | 🚩 실데이터 조달 **또는** 결론에 불확실 경고 부착 |

### 6-3. 스윕 대상 노브 (4블록 실제 값·범위)
한 값을 흔들면 그 조건부 분포의 나머지 범주를 **비례 재정규화**(합=1, loader 계약).

**P5_lighting** (`lighting_P5.csv` + mapping §5-4)
| 노브 | 현재값 | 범위 | 근거 |
|---|---|---|---|
| **L1** 고속 야간 조명 분리 | moderate/poorly_lit = **0.50/0.50** | 0.30/0.70 ~ 0.70/0.30 | 고속 부분조명 실태 불확실(최대 추측) |
| **L2** dusk_dawn 창 폭 | **±30min** | ±15 ~ ±45min | "박명" 정의 → moderate 시각 수 좌우 |

**P4_speed** (`speed_P4.csv` + mapping §5-5)
| 노브 | 현재값 | 범위 | 근거 |
|---|---|---|---|
| **S1** 우천 고속비중(highway) | rain·high = **0.40** (clear 0.62) | 0.30 ~ 0.55 | 강수 감속폭 = 손계수 |
| **S2** rain_derate 정합성 | mapping "−10~15%" vs CSV 실제 −22pt | −10% ~ −25%(상대) | **문서·표 불일치** — 스윕으로 확정 |
| **S3** 노면 젖음 지속 ρ | **1.7** (road_surface) | 1.3 ~ 2.2 | P(wet) 좌우 → speed·weather 파급 |

**P3_agent** (`agent_P3.csv`) — 최약 데이터, fragile 1순위 후보
| 노브 | 현재값 | 범위 | 근거 |
|---|---|---|---|
| **A1** urban 주간 보행 노출 | ped(urban,8) = **0.12** | 0.05 ~ 0.25 | 보행량 데이터 빈약 |
| **A2** urban 자전거 노출 | cyc(urban,8) = **0.03** | 0.01 ~ 0.08 | 동상 |
| — | highway ped/cyc = 0 | **고정(제외)** | forbidden = 구조적 0 |

**P3_density** (`density_P3.csv`)
| 노브 | 현재값 | 범위 | 근거 |
|---|---|---|---|
| **D1** urban 첨두 혼잡 | dense(urban,8) = **0.45** | 0.30 ~ 0.60 | V/C→혼잡 매핑 손지정 |
| **D2** highway 첨두 혼잡 | dense(highway,8) = **0.30** | 0.20 ~ 0.45 | 동상 |

### 6-4. 방법 · 판정
1. **OAT(one-at-a-time):** 노브 하나씩 범위 5점(하한·중하·기준·중상·상한) 훑고 나머지 고정 →
   단독 영향 분리. 2. **코너(worst-case) 1회:** 전 노브를 선정 최대교란 방향 동시 설정 → 결합
   위험 상한. (전체 격자는 조합폭발 → 안 함.)

**지표:** Top-K 집합 Jaccard(기준 vs 교란) + 순위 Spearman/Kendall(phase0 `ODD_SPEARMAN` 재사용)
+ §9 편향맵 헤드라인 드리프트.

| Jaccard(범위 전체) | 판정 → 행동 |
|---|---|
| ≥ 0.90 | ✅ Robust — 손앵커 유지, §3에 "스윕 통과" 표기 |
| 0.80 ~ 0.90 | ⚠️ 주의(관찰) |
| < 0.80 또는 상위조합 등장/소멸 | 🚩 Fragile — 실데이터 조달 or 결론에 민감 경고+신뢰구간(design §13-R) |

### 6-5. 실행 순서 (선행 의존)
```
[미구현] compose.py(P_ext 조립) + analyze.py(선정)  — design §12
      ↓ 있어야 스윕이 '측정할 대상' 생김
sweep.py(신설 예정): for 노브 in 6-3: for 값 in 범위5점:
   교란 sources/mapping → compose → analyze → 선정집합; 기준대비 Jaccard·Spearman 기록
   → 노브별 Robust/Fragile 판정표
```
지금 할 수 있는 것: **6-3 노브표가 곧 스윕 스펙** → compose/analyze 완성 즉시 `sweep.py`가 이
표대로 돌리면 된다.

### 6-6. 예시 (직관)
L1 = 고속 야간 `{moderate:0.5, poorly_lit:0.5}`: `{0.7,0.3}`으로 흔들어 "야간 고속 저조도"
조합이 상위 선정에서 빠지면 🚩 Fragile(조명 실태 확인 필요) / 범위 전체에서 선정 그대로면
✅ Robust(0.5 추측 안심).
