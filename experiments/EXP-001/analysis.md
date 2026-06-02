# EXP-001 갭 분석

**실험**: BM25 / Embedding / Hybrid 베이스라인  
**완료일**: 2026-06-02 (phase2/3/4 재실행 반영)  
**데이터**: `results/metrics.csv` (20 쿼리 × 3 방법 = 60행)  
**클립 수**: 299,180개 (구버전 83,612개에서 전체 데이터셋으로 확장)

---

## 1. 실제 결과 (raw CSV 기반 재계산)

> 탐색 리포트의 수치와 달리, 아래는 `results/metrics.csv`를 직접 집계한 값이다.

| 방법 | Recall@5 평균 | MRR@5 평균 | 지연 평균 (ms) | 지연 중앙값 (ms) |
|------|--------------|-----------|--------------|----------------|
| BM25 | **0.900** | **0.900** | 182.26 † | 1.93 |
| Embedding | 0.520 | 0.623 | 929.53 †† | 5.56 |
| Hybrid | 0.520 | 0.623 | 26.82 ††† | 5.35 |

† BM25 첫 쿼리 3,598ms (299k 인덱스 로드) 포함.  
†† Embedding 첫 쿼리 18,485ms (모델 워밍업) 포함.  
††† Hybrid 첫 쿼리 434ms 포함.

### 쿼리별 Recall@5 비교

| 쿼리 | BM25 | Emb | Hybrid | Emb-BM25 차이 |
|------|------|-----|--------|--------------|
| pedestrian crossing at night intersection | 1.0 | 0.8 | 0.8 | −0.2 |
| nighttime driving on poorly lit street | 1.0 | 0.6 | 0.6 | −0.4 |
| night urban driving with streetlights | 0.8 | **1.0** | **1.0** | **+0.2** ← Emb 우세 |
| highway driving with truck overtaking | 0.6 | **1.0** | **1.0** | **+0.4** ← Emb 우세 |
| highway lane change merging | 1.0 | 0.2 | 0.2 | −0.8 |
| highway poor visibility warning sign | 1.0 | 0.6 | 0.6 | −0.4 |
| vehicle sudden braking ahead | 1.0 | 0.6 | 0.6 | −0.4 |
| emergency braking to avoid collision | 1.0 | 0.6 | 0.6 | −0.4 |
| red light stopping intersection | 0.8 | 0.4 | 0.4 | −0.4 |
| pedestrian suddenly enters road | 1.0 | **0.0** | **0.0** | **−1.0** ← Emb 완전 실패 |
| pedestrian crossing with dog | 0.8 | 0.6 | 0.6 | −0.2 |
| children near school zone | 0.8 | 0.6 | 0.6 | −0.2 |
| foggy conditions reduced visibility | 1.0 | 0.4 | 0.4 | −0.6 |
| rainy road wet conditions | 1.0 | 0.4 | 0.4 | −0.6 |
| parking lot reversing | 1.0 | 0.8 | 0.8 | −0.2 |
| narrow road parked vehicles on both sides | 1.0 | 0.6 | 0.6 | −0.4 |
| cyclist entering road unexpectedly | 1.0 | **0.0** | **0.0** | **−1.0** ← Emb 완전 실패 |
| truck parked blocking lane | 0.8 | 0.2 | 0.2 | −0.6 |
| bus stop with passengers | 0.8 | 0.2 | 0.2 | −0.6 |
| animal crossing road wildlife | 0.6 | 0.8 | 0.8 | **+0.2** ← Emb 우세 |

---

## 2. 핵심 갭 목록

### Gap-1 🔴 평가셋 구조적 편향 (Critical)

**현상**: BM25 Recall@5 = 0.90, Embedding = 0.53. 격차가 예상보다 크다.

**근본 원인**: `keyword_relevance()` 함수가 정답 레이블 기준이다.

```python
# build_eval_set.py
def keyword_relevance(text: str, query: str) -> bool:
    query_words = [w for w in re.split(r"\W+", query.lower()) if len(w) > 3]
    return all(w in text_lower for w in query_words)
```

쿼리 단어가 캡션에 **글자 그대로 포함**돼야 정답이 된다.  
BM25도 동일하게 **토큰 매칭**으로 검색 → 정답셋이 BM25에 유리하게 편향.

**실제로 무엇을 측정했는가**:
- BM25가 키워드 포함 문서를 잘 찾는가? → Yes (당연한 결과)
- Embedding이 의미상 유사한 문서를 잘 찾는가? → **측정 불가** (정답이 키워드 기반이므로)

**Embedding 완전 실패 쿼리 분석** (Recall@5 = 0.0):
- `pedestrian suddenly enters road`: 정답 클립이 "pedestrian", "suddenly", "enters", "road" 4단어를 모두 포함해야 함. Embedding 상위 5개는 의미상 관련(보행자 갑작스러운 등장)이지만 "suddenly"나 "enters" 대신 다른 표현 사용 → 평가 지표상 0점
- `cyclist entering road unexpectedly`: 정답 클립이 "cyclist", "entering", "road" 3단어를 모두 포함해야 함. Embedding은 의미상 유사한 클립을 반환하지만 해당 단어를 그대로 쓰지 않은 캡션이 상위에 랭크됨 → 평가 지표상 0점
- → 두 경우 모두 실제 검색 품질이 낮다기보다 **평가 정답이 키워드 기반**으로 생성된 구조적 편향

**다음 실험으로 연결**: EXP-002 — 의미 기반 쿼리 + LLM 평가 레이블링

---

### Gap-2 🟠 Hybrid Search = Embedding (ODD 필터 무효)

**현상**: Hybrid Recall@5 수치가 Embedding과 **완전 동일**.

**원인 가설**:
- `searcher.py`의 hybrid 모드에서 ODD 필터가 없거나 너무 관대해서 전체 코퍼스를 통과
- 필터가 작동해도 정답 클립들이 그 안에 포함되어 있어 embedding 결과와 동일
- 또는 현재 hybrid = ODD tagging 단계 없이 embedding만 실행

**근거**: 
- Hybrid와 Embedding의 Recall@5가 20개 쿼리 **모두** 동일한 값
- Latency만 다름 (첫 쿼리: Hybrid 141ms vs Embedding 20,428ms → 초기화 경로가 다름)

**확인 필요**: `src/avdata/search/searcher.py`의 hybrid 분기 로직 검토

**다음 실험으로 연결**: EXP-004 — Hybrid 소프트 필터 재설계

---

### Gap-3 🟠 ODD 태그 커버리지 편차 심각

**현상**: 필드별 커버리지 격차가 크다.

| 필드 | 커버리지 | Unknown 클립 수 | 비고 |
|------|---------|----------------|------|
| agent_type | 100.0% | 0 | 완전 (165,956개가 "none") |
| ego_action | 100.0% | 0 | 완전 (braking 편향: 151,310개) |
| road_type | 96.7% | 9,929 | 양호 (intersection 편향: 181,612개) |
| hazard_level | 84.7% | 45,712 | 보통 |
| time_of_day | 62.7% | 111,554 | **저조** |
| weather | 52.9% | 140,937 | **저조** |
| traffic_density | 37.4% | 187,356 | **최악** |

**원인**: Regex 패턴이 캡션의 다양한 표현을 커버하지 못함.
- `traffic_density` 예: "bumper-to-bumper", "light traffic", "stop-and-go" 등 미캡처
- `weather` 예: "overcast skies", "drizzling", "slippery surface" 등 미캡처

**영향**: Hybrid search의 ODD 필터가 36~62%만 태그된 데이터에 적용되면  
unknown 클립 53k개는 필터에서 탈락 → 실제 관련 클립 누락 가능성

**다음 실험으로 연결**: EXP-003 — LLM fallback ODD 태깅

---

### Gap-4 🟡 분포 편향 (정상 시나리오 과다, 희귀 시나리오 과소)

**현상**: ODD 태그 분포가 극단적으로 편향.

- `ego_action`: braking(151,310) vs reversing(562) → **비율 269:1**
- `road_type`: intersection(181,612) vs tunnel(802) → **비율 226:1**
- `agent_type`: none(165,956) vs emergency_vehicle(773) → **비율 214:1**

**영향**: 임베딩 공간도 동일하게 편향 → 희귀 시나리오는 UMAP에서 저밀도 영역  
Long-tail 클립(14,959개, 밀도 하위 5%) 탐지는 됐지만 이들이 **진짜 OOD**인지 검증 미완료

**다음 실험으로 연결**: EXP-003 후속 — Long-tail 클립 수동 검증

---

### Gap-5 🟡 임베딩 모델 워밍업 미처리

**현상**: 첫 쿼리 cold start 지연이 모든 방법에서 발생.

| 방법 | 첫 쿼리 지연 | 2번째 이후 중앙값 |
|------|------------|----------------|
| BM25 | 3,598ms (299k 인덱스 로드) | 1.93ms |
| Embedding | 18,485ms (모델 로드 + HNSW 초기화) | 5.56ms |
| Hybrid | 434ms | 5.35ms |

**평균 지연 왜곡**: cold start가 포함된 평균은 실제 서비스 지연을 반영하지 않음.  
중앙값이 실제 지연에 가까우며, BM25/Embedding/Hybrid 모두 중앙값 기준 200ms 이하.

**수정 방법**: evaluate.py에 워밍업 더미 쿼리 1회 추가 후 타이머 시작

---

### Gap-6 🟡 평가 쿼리 다양성 부족

**현상**: 20개 쿼리가 모두 영어 키워드 직접 사용 방식. 다음 유형이 없음.

| 누락 쿼리 유형 | 예시 |
|--------------|------|
| 동의어/바꿔쓰기 | "vehicle stopped abruptly" (braking 의미) |
| 부정 표현 | "clear weather without fog" |
| 복합 조건 | "night + rain + pedestrian + highway" |
| 한국어 쿼리 | 실사용 시나리오 |
| 추상적 묘사 | "dangerous urban scenario at dusk" |

**영향**: 현재 쿼리로는 Embedding의 의미 이해 능력을 실제로 테스트할 수 없음.

---

## 3. 갭 우선순위 매트릭스

| 갭 | 심각도 | 수정 난이도 | 다음 실험 |
|----|--------|------------|---------|
| Gap-1: 평가셋 편향 | 🔴 Critical | 중 | EXP-002 |
| Gap-2: Hybrid = Embedding | 🟠 High | 중 | EXP-004 |
| Gap-3: ODD 커버리지 | 🟠 High | 높음 (LLM 비용) | EXP-003 |
| Gap-4: 분포 편향 | 🟡 Medium | 높음 (데이터 수집) | 장기 |
| Gap-5: 워밍업 미처리 | 🟡 Medium | 낮음 (코드 1줄) | EXP-002에 포함 |
| Gap-6: 쿼리 다양성 | 🟡 Medium | 중 | EXP-002 |

---

## 4. 다음 실험 권고

**EXP-002 (즉시)**: 평가셋 재설계
- Gap-1, Gap-5, Gap-6 동시 해결
- LLM(GPT-4o-mini)으로 의미 기반 정답 레이블 생성
- 동의어 쿼리, 복합 조건 쿼리 추가 (목표: 50개+)
- 워밍업 쿼리 추가

**EXP-003 (EXP-002 완료 후)**: LLM ODD 태깅
- Gap-3 해결
- traffic_density, weather 필드 우선 (커버리지 최저)
- GPT-4o-mini로 low-coverage 53k 클립 처리

**EXP-004 (EXP-003 완료 후)**: Hybrid 재설계
- Gap-2 해결
- ODD 소프트 필터 (exact match → 확률 기반 가중)
- EXP-003의 개선된 ODD 태그 활용

---

## 5. 재현 방법

```bash
# EXP-001 결과 재현 (299,180개 전체 데이터셋 기준)
uv sync

# Phase 1: BM25 인덱스
uv run python -m avdata.phase1.build_bm25

# Phase 2: 임베딩 + HNSW (299,180개, GPU 권장)
uv run python -m avdata.phase2.build_embeddings

# Phase 3: ODD 태그 추출
uv run python -m avdata.phase3.extract_odd_tags

# Phase 4: 분포 분석 시각화 (전체, 수 시간 소요)
uv run python -m avdata.phase4.distribution_analysis

# 평가
uv run python -m avdata.eval.evaluate > experiments/EXP-001/results/raw_output.txt
```
