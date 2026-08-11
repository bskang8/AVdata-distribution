# sources/ 커버리지 한계 (전사본에 따라붙는 사실)

전사된 `sources/*.csv`는 계약(합=1)은 통과하지만, **모집단 전체를 담지 못하는 표가 있다.**
아래 한계를 compose/analyze 단계가 반드시 인지해야 한다 — 표가 합=1이라고 "전체 분포"가
아니다.

## w_vkt (`vkt_weight.csv`) · w_hourly (`hourly_profile.csv`) — KTDB itmsh_yearly

- **출처:** 국토부/KICT 상시교통량조사 `KictTmsStat/itmsh_yearly` (data.go.kr 1613000).
- **실제 커버:** `highway`(고속도로) + `national_road`(일반국도) **2종뿐.**
- **미확보 및 사유:**
  - `지방도`·`국가지원지방도` (dtype 3·5) → API 백엔드가 **연도·포맷·numOfRows 무관 즉시
    502**(`Error forwarding request to backend server`). 우리 입력 오류·일시 플레이크가
    아니라 **백엔드 미적재(구조적)**. 재시도로 안 풀림.
  - `urban`(도시부)·`tunnel`(터널) → itmsh **상시조사 대상 자체가 아님**(mapping.yaml §5-3의
    터널 구멍과 동일 맥락).
- **함의:** `vkt_weight.csv`의 2행 합=1은 **"고속+일반국도 안에서의" 노출 구성비**이지
  전체 도로유형 분포가 아니다. compose에서 P(road_type)를 전 도로로 해석하면 urban/rural/
  tunnel 노출을 0으로 취급하는 **왜곡**이 된다. `hourly_profile.csv`의 시간대 형상도 이 2종만.
- **방침:** 현재 **타 소스로 보완하지 않음**(지방도/urban은 통계연보·용량편람 별도 조달 대상).
  한계를 메우지 않고 그대로 노출하는 것이 현 결정.
- **복구/확장 경로:** dtype 3·5 서버 복구 시 `fetch_ktdb.py` → `transcribe_vkt.py` /
  `transcribe_hourly.py` 재실행만으로 rural 반영됨. urban·tunnel은 통계연보 별도 전사 필요.
- **교차확인:** `recon/recon_report.md`의 `⚠ 등급 부분커버` 줄 및
  `recon/availability.json`의 `vocab_missing` 필드와 일치해야 한다.

## P1_weather (`weather_P1.csv`) · P1_fog (`fog_P1.csv`) — KMA ASOS

- **출처:** KMA ASOS 시간자료(`kma_sfctm2`), 2022~2024 전일·전시간 `raw/kma/asos_hourly.csv`
  (2,529,142행). `transcribe_weather.py`가 (월,시) 288칸으로 집계.
- **한계 ⑤ — 겨울 강수 3시간 보고:** KMA는 겨울철 **비종관시각(h%3≠0)엔 비가 와도 rn>0을
  안 찍는다**(측정 rn≥0 이 0건). 이 '강수-맹점' 셀(**80/288**, 대부분 11~2월 비종관시각)은
  가장 가까운 종관시각(0/3/…/21)의 분포를 **상속**했다 — 즉 그 시각들의 weather는 직접 관측이
  아니라 ±1~2h 이웃 종관값의 근사다. 강수는 시간 자기상관이 커서 방어적이지만, **비종관
  겨울시각의 시간해상도는 실질 3시간**임을 인지할 것.
- **rn 센티넬:** `-9.0` = 건조(clear)로 해석(측정 검증: 미측정으로 빼면 강수율 겨울 54%로
  폭증·비현실 → -9=건조가 맞음). fog의 `vs=-9`(시정 결측)만 분모 제외.
- **비영향:** 여름·종관시각·fog(시정 전시각 측정)는 직접 관측. weather 288칸 중 **208칸 직접
  / 80칸 상속**. fog는 288칸 전부 직접.

## 그 외 블록

- `P4_speed`·`P3_agent`·`P3_density`·`P5_lighting` = HAND_ANCHOR (손앵커, §11 민감도 스윕).
  데이터 조달이 아니라 설계자 지정값 → 커버리지 한계와는 다른 범주.
