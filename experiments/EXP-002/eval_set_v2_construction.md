# eval_set_v2.json 구성 방식 해설

**작성**: 2026-06-04  
**대상 파일**: `data/eval/eval_set_v2.json`  
**관련 코드**: `src/avdata/eval/build_eval_set_v2.py`

---

## 1. 왜 이 파일이 필요한가

EXP-001의 eval_set.json은 키워드 일치율로 relevant를 판정했다.  
이 방식은 BM25에 구조적으로 유리한 라벨을 만들기 때문에, Embedding이 실제로 좋아도 낮은 점수를 받는 **평가셋 편향(Gap-1)** 이 발생했다.

eval_set_v2.json은 이 편향을 제거하기 위해 **GPT-4o-mini가 의미 기반으로 라벨을 직접 판정**하는 방식으로 교체한 파일이다.

---

## 2. 전체 생성 파이프라인

```
queries_v2.json (60개 쿼리, L0~L4)
        │
        ▼
[1] BM25 top-50 + Embedding top-50 검색 → 중복 제거
        │
[2] 랜덤 샘플 15개 추가 (천장 효과 확인용)
        │
        ▼
     후보군 (최대 115개 → dedup → ~110개)
        │
[3] 각 후보 클립의 캡션을 GPT-4o-mini로 점수화
        │  condition_score (0~2)
        │  causal_score    (0~2)
        ▼
[4] 레벨별 relevance 임계값 적용
        │  L0/L1/L4: condition_score >= 2
        │  L2/L3:    condition_score + causal_score >= 3
        ▼
eval_set_v2.json (정답셋)
```

---

## 3. 단계별 상세 설명

### 3-1. 입력

| 항목 | 위치 | 내용 |
|------|------|------|
| 쿼리 파일 | `data/eval/queries_v2.json` | 60개 쿼리 (L0×20, L1×10, L2×15, L3×10, L4×5) |
| 전체 클립 ID | `data/index/clip_ids.json` | 299,180개 클립 |
| 캡션 텍스트 | `/Data1/home/bskang/cds-data/captions/{uuid}.camera_front_wide_120fov.txt` | 클립당 1개, 최대 3000자 사용 |
| 검색 인덱스 | `data/active/` (심볼릭 링크 → `data/artifacts/exp-001/`) | BM25 인덱스 + HNSW 임베딩 인덱스 |

---

### 3-2. 후보군 구성

쿼리 1개당:

```
BM25.search(query, top_k=50)         → 50개
Embedding.search(query, top_k=50)    → 50개
                                     ──────────
                                     합집합(set) → ~95개 (중복 제거)
random.sample(random_pool, 15)       → 15개
                                     ──────────
                                     최종 후보  → ~110개
```

**random_pool의 범위:**

```python
# all_clip_ids = data/index/clip_ids.json → 299,180개 전체
random_pool = [c for c in all_clip_ids if c not in candidate_ids]
# = 299,180 - ~95(BM25+Embedding 결과) = ~299,085개
```

즉 랜덤 풀은 **29만 개 전체에서 이미 뽑힌 ~95개를 제외한 나머지** 이며, 여기서 15개를 무작위 추출한다.

**왜 랜덤 샘플을 추가하는가?**  
BM25와 Embedding 모두 관련 클립을 top-50에 포함시키지 못하는 경우(천장 효과)가 있을 수 있다.  
29만 개 중 랜덤 15개를 넣어서 그 중에 relevant가 나오면 두 검색기 모두 해당 클립을 놓쳤다는 증거가 된다.  
RUNBOOK 기준 L0/L1/L4에서 `random hits > 0`이면 천장 효과가 존재한다고 해석한다.

---

### 3-3. LLM 점수화

각 후보 클립에 대해 다음 프롬프트를 GPT-4o-mini에 전달한다.

```
System: "You are an expert autonomous driving data annotator. ..."

User:
  Query: {쿼리 텍스트}
  Caption: {클립 캡션 최대 2000자}

  Score:
  - condition_score (0-2): 환경/상황 조건 일치도
  - causal_score    (0-2): 인과 체인 일치도
  - relevant (true/false): 종합 판정

  Return JSON: {"condition_score": int, "causal_score": int, "relevant": bool}
```

호출 설정:
- `response_format: json_object` — JSON 파싱 실패 방지
- `temperature: 0` — 재현성 확보
- `max_tokens: 64` — 비용 절감
- 실패 시 `condition_score=0, causal_score=0`으로 fallback

---

### 3-4. relevance 임계값 규칙

```python
def _relevance_threshold(level: str, condition: int, causal: int) -> bool:
    if level in ("L2", "L3"):
        return (condition + causal) >= 3
    return condition >= 2
```

| 레벨 | 규칙 | 설계 의도 |
|------|------|---------|
| L0, L1, L4 | `condition_score >= 2` | 조건이 완전 일치한 클립만 정답 |
| L2, L3 | `condition_score + causal_score >= 3` | 인과 체인이 있으면 조건 점수가 1이어도 정답 가능 |

**L2/L3에서 임계값이 다른 이유**:  
L2는 "wet road **causes** emergency braking **near pedestrian**"처럼 인과 서술이 핵심이다.  
클립 캡션이 조건(wet road)만 언급하더라도 인과 반응(emergency braking)이 명확하면 정답으로 인정해야 한다.  
반대로 조건 묘사 없이 인과 장면만 있는 경우(cond=1, causal=2)는 L2 기준에서도 미달이다.

---

### 3-5. 저장 포맷

쿼리별 JSON 구조:

```json
{
  "L0-01": {
    "source": "llm",
    "level": "L0",
    "text": "pedestrian crossing at night intersection",
    "relevant_clip_ids": ["uuid-1", "uuid-2", ...],
    "n_candidates": 112,
    "n_relevant": 91,
    "scored_details": [
      {
        "clip_id": "uuid-1",
        "condition_score": 2,
        "causal_score": 2,
        "relevant": true
      },
      ...
    ]
  }
}
```

- `source: "llm"` — 체크포인트 재시작 시 이 키가 있어야만 이어쓰기에 사용됨 (`source: "dry_run"` 항목은 스킵됨)
- 매 쿼리 처리 후 즉시 파일 저장 → 중간에 중단돼도 완료된 쿼리부터 재개 가능

---

## 4. 사례 해설 — L0-01 쿼리

### 기본 정보

```
쿼리 ID : L0-01
레벨    : L0
텍스트  : "pedestrian crossing at night intersection"
후보 수 : 112개
relevant: 91개 (81.2%)
```

L0 규칙: **`condition_score >= 2`** 이면 relevant

---

### 4-1. 점수 분포

| condition | causal | 개수 | 판정 | 설명 |
|-----------|--------|------|------|------|
| 2 | 2 | 69개 | **PASS** | 조건·인과 모두 완전 일치 |
| 2 | 1 | 22개 | **PASS** | 조건 완전 일치, 인과는 부분 |
| 1 | 2 | 1개 | **FAIL** | 인과는 풍부하지만 조건 미달 |
| 1 | 1 | 14개 | **FAIL** | 조건·인과 모두 부분 일치 |
| 1 | 0 | 3개 | **FAIL** | 조건 부분, 인과 없음 |
| 0 | 0 | 3개 | **FAIL** | 무관한 클립 |

**합계**: 91개 PASS + 21개 FAIL = 112개

---

### 4-2. PASS 클립 예시

#### (cond=2, causal=2) — 가장 강한 relevant

캡션 일부:
```
Driving at night on a multi-laned boulevard, the ego-vehicle travels in the
third lane of a four-laned roadway. Streetlights illuminate the scene ...
Approaching an intersection, the ego-vehicle encounters several warning signs:
a yield sign instructing drivers to ...
```

**판정 근거**:
- `condition_score=2`: "night" + "intersection" 두 조건 모두 완전 언급
- `causal_score=2`: 접근-감속-반응의 행동 체인이 서술됨
- L0 규칙 `condition>=2` 만족 → PASS

#### (cond=2, causal=1) — 조건 완전·인과 부분

캡션 일부:
```
Nighttime driving occurs on a narrow street, illuminated by streetlights.
... Ahead, there is an intersection marked with pedestrian signs, indicating
potential crossings or intersections where pedestrians may be present.
```

**판정 근거**:
- `condition_score=2`: "nighttime" + "intersection" 명확히 언급
- `causal_score=1`: 보행자 예고만 있고 실제 사건·반응 없음 (부분)
- L0 규칙 `condition>=2` 만족 → PASS

---

### 4-3. FAIL 클립 예시

#### (cond=0, causal=0) — 완전 무관 클립

캡션 일부:
```
Driving forward in a tunnel, the ego-vehicle is traveling on a multi-laned
roadway. Ahead of it, a truck occupies the middle lane, moving steadily while
its brake lights illuminate intermittently ...
```

**판정 근거**:
- 야간(night) 언급 없음 (터널 내부 조명)
- 교차로(intersection) 없음
- 보행자 없음
- L0 규칙 미달 → FAIL

#### (cond=1, causal=0) — 조건 부분·인과 없음

캡션 일부:
```
Driving on a multi-laned road, the ego-vehicle travels in the fourth lane from
the right. The roadway is divided into three lanes ... Adjacent to these through
lanes, there are two additional lanes—one designated exclusively for buses and
another marked as a bike lane ...
```

**판정 근거**:
- 야간 조건 미언급
- 교차로는 간접 암시 수준 (`condition_score=1`)
- 보행자·사건 없음 (`causal_score=0`)
- L0 규칙 미달 → FAIL

#### (cond=1, causal=1) — 가장 많은 FAIL 패턴 (14개)

캡션 일부:
```
Driving at night on a narrow road lined with buildings and parked cars, the
scene is illuminated by streetlights. ... Ahead, there is an intersection
marked by a red traffic light. The ego-vehicle approaches this junction
cautiously, slowing down as it nears the stop line.
```

**판정 근거**:
- "night" ✓, "intersection" ✓ 언급 있음 → 조건 인식됨
- 그러나 보행자가 직접 등장하지 않음 → "pedestrian crossing" 조건 불완전
- 인과: 접근·감속 있으나 보행자로 인한 반응 아님 → 부분
- 종합: 야간 교차로 장면이긴 하지만 "pedestrian crossing"의 핵심이 없음
- L0 규칙 `condition_score < 2` → FAIL

#### (cond=1, causal=2) — 1개 존재하는 특수 케이스

캡션 일부:
```
The scene unfolds on a sunny day along a bustling city street ...
The ego-vehicle is positioned at an intersection, waiting at a red traffic light.
Pedestrian crosswalks are visible ahead ... A pedestrian crosses in front ...
```

**판정 근거**:
- "sunny day" — 야간 조건 미충족 (`condition_score=1`)
- 교차로+보행자 횡단 장면은 있어서 인과 서술은 풍부 (`causal_score=2`)
- L0 규칙은 `condition >= 2` 만 보고, causal 무시 → FAIL
- **핵심**: 낮의 교차로 보행자 장면은 "야간 교차로 보행자"와 의미적으로 다름 → 올바른 탈락

---

### 4-4. 탈락 21개 요약

| 탈락 원인 | 개수 |
|---------|------|
| 조건 부분 일치 (야간 OR 교차로 중 하나만) | 18개 |
| 조건 완전 미일치 (다른 장면) | 3개 |
| **합계** | **21개** |

---

## 5. 전체 60쿼리 현황 요약

현재 파일 기준 (2026-06-04):

| 항목 | 값 |
|------|-----|
| `source` | 전부 `"llm"` (60개) |
| 총 쿼리 | 60개 |
| 정답 없는 쿼리 | 0개 |
| 총 relevant 클립 수 | (단말 확인 필요, 앞 세션 명령 참조) |

---

## 6. dry-run과의 차이

| 구분 | dry-run | LLM (현재) |
|------|---------|-----------|
| 라벨 방식 | 쿼리 단어가 캡션에 포함되면 relevant | LLM이 의미·인과를 직접 판단 |
| L2 쿼리 편향 | BM25 키워드 중심 → Embedding 불리 | 의미 일치 기반 → 공정 비교 가능 |
| 처리 비용 | 무료 | ~$0.60 |
| `source` 필드 | `"dry_run"` | `"llm"` |
| 재시작 시 동작 | 무시(스킵)됨 | 이어쓰기에 사용 |

---

## 7. evaluate_v2.py에서의 사용 방식

이 파일이 평가 단계에서 어떻게 쓰이는지:

```python
eval_set = json.loads(eval_set_v2.json)

# n_relevant == 0인 쿼리는 평가에서 제외
eval_set = {qid: v for qid, v in eval_set.items() if v["n_relevant"] > 0}

for qid, qdata in eval_set.items():
    results = searcher.search(qdata["text"], method=method, top_k=k)
    retrieved = [r.clip_id for r in results]
    relevant  = qdata["relevant_clip_ids"]           # ← 이 파일의 정답 목록
    
    recall = len(set(retrieved[:k]) & set(relevant)) / min(k, len(relevant))
    mrr    = 1/rank  if any found in top-k else 0
```

즉, `relevant_clip_ids` 필드가 검색 결과의 정오(正誤)를 판정하는 **정답 키** 역할을 한다.

---

## 8. 관련 파일 위치

| 파일 | 역할 |
|------|------|
| `data/eval/queries_v2.json` | 입력 쿼리 60개 |
| `data/eval/eval_set_v2.json` | 이 문서가 설명하는 정답셋 |
| `src/avdata/eval/build_eval_set_v2.py` | 생성 스크립트 |
| `src/avdata/eval/evaluate_v2.py` | 이 파일을 사용하는 평가 스크립트 |
| `src/avdata/search/searcher.py` | 후보 생성에 사용된 Searcher |
| `experiments/EXP-002/RUNBOOK.md` | 실행 가이드 |
