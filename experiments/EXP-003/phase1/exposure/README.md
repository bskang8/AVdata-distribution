# Phase 1 — 구현 현황 & 구동 흐름

> 이 문서 = 스크립트 *작동법*. 실제 실행기록·결과 현황·한계·향후는 [`RESULTS.md`](RESULTS.md).

design.md의 파이프라인(§12)은 **1부 조달(`procure/`) → 공유 코어 → 2부 선정(`select/`)까지
전 구간 구현**됐다(현황·결과는 [RESULTS.md](RESULTS.md)). 이 문서는 그중 **조달 파이프라인의
두 관문** recon·loader의 작동법을 설명한다:

- **recon.py**(`procure/`) = 데이터 받기 *전* 정찰관. "이 자료로 표를 만들 수 있나?"
- **loader.py**(root) = 데이터 받은 *후* 검사관. "채워진 표가 규칙을 지키나?"

각각 단독 실행형이고, 그 아래·위 전 단계는 `run_all.py`가 의존순서로 잇는다.

```
[사람이 소스 export]                      [사람이 실값 전사]
  raw/<source>/*  ──① recon.py──▶ 게이트 판정 ─────▶ sources/*.csv ──② loader.py──▶ {block: 확률표}
                       │                                                  │            (2부 진입점)
                       └─ recon/availability.json                         └─ 계약 검증 (합=1)
                          recon/recon_report.md
```

## ① recon.py — 조달 *전* 게이팅

**한 줄 목적:** 본격적으로 데이터를 긁어오기 전에, **각 기관 자료 샘플 1장만 열어보고
→ 내가 설계한 표(블록)를 채울 수 있는지 미리 정찰**한다.

**실행:** `python3 procure/recon.py`

### 왜 필요한가

design.md는 8개 "블록"(= 조건부 확률표 한 장씩)을 설계했다. 예:
`P1_weather = P(weather | month, hour)`(기상청), `w_vkt = P(road_type)`(국토부).
이 표를 채우려면 외부 기관(KMA/KTDB/KoROAD/KASI) 자료에 **필요한 컬럼이 실제로
들어있어야** 하는데, 그건 열어보기 전엔 모른다. 수십만 행을 다 받고 전사한 뒤에야
"이 컬럼이 없네"를 깨달으면 헛수고 → 그래서 **샘플 1장으로 블록별 "만들 수 있음/없음"을
미리 판정(게이팅)** 한다. 표를 *직접 만들지 않고*, 실데이터가 설계를 뒷받침하는지만
검증·축소하고, 어디가 손저작으로 갈 수밖에 없는지 솔직하게 표시하는 관문이다.

### 판정 게이트 5종

| 게이트 | 뜻 | 다음 행동 |
|---|---|---|
| **SUPPORTED** | 샘플에 필요한 컬럼 다 있음 | 전체 조달 → `sources/*.csv` 전사 |
| **LOW_RES** | 소스는 있으나 조건키 일부 못 만듦 | 표를 더 거칠게(조건 줄여) |
| **INSUFFICIENT** | 필요 컬럼이 안 보임 | 다른 샘플/컬럼 재확인 |
| **NOT_OBTAINED** | 아직 샘플조차 없음 | 기관 export → `raw/`에 투입 |
| **HAND_ANCHOR** | 이 축은 어떤 데이터에도 없음 | 사람이 손 지정(§11 스윕) |

> **HAND_ANCHOR가 따로 있는 이유:** 예를 들어 "밝기(well_lit/poorly_lit)"는 어떤 기관도
> 측정해주지 않는다(KASI는 일출·일몰 *시각*만 준다). 이런 블록은 데이터 확인 자체가
> 무의미 → 샘플을 찾지도 않고 바로 `HAND_ANCHOR` 도장을 찍고 넘어간다.

### 동작 흐름 (블록 하나 기준, `gate_block`)

```
1. apriori=HAND_ANCHOR 인가?            → 예: 바로 HAND_ANCHOR 찍고 끝 (최우선)
2. raw_glob 샘플이 있나?                → 없음: NOT_OBTAINED
3. 헤더에서 필요한 role 컬럼 부분일치 검출  → 하나라도 없음: INSUFFICIENT
4. 조건키(month,hour…)를 그 컬럼으로 만들 수 있나?
      다 됨: SUPPORTED / 일부만: LOW_RES
```

전체 진입점(`__main__`):
1. `_selfcheck()` — 임시 디렉터리에 가짜 KMA/KTDB 샘플을 깔아 게이트 로직 +
   `edge_max_tv` 단위검증 assert. 깨지면 즉시 종료.
2. `run()` — 8개 블록에 위 `gate_block()` 반복.
3. `write_outputs()` — `recon/availability.json` + `recon_report.md` 갱신.

### 덤으로 하는 품질 점검 두 가지

- **`vocab_found`(어휘 확인)** — 실제 컬럼 값 목록을 뽑아 taxonomy 확인. 예: KTDB
  도로등급에 "터널" 태그가 없음(mapping.yaml의 최대 구멍)을 여기서 잡는다.
- **`edge_max_tv`(조건부 필요성)** — "도로유형별로 시간분포가 정말 다른가"를 숫자로 잰다.
  거의 같으면(TV < 0.05) 조건 나눌 필요 없이 합쳐도 됨(단순화 신호), 다르면 조건부 정당.

> 게이트 판정 최신값은 생성물 `recon/recon_report.md`·`availability.json`이 정답,
> 현황 요약은 [RESULTS.md](RESULTS.md) §0. (KMA·KTDB 실데이터 조달·전사 완료 상태.)

## ② loader.py — 조달 *후* CSV 계약 검증 + 확률표 노출

**한 줄 목적:** 사람이 채워 넣은 `sources/*.csv` 8장을 읽어 **약속한 규칙(계약)을
지켰는지 검사**하고, 통과하면 다음 단계가 바로 쓸 수 있는 **확률표(딕셔너리)로 넘겨준다.**

**실행:** `python3 loader.py`

### 왜 필요한가

CSV는 사람이 손으로 전사하다 오타·누락이 나기 쉽다. 특히 확률표는 **"한 조건에서 값들의
합이 1이어야 한다"**(맑음+비+눈 = 100%)는 규칙이 있는데, 이게 깨진 채로 뒷단(compose)에
흘러가면 조용히 틀린 결과가 나온다. loader는 그 사고를 **입구에서 막는 검사관**이다.
소스를 바꾸고 싶으면 CSV만 갈아 끼우면 되고(코드 수정 없음), loader가 새 파일이 규칙을
지키는지 다시 확인해준다.

### 동작 흐름

1. `validate()` — `BLOCKS`에 등록된 8장을 순회하며 세 가지를 본다:
   (a) 파일이 있나, (b) 헤더(컬럼 이름)가 약속과 같나,
   (c) 합=1 대상 블록은 **조건마다 확률 합이 1인가**(반올림 오차 ±0.01 허용).
   어긴 것들을 목록으로 모은다.
2. 하나라도 어기면 `[FAIL]` 찍고 `exit 1`(멈춤).
3. 다 통과하면 `load_all()`이 `{블록이름: 확률표}` 형태로 반환 —
   이게 **2부(compose.py)가 받을 유일한 입력**이다.

`P1_fog`(안개)만 "있음/없음"을 재는 독립 축이라 합=1 규칙에서 예외(`sum1=False`).
계약 통과 현황(현재 8블록 전부 통과)은 [RESULTS.md](RESULTS.md) §0 참조.

## 실행 방법

> 코드 정리(2026-07): 조달 one-shot은 `procure/`, 2부 선정은 `select/`, 공유 코어
> (loader·compose·criticality)·run_all·`paths.py`는 root. 경로는 `paths.py`가 일원화.
> 전체는 `python3 run_all.py`(RESULTS §1). 개별 실행 예:

```bash
cd .../EXP-003/phase1/exposure

# 전체 파이프라인 (조달→조립→선정). 외부 raw/클립 읽는 느린 단계는 캐시 스킵, 조립은 항상 재실행.
python3 run_all.py                 # 기본(캐시 활용) — 끝에 §8·§10·§11 요약 출력
python3 run_all.py --force         # 전부 강제 재실행
python3 run_all.py --force pself    # 특정 단계만 강제(예: pself·criticality)
python3 run_all.py --fetch         # 1부 API 조달(fetch_*)부터 포함 — 키 필요(아래)

# 개별 실행(각 스크립트 단독 실행형)
python3 procure/recon.py   # 조달 전: 소스 게이팅 → recon/ 갱신
python3 loader.py          # 조달 후: CSV 8장 계약 검증 + 확률표 로드
```

- **API 키(fetch_*·pself만 필요):** `KMA_API_KEY`(KMA)·`DATAGO_API_KEY`(KTDB=공공데이터포털)를
  프로젝트 `.env`에 두고 실행 전 셸에 로드:  `set -a; . <project>/.env; set +a`.
  (recon·loader·2부 조립은 키 불필요. pself/criticality는 phase0 클립 경로만 접근.)
- **필요한 것:** 추가 설치 없음. 표준 라이브러리(`csv/glob/json/statistics/collections`)만.
  `mapping.yaml`은 코드가 읽지 않는 사람용 근거 문서다.
- **어디서 실행하나:** 스크립트는 `__file__` 기준 절대경로(`paths.py`)라 cwd 무관하게 돈다.
  서브디렉토리 스크립트는 상단 1줄로 root를 sys.path에 얹어 코어를 import한다.
- **성공/실패 판별:** 정상 종료면 0, `loader` 계약 위반이면 1로 멈춘다. 코드 자체 자가진단
  (self-check)이 깨지면 `AssertionError`로 죽는다 → 그대로 CI 검사에 붙일 수 있다.

## 소스 재조달·갱신 흐름

`sources/*.csv`의 데이터 블록(KMA weather/fog·KTDB w_vkt/w_hourly)은 **실데이터 전사 완료**.
소스를 갱신하거나 새로 받으려면:

1. `procure/fetch_*.py`(키 필요) 또는 수동 export로 `raw/{kma,ktdb}/`에 조달 → `procure/recon.py` 재실행.
2. `SUPPORTED` 블록만 `procure/transcribe_*.py`로 `sources/*.csv` 전사 → `loader.py` 계약 검사.
3. 조립·선정(compose→pself→analyze→validate→criticality→extrapolate→sweep, design §12)은
   **구현 완료** → `python3 run_all.py`로 일괄 실행.

손앵커 4블록(P4_speed·P3_agent·P3_density·P5_lighting)은 데이터 부재 축이라 `sources/*.csv`가
손지정값이다(§11 스윕으로 방어). 미조달·한계(지방도 등)는 [RESULTS.md](RESULTS.md) §3.

## 참고 — recon은 "발견"이 아니라 "확인" 도구다

recon은 `REQUIREMENTS`의 `roles`·`BLOCKS`의 `keys`에 **미리 적어둔 필드만** 쳐다본다.
거기 없는 컬럼은 무시하므로, **우리가 미처 생각 못 한 유용한 필드가 샘플에 숨어 있어도
recon이 먼저 알려주지 않는다.** 이건 버그가 아니라 의도된 설계다 — "무엇이 중요한가"는
데이터가 아니라 도메인 지식(설계자)이 정하고, recon은 그 가설을 게이팅만 한다
(recon.py 첫머리: "구조를 만들지 않고 검증·축소만 한다").

**그럼 "등록 안 된 컬럼도 항상 나열"해주는 발견 보조기능을 붙이면?** 객관적으로 따지면
효용이 작다:

- **증분 커버리지가 좁다.** INSUFFICIENT는 이미 `note`에 전체 헤더를 찍고, NOT_OBTAINED·
  HAND_ANCHOR는 샘플을 안 읽는다. 새로 채워지는 건 SUPPORTED·LOW_RES 두 게이트뿐.
- **하필 그 블록은 사람이 곧 파일을 연다.** SUPPORTED의 다음 행동이 "실값 전사"라
  어차피 CSV를 열어 모든 컬럼을 눈으로 본다 → 리포트 나열과 중복.
- **소스가 문서화된 정형 데이터(KMA/KTDB/KoROAD/KASI)라** 미지의 유용 컬럼 리스크가 낮다.
- **노이즈 비용.** 정부 CSV는 컬럼 20~50개(관측소ID·품질플래그 등 잡음 다수)라, markdown
  리포트에 매번 나열하면 신호 대 잡음비만 떨어진다.

**결론:** 발견 도구로선 과대평가. 정당화되는 유일한 근거는 "발견"이 아니라 **감사 추적**
(recon 시점에 그 샘플이 무슨 컬럼을 가졌는지의 영구 기록)이다. 그래서 필요해지면
markdown 리포트가 아니라 **`availability.json`에 `all_columns` 한 필드로만** 기록하는 게
맞다 — 사람이 안 읽으니 노이즈 비용이 없고 나중에 조회 가능. (현재 미구현, 필요 시 추가.)
