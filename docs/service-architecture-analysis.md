# 서비스 아키텍처 분석 — 실험 반복 환경에서의 유지 가능성

**작성일**: 2026-06-01  
**대상 파일**: `src/avdata/api/`, `src/avdata/ui/app.py`, `src/avdata/search/searcher.py`, `src/avdata/config.py`

---

## 1. 현재 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                       현재 아키텍처                              │
│                                                                 │
│  [Streamlit UI]  ──imports──▶  [Searcher]  ◀──imports──  [FastAPI]
│   src/avdata/ui/app.py          search/searcher.py    api/routes/search.py
│                                      │
│                                      ▼
│                              [config.py] — 경로 하드코딩
│                                      │
│                            data/index/hnsw.index       ← 단일 파일
│                            data/index/bm25s_index/     ← 단일 디렉토리
│                            data/tags/odd_tags.json     ← 단일 파일
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 서비스 레이어별 역할

| 레이어 | 파일 | 역할 | 서비스 의존성 |
|--------|------|------|-------------|
| **Config** | `config.py` | 경로, 상수, ODD taxonomy 정의 | 모든 레이어가 import |
| **Searcher** | `search/searcher.py` | BM25/Embedding/Hybrid 검색 로직 | API + UI 양쪽에서 직접 인스턴스화 |
| **FastAPI** | `api/main.py`, `api/routes/` | REST API (/v1/search, /v1/clips, /v1/odd) | 독립 프로세스 |
| **Streamlit** | `ui/app.py` | 웹 UI, Searcher 직접 호출 | 독립 프로세스 |

---

## 2. 실험 반복 시 발생하는 구체적 문제

### 문제 1 🔴 실험 실행이 서비스를 파괴한다

**현상**: 새 실험을 위해 파이프라인을 실행하면 아티팩트가 덮어쓰인다.

```
# EXP-001 서비스가 실행 중인 상태에서 EXP-002 파이프라인 실행 시:
uv run python -m avdata.phase2.build_embeddings   # ← hnsw.index 덮어쓰기
uv run python -m avdata.phase3.extract_odd_tags   # ← odd_tags.json 덮어쓰기
```

FastAPI와 Streamlit은 시작 시 `hnsw.index`를 메모리에 로드하는데,  
실험 파이프라인이 이 파일을 교체하면 세 가지 결과 중 하나가 발생한다:

- 서버 크래시 (faiss index 손상)
- 서버는 살아있지만 새 인덱스를 읽지 못함 (이전 메모리 유지)
- 결과가 바뀌었는데 버전이 표시되지 않아 혼란

**영향 범위**: 새 실험을 실행할 때마다 서비스를 수동으로 내리고 올려야 한다.

---

### 문제 2 🔴 UI와 API가 다른 코드 경로를 사용한다

**현상**: Streamlit UI는 FastAPI를 통하지 않고 Searcher를 직접 호출한다.

```python
# ui/app.py — FastAPI를 거치지 않고 Searcher 직접 인스턴스화
@st.cache_resource(show_spinner="인덱스 및 모델 로딩 중…")
def load_searcher() -> Searcher:
    return Searcher()          # ← API와 별개의 Searcher 인스턴스

# api/deps.py — 별도 Searcher 인스턴스
def init_searcher() -> None:
    global _searcher
    _searcher = Searcher()    # ← UI와 별개
```

**결과**:
- Searcher 로직을 수정하면 UI/API 양쪽에서 독립적으로 동작이 달라질 수 있다
- 새 검색 method를 추가할 때 ui/app.py의 radio 버튼, api/models.py의 Literal enum을 **따로** 수동 업데이트해야 한다
- 두 프로세스가 메모리에 각각 BAAI/bge-m3 (약 2GB)를 올린다 → 메모리 낭비

---

### 문제 3 🟠 검색 method가 코드 3곳에 하드코딩된다

새 검색 method(예: ColBERT, sparse retrieval)를 추가할 때 수정해야 하는 파일:

```python
# 1. api/models.py
method: Literal["bm25", "embedding", "hybrid"]   # ← Literal에 추가

# 2. search/searcher.py
def search(self, method: Literal["bm25", "embedding", "hybrid"], ...):
    if method == "bm25": ...
    elif method == "embedding": ...
    else: ...                    # ← elif/else 추가

# 3. ui/app.py
method = st.sidebar.radio(
    "검색 방법",
    ["hybrid", "embedding", "bm25"],   # ← 리스트에 추가
    format_func=lambda m: {"hybrid": "🔀 ...", ...}[m],  # ← dict에 추가
)
```

3곳 중 하나라도 빠뜨리면 런타임 오류 또는 UI 불일치가 발생한다.

---

### 문제 4 🟠 ODD taxonomy 변경이 전체에 전파된다

EXP-003에서 ODD 필드를 추가하거나 값을 변경하면:

```python
# config.py — taxonomy 변경
ODD_FIELDS = {
    "traffic_density": ["free", "moderate", "congested", "gridlock"],  # 값 추가
    "scene_complexity": ["simple", "complex"],                          # 필드 추가
}
```

이 변경이 영향을 주는 곳:
- `phase3/extract_odd_tags.py` — 추출 로직 수정 필요
- `ui/app.py` — 사이드바 필터 UI 자동 반영 (ODD_FIELDS 참조 중이므로 OK)
- `phase4/distribution_analysis.py` — UMAP 컬러링 컬럼 변경 필요
- `data/tags/odd_tags.json` — 전체 재생성 필요 (83k 클립)
- 기존 EXP-001 결과와 비교 불가 (taxonomy 기준이 달라짐)

---

### 문제 5 🟡 실험별 아티팩트 버전 관리 없음

현재 아티팩트 구조:
```
data/index/
├── hnsw.index          ← EXP-001? EXP-002? 알 수 없음
├── bm25s_index/
└── embeddings.npy
data/tags/
└── odd_tags.json       ← regex-only? LLM fallback? 알 수 없음
```

어떤 실험의 결과물이 현재 서비스 중인지 추적할 수 없다.  
서비스를 복원하거나 과거 실험과 비교할 방법이 없다.

---

## 3. 유지 가능성 종합 평가

| 시나리오 | 현재 구조의 대응 | 평가 |
|---------|---------------|------|
| 새 실험 실행 (파이프라인 재실행) | 서비스 중단 필요 | 🔴 불가 (수동 개입 필수) |
| 새 검색 method 추가 | 3개 파일 동시 수정 | 🟠 위험 (누락 가능) |
| 실험 결과 A/B 비교 (서비스에서) | 불가 | 🔴 불가 |
| 이전 실험 아티팩트로 롤백 | 불가 (백업 없음) | 🔴 불가 |
| ODD 필드 추가/수정 | 다수 파일 수정 | 🟠 번거로움 |
| 메모리 효율 | UI + API가 각각 2GB 모델 로드 | 🟡 낭비 |

**결론**: 현재 구조는 EXP-002~004 수준의 변경이 누적되면 서비스 안정성이 크게 저하된다.  
단, 완전한 재설계는 연구 속도를 오히려 늦춘다. 핵심 3가지만 개선하면 충분하다.

---

## 4. 권고 개선안

### 개선 1 ✅ 아티팩트 버전 관리 (즉시, 30분)

**아이디어**: 실험별 아티팩트를 별도 폴더에 저장하고, 서비스는 심볼릭 링크(`active`)를 읽는다.

**변경 후 디렉토리 구조**:
```
data/
├── artifacts/
│   ├── exp-001/            ← EXP-001 아티팩트 (영구 보존)
│   │   ├── hnsw.index
│   │   ├── bm25s_index/
│   │   ├── embeddings.npy
│   │   └── odd_tags.json
│   └── exp-002/            ← EXP-002 아티팩트 (실험 완료 후 저장)
│       └── ...
├── active -> artifacts/exp-001/   ← 심볼릭 링크, 서비스는 여기를 읽음
├── eval/
└── tags/
    └── odd_coverage.json   ← active 아티팩트 기반으로 생성
```

**config.py 변경**:
```python
# 변경 전
FAISS_INDEX_PATH = INDEX_DIR / "hnsw.index"

# 변경 후
ACTIVE_DIR       = DATA_DIR / "active"         # 심볼릭 링크
FAISS_INDEX_PATH = ACTIVE_DIR / "hnsw.index"
BM25_INDEX_DIR   = ACTIVE_DIR / "bm25s_index"
ODD_TAGS_PATH    = ACTIVE_DIR / "odd_tags.json"
```

**실험 전환 방법** (서버 재시작 없이):
```bash
# 새 실험 완료 후
ln -sfn artifacts/exp-002 data/active

# FastAPI는 --reload 모드에서 파일 변경 감지 후 자동 재시작
# Streamlit은 수동 재시작 필요 (캐시 초기화)
kill $(lsof -ti :8501) && uv run streamlit run src/avdata/ui/app.py --server.port 8501 &
```

**파이프라인 수정** — 실험별 출력 디렉토리 지정:
```bash
# 실험 실행 시 출력 경로를 실험 폴더로 지정
uv run python -m avdata.phase2.build_embeddings --output-dir data/artifacts/exp-002
uv run python -m avdata.phase3.extract_odd_tags --output-dir data/artifacts/exp-002
```

---

### 개선 2 ✅ Streamlit UI → FastAPI 호출로 전환 (중기, 2~3시간)

**아이디어**: Streamlit이 Searcher를 직접 부르지 않고, FastAPI 엔드포인트를 HTTP로 호출한다.  
서비스 로직이 한 곳(FastAPI)에만 존재하게 된다.

**ui/app.py 변경 핵심**:
```python
# 변경 전 — Searcher 직접 호출
@st.cache_resource
def load_searcher() -> Searcher:
    return Searcher()

results, latency_ms = searcher.search(query, method=method, ...)

# 변경 후 — FastAPI HTTP 호출
import httpx

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

def api_search(query: str, method: str, odd_filter: dict, top_k: int) -> dict:
    resp = httpx.post(
        f"{API_BASE}/v1/search",
        json={"query": query, "method": method, "odd_filter": odd_filter, "top_k": top_k},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()
```

**장점**:
- Searcher 코드가 한 곳에만 존재 → 실험 중 로직 변경이 API에만 반영되면 됨
- 모델을 메모리에 한 번만 로드 (FastAPI만)
- FastAPI가 꺼져 있으면 UI에서 명확한 오류 메시지 표시

**단점**: 로컬 개발 시 FastAPI를 항상 먼저 실행해야 함 (현재도 권장 순서이므로 실질적 불이익 없음)

---

### 개선 3 ✅ 검색 method 등록 방식 (중기, 1~2시간)

**아이디어**: 하드코딩된 `Literal["bm25", "embedding", "hybrid"]` 대신,  
Searcher가 등록된 method 목록을 동적으로 제공한다.

**Searcher 변경**:
```python
# search/searcher.py
class Searcher:
    _registry: dict[str, callable] = {}

    def register(self, name: str, fn):
        self._registry[name] = fn

    def available_methods(self) -> list[str]:
        return list(self._registry.keys())

    def search(self, query: str, method: str, ...):
        if method not in self._registry:
            raise ValueError(f"Unknown method: {method}. Available: {self.available_methods()}")
        return self._registry[method](query, ...)
```

**UI 변경**: `["hybrid", "embedding", "bm25"]` → `searcher.available_methods()` 자동 조회

**효과**: 새 실험에서 method 추가 시 Searcher에만 등록하면 UI/API에 자동 반영된다.

---

## 5. 단계별 실행 계획

### Phase A — 즉시 (오늘, 30분)

실험을 실행하기 전에 아티팩트를 현재 상태로 스냅샷한다:

```bash
mkdir -p data/artifacts/exp-001
cp data/index/hnsw.index          data/artifacts/exp-001/
cp -r data/index/bm25s_index      data/artifacts/exp-001/
cp data/index/clip_ids.json       data/artifacts/exp-001/
cp data/index/embeddings.npy      data/artifacts/exp-001/
cp data/tags/odd_tags.json        data/artifacts/exp-001/

# 심볼릭 링크 생성
ln -sfn artifacts/exp-001 data/active

echo "EXP-001 아티팩트 스냅샷 완료"
```

이후 config.py의 경로를 `data/active/`로 변경한다.

### Phase B — 단기 (EXP-002 시작 전)

- Streamlit UI → FastAPI 호출로 전환 (개선 2)
- 파이프라인 스크립트에 `--output-dir` 옵션 추가

### Phase C — 중기 (EXP-003~004 시작 전)

- Method 등록 방식 도입 (개선 3)
- `/health` 엔드포인트에 현재 활성 아티팩트 버전 정보 추가

---

## 6. 변경하지 않아도 되는 것

연구 맥락에서는 다음은 현재 구조를 유지해도 충분하다:

| 항목 | 이유 |
|------|------|
| FastAPI 버전 관리 (`/v1/`) | 현재 단일 사용자, 하위 호환성 불필요 |
| 분산 인덱스 (Milvus 등) | 83k 클립 규모에서 Faiss HNSW로 충분 |
| 자동 스케일링, 컨테이너화 | 로컬 연구 환경에서 불필요 |
| CI/CD 파이프라인 | 단일 개발자, 자동화 오버헤드가 이득보다 큼 |

---

## 7. 요약

| 개선 | 효과 | 난이도 | 시기 |
|------|------|--------|------|
| **아티팩트 버전 관리** (심볼릭 링크) | 실험 중 서비스 보호, 롤백 가능 | 낮음 (30분) | 즉시 |
| **UI → API 호출 전환** | 로직 단일화, 메모리 절감 | 중간 (2시간) | EXP-002 전 |
| **Method 동적 등록** | 새 method 추가 시 파일 1개만 수정 | 중간 (1시간) | EXP-003 전 |
