# Research Log — AV Data Distribution Analysis

연구의 타임라인을 기록한다. 각 행은 실험, 문헌 투입, 설계 결정 중 하나다.

---

## Timeline

| 날짜 | 유형 | 내용 | 링크 |
|------|------|------|------|
| 2026-05-15 | 실험 | Phase1: 데이터 탐색 완료 (83,612 captions 확인) | `experiments/EXP-001/` |
| 2026-05-17 | 실험 | Phase2: BAAI/bge-m3 임베딩 생성 완료 (327MB) | `data/index/embeddings.npy` |
| 2026-05-18 | 실험 | Phase3: ODD 태그 추출 완료 (regex-only) | `data/tags/odd_coverage.json` |
| 2026-05-18 | 실험 | Phase2: BM25 인덱스 빌드 완료 | `data/index/bm25s_index/` |
| 2026-05-20 | 실험 | EXP-001 완료: BM25/Embedding/Hybrid 성능 비교 | `experiments/EXP-001/analysis.md` |
| 2026-05-20 | 결정 | Hybrid search가 embedding과 동일한 결과 → ODD 필터 실효성 없음 확인 | `experiments/EXP-001/analysis.md §Gap-2` |
| 2026-06-01 | 결정 | 연구 관리 구조 수립 (iterative experiment framework) | 이 문서 |
| — | 실험 | EXP-002: 평가셋 품질 개선 (의미 기반 쿼리 + LLM 검수) | `experiments/EXP-002/` |

---

## 실험 목록

| ID | 제목 | 상태 | 핵심 발견 |
|----|------|------|----------|
| EXP-001 | BM25 / Embedding / Hybrid 베이스라인 | ✅ 완료 | 평가셋이 키워드 기반 → BM25 유리한 구조적 편향 |
| EXP-002 | 평가셋 재설계 + 의미 검색 정밀 측정 | 🔲 설계 중 | — |
| EXP-003 | LLM 기반 ODD 태그 품질 개선 | 🔲 대기 | — |
| EXP-004 | Hybrid search 재설계 (소프트 필터) | 🔲 대기 | — |

---

## 문헌 → 실험 연결

| 문헌 | 관련 갭 | 검토 예정 실험 |
|------|--------|--------------|
| (추가 예정) | — | — |

---

## 주요 설계 결정 이력

| 날짜 | 결정 | 근거 |
|------|------|------|
| 2026-05-18 | ODD 추출 regex-only (LLM fallback 미사용) | 속도 우선, LLM 비용 절감 |
| 2026-05-20 | 평가셋 20개 쿼리, keyword_relevance() 기반 | 빠른 구축 우선 → 이후 EXP-002에서 개선 예정 |
| 2026-06-01 | 단일 master 브랜치 + git tag 방식 | 실험이 순차적, merge 비용 절감 |
