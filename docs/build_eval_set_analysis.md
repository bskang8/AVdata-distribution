# `build_eval_set --sample 83612` 상세 분석

## 실행 명령

```bash
uv run python -m avdata.eval.build_eval_set --sample 83612
```

---

## 전체 흐름

```
83,612개 캡션 파일 목록
    → random.Random(42).sample(83612개)   # 전체 = 셔플만
    → 텍스트 전체 메모리 로드 (corpus dict)
    → 20개 쿼리 × corpus 전체 스캔
        → keyword_relevance() 판정
    → eval_set.json 저장
```

---

## 1단계 — 캡션 파일 목록 수집 및 샘플링

```python
caption_files = sorted(CAPTIONS_DIR.glob("*.camera_front_wide_120fov.txt"))
# → 83,612개 파일 목록

rng          = random.Random(42)          # 고정 시드 → 재현 가능
sample_files = rng.sample(caption_files, min(83612, len(caption_files)))
# --sample 83612 = 전체 개수이므로 사실상 전체 셔플
```

`random.Random(42)` 고정 시드 덕분에 **항상 동일한 순서**로 샘플링됩니다.

---

## 2단계 — 전체 캡션 메모리 로드

```python
corpus = {
    f.name[: -len(".camera_front_wide_120fov.txt")]: f.read_text(...)
    for f in sample_files
}
# corpus = { "3de966fb-71c2-44bf-90cb-...": "The vehicle was driving at night...", ... }
```

키 = clip_id (UUID), 값 = 캡션 전체 텍스트  
83,612개 × 평균 331단어 → 메모리 약 **200~300MB** 차지

---

## 3단계 — 20개 쿼리 × corpus 전체 스캔

각 쿼리마다 83,612개 캡션을 전부 순회하여 `keyword_relevance()`로 관련성 판정:

```python
def keyword_relevance(text: str, query: str) -> bool:
    text_lower  = text.lower()
    query_words = [w for w in re.split(r"\W+", query.lower()) if len(w) > 3]
    return all(w in text_lower for w in query_words)
```

### 판정 기준 — 길이 4 이상인 단어가 **모두** 캡션에 포함되어야 `True`

쿼리 예시로 살펴보면:

| 쿼리 | 추출되는 단어 (len > 3) | 판정 조건 |
|------|----------------------|---------|
| `"pedestrian crossing at night intersection"` | `["pedestrian", "crossing", "night", "intersection"]` | 4개 단어 모두 캡션에 존재해야 함 |
| `"animal crossing road wildlife"` | `["animal", "crossing", "road", "wildlife"]` | 4개 단어 모두 존재해야 함 |
| `"foggy conditions reduced visibility"` | `["foggy", "conditions", "reduced", "visibility"]` | 4개 단어 모두 존재해야 함 |

불용어 처리는 없고, 단순 `in` 연산자로 **부분 문자열 매칭**을 수행합니다.  
(`"crossing"` 검색 시 `"crossings"`, `"crossing"` 모두 매칭)

### 평가 대상 쿼리 20개

```
# Night scenarios
"pedestrian crossing at night intersection"
"nighttime driving on poorly lit street"
"night urban driving with streetlights"
# Highway scenarios
"highway driving with truck overtaking"
"highway lane change merging"
"highway poor visibility warning sign"
# Hazard / braking
"vehicle sudden braking ahead"
"emergency braking to avoid collision"
"red light stopping intersection"
# Pedestrians
"pedestrian suddenly enters road"
"pedestrian crossing with dog"
"children near school zone"
# Weather
"foggy conditions reduced visibility"
"rainy road wet conditions"
# Parking / slow manoeuvre
"parking lot reversing"
"narrow road parked vehicles on both sides"
# Special agents
"cyclist entering road unexpectedly"
"truck parked blocking lane"
"bus stop with passengers"
# OOD / rare
"animal crossing road wildlife"
```

---

## 4단계 — 정답 필터링 및 쿼리 제외

```python
if len(relevant) < min_relevant:   # min_relevant = 2 (기본값)
    print(f"  SKIP (too few): '{query}'")
    continue
```

관련 클립이 2개 미만이면 해당 쿼리를 eval set에서 제외합니다.  
`"animal crossing road wildlife"` 같은 희귀 시나리오가 이 조건에 걸릴 가능성이 높습니다.

---

## 5단계 — JSON 저장

```python
# data/eval/eval_set.json
{
  "pedestrian crossing at night intersection": [
    "3de966fb-71c2-44bf-90cb-85e52dc42fd5",
    "1c5b4cd5-...",
    ...   // 83,612개 중 모든 매칭 clip_id
  ],
  "highway driving with truck overtaking": [ ... ],
  ...
}
```

저장 경로: `data/eval/eval_set.json`

---

## `--sample 5000` vs `--sample 83612` 비교

| 항목 | `--sample 5000` | `--sample 83612` |
|------|----------------|-----------------|
| 스캔 대상 | 83,612개 중 5,000개 랜덤 | 전체 83,612개 |
| 정답 pool | 5,000개 내에서만 존재 | 전체 코퍼스 기반 |
| 문제점 | 검색 인덱스는 83,612개 전체 대상 → 정답이 샘플 밖이면 **Recall/MRR = 0** | 없음 |
| 실행 시간 | ~1분 | ~10~20분 |

---

## 주요 한계 — `keyword_relevance`의 정밀도 문제

`all()` 조건이므로 단어 하나라도 캡션에 없으면 제외됩니다.

| 상황 | 결과 |
|------|------|
| 캡션에 `"pedestrian"` 대신 `"person on foot"` | ❌ False (false negative) |
| 캡션에 쿼리 단어가 우연히 모두 등장하지만 관련 없는 씬 | ✅ True (false positive) |

이 방식은 **weak supervision** — 정밀한 레이블이 아니라 키워드 기반 휴리스틱입니다.  
실제 성능 측정의 신뢰도를 높이려면 일부 쿼리에 대해 수동 검수가 필요합니다.
