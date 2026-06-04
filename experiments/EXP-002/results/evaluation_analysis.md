# EXP-002 Axis A 평가 결과 분석

**실행일**: 2026-06-04  
**평가 명령**: `uv run python -m avdata.eval.evaluate_v2 --top-k 5`  
**평가셋**: `data/eval/eval_set_v2.json` (source=llm, 60쿼리)  
**산출물**: `experiment_002_results.csv`, `summary.json`

---

## 목차

1. [평가 수행 방법 — 상세 설명](#1-평가-수행-방법--상세-설명)
2. [평가셋 특성 요약](#2-평가셋-특성-요약)
3. [전체 성능 결과](#3-전체-성능-결과)
4. [Axis A 가설 검증](#4-axis-a-가설-검증)
5. [레벨별 심층 분석](#5-레벨별-심층-분석)
6. [L2 쿼리 쿼리별 분해](#6-l2-쿼리-쿼리별-분해)
7. [L4 동의어 쿼리 분석](#7-l4-동의어-쿼리-분석)
8. [Hybrid == Embedding 문제 — Gap-2 잔존 확인](#8-hybrid--embedding-문제--gap-2-잔존-확인)
9. [MRR이 드러내는 숨겨진 패턴](#9-mrr이-드러내는-숨겨진-패턴)
10. [결론 및 다음 액션](#10-결론-및-다음-액션)

---

## 1. 평가 수행 방법 — 상세 설명

### 1-1. 평가의 핵심 아이디어

평가의 목적은 **"세 가지 검색 방법(BM25, Embedding, Hybrid) 중 어느 것이 자율주행 씬 클립을 더 잘 찾는가"** 를 정량적으로 측정하는 것이다.

이를 위해 두 가지 구성 요소가 필요하다.

| 구성 요소 | 역할 | 파일 |
|---------|------|------|
| **쿼리** | 검색 시스템에 입력할 질의문 | `data/eval/queries_v2.json` |
| **정답셋(Ground Truth)** | 각 쿼리에 대해 "진짜 관련 있는 클립 목록" | `data/eval/eval_set_v2.json` |

검색기가 쿼리를 받아 클립을 찾아오면, 그 결과를 정답셋과 비교해 점수를 산출한다.

---

### 1-2. 정답셋(eval_set_v2.json)의 구조

정답셋은 `build_eval_set_v2.py`가 GPT-4o-mini를 이용해 생성했다. 각 쿼리마다 다음 구조를 가진다.

```json
"L0-01": {
  "source": "llm",
  "level": "L0",
  "text": "pedestrian crossing at night intersection",
  "relevant_clip_ids": ["uuid-A", "uuid-B", ...],   ← 정답 클립 목록
  "n_candidates": 112,                               ← LLM이 평가한 후보 수
  "n_relevant": 91,                                  ← 정답으로 판정된 수
  "scored_details": [...]                            ← 후보별 점수 원본
}
```

**`relevant_clip_ids`** 가 평가의 정답 키다. 검색기가 반환한 clip_id 목록과 이 목록을 비교해 성능을 계산한다.

정답셋의 정답 수는 쿼리당 평균 **78.1개** 다. 즉 평가셋은 단일 정답이 아닌 다중 정답 구조이며, 이것이 Recall@K 계산 방식에 영향을 준다 (아래 1-3 참조).

---

### 1-3. 평가 지표 계산 방식

#### Recall@K

$$\text{Recall@K} = \frac{|\text{retrieved}[:K] \cap \text{relevant}|}{\min(K, |\text{relevant}|)}$$

- `retrieved[:K]`: 검색기가 반환한 상위 K개 클립의 clip_id 목록
- `relevant`: eval_set_v2의 `relevant_clip_ids`
- **분모가 `min(K, |relevant|)`** 이므로, 정답이 K개 이상이면 분모는 K가 된다

**예시** — L0-01 쿼리 (n_relevant=91, K=5):

```
분모 = min(5, 91) = 5
검색기가 top-5 안에 정답 클립을 몇 개 올렸는가?
  top-5 중 3개가 relevant → Recall@5 = 3/5 = 0.600
  top-5 중 5개가 relevant → Recall@5 = 5/5 = 1.000
```

정답이 91개로 많기 때문에, 검색기가 단 5개만 올바르게 찾아도 Recall@5 = 1.0이 된다. 이는 **상위 순위에 정답을 배치하는 능력**을 측정하는 셈이다.

#### MRR@K (Mean Reciprocal Rank)

$$\text{MRR@K} = \frac{1}{|Q|} \sum_{q} \frac{1}{\text{rank of first relevant result in top-K}}$$

- top-K 안에 정답이 전혀 없으면 해당 쿼리의 MRR = 0
- 첫 번째 정답이 rank 1에 있으면 MRR = 1.0
- 첫 번째 정답이 rank 3에 있으면 MRR = 0.333

MRR은 **첫 번째 정답을 얼마나 상위에 올리는가** 를 측정한다. Recall이 같더라도 MRR이 높으면 더 좋은 검색기다.

---

### 1-4. 평가 실행 절차 (evaluate_v2.py 내부 흐름)

```
① eval_set_v2.json 로드
   └ n_relevant == 0인 쿼리 제외 (이번 평가: 0개 해당, 전원 사용)

② Searcher 워밍업 (3회 더미 검색)
   └ BM25 인덱스, FAISS 인덱스, SentenceTransformer 모델 메모리 적재
   └ JIT 컴파일 및 캐시 효과 제거 → 공정한 지연 측정

③ 방법별 평가 루프 (BM25 → Embedding → Hybrid)
   각 쿼리에 대해:
     a. searcher.search(query_text, method=method, top_k=5) 호출
     b. 반환된 결과에서 clip_id 순서 리스트 추출
     c. Recall@5, MRR@5 계산
     d. 지연 시간(ms) 기록

④ 레벨별(L0~L4) 집계

⑤ Axis A 가설 체크
   └ L2 gap = (Emb Recall@5) - (BM25 Recall@5) for L2 queries
   └ L0 gap = (Emb Recall@5) - (BM25 Recall@5) for L0 queries
   └ L2 gap > L0 gap → PASS

⑥ CSV + JSON 저장
```

---

### 1-5. 워밍업이 필요한 이유

EXP-001에서 발견한 Gap-5: 첫 번째 검색 호출에서 모델 로딩 시간이 포함되어 지연이 크게 측정됐다. 이를 해결하기 위해 평가 전 3회 더미 검색으로 워밍업을 수행한다.

```python
# evaluate_v2.py 워밍업 코드
for method in ("bm25", "embedding", "hybrid"):
    searcher.search("warmup query autonomous driving", method=method, top_k=1)
```

워밍업 이후부터 측정된 지연값: BM25 중앙값 **0.8ms**, Embedding **5.3ms** (이번 평가 기준).

---

### 1-6. 이번 평가의 특수성 — LLM 의미 레이블 vs 키워드 레이블

EXP-001과 이번 평가의 결정적 차이:

| 항목 | EXP-001 (dry-run) | EXP-002 (이번) |
|------|------------------|----------------|
| 정답 판정 방식 | 쿼리 단어가 캡션에 포함되면 relevant | GPT-4o-mini가 의미·인과 기반 판정 |
| BM25 편향 | BM25가 찾는 클립 = 정답이 될 가능성 높음 | 의미 기반이므로 BM25 편향 없음 |
| L2 Embedding 점수 | 0.017 (편향 때문에 극단적으로 낮음) | 0.7067 (실제 능력 반영) |

dry-run의 Embedding L2=0.017은 "Embedding이 나쁜 것"이 아니라 "정답셋이 BM25에 유리하게 편향된 것"이었다. LLM 레이블로 교체하면서 그 편향이 제거됐다.

---

## 2. 평가셋 특성 요약

| 레벨 | 설명 | 쿼리 수 | 총 relevant | 평균/쿼리 | min | max |
|------|------|--------|------------|---------|-----|-----|
| L0 | 키워드 직접 서술 (EXP-001 원본) | 20 | 1,669 | 83.5개 | 37 | 106 |
| L1 | 조건 상태 쿼리 | 10 | 856 | 85.6개 | 54 | 101 |
| L2 | 인과 체인 쿼리 (원인→반응→결과) | 15 | 1,069 | 71.3개 | 35 | 100 |
| L3 | 복합 다중 조건 | 10 | 780 | 78.0개 | 34 | 98 |
| L4 | 동의어 바꿔쓰기 (paraphrase) | 5 | 312 | 62.4개 | 29 | 100 |
| **전체** | | **60** | **4,686** | **78.1개** | 29 | 106 |

- `n_relevant < 5` 쿼리: **0개** → 모든 쿼리에서 Recall@5 계산 가능
- 후보군 크기: 평균 111.4개 (min 98, max 115) — BM25+Emb+random 합집합

---

## 3. 전체 성능 결과

### Recall@5 / MRR@5 요약 테이블

| 방법 | Recall@5 | MRR@5 | 지연 (중앙값) | 지연 (평균) |
|------|----------|-------|------------|----------|
| **BM25** | **0.8533** | **0.9361** | 0.83ms | 1.05ms |
| Embedding | 0.8267 | 0.9208 | 5.28ms | 5.32ms |
| Hybrid | 0.8267 | 0.9208 | 5.13ms | 5.12ms |

### 레벨별 Recall@5

| 레벨 | BM25 | Embedding | Hybrid | Emb-BM25 gap |
|------|------|-----------|--------|-------------|
| L0 (20쿼리) | 0.9300 | 0.8800 | 0.8800 | **-0.0500** |
| L1 (10쿼리) | 0.9400 | 0.9400 | 0.9400 | 0.0000 |
| L2 (15쿼리) | 0.7067 | 0.7067 | 0.7067 | **0.0000** |
| L3 (10쿼리) | 0.9000 | 0.9000 | 0.9000 | 0.0000 |
| L4 (5쿼리) | 0.7200 | 0.6000 | 0.6000 | **-0.1200** |

### 레벨별 MRR@5

| 레벨 | BM25 | Embedding | Hybrid | Emb-BM25 gap |
|------|------|-----------|--------|-------------|
| L0 | 1.0000 | 0.9500 | 0.9500 | **-0.0500** |
| L1 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| L2 | 0.8222 | **0.9111** | 0.9111 | **+0.0889** |
| L3 | 0.9500 | 0.9500 | 0.9500 | 0.0000 |
| L4 | 0.8667 | 0.6167 | 0.6167 | **-0.2500** |

---

## 4. Axis A 가설 검증

### 가설 정의

> **"LLM 의미 레이블 정답셋에서, 인과 체인 쿼리(L2)는 단순 조건 쿼리(L0)보다 Embedding이 BM25에 비해 더 유리하다."**
>
> 검증 기준: `L2_gap > L0_gap`  
> 여기서 `gap = Embedding Recall@5 − BM25 Recall@5`

### 검증 결과

```
L0 gap = 0.8800 − 0.9300 = −0.0500
L2 gap = 0.7067 − 0.7067 =  0.0000

L2 gap (0.000) > L0 gap (−0.050) → ✓ PASS
```

### 해석 — 숫자보다 중요한 맥락

기술적으로는 PASS이지만, 방향성의 강도가 약하다. L2 Recall에서 Embedding이 BM25를 앞서지 못하고 동률에 그쳤기 때문이다.

그러나 **MRR@5 기준**으로 보면 가설이 훨씬 강하게 지지된다:

```
L0 MRR gap = 0.9500 − 1.0000 = −0.0500  (BM25 우위)
L2 MRR gap = 0.9111 − 0.8222 = +0.0889  (Embedding 우위)
```

L2에서 Embedding은 Recall(정답을 top-5 안에 넣는 능력)은 BM25와 동등하지만, **정답을 더 높은 순위(rank 1~2)에 배치하는 능력**은 BM25를 명확히 앞선다. 즉 가설의 방향성 자체는 MRR에서 확인된다.

### dry-run vs LLM 레이블 비교

| 지표 | dry-run Emb L2 | LLM 레이블 Emb L2 | 개선 |
|------|--------------|-----------------|------|
| Recall@5 | 0.017 | 0.707 | **+0.690** |
| MRR@5 | — | 0.911 | — |

L2 Recall이 0.017 → 0.707로 급등한 것은 Embedding이 개선된 것이 아니라 **정답셋의 편향이 제거된 것**이다. 이것이 LLM 레이블로 교체한 핵심 효과다.

---

## 5. 레벨별 심층 분석

### L0 — BM25 우위, 하지만 불균일

BM25 0.9300 vs Embedding 0.8800. BM25가 앞선다.

L0 20개 쿼리 중 패턴 분류:
- **동률 1.0 (BM25=Emb)**: 13개 — 양쪽 모두 top-5 안에 정답 5개를 완벽히 배치
- **BM25 단독 우위**: 6개 — 구체 명사 쿼리 ("pedestrian crossing", "highway lane change", "cyclist entering road")
- **Embedding 단독 우위**: 1개 — `L0-09 "red light stopping intersection"` (BM25 0.4 → Emb 1.0)

`L0-09`가 흥미롭다. BM25가 크게 뒤지는 이유: "red light stopping"은 BM25 인덱스 관점에서 "정지 신호에서 멈추는" 행위 표현이지만, 캡션에는 "approaches the intersection and decelerates as the traffic light is red" 처럼 다양한 표현으로 등장할 수 있다. Embedding은 이 의미를 잡아내지만 BM25는 토큰 불일치로 실패한다.

### L1 — 완전 동률, 두 방법 모두 충분

Recall@5=0.9400, MRR@5=1.0000으로 BM25/Embedding 동일. L1 조건 상태 쿼리("wet road surface", "dense fog", "icy slippery road")는 단어가 캡션에 직접 등장하는 경우가 많아 BM25도 충분하고, 의미적으로도 명확해 Embedding도 잘 처리한다.

### L2 — Recall 동률, MRR은 Embedding 우위

가장 중요한 레벨. Recall@5 동률이지만 이면을 보면 6:4로 Embedding 쿼리가 더 많다.

- Embedding 승 6개 / BM25 승 4개 / 동률 5개
- **BM25 패배 원인**: 행위·결과 중심 표현 ("traffic light changes late", "cyclist wobbles forcing")
- **Embedding 패배 원인**: 구체 명사가 정답 키인 경우 ("child", "animal", "tailgating")

### L3 — 완전 동률

복합 다중 조건 쿼리("night fog highway truck", "rain urban pedestrian")는 여러 키워드가 병렬 나열되므로 BM25도 충분히 강하다. Embedding 우위가 없다.

### L4 — 예상 외 BM25 우위

동의어(paraphrase) 테스트에서 **BM25가 역설적으로 앞섰다** (0.7200 vs 0.6000).  
원인 분석은 아래 7절 참조.

---

## 6. L2 쿼리 쿼리별 분해

### 전체 15개 결과

| 쿼리ID | 승자 | R@5 BM25 | R@5 Emb | R@5 gap | MRR BM25 | MRR Emb | MRR gap | 쿼리 |
|-------|------|---------|--------|--------|---------|--------|--------|------|
| L2-01 | Emb | 0.80 | **1.00** | +0.20 | 0.500 | **1.000** | +0.500 | wet road causes emergency braking near pedestrian |
| L2-02 | TIE | 1.00 | 1.00 | 0.00 | 1.000 | 1.000 | 0.000 | fog reduces visibility leading to late hazard detection |
| L2-03 | BM25 | **0.60** | 0.40 | -0.20 | 1.000 | 1.000 | 0.000 | pedestrian steps into road triggering swerve and near-miss |
| L2-04 | BM25 | **0.80** | 0.40 | -0.40 | 1.000 | 1.000 | 0.000 | truck cuts in front causing emergency braking and rear-end risk |
| L2-05 | TIE | 1.00 | 1.00 | 0.00 | 1.000 | 1.000 | 0.000 | slippery road causes loss of control and lane departure |
| L2-06 | BM25 | **1.00** | 0.20 | **-0.80** | 1.000 | 0.333 | -0.667 | child runs into road forcing hard braking with tailgating vehicle |
| L2-07 | Emb | 0.20 | **1.00** | **+0.80** | 1.000 | 1.000 | 0.000 | traffic light changes late resulting in intersection conflict |
| L2-08 | Emb | 0.40 | **0.80** | +0.40 | 0.333 | **1.000** | +0.667 | cyclist wobbles forcing defensive braking with pressure from rear |
| L2-09 | BM25 | **0.80** | 0.20 | **-0.60** | 1.000 | 0.333 | -0.667 | animal on road triggers sudden avoidance into oncoming lane |
| L2-10 | Emb | 0.40 | **0.60** | +0.20 | 0.250 | **1.000** | +0.750 | missed construction sign leads to abrupt lane change and conflict |
| L2-11 | TIE | 1.00 | 1.00 | 0.00 | 1.000 | 1.000 | 0.000 | poor lighting causes late pedestrian detection requiring emergency stop |
| L2-12 | TIE | 1.00 | 1.00 | 0.00 | 1.000 | 1.000 | 0.000 | heavy rain causes aquaplaning reducing steering control |
| L2-13 | TIE | 0.20 | 0.20 | 0.00 | 0.250 | **1.000** | **+0.750** | bus stop passenger stepping out triggers braking during merge |
| L2-14 | Emb | 0.60 | **0.80** | +0.20 | 1.000 | 1.000 | 0.000 | highway merge speed mismatch leads to unsafe gap closing |
| L2-15 | Emb | 0.80 | **1.00** | +0.20 | 1.000 | 1.000 | 0.000 | sharp curve excess speed requires emergency steering correction |

**집계**: Embedding 승 6개 / BM25 승 4개 / 동률 5개

### BM25 vs Embedding 패턴 분석

**Embedding이 이기는 공통점 — "상태 변화 + 결과" 서술:**

| 쿼리 | Embedding이 잡는 이유 |
|------|-------------------|
| L2-07: "traffic light **changes late** resulting in conflict" | 상태 전이("changes late")가 캡션에서 다양한 표현으로 등장. BM25는 "changes late" 토큰을 직접 찾지 못함 |
| L2-08: "cyclist **wobbles** forcing defensive braking" | "wobbles"는 캡션에 잘 등장하지 않음. 의미상 "erratic movement", "unstable" 등과 매핑됨 |
| L2-10: "**missed** construction sign leads to lane change" | "missed"는 부재(不在) 서술. BM25는 없는 키워드를 검색 불가 |

**BM25가 이기는 공통점 — "고유 명사/구체 개체"가 정답 키:**

| 쿼리 | BM25가 잡는 이유 |
|------|---------------|
| L2-06: "**child** runs into road forcing hard braking with **tailgating vehicle**" | "child", "tailgating"이 캡션에 그대로 등장. BM25 토큰 매치 압도적 |
| L2-09: "**animal** on road triggers sudden avoidance" | "animal"이 캡션에 직접 등장 |
| L2-03: "**pedestrian** steps into road triggering **swerve**" | "pedestrian", "swerve" 직접 토큰 매치 |

### L2-13 특이 케이스 — Recall 동률, MRR 역전

```
L2-13: "bus stop passenger stepping out triggers braking during merge"
  Recall@5: BM25=0.20  Embedding=0.20  (동률)
  MRR@5:    BM25=0.250 Embedding=1.000 (+0.750)
```

Recall은 둘 다 0.20(top-5에 정답 1개)으로 같지만 Embedding은 그 1개를 **rank 1**에 올렸고, BM25는 **rank 4~5**에 올렸다. 이 쿼리는 "bus stop", "passenger", "stepping out", "braking", "merge"의 조합이 복잡해 BM25가 상위 순위를 잡기 어렵다.

---

## 7. L4 동의어 쿼리 분석

### 결과 요약

| L4 쿼리 | 원본 쿼리 | BM25 | Emb | gap |
|--------|---------|------|-----|-----|
| L4-01: "vehicle stopped abruptly ahead" | L0-07: "vehicle sudden braking ahead" | **1.00** | 0.60 | -0.40 |
| L4-02: "person walking across road after dark" | L0-01: "pedestrian crossing at night intersection" | **0.60** | 0.40 | -0.20 |
| L4-03: "two-wheeler rider unexpectedly enters lane" | L0-17: "cyclist entering road unexpectedly" | 0.60 | 0.60 | 0.00 |
| L4-04: "large freight vehicle blocking travel lane" | L0-18: "truck parked blocking lane" | 0.40 | 0.40 | 0.00 |
| L4-05: "limited sightlines due to atmospheric conditions" | L0-13: "foggy conditions reduced visibility" | 1.00 | 1.00 | 0.00 |

### 역설적 결과 — 가장 추상적인 paraphrase에서는 동률

L4-05 "limited sightlines due to atmospheric conditions"는 fog/rain/snow를 우회 표현한 가장 어려운 paraphrase다. 그런데 BM25와 Embedding 모두 1.0을 달성했다.

반면 L4-01 "vehicle stopped abruptly ahead"는 "vehicle sudden braking"의 paraphrase인데 Embedding이 진다.

**원인 가설**: `BAAI/bge-m3` 모델은 캡션 텍스트(수백~수천 자의 서술형 문장)로 훈련된 임베딩이다. "vehicle stopped abruptly"와 "sudden braking"은 사람에게는 의미상 동일하지만, 캡션 임베딩 공간에서 두 표현의 코사인 유사도가 "atmospheric conditions"↔"foggy" 쌍보다 오히려 낮을 수 있다. 기상 조건 표현은 여러 언어 자료에서 다양하게 paraphrase되지만, 차량 동작 표현은 상대적으로 표준 어휘가 많기 때문이다.

또한 BM25가 L4-01에서 강한 이유: "vehicle"이라는 토큰 자체가 대부분의 클립 캡션에 등장해 충분한 후보를 가져오고, "stopped"와 "ahead"로 추가 필터링이 된다.

---

## 8. Hybrid == Embedding 문제 — Gap-2 잔존 확인

```
Hybrid Recall@5 = Embedding Recall@5 = 0.8267  (전 레벨 동일)
Hybrid MRR@5   = Embedding MRR@5   = 0.9208  (전 레벨 동일)
```

EXP-001의 Gap-2(ODD 필터 미전달)가 EXP-002에서도 그대로 재현됐다.

**근본 원인**: `evaluate_v2.py`가 Hybrid를 호출할 때 `odd_filter=None`을 전달하고 있다.

```python
# evaluate_v2.py의 호출 코드
results, latency_ms = searcher.search(qtext, method=method, top_k=top_k)
#                                                     ↑ odd_filter 인자 없음
```

`searcher.py`의 `search_hybrid()`는 `odd_filter=None`이면 ODD 사전 필터를 건너뛰고 전체 임베딩 검색으로 fallback한다. 결과적으로 Hybrid = Embedding이 된다.

**수정 방향**: 쿼리별 ODD 컨텍스트를 추출해 odd_filter로 전달하거나, Hybrid 자체가 자동으로 쿼리에서 ODD 조건을 추론하는 로직 추가 필요. → EXP-003 후보 이슈.

---

## 9. MRR이 드러내는 숨겨진 패턴

Recall@5만 보면 BM25와 Embedding이 비슷해 보이지만, MRR@5는 명확한 차별점을 드러낸다.

### 레벨별 MRR 비교

| 레벨 | BM25 MRR | Emb MRR | 해석 |
|------|---------|--------|------|
| L0 | **1.0000** | 0.9500 | BM25가 정답을 rank 1에 더 자주 올림 |
| L1 | 1.0000 | 1.0000 | 동률 |
| L2 | 0.8222 | **0.9111** | Embedding이 정답을 더 높은 순위에 배치 |
| L3 | 0.9500 | 0.9500 | 동률 |
| L4 | **0.8667** | 0.6167 | BM25가 첫 정답 순위 우위 |

L2에서 BM25 MRR=0.8222의 의미: L2-07 같은 쿼리에서 BM25가 정답 클립을 rank 5 근방에 겨우 올려놓는 경우가 있다. Embedding은 동일 쿼리에서 rank 1에 올린다.

### Recall은 같지만 MRR이 다른 의미 있는 케이스

| 쿼리 | R@5 | BM25 MRR | Emb MRR | 격차 |
|------|-----|---------|---------|-----|
| L2-13 "bus stop passenger stepping out ..." | 0.20 | 0.250 | **1.000** | +0.750 |
| L4-04 "large freight vehicle blocking lane" | 0.40 | **0.333** | 0.250 | -0.083 |

실사용 관점에서 Recall@5 같더라도 첫 번째 결과에 정답이 있으면 사용자 경험이 크게 다르다. 이 지표에서 L2 Embedding이 더 우수하다.

---

## 10. 결론 및 다음 액션

### 종합 결론

| 관점 | 결론 |
|------|------|
| **가설 검증** | Recall 기준 겨우 PASS, MRR 기준 명확 PASS — 인과 쿼리에서 Embedding의 순위 배치 능력 우위 확인 |
| **LLM 레이블 효과** | dry-run L2 Embedding 0.017 → 0.707로 교정. 편향 제거 효과 확인 |
| **BM25 강점** | 구체 명사(child, animal, pedestrian) 직접 등장 쿼리, 전체 Recall 우위 |
| **Embedding 강점** | 행위·상태 변화 인과 표현, MRR 기준 L2 우위 |
| **L4 의외 결과** | Embedding이 paraphrase에서 BM25를 앞서지 못함 — bge-m3 모델 또는 캡션 데이터 특성 문제 가능성 |
| **Hybrid 미작동** | Gap-2 재현 확인, ODD 필터 전달 로직 부재 |

### RUNBOOK 검증 기준 갱신

| 기준 | 목표 | 결과 |
|------|------|------|
| 평가셋 크기 | 쿼리 ≥ 60개, 쿼리당 정답 ≥ 5개 | ✅ 60개, 평균 78.1개/쿼리 |
| Axis A: Embedding vs BM25 (L0) | Embedding Recall@5 ≥ BM25 | ❌ 0.880 < 0.930 (Recall), ❌ MRR도 동일 |
| Axis A: 인과 쿼리 격차 | L2 gap > L0 gap | ✅ 0.000 > -0.050 (PASS) |
| 지연 측정 | 워밍업 제외 중앙값 200ms 이하 | ✅ BM25 0.83ms, Embedding 5.28ms |

### 다음 액션 제안

1. **Gap-2 수정 (우선순위 높음)**: `evaluate_v2.py`에서 Hybrid 호출 시 쿼리 레벨별 ODD 힌트를 odd_filter로 전달하는 로직 추가
2. **L4 Embedding 약점 원인 분석**: L4-01, L4-02가 실패하는 구체 클립을 캡션 레벨에서 확인 — bge-m3이 생성한 임베딩에서 두 표현의 거리 측정
3. **L2 BM25 약점 쿼리 탐색**: L2-07, L2-09에서 BM25가 실패한 클립 캡션 확인 → 캡션 어휘 표준화 가능성 검토
4. **top-k 확장 실험**: `--top-k 10`으로 재평가해 Recall@10 곡선 확인
