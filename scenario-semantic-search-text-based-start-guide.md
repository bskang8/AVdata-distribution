---
title: "시나리오 시맨틱 서치: 텍스트 묘사 기반 실험 시작 가이드"
category: overviews
sources:
  - multimodal/kim-2025-genius-generative-framework-universal
  - rl-agents/song-2026-paperorchestra-multi-agent-framework
  - autonomous-driving/rivera-2025-scenario-understanding-traffic-scenes
  - autonomous-driving/chodowiec-2026-odd-behaviour-scenario-coverage
tags: [semantic-search, scenario, bm25, embedding, faiss, evaluation, autonomous-driving, korean-nlp]
created: 2026-05-08
---

## 현재 데이터 상황

```
보유 데이터:
  30만 클립 × (주행 영상 파일 + 한국어 구조화 묘사 .txt)

핵심 변화 (LVLM 태깅 방식 대비):
  ✗ LVLM 태깅 불필요 → 묘사 파일이 이미 텍스트 시맨틱을 담고 있음
  ✗ 키프레임 추출 불필요 → Phase 1까지 영상 미사용
  ✓ 텍스트만으로 BM25 + 임베딩 베이스라인 즉시 구축 가능
  ✓ 구조화 형식 → ODD 필드 파싱으로 태그 필터 자동 획득
```

---

## 전체 타임라인

| 기간 | 작업 | 산출물 |
|------|------|--------|
| Day 1 | 텍스트 파일 형식 확인 + 샘플 100개 정독 | 파일 형식 문서 |
| Day 2-4 | 평가셋 구축 (50 쿼리 × 수동 레이블링) | `eval_set.json` |
| Day 3-5 | BM25 인덱스 빌드 (30만 전체) | `bm25_index.pkl` |
| Day 4-7 | 임베딩 추출 + Faiss HNSW 인덱스 빌드 | `hnsw.index` |
| Day 5-7 | ODD 태그 파서 작성 | `odd_tags.json` |
| Day 8-10 | 첫 번째 Recall@5 비교 실험 | `experiment_001_results.csv` |

---

## Day 1: 텍스트 파일 형식 파악

모든 설계의 전제. **샘플 10개를 직접 읽어서** 4가지를 확인한다.

```bash
# 파일 구조 확인
ls /path/to/clips/ | head -20
ls /path/to/descriptions/ | head -20

# 샘플 묘사 파일 확인
cat /path/to/descriptions/clip_000001.txt
```

**확인 목록**:

| 항목 | 확인 내용 | 이후 결정에 영향 |
|------|---------|--------------|
| 파일명 규칙 | 클립ID ↔ txt 파일명 매핑 방식 | 인덱스 키 설계 |
| 묘사 길이 | 평균 몇 문장/몇 토큰인가 | 임베딩 모델 max_length |
| 구조 필드 | 날씨/시간/도로/이벤트 등 어떤 항목이 있는가 | ODD 파서 설계 |
| 일관성 | 모든 파일이 동일 형식인가 | 파싱 예외처리 범위 |

예상 형식 예시:
```
날씨: 맑음
시간대: 주간
도로유형: 편도 2차선 국도
주행속도: 약 60km/h
특이사항: 전방 100m 지점에서 자전거가 갑자기 차도로 진입함.
          자아차량이 급제동하며 우측으로 회피.
위험도: 높음
```

---

## Day 2-4: 평가셋 구축 (Ground Truth 50 쿼리)

**평가셋 없이 만든 시스템은 방향 없이 달리는 것과 같다.** 영상을 볼 필요 없이 txt 파일만으로 구축 가능하다.

```bash
# 500개 랜덤 샘플링
ls /path/to/descriptions/*.txt | shuf | head -500 > pilot_500.txt

# 묘사 한 파일로 합치기 (검토용)
while read f; do echo "=== $f ==="; cat "$f"; echo; done < pilot_500.txt > pilot_preview.txt
```

```python
# eval_builder.py
import json

QUERIES = [
    "야간 교차로에서 보행자가 갑자기 나타나는 상황",
    "비오는 날 고속도로에서 앞차가 급제동하는 상황",
    "주차장에서 후진 중 다른 차량과 충돌 위험",
    "어린이보호구역에서 어린이가 도로로 뛰어드는 상황",
    "야간 좌회전 중 반대편 차선 직진 차량과 충돌 위험",
    # ... 50개 작성
]

# pilot_500 클립 묘사를 읽고 각 쿼리에 해당하는 클립 ID를 수동 기입
eval_set = {
    "야간 교차로에서 보행자가 갑자기 나타나는 상황": [
        "clip_000123", "clip_004521", "clip_089234"
    ],
    # ...
}

with open("eval_set.json", "w", encoding="utf-8") as f:
    json.dump(eval_set, f, ensure_ascii=False, indent=2)
```

**쿼리 설계 기준**: 각 쿼리당 정답이 2-5개 나오도록 설계.
- 0개 → 쿼리가 너무 구체적
- 50개 이상 → 쿼리가 너무 광범위

---

## Day 3-5: BM25 베이스라인 (30만 전체)

텍스트 파일이 있으면 BM25 인덱스는 수 시간 안에 30만 전체 처리 가능.

```python
# build_bm25.py
import pickle
from pathlib import Path
from rank_bm25 import BM25Okapi
from kiwipiepy import Kiwi

kiwi = Kiwi()

def tokenize_ko(text: str) -> list[str]:
    tokens = kiwi.tokenize(text)
    return [t.form for t in tokens if t.tag in ('NNG', 'NNP', 'VV', 'VA', 'XR')]

desc_dir = Path("/path/to/descriptions")
clip_ids, corpus = [], []

for txt_file in sorted(desc_dir.glob("*.txt")):
    clip_ids.append(txt_file.stem)
    corpus.append(tokenize_ko(txt_file.read_text(encoding="utf-8")))

bm25 = BM25Okapi(corpus)

with open("bm25_index.pkl", "wb") as f:
    pickle.dump({"bm25": bm25, "clip_ids": clip_ids}, f)
```

```python
# search_bm25.py
import pickle
from kiwipiepy import Kiwi

kiwi = Kiwi()
with open("bm25_index.pkl", "rb") as f:
    data = pickle.load(f)
bm25, clip_ids = data["bm25"], data["clip_ids"]

def search(query: str, top_k: int = 10) -> list[str]:
    tokens = [t.form for t in kiwi.tokenize(query)
              if t.tag in ('NNG', 'NNP', 'VV', 'VA')]
    scores = bm25.get_scores(tokens)
    top_indices = scores.argsort()[::-1][:top_k]
    return [clip_ids[i] for i in top_indices]
```

설치: `pip install rank-bm25 kiwipiepy`

---

## Day 4-7: 임베딩 베이스라인 + Faiss HNSW 인덱스

### 임베딩 모델 선택

| 모델 | 장점 | 단점 | 권장 상황 |
|------|------|------|---------|
| `BAAI/bge-m3` | 한국어 최강, 8192 토큰 지원 | 모델 크기 큼 (570M) | GPU 있을 때 **(추천)** |
| `intfloat/multilingual-e5-large` | 가볍고 빠름 | 긴 묘사에서 성능 다소 저하 | GPU 제한 시 |

```python
# build_embeddings.py
import numpy as np
import faiss
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-m3"
BATCH_SIZE = 256
DESC_DIR = Path("/path/to/descriptions")
OUTPUT_DIR = Path("./index")
OUTPUT_DIR.mkdir(exist_ok=True)

model = SentenceTransformer(MODEL_NAME)

clip_ids, texts = [], []
for txt_file in sorted(DESC_DIR.glob("*.txt")):
    clip_ids.append(txt_file.stem)
    texts.append(txt_file.read_text(encoding="utf-8"))

# 30만개 기준 GPU에서 약 2-4시간
all_embeddings = model.encode(
    texts,
    batch_size=BATCH_SIZE,
    show_progress_bar=True,
    normalize_embeddings=True  # 코사인 유사도를 내적으로 계산 가능하게
)

# Faiss HNSW 인덱스 (속도-정확도 균형)
dim = all_embeddings.shape[1]
index = faiss.IndexHNSWFlat(dim, 32)  # M=32: 연결 수
index.hnsw.efConstruction = 200
index.add(all_embeddings.astype(np.float32))

faiss.write_index(index, str(OUTPUT_DIR / "hnsw.index"))
with open(OUTPUT_DIR / "clip_ids.json", "w") as f:
    json.dump(clip_ids, f)
```

```python
# search_embedding.py
import numpy as np
import faiss
import json
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-m3")
index = faiss.read_index("./index/hnsw.index")
index.hnsw.efSearch = 128  # 높을수록 정확하나 느림

with open("./index/clip_ids.json") as f:
    clip_ids = json.load(f)

def search(query: str, top_k: int = 10) -> list[tuple[str, float]]:
    q_emb = model.encode([query], normalize_embeddings=True)
    scores, indices = index.search(q_emb.astype(np.float32), top_k)
    return [(clip_ids[i], float(s)) for i, s in zip(indices[0], scores[0])]
```

---

## Day 5-7: ODD 태그 파서 (병렬 작업)

구조화 묘사에서 필드를 파싱해 Level 1 태그 필터를 구현한다. ([[autonomous-driving/chodowiec-2026-odd-behaviour-scenario-coverage|Chodowiec 2026]] ODD 4차원 커버리지 적용)

```python
# parse_odd_tags.py
import re
import json
from pathlib import Path

# 실제 묘사 파일 형식에 맞게 조정 필요
FIELD_PATTERNS = {
    "날씨": r"날씨[:\s]+([^\n]+)",
    "시간대": r"시간대[:\s]+([^\n]+)",
    "도로유형": r"도로유형[:\s]+([^\n]+)",
    "위험도": r"위험도[:\s]+([^\n]+)",
    "특이사항": r"특이사항[:\s]+([^\n]+(?:\n\s+[^\n]+)*)",
}

NORMALIZE = {
    "날씨": {"맑음": "clear", "흐림": "cloudy", "비": "rain", "눈": "snow", "안개": "fog"},
    "시간대": {"주간": "day", "야간": "night", "새벽": "dawn", "황혼": "dusk"},
}

def parse_description(text: str) -> dict:
    tags = {}
    for field, pattern in FIELD_PATTERNS.items():
        m = re.search(pattern, text)
        if m:
            val = m.group(1).strip()
            if field in NORMALIZE:
                for k, v in NORMALIZE[field].items():
                    if k in val:
                        val = v
                        break
            tags[field] = val
    return tags

desc_dir = Path("/path/to/descriptions")
all_tags = {}
for txt_file in sorted(desc_dir.glob("*.txt")):
    all_tags[txt_file.stem] = parse_description(
        txt_file.read_text(encoding="utf-8")
    )

with open("odd_tags.json", "w", encoding="utf-8") as f:
    json.dump(all_tags, f, ensure_ascii=False, indent=2)
```

---

## Day 8-10: 통합 평가 실험

3가지 접근법을 한 곳에서 비교한다.

```python
# evaluate.py
import json, time, pickle
import faiss, numpy as np
from sentence_transformers import SentenceTransformer
from kiwipiepy import Kiwi

# --- 로드 ---
with open("eval_set.json", encoding="utf-8") as f: eval_set = json.load(f)
with open("bm25_index.pkl", "rb") as f: bm25_data = pickle.load(f)
with open("odd_tags.json", encoding="utf-8") as f: odd_tags = json.load(f)
with open("./index/clip_ids.json") as f: clip_ids = json.load(f)

index = faiss.read_index("./index/hnsw.index")
index.hnsw.efSearch = 128
model = SentenceTransformer("BAAI/bge-m3")
kiwi = Kiwi()
clip_id_to_idx = {cid: i for i, cid in enumerate(clip_ids)}

def recall_at_k(retrieved, relevant, k):
    if not relevant: return 0.0
    return len(set(retrieved[:k]) & set(relevant)) / min(k, len(relevant))

def search_bm25(query, k=5):
    tokens = [t.form for t in kiwi.tokenize(query) if t.tag in ('NNG','NNP','VV','VA')]
    scores = bm25_data["bm25"].get_scores(tokens)
    return [bm25_data["clip_ids"][i] for i in scores.argsort()[::-1][:k]]

def search_embedding(query, k=5):
    q_emb = model.encode([query], normalize_embeddings=True)
    _, indices = index.search(q_emb.astype(np.float32), k)
    return [clip_ids[i] for i in indices[0]]

def search_hybrid_layered(query, odd_filter: dict, k=5):
    """Level 1: ODD 태그 필터 → Level 2: 임베딩 ANN"""
    filtered_ids = [
        cid for cid, tags in odd_tags.items()
        if all(tags.get(key) == val for key, val in odd_filter.items())
    ]
    if not filtered_ids:
        return search_embedding(query, k)

    candidate_indices = [clip_id_to_idx[cid] for cid in filtered_ids if cid in clip_id_to_idx]
    candidate_embs = index.reconstruct_batch(candidate_indices)
    q_emb = model.encode([query], normalize_embeddings=True).astype(np.float32)
    scores = candidate_embs @ q_emb.T
    top_i = scores[:, 0].argsort()[::-1][:k]
    return [filtered_ids[i] for i in top_i]

# --- 평가 루프 ---
results = []
for query, relevant in eval_set.items():
    row = {"query": query}

    t0 = time.perf_counter()
    row["bm25_recall5"] = recall_at_k(search_bm25(query), relevant, 5)
    row["bm25_ms"] = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    row["emb_recall5"] = recall_at_k(search_embedding(query), relevant, 5)
    row["emb_ms"] = (time.perf_counter() - t0) * 1000

    results.append(row)

import pandas as pd
df = pd.DataFrame(results)
print(df[["bm25_recall5","bm25_ms","emb_recall5","emb_ms"]].mean().round(3))
df.to_csv("experiment_001_results.csv", index=False)
```

---

## 첫 번째 실험 결과 예상 및 판단 분기

```
예상 결과표 (실제 수치는 직접 측정):

                 Recall@5    검색 지연
BM25             40-60%      <10ms
임베딩 (전체)     55-75%      50-200ms
계층 하이브리드    TBD         TBD       ← Phase 2 최적화 대상
목표              80%+        <500ms
```

**결과에 따른 분기**:

| 결과 패턴 | 진단 | 다음 행동 |
|---------|------|---------|
| BM25 >> 임베딩 | 묘사가 키워드 중심, 임베딩 모델 재검토 | 다른 임베딩 모델 시도 |
| 임베딩 >> BM25 | 시맨틱 이해가 핵심 | 계층 하이브리드 Level 2를 임베딩으로 확정 |
| 둘 다 60% 이하 | 평가셋 품질 또는 묘사 파일 품질 문제 | 평가셋 재검토 후 파일 샘플 확인 |

---

## 핵심 인사이트

| 인사이트 | 근거 |
|---------|------|
| LVLM 태깅 없이 기존 묘사 파일만으로 BM25·임베딩 베이스라인 즉시 구축 가능 | 데이터 상황 |
| 평가셋을 먼저 만들어야 실험 방향이 생긴다 | 실험 설계 원칙 |
| 구조화 묘사에서 ODD 필드 파싱으로 Level 1 태그 필터를 무료로 획득 | [[autonomous-driving/chodowiec-2026-odd-behaviour-scenario-coverage\|Chodowiec 2026]] |
| `BAAI/bge-m3`가 한국어 긴 묘사 임베딩에 가장 적합 | 모델 선택 기준 |
| HNSW 인덱스가 30만 규모에서 속도·정확도 균형 최적 | Faiss 인덱스 선택 |

---

## 관련 문서

- [[overviews/scenario-semantic-search-agent-research-design]] — 다중 에이전트 협업 프레임워크 전체 설계
- [[multimodal/kim-2025-genius-generative-framework-universal]] — 생성형 검색 (Phase 2 계층 하이브리드 근거)
- [[autonomous-driving/chodowiec-2026-odd-behaviour-scenario-coverage]] — ODD 4차원 커버리지 프레임워크
- [[autonomous-driving/rivera-2025-scenario-understanding-traffic-scenes]] — CatPipe (LVLM 태깅 방식, 필요 시 참조)
