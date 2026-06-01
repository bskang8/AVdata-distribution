# EXP-002 · 평가셋 재설계 — 의미 기반 쿼리 + LLM 레이블링

**상태**: 🔲 설계 중  
**대응 갭**: EXP-001/analysis.md §Gap-1, §Gap-5, §Gap-6

---

## 배경

EXP-001의 평가셋은 `keyword_relevance()`(키워드 완전 일치)로 정답을 결정했다.  
이는 BM25에 유리한 구조적 편향을 만들어, 세 방법의 실제 의미 검색 능력을 측정하지 못한다.

---

## 가설

> 의미 기반 정답 레이블(LLM 검수)과 다양한 쿼리 유형(동의어, 복합, 부정)을 사용하면
> Embedding 방식이 BM25보다 높은 Recall@5를 달성한다.

---

## 설계

### 쿼리 구성 (목표: 50개+)

| 유형 | 예시 | 개수 |
|------|------|------|
| 원본 (EXP-001 동일) | "pedestrian crossing at night intersection" | 20 |
| 동의어 바꿔쓰기 | "person walking across road after dark" | 10 |
| 복합 조건 | "rainy night highway with heavy traffic" | 10 |
| 추상적 묘사 | "dangerous low-visibility scenario" | 5 |
| 부정 표현 | "intersection without pedestrians in clear weather" | 5 |

### 정답 레이블링 방법

```
쿼리 → BM25 top-50 + Embedding top-50 합집합 (후보 풀)
     → GPT-4o-mini로 각 클립 캡션과 쿼리의 관련성 0/1 판정
     → 관련 클립 ≥ 5개인 쿼리만 채택
```

GPT-4o-mini 프롬프트 (초안):
```
Query: {query}
Caption: {caption}

Is this caption relevant to the query? Answer yes or no.
Relevant means the scene described matches the scenario in the query,
even if different words are used.
```

### 워밍업 처리

```python
# evaluate.py 수정: 측정 전 더미 쿼리 1회 실행
searcher.search("warmup query", method="embedding", top_k=1)
# 이후 타이머 시작
```

---

## 검증 기준

| 기준 | 통과 조건 |
|------|----------|
| 평가셋 크기 | 쿼리 ≥ 50개, 쿼리당 정답 클립 ≥ 5개 |
| Embedding vs BM25 | 의미 쿼리(동의어/추상)에서 Embedding Recall@5 ≥ BM25 |
| 지연 측정 신뢰도 | 워밍업 제외 중앙값 기준 |

---

## 실행 계획

```bash
# 1. 쿼리 파일 작성
# data/eval/queries_v2.txt — 50개 쿼리

# 2. 후보 풀 생성
uv run python -m avdata.eval.build_eval_set_v2 \
    --queries data/eval/queries_v2.txt \
    --candidate-k 50 \
    --llm-label gpt-4o-mini \
    --output data/eval/eval_set_v2.json

# 3. 평가
uv run python -m avdata.eval.evaluate \
    --eval-set data/eval/eval_set_v2.json \
    --warmup \
    --output experiments/EXP-002/results/
```

---

## 예상 비용 및 시간

| 항목 | 예상 |
|------|------|
| LLM API 비용 | ~$0.50 (50쿼리 × 100후보 × 0.1cent) |
| 실행 시간 | ~2시간 (LLM API 병렬 처리 포함) |
| 코드 수정 범위 | `eval/build_eval_set.py`, `eval/evaluate.py` |

---

## 선행 조건

- [ ] EXP-001 분석 완료 (`analysis.md` 작성) ✅
- [ ] OpenAI API 키 환경변수 설정 (`OPENAI_API_KEY`)
- [ ] `queries_v2.txt` 50개 쿼리 작성
