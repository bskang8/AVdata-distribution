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

| 기준 | 통과 조건 | 실제 결과 | 판정 |
|------|----------|----------|------|
| Embedding > BM25 | Embedding Recall@5 ≥ BM25 | 0.520 < 0.900 | ❌ 기각 |
| Hybrid ≥ max(BM25, Embedding) | Hybrid Recall@5 ≥ 0.900 | 0.520 < 0.900 | ❌ 기각 |
| Embedding 지연 < 200ms | 평균 지연 ≤ 200ms | 929ms > 200ms | ❌ 기각 |

**기각의 의미:**

- **기준 1 (Embedding < BM25)**: 평가셋 정답이 키워드 포함 여부로 생성되어 BM25에 구조적으로 유리하다. Embedding이 의미상 올바른 클립을 반환해도 정답으로 인정되지 않는 경우가 다수 발생했다 (예: "pedestrian suddenly enters road" 쿼리에서 Embedding Recall@5 = 0.0). 즉, Embedding의 실제 검색 품질이 낮다기보다 **평가 방법 자체가 편향**되어 있을 가능성이 높다.

- **기준 2 (Hybrid = Embedding)**: Hybrid가 BM25와 Embedding을 결합하지 못하고 Embedding과 동일한 결과를 냈다. ODD 필터가 사실상 동작하지 않아 Hybrid가 Embedding과 차별화되지 않은 것으로 추정된다.

- **기준 3 (지연 초과)**: 평균 929ms는 첫 쿼리의 cold start(18,485ms, 모델 초기 로드)가 포함된 값이다. 2번째 쿼리 이후 중앙값은 5.56ms로 기준(200ms)을 크게 만족한다. **워밍업을 포함한 측정 설계의 문제**이며 실제 서비스 지연이 200ms를 초과한다는 의미는 아니다.

## 실행 커맨드

```bash
# 환경 준비
uv sync

# BM25 인덱스 빌드
uv run python -m avdata.phase1.build_bm25

# 임베딩 + HNSW 빌드 (전체 299k, GPU 권장)
uv run python -m avdata.phase2.build_embeddings

# ODD 태그 추출
uv run python -m avdata.phase3.extract_odd_tags

# 분포 분석 시각화
uv run python -m avdata.phase4.distribution_analysis

# 평가셋 생성 (전체 코퍼스 기준)
uv run python -m avdata.eval.build_eval_set

# 3종 방법 평가
uv run python -m avdata.eval.evaluate
```
