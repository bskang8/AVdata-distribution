# AVdata-distribution

자율주행(AV) 주행영상 캡션 **83,612개**(원본 영상 306,152개)를 대상으로 한
**데이터 분포 분석 · 의미 검색 · 학습데이터 큐레이션** 연구 코드베이스.

> 목표: 자율주행 학습 데이터의 **분포 편향을 진단·해소**하여 모델 성능을 끌어올린다.
> 단순 검색 시스템이 아니라, "무엇을 더 모아야 하는가"를 데이터로 답하기 위한 실험 인프라다.

---

## 무엇을 하나

1. **의미 검색** — 캡션을 BM25 / 임베딩(`BAAI/bge-m3`) / 하이브리드로 검색하고 성능을 비교한다.
2. **ODD 태깅** — 캡션에서 운영설계영역(시간대·날씨·도로·행동 등) 속성을 추출해 필터·커버리지 분석에 쓴다.
3. **분포 분석** — 임베딩을 2D로 축소하고 밀도·커버리지를 추정해 **롱테일 희귀 시나리오**를 발굴한다.
4. **큐레이션 연구** — 밀도 갭·획득함수·curability 진단으로 "라벨 쓰기 전에 이 tail이 데이터로 고쳐지는 오차인가"를 검증한다(EXP-003).

## 갭 프레임워크

분석의 축이 되는 6개 문제:

| Gap | 내용 |
|-----|------|
| Gap-1 | 평가셋 편향 (키워드 기반 레이블) |
| Gap-2 | Hybrid ≈ Embedding (ODD 필터 실효성 없음) |
| Gap-3 | ODD 커버리지 저조 (36~62%) |
| Gap-4 | 분포 편향 (정상 과다 71%, 희귀 과소) |
| Gap-5 | 워밍업 미처리 |
| Gap-6 | 쿼리 다양성 부족 |

---

## 빠른 시작

```bash
cd /Data1/home/bskang/AVdata-distirbution
uv sync                         # pyproject.toml 기반 환경 복원 (Python ≥ 3.12)
```

### 파이프라인 (Step 1~6)

```bash
uv run python -m avdata.phase1.explore                      # 1. 데이터 탐색
uv run python -m avdata.phase1.build_bm25                   # 2. BM25 키워드 인덱스
uv run python -m avdata.phase2.build_embeddings --multi-gpu # 3. 임베딩 + Faiss HNSW
uv run python -m avdata.phase3.extract_odd_tags             # 4. ODD 태그 추출 (regex, --llm 옵션)
uv run python -m avdata.eval.build_eval_set --sample 83612  # 5. 평가셋 + 검색 비교
uv run python -m avdata.eval.evaluate
uv run python -m avdata.phase4.distribution_analysis --sample 20000  # 6. 분포 시각화
```

각 단계의 상세(옵션·산출물·GPU 요구)는 **[PIPELINE.md](PIPELINE.md)** 참고.

### 서비스

```bash
uv run uvicorn avdata.api.main:app --port 8000                 # FastAPI (Swagger: /docs)
uv run streamlit run src/avdata/ui/app.py --server.port 8501   # Streamlit UI
```

실행 방법 상세는 **[docs/HOW_TO_RUN.md](docs/HOW_TO_RUN.md)**.

---

## 코드 구조

```
src/avdata/
├── phase1/  explore, build_bm25          — 데이터 탐색 + BM25 인덱스
├── phase2/  build_embeddings             — bge-m3 임베딩 + Faiss HNSW
├── phase3/  extract_odd_tags             — ODD 속성 추출 (regex / LLM)
├── phase4/  distribution_analysis        — UMAP + KDE + 커버리지 시각화
├── phase5/  fit_normalizing_flow, detect_gaps  — 밀도 기반 갭 발굴
├── phase6/  fit_sanflow, embedding_cluster     — SANFlow / 클러스터링
├── eval/    build_eval_set, evaluate     — 검색 성능 평가
├── search/  searcher                     — BM25/임베딩/하이브리드 검색기
├── api/     FastAPI 백엔드 (routes: search, clips, odd)
└── ui/      Streamlit 웹 UI

src/caption_refine/                       — 캡션 정제 파이프라인 (Cosmos, 다단계)
experiments/  EXP-001~003                 — 실험별 설계·결과·결론
docs/wiki/                                — 문헌 위키 (분포/임베딩/평가/생성, 33편+)
literature/                               — 논문 원문 + 링크 인덱스
```

## 실험

| ID | 주제 | 상태 |
|----|------|------|
| EXP-001 | BM25 / Embedding / Hybrid 검색 베이스라인 | 완료 (Gap-1·2 발견) |
| EXP-002 | 평가셋 재설계 + SANFlow 밀도 갭 발굴 | 완료 |
| EXP-003 | 데이터 큐레이션 → **curability 진단**으로 피벗 | 진행 중 |

EXP-003은 "어떤 획득함수가 이기나(policy 경쟁)"에서
**"이 tail이 데이터로 고칠 수 있는 오차인가를 라벨 쓰기 전에 진단"**으로 질문을 바꿨다.
현재 기준점은 [`experiments/EXP-003/REDESIGN_BRIEF.md`](experiments/EXP-003/REDESIGN_BRIEF.md).

## 문서

- **[PIPELINE.md](PIPELINE.md)** — 6단계 파이프라인 전체 가이드
- **[docs/HOW_TO_RUN.md](docs/HOW_TO_RUN.md)** — API/UI 실행법
- **[RESEARCH_LOG.md](RESEARCH_LOG.md)** — 연구 타임라인·설계 결정 이력
- **[docs/wiki/INDEX.md](docs/wiki/INDEX.md)** — 문헌 위키 색인

## 스택

`uv` · Python 3.12 · sentence-transformers(bge-m3) · faiss-cpu · bm25s · normflows · UMAP · FastAPI · Streamlit
