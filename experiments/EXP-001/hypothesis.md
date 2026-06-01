# EXP-001 · BM25 vs Embedding vs Hybrid 베이스라인

## 가설

> Embedding 기반 검색이 의미론적 쿼리(예: "pedestrian suddenly enters road")에서
> BM25보다 높은 Recall@5를 달성하고, Hybrid는 두 방법을 결합해 최고 성능을 낸다.

## 검증 기준

| 기준 | 통과 조건 |
|------|----------|
| Embedding > BM25 (의미 쿼리) | Recall@5 평균에서 Embedding ≥ BM25 |
| Hybrid ≥ max(BM25, Embedding) | Hybrid Recall@5 ≥ 두 단일 방법 중 최댓값 |
| Embedding 지연 < 200ms | 평균 지연 200ms 이하 |

## 결과 요약

모든 검증 기준이 **기각**됨 → `analysis.md` 참조.

## 실행 커맨드

```bash
# 환경 준비
uv sync

# BM25 인덱스 빌드
uv run python -m avdata.phase1.build_bm25

# 임베딩 + HNSW 빌드 (전체 83k, GPU 권장)
uv run python -m avdata.phase2.build_embeddings

# ODD 태그 추출
uv run python -m avdata.phase3.extract_odd_tags

# 평가셋 생성 (전체 코퍼스 기준)
uv run python -m avdata.eval.build_eval_set --sample 83612

# 3종 방법 평가
uv run python -m avdata.eval.evaluate
```
