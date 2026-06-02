# EXP-001 · 실험 방법 및 평가 절차

## 1. 실험 목적

자율주행 영상 클립(299,180개) 중 특정 시나리오에 해당하는 클립을 자연어 쿼리로 검색할 때, 세 가지 검색 방법의 성능과 지연을 비교한다.

---

## 2. 검색 방법 3종

### 2-1. BM25 (키워드 검색)

- **라이브러리**: `bm25s` v0.2.12
- **인덱스 구축**: 299,180개 캡션 텍스트를 토큰화하여 역색인(inverted index) 생성
- **쿼리 처리**: 쿼리를 영어 불용어 제거 후 토큰화 → BM25 점수로 순위 산출
- **아티팩트**: `data/index/bm25s_index/` (희소 행렬 형태)
- **특징**: 쿼리 단어가 캡션에 그대로 포함되어야 높은 점수 → 동의어·의미 유사도 미반영

### 2-2. Embedding 검색 (의미 기반)

- **임베딩 모델**: `BAAI/bge-m3` (다국어, 최대 8,192 토큰)
- **벡터 차원**: 1,024-dim, L2 정규화 후 코사인 유사도
- **인덱스**: Faiss HNSW
  - `M=32`, `efConstruction=200`, `efSearch=128`
- **인덱스 구축**: 캡션 299,180개를 배치 32로 인코딩 → `embeddings.npy` (1.2GB) + `hnsw.index` (1.3GB) 저장
- **쿼리 처리**: 쿼리 텍스트를 동일 모델로 인코딩 → HNSW ANN(Approximate Nearest Neighbor) 검색
- **특징**: 캡션에 동일 단어가 없어도 의미상 유사한 문서 검색 가능

### 2-3. Hybrid 검색 (ODD 필터 + 임베딩 재순위)

- **구조**: 2단계 레이어드 검색
  1. **Level 1 — ODD 태그 사전 필터**: `odd_filter` 파라미터로 `time_of_day`, `weather`, `agent_type` 등 조건을 지정하면 해당 태그를 가진 클립만 후보로 추림
  2. **Level 2 — 임베딩 재순위**: 후보 클립의 임베딩 벡터를 HNSW 인덱스에서 재구성 → 쿼리 벡터와 코사인 유사도 계산 → 상위 K개 반환
- **Fallback**: `odd_filter`가 없거나 후보 클립이 0개면 전체 코퍼스 대상 Embedding 검색으로 자동 전환

> **주의**: EXP-001 평가에서는 `odd_filter`를 전달하지 않았으므로, Hybrid가 Fallback 경로(= 전체 Embedding 검색)를 항상 탔다. 이로 인해 Hybrid 결과가 Embedding과 완전히 동일했다 (Gap-2 참조).

---

## 3. 데이터셋

| 항목 | 값 |
|------|-----|
| 전체 클립 수 | 299,180개 |
| 캡션 소스 | `/Data1/home/bskang/cds-data/captions/` |
| 캡션 형식 | 영어 자유서술 내러티브 |
| 캡션 길이 | 평균 337.7 단어 (최소 55 ~ 최대 4,085) |
| 파일명 패턴 | `{uuid}.camera_front_wide_120fov.txt` |

---

## 4. 평가셋 구축 (`build_eval_set.py`)

### 쿼리 선정

시나리오 유형별 대표성을 고려해 20개 쿼리를 수동 선정:

| 카테고리 | 쿼리 수 |
|---------|--------|
| 야간 주행 | 3 |
| 고속도로 | 3 |
| 위험/제동 | 3 |
| 보행자 | 3 |
| 날씨 | 2 |
| 주차/저속 | 2 |
| 특수 행위자 | 3 |
| 희귀(OOD) | 1 |

### 정답 레이블 생성 방식 (약지도 · Weak Supervision)

`keyword_relevance()` 함수로 자동 레이블링:

```python
def keyword_relevance(text, query):
    query_words = [w for w in re.split(r"\W+", query.lower()) if len(w) > 3]
    return all(w in text.lower() for w in query_words)
```

- 쿼리를 단어로 분리 후 길이 4 이상인 단어만 추출
- 해당 단어들이 **모두** 캡션에 포함된 클립을 정답으로 간주
- 전체 299,180개 캡션에 적용 → 쿼리당 37~49,057개 정답 클립 생성
- **구조적 편향**: 정답이 키워드 포함 여부로 결정되므로, 동일한 토큰 매칭 방식인 BM25에 유리 (Gap-1 참조)

### 평가셋 통계 (현재 기준)

| 항목 | 값 |
|------|-----|
| 쿼리 수 | 20개 |
| 총 정답 레이블 수 | 186,285개 |
| 쿼리당 정답 수 | 최소 37 (`pedestrian suddenly enters road`) ~ 최대 49,057 (`pedestrian crossing with dog`) |

---

## 5. 평가 지표 및 측정 (`evaluate.py`)

### 지표

| 지표 | 설명 |
|------|------|
| **Recall@5** | 상위 5개 결과 중 정답 클립 비율. `len(retrieved[:5] ∩ relevant) / min(5, len(relevant))` |
| **MRR@5** | 첫 번째 정답 클립의 역순위 평균. 정답이 1위면 1.0, 2위면 0.5, 없으면 0.0 |
| **Latency (ms)** | 쿼리 1건 처리 시간 (인덱스 로드 포함, wall-clock time) |

### 측정 절차

1. 각 방법(`bm25` → `embedding` → `hybrid`) 순서로 실행
2. 방법별로 20개 쿼리를 순차 처리, 매 쿼리마다 `time.perf_counter()`로 지연 측정
3. 인덱스·모델은 첫 쿼리 시점에 lazy load → **첫 쿼리에 cold start 지연 포함**
4. 결과를 `experiments/experiment_001_results.csv`에 저장 (60행: 20 쿼리 × 3 방법)

### Cold Start 영향

| 방법 | 첫 쿼리 지연 | 원인 |
|------|------------|------|
| BM25 | 3,598ms | 299k 역색인 로드 |
| Embedding | 18,485ms | bge-m3 모델 로드 + HNSW 인덱스 메모리 맵 초기화 |
| Hybrid | 434ms | ODD 태그 JSON 로드 (모델·인덱스는 Embedding 단계에서 이미 로드됨) |

→ 평균 지연은 cold start로 왜곡됨. **중앙값**(BM25 1.93ms / Embedding 5.56ms / Hybrid 5.35ms)이 실제 서비스 지연에 가까움.

---

## 6. ODD 커버리지 분석 (`extract_odd_tags.py`)

### ODD 분류 체계 (Taxonomy)

자율주행 ODD(Operational Design Domain)를 7개 필드로 정의한다.

| 필드 | 유형 | 허용 값 |
|------|------|--------|
| `time_of_day` | 단일값 | day, night, dawn, dusk, unknown |
| `weather` | 단일값 | clear, cloudy, rain, snow, fog, unknown |
| `road_type` | 단일값 | highway, urban, intersection, parking_lot, rural, tunnel, bridge, unknown |
| `traffic_density` | 단일값 | free, moderate, congested, unknown |
| `hazard_level` | 단일값 | none, low, medium, high, unknown |
| `agent_type` | **다중값** | pedestrian, cyclist, motorcycle, truck, bus, emergency_vehicle, animal, none |
| `ego_action` | **다중값** | straight, left_turn, right_turn, uturn, lane_change, braking, stopping, reversing |

- 단일값 필드: 우선순위가 높은 패턴이 먼저 매칭되면 이후 패턴은 확인하지 않음 (first match wins)
- 다중값 필드(`agent_type`, `ego_action`): 매칭되는 값을 모두 수집, 없으면 `["none"]`

### 태그 추출 방식 — Regex 휴리스틱

캡션 텍스트(소문자 변환 후)에 정규식 패턴을 순서대로 적용하여 태그를 추출한다. 비용 없이 빠르게 실행 가능하며, EXP-001에서는 LLM fallback 없이 regex만 사용했다.

**적용 규칙:**
- 단일값 필드: 리스트 순서대로 패턴을 확인하다가 **첫 번째로 매칭된 값**에서 중단 (priority order)
- 다중값 필드(`agent_type`, `ego_action`): 리스트 전체를 확인하여 **매칭된 값을 모두 수집**
- 매칭 없음: 단일값 필드는 `"unknown"`, 다중값 필드는 `["none"]`

---

**`time_of_day`** (단일값, 우선순위: night > dawn > dusk > day)

| 값 | 매칭 패턴 |
|----|---------|
| night | `nighttime`, `night`, `nocturnal`, `after dark`, `darkness`, `pitch-black`, `headlight(s)`, `street-light(s)` |
| dawn | `dawn`, `early morning`, `sunrise`, `first light`, `pre-dawn` |
| dusk | `dusk`, `evening`, `sunset`, `twilight`, `nightfall`, `fading light` |
| day | `daytime`, `day`, `daylight`, `sunny`, `bright`, `morning`, `afternoon`, `midday`, `noon`, `well-lit` |

---

**`weather`** (단일값, 우선순위: rain > fog > snow > cloudy > clear)

| 값 | 매칭 패턴 |
|----|---------|
| rain | `rain`, `rainy`, `raining`, `wet road`, `shower`, `drizzle`, `precipitation`, `downpour`, `puddle(s)` |
| fog | `fog`, `foggy`, `visibility.*poor`, `poor visibility`, `mist`, `misty`, `haze`, `hazy`, `low-visibility` |
| snow | `snow`, `snowy`, `ice`, `icy`, `winter condition`, `sleet`, `frost`, `black ice`, `slippery` |
| cloudy | `cloudy`, `overcast`, `gloomy` |
| clear | `clear`, `fair`, `dry road` |

---

**`road_type`** (단일값, 우선순위: highway > intersection > parking_lot > tunnel > bridge > urban > rural)

| 값 | 매칭 패턴 |
|----|---------|
| highway | `highway`, `freeway`, `motorway`, `expressway`, `interstate` |
| intersection | `intersection`, `junction`, `crossroad`, `traffic light`, `stop sign`, `traffic signal` |
| parking_lot | `parking`, `parked`, `parking lot`, `parking area` |
| tunnel | `tunnel` |
| bridge | `bridge`, `overpass` |
| urban | `urban`, `city`, `street`, `block`, `boulevard`, `avenue` |
| rural | `rural`, `country road`, `farm`, `field` |

---

**`traffic_density`** (단일값, 우선순위: congested > moderate > free)

| 값 | 매칭 패턴 |
|----|---------|
| congested | `congested`, `heavy traffic`, `traffic jam`, `bumper-to-bumper`, `queue`, `slow-moving`, `stop-and-go`, `backed-up`, `standstill`, `gridlock`, `dense traffic`, `crawling` |
| moderate | `moderate traffic`, `some traffic`, `several vehicles`, `steady traffic`, `moving vehicles` |
| free | `light traffic`, `free-flowing`, `minimal traffic`, `empty road`, `open road`, `sparse traffic`, `no traffic`, `deserted` |

---

**`agent_type`** (다중값 — 해당하는 값 모두 수집)

| 값 | 매칭 패턴 |
|----|---------|
| pedestrian | `pedestrian`, `walker`, `person crossing`, `people crossing` |
| cyclist | `cyclist`, `bicycle`, `bike` |
| motorcycle | `motorcycle`, `motorbike`, `scooter` |
| truck | `truck`, `lorry`, `trailer`, `semi-truck` |
| bus | `bus` |
| emergency_vehicle | `ambulance`, `fire truck`, `police car`, `emergency vehicle` |
| animal | `dog`, `cat`, `animal`, `wildlife` |

---

**`hazard_level`** (단일값, 우선순위: high > medium > low > none)

| 값 | 매칭 패턴 |
|----|---------|
| high | `hazard`, `danger`, `collision`, `crash`, `accident`, `emergency brake`, `sudden stop`, `imminent`, `near-miss`, `close-call`, `aggressive driving`, `swerve(d)`, `reckless` |
| medium | `caution`, `careful`, `prudent`, `aware`, `vigilant`, `slow down`, `risky`, `erratic`, `unexpected` |
| low | `safe`, `normal`, `smooth` |
| none | `no hazard`, `no incident` |

---

**`ego_action`** (다중값 — 해당하는 값 모두 수집)

| 값 | 매칭 패턴 |
|----|---------|
| braking | `brake`, `braking`, `slows down`, `reduces speed` |
| stopping | `stop(s)`, `stands still`, `stops at`, `halt` |
| left_turn | `left turn`, `turns left` |
| right_turn | `right turn`, `turns right` |
| uturn | `u-turn` |
| lane_change | `lane change`, `changes lane`, `merge`, `merging`, `overtake` |
| reversing | `reverse`, `reversing`, `back up` |
| straight | `continues`, `proceeds`, `maintains course`, `straight` |

매칭되는 패턴이 없으면 단일값 필드는 `"unknown"`, 다중값 필드는 `["none"]` 할당.

### 커버리지 통계 계산

각 필드에 대해 `unknown`이 아닌 클립의 비율을 커버리지(%)로 산출한다.

```
coverage_pct = (unknown이 아닌 클립 수) / (전체 클립 수) × 100
```

### EXP-001 커버리지 결과

| 필드 | 커버리지 | Unknown 클립 수 | 원인 |
|------|---------|----------------|------|
| agent_type | 100.0% | 0 | 다중값 + 없으면 "none" 처리 |
| ego_action | 100.0% | 0 | 다중값 + 없으면 "none" 처리 |
| road_type | 96.7% | 9,929 | 패턴이 다양한 도로 유형을 포괄 |
| hazard_level | 84.7% | 45,712 | 위험 표현 다양성으로 일부 미탐지 |
| time_of_day | 62.7% | 111,554 | 시간대 언급이 없는 캡션 다수 |
| weather | 52.9% | 140,937 | "overcast", "drizzling" 등 미등록 표현 |
| traffic_density | 37.4% | 187,356 | "bumper-to-bumper", "stop-and-go" 등 미등록 표현 |

### LLM Fallback (EXP-001 미사용)

`--llm` 플래그 사용 시 `unknown` 필드가 남은 클립에 대해 GPT-4o-mini로 추가 추출 가능. EXP-001에서는 비용 절감을 위해 regex만 사용했으며, EXP-003에서 적용 예정.

---

## 7. 분포 분석 (`distribution_analysis.py`)

전체 클립 임베딩을 2D로 축소하여 데이터 분포를 시각화하고, 희귀/롱테일 시나리오를 자동으로 발굴한다.

### 처리 흐름

```
임베딩 [299,180 × 1,024]
    │
    ├── 1. UMAP 2D 축소        → xy 좌표 [299,180 × 2]
    ├── 2. KDE 밀도 추정       → density 값 [299,180]
    ├── 3. ODD 커버리지 행렬   → time×weather vs ego_action 히트맵
    ├── 4. Plotly 시각화       → distribution.html (4패널)
    ├── 5. 롱테일 추출         → longtail_clips.json
    └── 6. 좌표 저장           → umap_coords.parquet
```

### Step 1 — UMAP 2D 축소

| 파라미터 | 값 | 의미 |
|---------|-----|------|
| `n_components` | 2 | 2D로 축소 |
| `n_neighbors` | 15 | 로컬 구조 보존 범위 |
| `min_dist` | 0.1 | 클러스터 압축 정도 |
| `metric` | cosine | 임베딩 유사도 기준 |
| `random_state` | 42 | 재현성 고정 |

- 의미상 유사한 클립들이 2D 공간에서 가깝게 위치
- 희귀 시나리오는 고밀도 군집에서 멀리 분리되어 나타남

### Step 2 — KDE 밀도 추정

- **방법**: Gaussian Kernel Density Estimation (`sklearn.neighbors.KernelDensity`)
- **bandwidth**: 0.3 (UMAP 2D 좌표 스케일 기준)
- 각 클립이 임베딩 공간에서 얼마나 밀집된 곳에 있는지를 수치화
- 밀도가 낮을수록 = 주변에 유사한 클립이 적은 희귀 시나리오

### Step 3 — ODD 커버리지 행렬

- **행(Row)**: `time_of_day × weather` 조합 (예: `night×rain`, `day×clear`)
- **열(Column)**: `ego_action` 값 (예: `braking`, `lane_change`)
- **셀 값**: 해당 조합에 속하는 클립 수
- **목적**: 수집 갭(빈 셀 또는 값이 매우 작은 셀) 시각적 파악

### Step 4 — Plotly 4패널 시각화

| 패널 | 내용 | 색상 기준 |
|------|------|---------|
| 1 (좌상) | UMAP 전체 분포 | 밀도 (Viridis: 노란색=저밀도, 보라=고밀도) |
| 2 (우상) | 시간대별 분포 | time_of_day 카테고리별 색상 |
| 3 (좌하) | 위험도별 분포 | high=빨강, medium=주황, low=초록, unknown=회색 |
| 4 (우하) | ODD 커버리지 행렬 | Blues 히트맵 (진할수록 클립 수 많음) |

결과물: `data/index/distribution.html` (40MB, 브라우저에서 열기)

### Step 5 — 롱테일 클립 추출

밀도 하위 5% 기준으로 희귀 클립을 자동 선별:

```
threshold = np.percentile(density, 5)
longtail_clips = [clip_id for clip_id, d in zip(clip_ids, density) if d < threshold]
```

- EXP-001 결과: **14,959개** (전체의 5%)
- 저장: `data/index/longtail_clips.json`

### Step 6 — 좌표 저장

각 클립의 2D 좌표와 ODD 메타데이터를 parquet으로 저장:

| 컬럼 | 내용 |
|------|------|
| `clip_id` | 클립 UUID |
| `x`, `y` | UMAP 2D 좌표 |
| `density` | KDE 밀도값 |
| `time_of_day`, `weather`, `road_type`, `hazard_level`, `agent_type` | ODD 태그 |

저장: `data/index/umap_coords.parquet` (17MB)

---

## 8. 실험 재현 커맨드

```bash
uv sync

# Phase 1: BM25 인덱스 구축
uv run python -m avdata.phase1.build_bm25

# Phase 2: 임베딩 벡터 생성 + HNSW 인덱스 구축 (299k, GPU 권장)
uv run python -m avdata.phase2.build_embeddings

# Phase 3: ODD 태그 추출
uv run python -m avdata.phase3.extract_odd_tags

# Phase 4: 분포 분석 시각화
uv run python -m avdata.phase4.distribution_analysis

# 평가셋 생성 (전체 코퍼스 기준)
uv run python -m avdata.eval.build_eval_set --sample 299180

# 3종 방법 평가
uv run python -m avdata.eval.evaluate
```
