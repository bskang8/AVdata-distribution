# 연구 반복 워크플로우 — 수동 수행 가이드

이 문서는 iterative 연구 과정에서 **사람이 직접 수행해야 하는 단계**를 설명한다.  
코드 실행 방법이 아니라, 연구를 어떻게 진행하고 기록하고 고도화할지에 대한 절차 지침이다.

---

## 전체 루프 구조

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│   [1] 실험 완료                                      │
│        ↓                                            │
│   [2] 갭 분석 작성          ← 결과 데이터 직접 분석    │
│        ↓                                            │
│   [3] 문헌 추가 → 위키화     ← 논문/자료 탐색         │
│        ↓                                            │
│   [4] 기술 선정 → 실험 설계  ← 위키 INDEX 참조        │
│        ↓                                            │
│   [5] 실험 실행 → [1]로 반복                         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

각 단계는 독립적인 문서를 생성한다.  
모든 문서의 연결고리는 `RESEARCH_LOG.md`다.

---

## 단계별 상세 절차

---

### [1] 실험 완료 직후 할 일

실험 코드 실행이 끝나면 즉시 아래를 수행한다.

#### 1-1. 결과 파일 저장

```
experiments/EXP-00N/results/
├── metrics.csv          ← 수치 결과 (Recall, MRR, Latency 등)
├── raw_output.txt       ← 콘솔 출력 전체
└── artifacts/           ← 생성된 시각화, 인덱스 등 (크기가 작은 것만)
```

결과 파일이 다른 위치에 생성됐다면 직접 복사 또는 이동한다.

#### 1-2. Git 태그 생성

```bash
git add experiments/EXP-00N/results/
git commit -m "EXP-00N: [실험명] 결과 기록"
git tag -a exp-00N-complete -m "EXP-00N: [실험명] 완료"
```

태그를 만들면 나중에 이 시점의 코드와 결과를 정확히 복원할 수 있다.

---

### [2] 갭 분석 작성

실험 결과에서 **무엇이 부족한지**를 구조화하는 가장 중요한 단계다.  
파일 위치: `experiments/EXP-00N/analysis.md`

#### 2-1. 결과 수치 직접 재계산

자동 출력된 평균값을 그대로 쓰지 않는다.  
`results/metrics.csv`를 열어 쿼리별로 확인하고, 이상값(outlier)을 찾는다.

확인할 것:
- 특정 쿼리에서만 성능이 유독 낮은가?
- 지연(latency)에 워밍업 등 이상값이 포함됐는가?
- 방법 A가 방법 B보다 나은 경우와 반대인 경우를 모두 나열하라.

#### 2-2. 원인 가설 작성

수치를 보고 **왜 이 결과가 나왔는지** 가설을 쓴다.  
"~였기 때문일 것이다"로 끝나는 문장 형태로 작성한다.

예시:
```
Hybrid Recall@5 = Embedding Recall@5 (동일)인 이유:
  → ODD 필터가 너무 관대해서 전체 클립을 통과시켰기 때문일 것이다.
  → 또는 hybrid 코드가 실제로 ODD 필터를 적용하지 않고 있기 때문일 것이다.
```

#### 2-3. 갭 목록 작성

각 갭은 아래 4가지를 포함한다.

```markdown
### Gap-N [심각도 이모지] 갭 제목

**현상**: 수치/관찰로 기술
**원인 가설**: 왜 이런 결과가 나왔는지 (확실하지 않아도 됨)
**영향**: 이 갭이 연구 전체에 미치는 영향
**다음 실험으로 연결**: EXP-XXX
```

심각도 기준:
- 🔴 Critical: 이걸 고치지 않으면 다음 실험 결과를 신뢰할 수 없다
- 🟠 High: 성능에 직접 영향, 가능한 빨리 해결
- 🟡 Medium: 알고 있어야 하지만 즉시 해결 불필요

#### 2-4. 갭 우선순위 매트릭스 작성

```markdown
| 갭 | 심각도 | 수정 난이도 | 다음 실험 |
|----|--------|------------|---------|
| Gap-1: ... | 🔴 Critical | 중 | EXP-002 |
| Gap-2: ... | 🟠 High | 낮음 | EXP-003 |
```

**다음 실험으로 연결할 갭을 최대 2개만 선택한다.**  
한 번에 모든 갭을 고치려 하면 무엇이 효과적이었는지 알 수 없다.

---

### [3] 문헌 추가 및 위키화

갭 분석에서 "어떤 기술로 해결할 수 있을까"를 생각했다면,  
관련 논문이나 자료를 찾아 추가한다.

#### 3-1. 자료 찾기

찾아볼 곳:
- [arXiv](https://arxiv.org) — 최신 논문
- [Papers with Code](https://paperswithcode.com) — 구현 포함 논문
- [Semantic Scholar](https://semanticscholar.org) — 인용 탐색
- GitHub — 오픈소스 구현체
- 기술 블로그 — 실전 경험

검색 키워드 예시 (본 프로젝트 기준):

| 갭 | 검색 키워드 |
|----|-----------|
| 평가셋 품질 | "LLM relevance labeling retrieval", "zero-shot relevance annotation" |
| ODD 태깅 | "LLM scene understanding autonomous driving", "VLM tagging pipeline" |
| Hybrid search | "late interaction retrieval", "learned sparse retrieval", "ColBERT" |
| 희귀 시나리오 | "long-tail distribution autonomous driving", "rare event detection" |

#### 3-2. 자료 등록

**PDF 논문**인 경우:
```
literature/papers/[저자-연도-제목약어].pdf
예: literature/papers/thakur-2021-beir.pdf
```

**URL 자료**인 경우, `literature/links.md`에 아래 형식으로 추가:

```markdown
## [논문/자료 제목]
- **출처**: 저자, 연도, 학술대회
- **URL**: https://...
- **관련 갭**: Gap-1
- **핵심 아이디어**: 한 문장 요약
- **위키 파일**: docs/wiki/evaluation/llm-labeling.md (생성 후 기입)
```

#### 3-3. 위키화 (`/graphify` 사용)

Claude Code에서 아래 명령을 입력한다:

```
/graphify
```

프롬프트에서 처리할 대상을 지정한다:
```
literature/papers/thakur-2021-beir.pdf 를 읽고
핵심 기술, 방법론, 장단점을 추출해서
docs/wiki/evaluation/beir-benchmark.md 로 정리해줘.
이 논문은 Gap-1 (평가셋 편향) 해결에 관련이 있어.
```

#### 3-4. 위키 파일 형식

`/graphify`가 생성하거나, 직접 작성할 때의 표준 형식:

```markdown
# [기술명]

## 개요
한 문단으로 무엇인지 설명.

## 핵심 아이디어
- 포인트 1
- 포인트 2

## 장점
- ...

## 단점 / 한계
- ...

## 본 프로젝트 적용 가능성
어떤 갭에 어떻게 적용할 수 있는지.

## 구현 참고
- 공식 코드: https://...
- 주요 파라미터: ...
- 예상 비용/시간: ...

## 출처
- 논문: [제목] (저자, 연도)
- 원본: literature/papers/파일명.pdf
```

#### 3-5. INDEX.md 업데이트

위키 파일을 만들었으면 `docs/wiki/INDEX.md`의 해당 카테고리 표에 행을 추가한다:

```markdown
| BEIR Benchmark | evaluation/beir-benchmark.md | Gap-1 | EXP-002 |
```

---

### [4] 기술 선정 및 실험 설계

#### 4-1. 기술 선정 기준

`docs/wiki/INDEX.md`의 갭-기술 대응표를 보고 다음 기준으로 선정한다:

| 기준 | 설명 |
|------|------|
| **갭 직결성** | 해결하려는 갭과 직접 연결되는가 |
| **구현 가능성** | 현재 코드베이스에 통합하기 얼마나 어려운가 |
| **비용** | GPU 시간, API 비용, 데이터 수집 비용 |
| **독립성** | 이 기술의 효과를 다른 변수와 분리해서 측정할 수 있는가 |

**한 실험에서 한 번에 하나의 핵심 변수만 바꾼다.**  
두 개 이상 바꾸면 무엇이 효과를 낸 건지 알 수 없다.

#### 4-2. 새 실험 폴더 생성

```bash
mkdir -p experiments/EXP-00N/results
```

#### 4-3. hypothesis.md 작성

아래 섹션을 모두 채운다:

```markdown
# EXP-00N · [실험명]

**상태**: 🔲 설계 중
**대응 갭**: EXP-00X/analysis.md §Gap-N

## 배경
이전 실험에서 무엇이 문제였는지 2-3줄로 기술.

## 가설
> "~을 하면 ~가 ~보다 높아진다."
구체적인 수치 목표를 포함한다.

## 설계
변경하는 것 하나, 나머지는 EXP-이전과 동일하게 유지.

### 검증 기준
| 기준 | 통과 조건 |
|------|----------|
| 지표 A | 수치 기준 |

## 실행 계획
단계별 커맨드.

## 선행 조건
- [ ] 조건 1
- [ ] 조건 2
```

#### 4-4. config.yaml 작성

이전 실험의 config.yaml을 복사하고, **바꾸는 부분만 수정**한다.  
변경된 파라미터는 주석으로 표시한다:

```yaml
# EXP-00N config — EXP-00X 대비 변경사항: ground_truth_method
ground_truth_method: llm_relevance   # 변경: keyword_relevance → llm_relevance
llm_model: gpt-4o-mini
...
```

---

### [5] 실험 실행 중 할 일

#### 5-1. 중간 관찰 기록

실험이 오래 걸린다면, 중간 상태를 `results/notes.md`에 적는다:

```markdown
## 실행 중 메모
- 13:20 — 임베딩 생성 완료, 예상보다 2배 느림 (GPU 메모리 부족으로 배치 축소)
- 14:05 — LLM API rate limit 발생, 지연 추가
```

#### 5-2. 예상 밖 결과 즉시 기록

실행 중 이상한 점이 보이면 멈추고 기록한다.  
무시하고 계속 실행하면 나중에 원인을 추적하기 어렵다.

---

### [6] RESEARCH_LOG.md 업데이트

모든 단계가 완료될 때마다 `RESEARCH_LOG.md`의 Timeline 표에 행을 추가한다.

```markdown
| 2026-06-15 | 실험 | EXP-002 완료: LLM 평가셋으로 Embedding Recall@5 0.53→0.71 확인 | experiments/EXP-002/ |
| 2026-06-15 | 결정 | Embedding이 의미 쿼리에서 우세 확인 → EXP-004 Hybrid 재설계로 진행 | RESEARCH_LOG.md |
```

유형은 세 가지만 쓴다: `실험`, `문헌`, `결정`.

실험 목록 표도 상태를 업데이트한다:

```markdown
| EXP-002 | 평가셋 재설계 | ✅ 완료 | LLM 레이블로 Embedding 실제 성능 확인 |
```

---

## 전체 체크리스트

### 실험 완료 시

- [ ] `experiments/EXP-00N/results/`에 결과 파일 저장
- [ ] `git commit` + `git tag -a exp-00N-complete` 생성
- [ ] `experiments/EXP-00N/analysis.md` 작성 (갭 분석)
- [ ] `RESEARCH_LOG.md` Timeline 업데이트

### 문헌 추가 시

- [ ] PDF → `literature/papers/` 또는 URL → `literature/links.md`
- [ ] `/graphify`로 위키 파일 생성 → `docs/wiki/카테고리/파일명.md`
- [ ] `docs/wiki/INDEX.md` 표에 행 추가
- [ ] `literature/links.md`에 위키 파일 경로 기입
- [ ] `RESEARCH_LOG.md` Timeline에 문헌 행 추가

### 새 실험 설계 시

- [ ] `experiments/EXP-00N/hypothesis.md` 작성
- [ ] `experiments/EXP-00N/config.yaml` 작성 (이전 config 기반)
- [ ] `RESEARCH_LOG.md` 실험 목록 표에 새 행 추가 (상태: 🔲 설계 중)
- [ ] `docs/wiki/INDEX.md` 해당 기술의 적용 실험 컬럼 업데이트

---

## 파일별 역할 한눈에 보기

| 파일 | 언제 쓰나 | 누가 업데이트하나 |
|------|----------|----------------|
| `RESEARCH_LOG.md` | 항상, 모든 단계 완료 시 | 사람 (직접) |
| `experiments/EXP-N/hypothesis.md` | 실험 설계 시 | 사람 (직접) |
| `experiments/EXP-N/config.yaml` | 실험 설계 시 | 사람 (직접) |
| `experiments/EXP-N/analysis.md` | 실험 완료 후 | 사람 (직접) |
| `experiments/EXP-N/results/` | 실험 완료 직후 | 코드 자동 + 사람 이동 |
| `literature/links.md` | 자료 추가 시 | 사람 (직접) |
| `docs/wiki/*/파일.md` | 자료 위키화 시 | `/graphify` + 사람 검토 |
| `docs/wiki/INDEX.md` | 위키 파일 생성 시 | 사람 (직접) |

---

---

## src/ 코드 버전 관리

> **이 섹션이 다루는 문제**: 실험마다 `src/` 코드가 바뀐다.  
> 어떤 코드가 어떤 결과를 만들었는지 추적하고, 서비스를 안정적으로 유지하는 방법.

---

### 핵심 원칙

실험을 추적하는 두 가지 버전이 항상 쌍으로 존재해야 재현이 가능하다.

```
코드 버전  →  git tag (exp-00N-complete)
데이터 버전 →  data/active 심볼릭 링크 (→ artifacts/exp-00N)
```

두 버전이 서로 어긋나면 결과를 재현할 수 없다.

---

### 초기 커밋 (최초 1회)

현재 이 저장소는 커밋이 없다. 실험을 시작하기 전에 초기 커밋을 만들어야 한다.

```bash
# 1. 대용량 바이너리는 .gitignore로 제외 (이미 설정됨)
#    data/index/embeddings.npy, hnsw.index, bm25s_index/ 등

# 2. 전체 스테이징 (바이너리 제외)
git add \
  src/ pyproject.toml uv.lock .gitignore \
  main.py PIPELINE.md README.md RESEARCH_LOG.md \
  docs/ experiments/ literature/ scripts/ \
  data/eval/ data/tags/odd_coverage.json \
  data/artifacts/exp-001/clip_ids.json

# 3. 초기 커밋
git commit -m "초기 커밋: EXP-001 베이스라인 완료 상태"

# 4. EXP-001 완료 태그
git tag -a exp-001-complete -m "BM25/Embedding/Hybrid 베이스라인 — Recall@5 BM25=0.90, Emb=0.53"
```

> **주의**: `data/artifacts/exp-001/` 의 대용량 파일(`embeddings.npy`, `hnsw.index`)은  
> git에 추가하지 않는다. 아티팩트 관리는 `data/artifacts/` 디렉토리와 심볼릭 링크가 담당한다.

---

### 실험별 브랜치 전략

```
master ──────────────────────────────────────────────────────▶
        │                   │                   │
        └─ exp/002-eval    └─ exp/003-llm-odd  └─ exp/004-hybrid
           (개발 중)           (대기)               (대기)
```

실험 하나 = 브랜치 하나. 완료되면 master에 merge하고 태그를 붙인다.

#### 실험 시작 시

```bash
# master를 기준으로 새 브랜치 생성
git checkout master
git checkout -b exp/00N-[실험-짧은-이름]
# 예: git checkout -b exp/002-eval-redesign
```

이 브랜치에서만 이번 실험 관련 코드를 수정한다.

#### 수정 범위 가이드

| 실험 목표 | 주로 수정되는 src 파일 |
|-----------|----------------------|
| 평가셋 재설계 (EXP-002) | `eval/build_eval_set.py`, `eval/evaluate.py` |
| LLM ODD 태깅 (EXP-003) | `phase3/extract_odd_tags.py`, `config.py` (ODD_FIELDS) |
| Hybrid 재설계 (EXP-004) | `search/searcher.py`, `api/models.py`, `ui/app.py` |
| 임베딩 모델 교체 | `config.py` (EMBED_MODEL_NAME), `phase2/build_embeddings.py` |

새 실험 전용 스크립트는 기존 파일을 수정하지 말고 **새 파일**로 추가한다.  
예: `build_eval_set.py` 수정 대신 `build_eval_set_v2.py` 추가 후 비교 가능하게 유지.

#### 실험 완료 시

```bash
# 1. 최종 코드 커밋
git add src/ experiments/EXP-00N/
git commit -m "EXP-00N: [실험명] 코드 완료"

# 2. master에 merge
git checkout master
git merge exp/00N-[실험-이름] --no-ff
# --no-ff: merge 커밋을 만들어 실험 경계를 git log에서 명확히 구분

# 3. 아티팩트 스냅샷 + 서비스 전환
./scripts/snapshot_artifacts.sh exp-00N --activate

# 4. 완료 태그 (코드 + 아티팩트가 모두 준비된 시점)
git tag -a exp-00N-complete -m "EXP-00N: [결과 한 줄 요약]"

# 5. 브랜치 정리 (선택)
git branch -d exp/00N-[실험-이름]
```

---

### 서비스 중 코드 수정 시 유의사항

FastAPI는 `--reload` 옵션으로 실행하면 `src/` 파일 변경을 감지해 자동으로 재시작된다.  
즉, **실험 브랜치에서 코드를 수정하는 동안 서비스가 그 변경을 즉시 반영한다.**

| 상황 | 영향 | 대처 |
|------|------|------|
| 실험 브랜치에서 `searcher.py` 수정 | FastAPI 자동 재시작 → 새 로직으로 서비스 | 의도된 동작이면 그대로, 아니면 서버를 내리고 개발 |
| 실험 중 서비스 결과가 달라짐 | 정상 — 코드가 바뀐 것 | `git diff master` 로 변경 사항 확인 |
| 실험 브랜치 코드에서 서버 크래시 | `git stash` 또는 `git checkout master` 로 복구 | 서비스 재시작 |

안정적인 서비스가 필요한 경우:
```bash
# 실험 개발은 로컬에서, 서비스는 master 코드로만 실행
git stash          # 실험 중 변경사항 임시 저장
git checkout master
# 서비스 재시작
uv run uvicorn avdata.api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### 특정 실험 재현 방법

```bash
# 코드 복원
git checkout exp-002-complete   # 태그 시점 코드로 전환

# 아티팩트 복원
ln -sfn artifacts/exp-002 data/active

# 서비스 재시작
uv run uvicorn avdata.api.main:app --host 0.0.0.0 --port 8000

# 재현 완료 후 최신으로 돌아오기
git checkout master
ln -sfn artifacts/exp-003 data/active   # 최신 실험으로
```

---

### git log 모습 (이상적인 상태)

```
* a1b2c3d (tag: exp-003-complete, master) Merge exp/003-llm-odd-tagging
|\
| * d4e5f6g EXP-003: LLM fallback ODD 태깅 추가
| * h7i8j9k EXP-003: config.py ODD_FIELDS 업데이트
|/
* k1l2m3n (tag: exp-002-complete) Merge exp/002-eval-redesign
|\
| * n4o5p6q EXP-002: evaluate.py 워밍업 추가
| * r7s8t9u EXP-002: build_eval_set_v2.py 추가 (LLM 레이블링)
|/
* v1w2x3y (tag: exp-001-complete) 초기 커밋: EXP-001 베이스라인
```

각 태그에서 `git checkout <tag>` + `ln -sfn artifacts/<exp> data/active` 로 완전 재현 가능.

---

### 전체 버전 대응표 (업데이트 필요)

실험이 완료될 때마다 아래 표를 `RESEARCH_LOG.md`에 추가한다.

| 실험 | git 태그 | data/active 대상 | 주요 src 변경 |
|------|---------|-----------------|-------------|
| EXP-001 | `exp-001-complete` | `artifacts/exp-001` | 초기 베이스라인 |
| EXP-002 | (예정) | `artifacts/exp-002` | `eval/build_eval_set_v2.py`, `eval/evaluate.py` |

---

## 자주 하는 실수

**실수 1: 실험 결과 보고 바로 다음 실험으로 진행**  
→ `analysis.md`를 먼저 쓴다. 원인이 불분명한 채 다음 실험을 하면 같은 문제가 반복된다.

**실수 2: 한 실험에서 여러 변수를 동시에 변경**  
→ 한 번에 하나만 바꾼다. 두 개 이상 바꾸면 어느 변경이 효과를 냈는지 알 수 없다.

**실수 3: 평균값만 보고 쿼리별 세부 수치를 확인하지 않음**  
→ 평균이 같아도 어떤 쿼리가 좋아지고 나빠졌는지가 중요하다. 반드시 쿼리별로 분석한다.

**실수 4: RESEARCH_LOG.md 업데이트를 나중으로 미룸**  
→ 실험 완료 당일에 바로 기록한다. 일주일 지나면 결정의 이유를 기억하기 어렵다.

**실수 5: 위키 파일을 만들고 INDEX.md에 추가하지 않음**  
→ INDEX.md가 없으면 나중에 이 기술이 있는지 모른다.

---

## 예시: 한 사이클 전체 흐름

```
2026-06-01  EXP-001 완료
            → experiments/EXP-001/results/metrics.csv 저장
            → git tag -a exp-001-complete
            → experiments/EXP-001/analysis.md 작성
              (Gap-1: 평가셋 편향, Gap-2: Hybrid 무효 발견)
            → RESEARCH_LOG.md 업데이트

2026-06-02  문헌 탐색: "LLM relevance labeling" 논문 2편 찾음
            → literature/papers/sun-2023-llm-ranker.pdf 저장
            → literature/links.md 업데이트
            → /graphify → docs/wiki/evaluation/llm-ranker.md 생성
            → docs/wiki/INDEX.md 업데이트
            → RESEARCH_LOG.md 문헌 행 추가

2026-06-03  기술 선정: LLM relevance labeling을 EXP-002에 적용 결정
            → experiments/EXP-002/hypothesis.md 작성
            → experiments/EXP-002/config.yaml 작성
            → RESEARCH_LOG.md 실험 목록 상태 업데이트

2026-06-04  EXP-002 실행
            → [코드 실행]

2026-06-05  EXP-002 완료
            → experiments/EXP-002/results/ 저장
            → git checkout master && git merge exp/002-eval-redesign
            → git tag -a exp-002-complete -m "EXP-002 완료"
            → ./scripts/snapshot_artifacts.sh exp-002 --activate
            → experiments/EXP-002/analysis.md 작성
            → RESEARCH_LOG.md 업데이트
            → 다음 사이클 시작...
```
