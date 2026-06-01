# AV Data Distribution & Semantic Search — 파이프라인 가이드

## 데이터 현황

| 항목 | 값 |
|------|-----|
| 주행 영상 | 306,152개 (`/Data1/home/bskang/cds-data/front_camera_videos/`) |
| 텍스트 캡션 | 83,612개 (`/Data1/home/bskang/cds-data/captions/`) |
| 캡션 언어/형식 | 영어 자유서술 내러티브 |
| 캡션 길이 | 평균 331 단어 (63 ~ 4,091 단어) |
| 파일명 패턴 | `{uuid}.camera_front_wide_120fov.{mp4\|txt}` |

---

## 현재 진행 상태 (2026-05-17 기준)

| 단계 | 명령 | 상태 | 비고 |
|------|------|------|------|
| Step 1 | `explore` | ✅ 완료 (2026-05-15) | `exploration_summary.json` 생성됨 |
| Step 2 | `build_bm25` | ⚠️ **재실행 필요** | 구버전 `bm25_index.pkl` 존재 — 현재 코드와 포맷 불일치 |
| Step 3 | `build_embeddings` | ❌ 미실행 | `embeddings.npy`, `hnsw.index` 없음 |
| Step 4 | `extract_odd_tags` | ❌ 미실행 | `odd_tags.json` 없음 |
| Step 5 | `evaluate` | ❌ 미실행 | Step 3·4 선행 필요 |
| Step 6 | `distribution_analysis` | ❌ 미실행 | Step 3 선행 필요 |

---

## 전체 파이프라인 흐름

```
캡션 83,612개
    │
    ├─── Step 1: explore        → 데이터 통계 파악
    ├─── Step 2: build_bm25     → 키워드 검색 인덱스 (빠른 베이스라인)
    ├─── Step 3: build_embeddings → 의미 벡터 + Faiss 인덱스 (정확한 검색)
    ├─── Step 4: extract_odd_tags → 각 클립에 ODD 태그 부착 (필터링용)
    ├─── Step 5: evaluate       → 세 가지 검색 방법 성능 비교
    └─── Step 6: distribution   → 전체 데이터 분포 시각화 + 희귀 클립 발굴
```

---

## 환경 설정 (처음 한 번)

```bash
# uv PATH 등록 (새 터미널마다 필요 없도록 .bashrc에 이미 등록됨)
source $HOME/.local/bin/env

# 모든 의존성 설치 (.venv에 동기화)
cd /Data1/home/bskang/AVdata-distirbution
uv sync
```

**`uv sync` 란?**  
`pyproject.toml`에 정의된 패키지 목록을 읽어 `.venv`에 정확히 반영합니다.  
추가/제거된 패키지를 자동으로 맞춰주므로, `git pull` 후에도 이 명령 하나로 환경이 복원됩니다.

---

## Step 1 — 데이터 탐색

```bash
uv run python -m avdata.phase1.explore
```

**무엇을 하나요?**  
코드를 짜거나 인덱스를 빌드하기 전에, 실제 데이터가 어떻게 생겼는지 파악합니다.

**수행 작업:**
1. 영상 파일 수 / 캡션 파일 수 / 매칭 현황 집계
2. 캡션 텍스트 길이 분포 (단어 수 히스토그램, 1,000개 샘플 기준)
3. ODD 관련 키워드 빈도 집계 (`night`, `pedestrian`, `rain` 등 29개)

**산출물:**
```
data/eval/exploration_summary.json   ← 통계 요약 (JSON)
```

**탐색 결과 요약 (2026-05-15 기준):**
- 가장 빈번한 시나리오: `intersection`(2,285회), `bus`(743회), `pedestrian`(738회)
- 야간 관련: `night`(402회) + `nighttime`(200회)
- 날씨: `rain`(380회) > `snow`(110회) > `fog`(26회)
- 희귀 시나리오: `animal`(3회), `emergency`(22회) → 롱테일 후보

---

## Step 2 — BM25 키워드 검색 인덱스 빌드

```bash
# 빠른 테스트 (5,000개, ~30초)
uv run python -m avdata.phase1.build_bm25 --limit 5000

# 전체 빌드 (83,612개, ~5~10분)
uv run python -m avdata.phase1.build_bm25
```

**무엇을 하나요?**  
캡션 텍스트를 토큰화하여 BM25 키워드 검색 인덱스를 만듭니다.

**BM25란?**  
쿼리 단어가 문서에 얼마나 자주, 그리고 희귀하게 등장하는지를 점수로 매기는 고전적 검색 알고리즘입니다.  
LLM이나 GPU 없이 즉시 동작하는 강력한 베이스라인입니다.

**처리 흐름:**
```
캡션 텍스트
    → 소문자 변환 + 불용어 제거 + 어간 추출 (bm25s 내장 토크나이저)
    → 토큰 리스트
    → BM25 역인덱스 구축
    → 디렉토리로 저장
```

**산출물:**
```
data/index/bm25s_index/   ← BM25 인덱스 (디렉토리, bm25s 포맷)
data/index/clip_ids.json  ← 클립 ID 목록 (Phase 3 임베딩과 공유)
```

> ⚠️ **주의**: `data/index/bm25_index.pkl` (124 MB, 2026-05-15) 파일이 존재하지만  
> 이는 **구버전 코드(pickle 포맷)**의 산출물입니다. 현재 코드는 `bm25s` 라이브러리를  
> 사용하며 `bm25s_index/` 디렉토리 포맷으로 저장합니다. **반드시 재실행**하세요.

> **`--limit N`** 옵션: 앞에서 N개만 처리. 코드 동작 확인용으로 사용.  
> 테스트 성공 후 옵션 없이 전체 빌드하면 됩니다.

---

## Step 3 — 임베딩 추출 + Faiss HNSW 인덱스 빌드

```bash
# 테스트 (5,000개, 단일 GPU 기준 ~5분)
uv run python -m avdata.phase2.build_embeddings --limit 5000

# 전체 빌드 (83,612개, 단일 GPU 기준 ~1~2시간)
uv run python -m avdata.phase2.build_embeddings

# GPU 1번 지정 (GPU 0에 다른 작업이 있을 때)
CUDA_VISIBLE_DEVICES=1 uv run python -m avdata.phase2.build_embeddings --limit 5000
CUDA_VISIBLE_DEVICES=1 uv run python -m avdata.phase2.build_embeddings

# 두 GPU 병렬 처리 (속도 ~1.8배, 전체 빌드 권장)
uv run python -m avdata.phase2.build_embeddings --multi-gpu
```

**무엇을 하나요?**  
각 캡션 텍스트를 1,024차원 의미 벡터로 변환하고, 고속 유사도 검색이 가능한 Faiss HNSW 인덱스를 만듭니다.

**임베딩 모델:** `BAAI/bge-m3`
- 다국어 지원, 최대 8,192 토큰
- 코사인 유사도 기반 검색에 최적화

**HNSW (Hierarchical Navigable Small World)란?**  
수십만 벡터 중에서 가장 유사한 것을 `< 100ms` 안에 찾아주는 근사 최근접 이웃(ANN) 알고리즘입니다.

**처리 흐름:**
```
캡션 텍스트
    → bge-m3 모델 fp16 로딩 (배치 크기 64, GPU 메모리 절약)
    → 1,024차원 float32 벡터 (정규화됨)
    → Faiss HNSW 인덱스 추가
    → 파일로 저장
```

**산출물:**
```
data/index/embeddings.npy    ← 원본 임베딩 행렬 [N × 1024]
data/index/hnsw.index        ← Faiss HNSW 인덱스
data/index/clip_ids.json     ← 클립 ID 목록 (Step 2와 동일 파일)
```

> **GPU가 없을 때**: CPU로도 동작하지만 약 6~8시간 소요됩니다.  
> **OOM 방지**: 배치 크기 64 + fp16 적용으로 GPU당 ~2GB만 사용합니다.  
> **두 GPU 사용**: `--multi-gpu` 플래그로 RTX 4090 × 2를 모두 활용할 수 있습니다.

---

## Step 4 — ODD 태그 추출

```bash
# 전체 83,612개 (regex 방식, ~10~20분)
uv run python -m avdata.phase3.extract_odd_tags

# LLM 보완 (낮은 커버리지 클립에 추가 처리)
uv run python -m avdata.phase3.extract_odd_tags --llm --llm-batch 50
```

**무엇을 하나요?**  
영어 서술문 캡션에서 ODD(Operational Design Domain) 속성을 자동으로 추출합니다.  
이 태그는 Step 5의 하이브리드 검색에서 **Level 1 필터**로 사용되어 검색 대상을 97% 이상 줄여줍니다.

**추출하는 ODD 필드:**

| 필드 | 가능한 값 (전체) |
|------|---------|
| `time_of_day` | `day`, `night`, `dawn`, `dusk` |
| `weather` | `clear`, `cloudy`, `rain`, `snow`, `fog` |
| `road_type` | `highway`, `urban`, `intersection`, `parking_lot`, `rural`, `tunnel`, `bridge` |
| `traffic_density` | `free`, `moderate`, `congested` |
| `agent_type` | `pedestrian`, `cyclist`, `motorcycle`, `truck`, `bus`, `emergency_vehicle`, `animal`, `none` |
| `hazard_level` | `none`, `low`, `medium`, `high` |
| `ego_action` | `straight`, `left_turn`, `right_turn`, `uturn`, `lane_change`, `braking`, `stopping`, `reversing` |

**처리 방식:**
```
캡션 텍스트
    → regex 패턴 매칭 (무료, 빠름)
    → ODD 태그 dict
    → (선택) 커버리지 낮은 클립 → LLM(gpt-4o-mini) 보완
```

**산출물:**
```
data/tags/odd_tags.json       ← {clip_id: {field: value, ...}} 전체
data/tags/odd_coverage.json   ← 필드별 커버리지 통계
```

> **GPU 불필요**: 기본 실행은 순수 CPU + Python 표준 라이브러리(`re`)만 사용합니다.  
> `--llm` 옵션 사용 시에만 `OPENAI_API_KEY` 환경변수가 필요합니다.

### ⚠️ Regex 방식의 한계 — 동의어·패러프레이즈 누락

regex는 패턴에 **정확히 일치하는 단어**만 잡습니다.  
캡션 작성자가 다른 표현을 쓰면 해당 필드는 `"unknown"`으로 남습니다.

**필드별 누락 예시:**

| 필드 | 캡션 표현 | 실제 의미 | regex 결과 |
|------|-----------|-----------|------------|
| `traffic_density` | `"cars were slow-moving"` | congested | ❌ `unknown` |
| `traffic_density` | `"stop-and-go traffic"` | congested | ❌ `unknown` |
| `traffic_density` | `"traffic backed up"` | congested | ❌ `unknown` |
| `traffic_density` | `"sparse vehicles on the road"` | free | ❌ `unknown` |
| `weather` | `"drizzle"` | rain | ❌ `unknown` |
| `weather` | `"mist"` / `"haze"` | fog | ❌ `unknown` |
| `weather` | `"slippery road"` | snow | ❌ `unknown` |
| `weather` | `"precipitation"` | rain | ❌ `unknown` |
| `hazard_level` | `"close call"` / `"near miss"` | high | ❌ `unknown` |
| `hazard_level` | `"aggressive driving"` | high | ❌ `unknown` |
| `hazard_level` | `"cut in"` / `"cut off"` | high | ❌ `unknown` |
| `agent_type` | `"car"` / `"vehicle"` / `"van"` / `"SUV"` | (일반 차량) | ❌ 미등록 |

> `traffic_density`와 `hazard_level`이 자연어 표현 다양성으로 인해 커버리지가 가장 낮을 것으로 예상됩니다.

**개선 방법 (커버리지 확인 후 선택):**

| 방법 | 비용 | 설명 |
|------|------|------|
| `_HEURISTICS` 패턴 직접 추가 | 무료 | `extract_odd_tags.py`에 누락 표현 추가 |
| `--llm` 옵션 | OpenAI API 비용 | `unknown` 필드만 gpt-4o-mini로 보완 |
| 임베딩 zero-shot 분류 | GPU 필요 | `bge-m3`로 각 필드 semantic classification |

**권장 순서**: 먼저 regex-only로 전체 실행 → `odd_coverage.json`에서 커버리지 확인 → 낮은 필드만 선택적으로 LLM 보완

---

## Step 5 — 평가

```bash
# 평가셋 자동 생성 — 전체 83,612개 기준 (필수: --sample 83612)
uv run python -m avdata.eval.build_eval_set --sample 83612

# 세 가지 검색 방법 비교 실험
uv run python -m avdata.eval.evaluate
```

> ⚠️ **주의**: `--sample` 없이 실행하면 기본값 5,000개 샘플만 사용합니다.  
> 검색 인덱스는 83,612개 전체를 대상으로 하기 때문에, 정답 클립이 샘플에 없는 클립이면  
> 검색이 올바르게 동작해도 Recall/MRR이 **모두 0**으로 측정됩니다.  
> 반드시 `--sample 83612`로 전체 코퍼스 기준 eval_set을 빌드하세요.

**무엇을 하나요?**  
BM25, 임베딩, 하이브리드 세 가지 검색 방법을 동일 조건에서 비교합니다.

**평가셋 구성 (20개 쿼리):**
```
"pedestrian crossing at night intersection"
"highway driving with truck overtaking"
"vehicle sudden braking ahead"
"foggy conditions reduced visibility"
"animal crossing road wildlife"
... (총 20개)
```

**측정 지표:**

| 지표 | 의미 | 목표 |
|------|------|------|
| `Recall@5` | 상위 5개 결과 중 정답 포함 비율 | > 0.80 |
| `MRR@5` | 첫 번째 정답이 몇 위에 나오는지 역수 평균 | 높을수록 좋음 |
| `Latency (ms)` | 쿼리 1회 응답 시간 | < 500ms |

**산출물:**
```
data/eval/eval_set.json                        ← 평가셋
experiments/experiment_001_results.csv         ← 3가지 방법 비교 결과
```

---

## Step 6 — 분포 분석 시각화

```bash
# 20,000개 샘플 기준 (빠른 확인, ~10분)
uv run python -m avdata.phase4.distribution_analysis --sample 20000

# 전체 83,612개 (정밀 분석, ~30~60분)
uv run python -m avdata.phase4.distribution_analysis
```

**무엇을 하나요?**  
전체 클립 임베딩을 2D로 축소하여 데이터 분포를 시각화하고, 희귀/롱테일 시나리오를 자동으로 발굴합니다.

**처리 흐름:**
```
임베딩 [N × 1024]
    → UMAP 2D 축소 (n_neighbors=15, cosine 거리)
    → KDE 밀도 추정
    → ODD 커버리지 행렬 (시간대×날씨 vs 주행행동)
    → Plotly 인터랙티브 HTML 생성
```

**4가지 시각화 패널:**
1. **밀도 맵** — 저밀도(노란색) = 롱테일 희귀 시나리오
2. **시간대별 분포** — 주간/야간/새벽 클립이 어디 모여있는지
3. **위험도별 분포** — 고위험 클립의 임베딩 공간 위치
4. **ODD 커버리지 행렬** — 수집 갭(빈 셀) 시각화

**산출물:**
```
data/index/distribution.html        ← 인터랙티브 시각화 (브라우저에서 열기)
data/index/longtail_clips.json      ← 밀도 하위 5% 희귀 클립 ID 목록
data/index/umap_coords.parquet      ← 2D 좌표 + 메타데이터
```

---

## 전체 실행 순서 요약

```bash
cd /Data1/home/bskang/AVdata-distirbution

# 0. 환경 확인
uv sync

# 1. 데이터 파악 (5분)
uv run python -m avdata.phase1.explore

# 2. BM25 인덱스 (전체 ~10분)
uv run python -m avdata.phase1.build_bm25

# 3. 임베딩 + Faiss (단일 GPU ~1~2시간 / 두 GPU ~multi-gpu 권장)
uv run python -m avdata.phase2.build_embeddings --multi-gpu

# 4. ODD 태그 (~20분)
uv run python -m avdata.phase3.extract_odd_tags

# 5. 평가
uv run python -m avdata.eval.build_eval_set --sample 83612
uv run python -m avdata.eval.evaluate

# 6. 분포 시각화 (~10분, 20k 샘플)
uv run python -m avdata.phase4.distribution_analysis --sample 20000
```

---

## 생성 파일 트리

```
data/
├── index/
│   ├── bm25s_index/            ← Step 2 산출물
│   ├── clip_ids.json           ← Step 2/3 공유
│   ├── embeddings.npy          ← Step 3 산출물
│   ├── hnsw.index              ← Step 3 산출물
│   ├── distribution.html       ← Step 6 산출물
│   ├── longtail_clips.json     ← Step 6 산출물
│   └── umap_coords.parquet     ← Step 6 산출물
├── tags/
│   ├── odd_tags.json           ← Step 4 산출물
│   └── odd_coverage.json       ← Step 4 산출물
└── eval/
    ├── exploration_summary.json ← Step 1 산출물
    └── eval_set.json           ← Step 5 산출물

experiments/
└── experiment_001_results.csv  ← Step 5 산출물
```
