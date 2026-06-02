# EXP-002 · 인과 기반 평가셋 재설계 + ODD 연속 다양체 + 조건부 밀도 갭 탐지

**상태**: 🔲 설계 중  
**대응 갭**: EXP-001/analysis.md §Gap-1, §Gap-2, §Gap-3, §Gap-5, §Gap-6  
**탐지 목표**: 인과 체인 기반 인코더 / ODD 연속 다양체 / 조건부 밀도 갭 자동 탐지

---

## 배경

EXP-001은 세 가지 구조적 한계를 드러냈다.

1. **평가 편향**: `keyword_relevance()`가 BM25에 유리한 정답셋을 만들어, Embedding의 의미 검색 능력을 실제로 측정하지 못함
2. **Hybrid = Embedding**: ODD 필터가 `evaluate.py`에서 전달되지 않아 Hybrid가 Embedding과 동일한 결과를 냄
3. **ODD 커버리지 불완전**: Regex 기반 추출로 traffic_density(37.4%), weather(52.9%) 커버리지가 낮아, 연속적 ODD 공간을 이산 태그로 표현하는 데 한계

EXP-002는 이 세 한계를 동시에 해결하며, 최종 탐지 목표(인과 체인 인코더, ODD 연속 다양체, 조건부 밀도 갭 탐지)의 기반을 구축한다.

---

## 가설

> **Axis A**: 인과 체인 기반 쿼리 + LLM 의미 레이블링을 사용하면,  
> Embedding이 BM25보다 높은 의미 Recall@5를 달성하고,  
> 인과 체인 쿼리(L2)에서 BM25와의 격차가 가장 크게 나타난다.
>
> **Axis B**: LLM으로 추출한 5차원 연속 ODD 변수(visibility_level,  
> precipitation_intensity, traffic_density_continuous, hazard_proximity,  
> agent_density)가 Regex 기반 이산 태그보다 커버리지와 표현력이 높다.
>
> **Axis C**: 5D ODD 공간에 Normalizing Flow를 적용한 조건부 밀도 추정이  
> KDE보다 고차원 희소 구간에서 정밀한 갭을 탐지한다.

---

## 설계

### Axis A — 인과 기반 쿼리 + LLM 레이블링

#### 쿼리 유형 (목표: 60개+)

| 레벨 | 유형 | 예시 | 개수 |
|------|------|------|------|
| L0 | 원본 (EXP-001 동일) | "pedestrian crossing at night intersection" | 20 |
| L1 | 조건 상태 쿼리 | "wet road surface after rain" | 10 |
| L2 | **인과 체인 쿼리** | "wet road → emergency braking near pedestrian" | 15 |
| L3 | 복합 다중 조건 | "night + fog + highway + truck overtaking + high hazard" | 10 |
| L4 | 동의어 바꿔쓰기 | "person walking across road after dark" | 5 |

L2 인과 체인 쿼리는 원인(환경 조건) → 매개(ego 반응) → 결과(위험 상황)의 3단계 구조를 따른다.  
예: "slippery road → sudden braking → near-collision with cyclist"

#### LLM 레이블링 — 인과 관련성 스코어

후보 풀: BM25 top-50 + Embedding top-50 합집합 (쿼리당 최대 100개 클립)

```
GPT-4o-mini 프롬프트:
Query: {query}
Caption: {caption}

Score this caption's relevance to the query in two dimensions.
Return JSON:
{
  "condition_score": 0~2,   // 0=무관, 1=부분, 2=완전 일치 (환경/상황 조건)
  "causal_score": 0~2,      // 0=무관, 1=부분, 2=완전 일치 (인과 관계 포착)
  "relevant": true/false    // condition_score + causal_score >= 2
}
```

L0/L1 쿼리: `relevant = (condition_score >= 2)`  
L2/L3 쿼리: `relevant = (condition_score + causal_score >= 3)`

#### 워밍업 처리

```python
# evaluate.py 수정: 측정 전 더미 쿼리 1회 실행
searcher.search("warmup query", method="embedding", top_k=1)
searcher.search("warmup query", method="bm25", top_k=1)
# 이후 타이머 시작
```

---

### Axis B — 5D 연속 ODD 변수 추출 (LLM)

EXP-001 Regex 기반 이산 태그(7필드)를 5차원 연속 변수로 교체한다.

| 변수 | 범위 | 설명 |
|------|------|------|
| `visibility_level` | 0.0 ~ 1.0 | 0=완전불투명(dense fog), 1=완전투명(clear day) |
| `precipitation_intensity` | 0.0 ~ 1.0 | 0=없음, 1=폭우/폭설 |
| `traffic_density_continuous` | 0.0 ~ 1.0 | 0=도로 비어있음, 1=극심한 정체 |
| `hazard_proximity` | 0.0 ~ 1.0 | 0=안전, 1=즉각적 충돌 위험 |
| `agent_density` | 0.0 ~ 1.0 | 0=에이전트 없음, 1=다수의 복잡한 에이전트 |

```
GPT-4o-mini 프롬프트 (배치 처리):
Caption: {caption}

Extract driving environment variables. Return JSON:
{
  "visibility_level": float,          // 0.0~1.0
  "precipitation_intensity": float,   // 0.0~1.0
  "traffic_density_continuous": float,// 0.0~1.0
  "hazard_proximity": float,          // 0.0~1.0
  "agent_density": float              // 0.0~1.0
}
```

**비용 추정**: 299,180개 전체 처리 시 ~$300 (GPT-4o-mini). 초기 실험은 low-coverage 클립 우선 — ODD 이산 태그 기준 Unknown 비율 높은 53,000개 우선 처리(~$53).

---

### Axis C — 조건부 밀도 갭 탐지 (Normalizing Flow)

#### 방법론 선택: Normalizing Flow vs KDE

EXP-001에서 UMAP + KDE를 사용했으나, 5D 연속 ODD 공간에서는 KDE가 적합하지 않다.

| 방법 | 고차원 성능 | 희소 구간 표현 | ADS 적용 사례 |
|------|------------|--------------|-------------|
| KDE | 차원의 저주, bandwidth 불안정 | 0으로 수렴 | UMAP 2D 이후 적용 |
| **MAF (Masked Autoregressive Flow)** | **차원 증가에 강건** | **희소 구간 확률 추정 가능** | **arXiv:2507.22429** (ADS 리스크 정량화) |
| GMM | 모드 수 가정 필요 | 가우시안 혼합에 한정 | — |

참조: "Comparing Normalizing Flows with KDE in Estimating Risk of Automated Driving Systems" (arXiv:2507.22429, IEEE IAVVC 2025) — NF가 고차원에서 KDE보다 리스크 불확실성 추정 정밀도 향상 확인.

#### 갭 탐지 파이프라인

```
299k 클립 × 5D ODD 벡터
    → MAF 학습: p(ODD) 추정
    → 조건부 밀도: p(ODD | hazard_proximity > 0.7)
    → 그리드 기반 갭 스코어 계산:
        gap_score = (1 / density) × hazard_proximity × real_world_freq_weight
    → 상위 N 구간을 "취약 시나리오 구간"으로 우선순위화
```

`real_world_freq_weight`: 실세계 발생 빈도 가중치 (예: rain × highway = 높음, snow × tunnel = 낮음)

#### TrimFlow 연계

희소 구간(gap_score 상위 5%) 클립을 Importance Sampling 기반으로 재샘플링하여 검색 평가 쿼리 집중 → arXiv:2407.07320 (TrimFlow, 2024) 패턴 차용.

---

### Axis A 인코더 — 인과 표현 학습 참조

현재 bge-m3 인코더를 인과 거리를 포착하도록 fine-tuning하는 방향의 설계 참조:

- **PCM (arXiv:2602.13936, 2026)**: Disentangled Scene Encoder — intervention-based disentanglement으로 도메인 불변 인과 피처 추출. "원인 클립 vs 결과 클립" 대조 학습 신호로 활용 가능.
- **CEWM (arXiv:2311.10747, 2024)**: Safety-aware Causal Transformer — state ↔ cost 인과 관계 모델링. Hazard 예측 task에 적용.

EXP-002에서는 기존 bge-m3를 사용하고, 인과 인코더 fine-tuning은 EXP-005로 분리한다.

---

## 검증 기준

| 기준 | 통과 조건 |
|------|----------|
| 평가셋 크기 | 쿼리 ≥ 60개, 쿼리당 정답 클립 ≥ 5개 |
| Axis A: Embedding vs BM25 (L0) | 의미 Recall@5: Embedding ≥ BM25 (EXP-001과 반전) |
| Axis A: 인과 쿼리 격차 | L2 쿼리에서 Embedding-BM25 Recall@5 격차 > L0 격차 |
| Axis B: 커버리지 | 5D 연속 ODD, Unknown 클립 비율 < 10% |
| Axis C: 갭 탐지 정밀도 | NF 밀도 추정 log-likelihood > KDE 기준치 |
| Axis C: 갭 발견 | gap_score 상위 구간에서 실제 희귀 시나리오 ≥ 3종 식별 |
| 지연 측정 신뢰도 | 워밍업 제외 중앙값 기준 (200ms 이하 목표) |

---

## 실행 계획

```bash
# Axis A-1: 쿼리 파일 작성 (수동)
# data/eval/queries_v2.json — 60개 쿼리 + 레벨 메타데이터

# Axis A-2: 후보 풀 생성 + LLM 레이블링
uv run python -m avdata.eval.build_eval_set_v2 \
    --queries data/eval/queries_v2.json \
    --candidate-k 50 \
    --llm-model gpt-4o-mini \
    --output data/eval/eval_set_v2.json

# Axis A-3: 평가 (워밍업 포함)
uv run python -m avdata.eval.evaluate \
    --eval-set data/eval/eval_set_v2.json \
    --warmup \
    --output experiments/EXP-002/results/

# Axis B: 연속 ODD 추출 (우선 53k unknown 클립)
uv run python -m avdata.phase3.extract_odd_continuous \
    --target unknown \
    --model gpt-4o-mini \
    --output data/tags/odd_continuous.json

# Axis C: Normalizing Flow 학습 + 갭 탐지
uv run python -m avdata.phase5.fit_normalizing_flow \
    --odd-vectors data/tags/odd_continuous.json \
    --method maf \
    --output data/density/nf_model.pkl

uv run python -m avdata.phase5.detect_gaps \
    --nf-model data/density/nf_model.pkl \
    --hazard-threshold 0.7 \
    --output experiments/EXP-002/results/gap_report.json
```

---

## 예상 비용 및 시간

| 항목 | 예상 |
|------|------|
| Axis A LLM 레이블링 | ~$0.60 (60쿼리 × 100후보 × $0.0001/call) |
| Axis B ODD 추출 (53k) | ~$5.30 (53k × $0.0001/call) |
| Axis C MAF 학습 | ~30분 (CPU, 53k 벡터) |
| 코드 신규 작성 | `eval/build_eval_set_v2.py`, `phase3/extract_odd_continuous.py`, `phase5/fit_normalizing_flow.py`, `phase5/detect_gaps.py` |

---

## 선행 조건

- [x] EXP-001 분석 완료 (`analysis.md` 작성)
- [ ] OpenAI API 키 환경변수 설정 (`OPENAI_API_KEY`)
- [ ] `queries_v2.json` 60개 쿼리 작성 (L0~L4 레벨별)
- [ ] `normalizing-flows` 또는 `nflows` Python 패키지 추가 (`uv add nflows`)

---

## 참조 논문

| 논문 | 적용 Axis | 핵심 기여 |
|------|---------|---------|
| arXiv:2507.22429 (2025) | Axis C | NF > KDE for ADS risk estimation in high-dimensional space |
| arXiv:2407.07320 (2024) | Axis C | TrimFlow: NF 기반 AV 희귀 사건 Importance Sampling |
| arXiv:2602.13936 (2026) | Axis A | Disentangled Scene Encoder, intervention-based causal feature |
| arXiv:2311.10747 (2024) | Axis A | Safety-aware Causal Transformer, state↔cost 인과 관계 |
