# AVdata-distirbution vs cosmos-dataset-search 기술 비교 분석

> 분석 일자: 2026-05-20  
> 목적: cosmos-dataset-search(CDS)의 기술을 수용해 현재 프로젝트를 고도화할 포인트 도출

---

## 1. 프로젝트 개요

### AVdata-distirbution (현재)

```
역할:     자율주행 데이터 시나리오 분포 분석 및 시맨틱 검색 파이프라인
형태:     연구용 CLI 배치 파이프라인 (웹 API 없음)
데이터:   83,612개 AV 드라이빙 클립 + 영어 내러티브 캡션
검색:     BM25 / Dense Embedding / Hybrid (ODD 필터 + 임베딩 재순위)
특화:     ODD 시나리오 분류, 분포 분석, 장기 평가 프레임워크
```

### cosmos-dataset-search (CDS, NVIDIA)

```
역할:     대규모 비디오 데이터셋 시맨틱 검색 프로덕션 서비스
형태:     FastAPI REST API + Streamlit UI + Docker/K8s 배포
데이터:   다중 컬렉션, Milvus DB 기반
검색:     멀티모달 Dense Embedding (텍스트 / 비디오 / 세션 클립)
특화:     GPU 가속 검색, 프로덕션 인프라, 쿼리 정제(Linear Probe)
```

---

## 2. 아키텍처 전체 비교

| 항목 | AVdata-distirbution | cosmos-dataset-search |
|---|---|---|
| **API 레이어** | 없음 (Python import만) | FastAPI REST API (v1) |
| **웹 UI** | 없음 | Streamlit |
| **배포** | 로컬 CLI | Docker Compose / Kubernetes Helm |
| **관측성** | 없음 | Prometheus + Grafana + OpenTelemetry |
| **동시성** | 없음 | AnyIO 스레드풀 (100 concurrent) |
| **컬렉션 관리** | 단일 인덱스 고정 | 다중 컬렉션 CRUD |
| **인증** | 없음 | Kubernetes Secrets / NVCF |

---

## 3. 벡터 검색 엔진 비교

| 항목 | Faiss HNSW (현재) | Milvus 2.6.2 (CDS) |
|---|---|---|
| **인덱스 타입** | IndexHNSWFlat (M=32) | GPU_CAGRA / IVF_PQ / HNSW 선택 가능 |
| **GPU 가속** | 없음 (CPU 전용) | NVIDIA cuVS GPU_CAGRA |
| **영속성** | 파일 기반 (.index) | 완전한 DB 서버 (Etcd + MinIO) |
| **스케일** | 단일 노드, 수십만 벡터 | 샤딩 + 파티셔닝, 수십억 벡터 |
| **메타데이터 필터** | Python in-memory 루프 (검색 후) | DB 내부 boolean 필터 (검색과 동시) |
| **증분 인제스트** | 전체 재구축 필요 | 실시간 document insert 지원 |
| **최대 top_k** | 제한 없음 | 16,000 |

**핵심 격차:** 현재의 Hybrid 검색은 ODD 필터를 Python 루프로 수행하므로,
필터 대상이 수만 개일 때 latency가 증가합니다. Milvus는 벡터 검색과 메타데이터
필터를 **DB 엔진 내부에서 동시에** 실행해 이 문제를 근본적으로 해결합니다.

---

## 4. 임베딩 모델 비교

| 항목 | BAAI/bge-m3 (현재) | Cosmos-Embed NIM (CDS) |
|---|---|---|
| **차원** | 1,024D | 256D |
| **입력 모달리티** | 텍스트(캡션) 전용 | 텍스트 + 비디오 + 세션 클립 |
| **언어** | 100+ 언어 (다국어) | 영어 중심 (비디오 특화) |
| **추론 방식** | 로컬 GPU (SentenceTransformer) | NIM 마이크로서비스 API 호출 |
| **비용** | 무료 (자체 GPU) | NVIDIA NIM API 비용 |
| **최대 토큰** | 8,192 토큰 | 비디오 길이 기반 |

**핵심 격차:** 현재는 **텍스트 쿼리 → 텍스트 캡션** 매핑만 가능합니다.
83,612개 캡션이 있는 클립만 검색 대상이며, 나머지 222,540개 영상(캡션 없음)은
검색 불가입니다. CDS의 Cosmos-Embed를 도입하면 **실제 비디오 → 비디오**
직접 크로스 모달 검색이 가능해집니다.

---

## 5. 검색 전략 비교

| 전략 | 현재 프로젝트 | CDS |
|---|---|---|
| **BM25 키워드** | ✅ bm25s 구현 | ❌ 없음 |
| **Dense Embedding ANN** | ✅ Faiss HNSW | ✅ Milvus ANN |
| **ODD/메타데이터 필터** | ✅ Python in-memory | ✅ Milvus 내부 필터 |
| **하이브리드 (2단계)** | ✅ ODD 필터 → 임베딩 재순위 | ❌ 단일 ANN + 필터 |
| **비디오 직접 쿼리** | ❌ 없음 | ✅ VideoQuery, SessionSegmentQuery |
| **사전 계산 임베딩 쿼리** | ❌ 없음 | ✅ EmbeddingQuery |
| **쿼리 학습/정제** | ❌ 없음 | ✅ Linear Probe |
| **반경 검색(Radius Search)** | ❌ 없음 | ✅ 유사도 임계값 기반 |
| **복수 컬렉션 동시 검색** | ❌ 없음 | ✅ /v1/retrieval cross-collection |

---

## 6. 메타데이터/필터 시스템 비교

| 항목 | ODD 태그 (현재) | CDS 메타데이터 |
|---|---|---|
| **필드 구조** | 고정 7개 ODD 필드 | 동적 스키마 (자유 정의) |
| **추출 방법** | 정규식 + GPT-4o-mini 폴백 | 외부 주입 (인덱싱 시 직접 첨부) |
| **필터 적용 위치** | Python 메모리 (검색 후 필터) | Milvus 엔진 내부 (검색 중 필터) |
| **복잡 조건 지원** | AND/OR 중첩 dict | AND/OR/NOT + in/not in |
| **커버리지 분석** | ✅ odd_coverage.json | ❌ 없음 |

### 현재 ODD 필드 (7개)

```python
ODD_FIELDS = {
    "time_of_day":     ["day", "night", "dawn", "dusk"],
    "weather":         ["clear", "cloudy", "rain", "snow", "fog"],
    "road_type":       ["highway", "urban", "intersection", "parking_lot",
                        "rural", "tunnel", "bridge"],
    "traffic_density": ["free", "moderate", "congested"],
    "agent_type":      ["pedestrian", "cyclist", "motorcycle", "truck",
                        "bus", "emergency_vehicle", "animal", "none"],
    "hazard_level":    ["none", "low", "medium", "high"],
    "ego_action":      ["straight", "left_turn", "right_turn", "uturn",
                        "lane_change", "braking", "stopping", "reversing"],
}
```

### 현재 ODD 커버리지 (실측값)

| 필드 | 커버리지 | 미분류(unknown) |
|---|---|---|
| road_type | 97.1% | 2,463개 |
| agent_type | 100.0% | 0개 |
| ego_action | 100.0% | 0개 |
| hazard_level | 84.9% | 12,625개 |
| time_of_day | 61.7% | 31,996개 |
| weather | 50.9% | 41,083개 |
| traffic_density | 36.3% | 53,297개 |

---

## 7. 데이터 인제스트 비교

| 항목 | 현재 | CDS |
|---|---|---|
| **인제스트 방법** | 배치 CLI 스크립트 | REST API (base64 / URL / 임베딩) |
| **대량 인제스트** | 없음 (전체 재구축) | Parquet + S3 비동기 job |
| **증분 추가** | 불가 | 실시간 document insert |
| **중복 처리** | 없음 | MUST_CHECK / SKIP / IGNORE 모드 |
| **스토리지** | 로컬 파일시스템 | S3 호환 오브젝트 스토리지 |
| **영상 접근** | 로컬 경로 직접 | Presigned URL (1시간 TTL) |

---

## 8. 현재 프로젝트만의 강점 (CDS에 없는 기능)

| 기능 | 설명 | 관련 파일 |
|---|---|---|
| **BM25 키워드 검색** | 캡션 텍스트 정확 키워드 매칭 | `phase1/build_bm25.py` |
| **ODD 시나리오 자동 분류** | 자율주행 도메인 7개 필드 정규식 추출 | `phase3/extract_odd_tags.py` |
| **UMAP 분포 시각화** | 임베딩 공간 2D 투영, 클러스터 시각화 | `phase4/distribution_analysis.py` |
| **KDE 밀도 추정** | 데이터 희소성 정량화 | `phase4/distribution_analysis.py` |
| **Long-tail 클립 식별** | 밀도 하위 5% 희귀 시나리오 자동 추출 | `data/index/longtail_clips.json` |
| **ODD 커버리지 히트맵** | 시나리오 조합별 데이터 공백 발견 | `data/tags/odd_coverage.json` |
| **정량 평가 프레임워크** | Recall@K, MRR@K 벤치마크 | `eval/evaluate.py` |

---

## 9. 수용 검토 포인트 (우선순위 순)

### ① FastAPI REST API 레이어 추가 — 최우선 / 즉시 가능

현재 `Searcher` 클래스는 이미 깔끔하게 설계되어 있어 HTTP 래핑이 용이합니다.
CDS의 API 구조를 참고해 최소한의 엔드포인트를 추가합니다.

**참고 파일:** `cosmos-dataset-search/src/visual_search/v1/apis/search.py`

**제안 엔드포인트:**
```
POST /v1/search
     body: {query, method, odd_filter, top_k}
     → SearchResult 리스트 + latency

GET  /v1/clips/{clip_id}
     → 캡션 텍스트, ODD 태그, 영상 경로

GET  /v1/odd/coverage
     → 필드별 커버리지 통계

GET  /v1/distribution/longtail
     → 밀도 하위 5% 클립 목록
```

**기대 효과:** 현재 Python import 전용인 파이프라인을 어떤 클라이언트에서도 호출 가능하게 전환.

---

### ② Streamlit 검색 UI — 빠른 체감 효과

CDS의 `ui/streamlit/retrieval.py` 구조를 참고해 사용자 인터페이스를 구축합니다.

**참고 파일:** `cosmos-dataset-search/src/visual_search/ui/streamlit/retrieval.py`

**제안 구성:**
- 상단: 텍스트 쿼리 입력창 + 검색 방법 선택 (BM25 / Embedding / Hybrid)
- 사이드바: ODD 필터 (time_of_day, weather, road_type 등 드롭다운)
- 결과: 클립 ID, 스코어, 캡션 미리보기, 영상 썸네일 그리드
- 탭 추가: 분포 히트맵(`distribution.html` 임베드), ODD 커버리지 차트

**기대 효과:** 비개발자도 시나리오 탐색 가능, 데이터 공백 발견 인터페이스 제공.

---

### ③ Milvus 마이그레이션 — 중장기 / 스케일 시 필요

현재 83,612클립 규모에서 Faiss HNSW는 충분하지만, 다음 조건에서 Milvus가 필요합니다:
- 클립 수가 수백만으로 증가할 때
- 동시 사용자 요청이 발생할 때
- ODD 필터 latency가 병목이 될 때

**참고 파일:**
```
cosmos-dataset-search/src/haystack/components/milvus/document_store.py
cosmos-dataset-search/src/haystack/components/milvus/embedding_retriever.py
cosmos-dataset-search/src/haystack/components/milvus/filter_utils.py
```

**마이그레이션 전략:**
1. `MilvusDocumentStore`를 현재 `Searcher._load_faiss()`와 교체
2. ODD 태그 7개 필드를 Milvus 동적 필드로 저장
3. `search_hybrid()`의 Python 필터 루프 → Milvus boolean 필터로 교체
4. GPU_CAGRA 인덱스로 검색 latency 10배 이상 단축 예상

**기대 효과:** 필터 latency 제거, 동시성 확보, 증분 인덱싱 지원.

---

### ④ 비디오 직접 쿼리 지원 — 중장기 / NIM 접근 전제

Cosmos-Embed NIM 접근이 가능하다면 텍스트 캡션 없이
**실제 비디오 클립 → 유사 클립 검색**이 가능해집니다.

**참고 파일:**
```
cosmos-dataset-search/src/haystack/components/video/cosmos_video_embedder.py
```

**현재 한계:**
- 캡션 파일이 존재하는 83,612개 클립만 검색 가능
- 나머지 222,540개 영상(캡션 없음) 검색 불가

**도입 시 확장:**
- 비디오 임베딩으로 전체 306,152개 클립 인덱싱 가능
- `VideoQuery`, `SessionSegmentQuery` 지원
- 텍스트 ↔ 비디오 크로스 모달 검색

---

### ⑤ Linear Probe 쿼리 정제 — 선택적 개선

CDS의 `LinearProbeQueryLearner` 로직을 참고해, 사용자가 검색 결과에
"관련/비관련" 피드백을 주면 쿼리 임베딩을 실시간으로 정제하는 기능입니다.

**참고 파일:**
```
cosmos-dataset-search/src/haystack/components/linear_probe/
```

**적용 시나리오:**
- 희귀 시나리오(long-tail) 탐색 시 초기 쿼리 결과가 부정확한 경우
- 사용자가 "이 클립은 맞다 / 틀리다" 피드백 → 쿼리 벡터 자동 보정
- 반복 검색 없이 관련 클립 밀집 영역으로 수렴

---

### ⑥ Parquet 벌크 인제스트 — 데이터 추가 시

현재는 새 클립 추가 시 `build_bm25.py`와 `build_embeddings.py`를 전체 재실행해야 합니다.
CDS의 Parquet + S3 기반 비동기 bulk insert 방식을 도입하면 증분 인덱싱이 가능해집니다.

**참고 파일:**
```
cosmos-dataset-search/src/visual_search/v1/apis/bulk_indexing.py
```

---

## 10. 수용 우선순위 요약

```
즉시 가능 (1~2주)
├── ① FastAPI REST API 레이어
└── ② Streamlit 검색 UI

중기 (1~3개월)
├── ③ Milvus 마이그레이션 (스케일 필요 시)
└── ⑤ Linear Probe 쿼리 정제

장기 (3개월+, 외부 의존성)
├── ④ 비디오 직접 쿼리 (Cosmos-Embed NIM 접근 전제)
└── ⑥ Parquet 벌크 인제스트
```

---

## 11. 기술 스택 전체 비교표

| 구성요소 | 현재 | CDS | 수용 방향 |
|---|---|---|---|
| 벡터 DB | Faiss HNSW (파일) | Milvus 2.6.2 (GPU) | → Milvus 마이그레이션 검토 |
| 임베딩 모델 | BAAI/bge-m3 (1024D, 텍스트) | Cosmos-Embed (256D, 멀티모달) | → 멀티모달 도입 (NIM 전제) |
| BM25 | bm25s ✅ | 없음 ❌ | 현재 유지 (CDS 대비 강점) |
| REST API | 없음 ❌ | FastAPI ✅ | → FastAPI 추가 |
| 웹 UI | 없음 ❌ | Streamlit ✅ | → Streamlit 추가 |
| ODD 분류 | 정규식 + LLM ✅ | 없음 ❌ | 현재 유지 (CDS 대비 강점) |
| 분포 분석 | UMAP + KDE ✅ | 없음 ❌ | 현재 유지 (CDS 대비 강점) |
| 평가 프레임워크 | Recall@K, MRR@K ✅ | 없음 ❌ | 현재 유지 (CDS 대비 강점) |
| 쿼리 정제 | 없음 ❌ | Linear Probe ✅ | → 선택적 도입 |
| 모니터링 | 없음 ❌ | Prometheus + Grafana ✅ | → API 도입 시 함께 |
| 배포 | 로컬 CLI ❌ | Docker/K8s ✅ | → API 도입 후 컨테이너화 |
