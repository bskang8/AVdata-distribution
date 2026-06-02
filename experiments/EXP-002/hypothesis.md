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

## 가설 수립 근거

### Axis A 근거 — "Embedding > BM25"가 성립하지 못한 이유가 방법 자체가 아니라 평가 설계의 결함이다

**EXP-001 결과**: Embedding Recall@5 = 0.520, BM25 = 0.900. 격차가 크다.

그러나 정답 레이블 생성 로직을 보면 이 숫자가 Embedding의 실제 검색 품질을 반영하지 않는다는 것이 명확하다.

```python
# build_eval_set.py — EXP-001 정답 생성 로직
def keyword_relevance(text, query):
    query_words = [w for w in re.split(r"\W+", query.lower()) if len(w) > 3]
    return all(w in text.lower() for w in query_words)
```

쿼리 단어가 캡션에 **글자 그대로** 모두 등장해야 정답이다. BM25도 동일하게 토큰 매칭으로 검색한다. 즉, 정답셋이 BM25가 찾는 방식과 동일한 로직으로 만들어졌다. `pedestrian suddenly enters road` 쿼리의 Embedding Recall@5 = 0.0은 Embedding이 의미상 유사한 클립을 반환했음에도 "suddenly"·"enters" 같은 단어가 캡션에 없어서 오답 처리된 결과다.

정답 레이블을 LLM 의미 판단으로 교체하면 "person walked into the roadway abruptly" 같은 캡션도 정답으로 인정된다. 이 조건에서 Embedding이 BM25를 앞선다는 가설을 세운 근거는 다음 두 가지다.

1. **의미 공간 우위**: bge-m3는 표현이 달라도 의미가 같은 문장을 가깝게 임베딩한다. 정답 기준이 의미 기반으로 바뀌면 이 능력이 처음으로 공정하게 평가된다.
2. **BM25의 동의어 맹점**: BM25는 "pedestrian"을 찾을 때 "person"·"walker"가 등장하는 클립을 놓친다. 정답셋이 의미 기반이면 BM25가 놓친 클립들이 오답으로 누적된다.

**L2 쿼리에서 격차가 가장 크다는 예측 근거**: L2 인과 체인 쿼리(`wet road → emergency braking → near-collision`)는 세 단계 개념이 하나의 캡션에 동시에 등장해야 BM25가 매칭한다. 실제 캡션은 보통 하나의 장면 단면만 묘사하므로 BM25는 세 키워드가 모두 포함된 클립만 반환하고 관련 클립 대부분을 놓친다. Embedding은 세 개념이 가리키는 의미 방향의 합을 단일 벡터로 포착하여 표현이 분산된 클립도 검색한다.

---

### Axis B 근거 — Regex 이산 태그는 구조적으로 두 가지 문제를 동시에 가진다

**문제 1: 커버리지 한계 (EXP-001 실측)**

| 필드 | 커버리지 | Unknown 클립 수 | 미캡처 표현 예시 |
|------|---------|----------------|----------------|
| traffic_density | 37.4% | 187,356개 | "bumper-to-bumper", "stop-and-go", "light traffic" |
| weather | 52.9% | 140,937개 | "overcast", "drizzling", "slippery surface after shower" |
| time_of_day | 62.7% | 111,554개 | "at dusk", "before sunrise", "dim lighting" |

Regex는 사전에 정의한 패턴 외의 표현을 전혀 처리하지 못한다. 패턴을 추가할수록 유지보수 비용이 늘고, 코퍼스의 자연어 다양성을 사전에 완전히 열거하는 것은 불가능하다.

**문제 2: 표현력 한계 — 이산 태그로는 ODD 공간의 거리를 계산할 수 없다**

`weather = "rain"` 태그는 가랑비와 폭우를 구분하지 못한다. `hazard_level = "high"`는 충돌 0.5초 전과 주의 요구 10초 전을 동일하게 취급한다. 이산 범주에서는 두 클립의 ODD 조건이 얼마나 다른지 수치로 표현할 수 없어 Axis C의 밀도 추정 입력으로 사용할 수 없다.

**LLM이 이 두 문제를 동시에 해결하는 이유**: GPT-4o-mini는 "drizzling", "light rain", "wet road conditions after shower"를 맥락으로 읽어 `precipitation_intensity ≈ 0.2~0.3`으로 수렴시킨다. Rivera et al. (2025, CatPipe)에서 GPT-4/LLaVA로 16개 씬 카테고리를 zero-shot 분류했을 때 Regex 대비 높은 커버리지를 달성한 것이 같은 원리의 선례다. 연속 수치 출력은 Axis C 입력으로 직접 사용 가능하다.

---

### Axis C 근거 — KDE는 5D 공간에서 수학적으로 신뢰하기 어렵고, "조건부" 밀도 추정이 목적이다

**EXP-001 UMAP+KDE의 한계**: 1024차원 임베딩을 UMAP으로 2D 축소 후 KDE를 적용했다. 2D 투영에서는 고차원의 세밀한 ODD 조건 차이(fog + highway vs. fog + urban)가 뭉개진다. Longtail 14,959개를 탐지했지만 이 클립들이 실제 위험 시나리오인지, 단순히 드문 캡션 스타일인지 구분하지 못한 것이 EXP-001 Gap-4의 미해결 문제다.

**KDE의 수학적 한계 (5D)**:

KDE의 bandwidth `h`는 차원 `d`가 커질수록 최적값이 급격히 변한다. 1D에서 쓰는 Silverman's rule을 5D에 적용하면 과대·과소 평활화가 발생한다. 핵심 문제는 갭을 탐지하려는 바로 그 구간 — 데이터가 희소한 구간 — 에서 KDE 추정값이 0에 수렴하거나, 인접 고밀도 클러스터의 밀도가 번져(bleed-over) 갭이 지워진다.

**Normalizing Flow가 이를 해결하는 이유**:

NF는 단순 분포(가우시안)를 학습된 가역 변환으로 데이터 분포로 변환한다. 희소 구간에서도 변환 함수가 정의되어 있어 밀도 추정값이 0으로 수렴하지 않는다. arXiv:2507.22429 (IEEE IAVVC 2025)가 ADS 리스크 파라미터 공간에서 NF와 KDE를 직접 비교하여 "NF가 고차원에서 KDE보다 리스크 불확실성 추정 정밀도가 높다"는 결과를 냈다. 이 논문의 실험 설정 — ADS 파라미터 공간 밀도 추정 — 이 EXP-002 Axis C와 동일하다.

**"조건부" 밀도가 목적인 이유**:

갭 탐지 목표는 단순히 드문 ODD 조건이 아니라 **드물면서 위험한 조건**이다. `p(ODD)` 대신 `p(ODD | hazard_proximity > 0.7)`을 추정해야 한다. KDE는 조건을 사후 데이터 필터링으로 처리하므로, 위험 클립이 드문 구간에서 표본이 너무 적어 추정이 불안정해진다. MAF 같은 Normalizing Flow는 조건부 분포를 학습 목표로 직접 설정할 수 있다. TrimFlow (arXiv:2407.07320)가 NF + Importance Sampling으로 희귀 위험 사건을 86.1% 적은 테스트로 커버한 것은 정확히 같은 원리를 AV 검증에 적용한 선례다.

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
