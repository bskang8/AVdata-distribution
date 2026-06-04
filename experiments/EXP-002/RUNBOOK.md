# EXP-002 실행 가이드 (RUNBOOK)

**실험명**: 인과 기반 평가셋 재설계 + ODD 커버리지 분석 + 임베딩 클러스터 갭 탐지  
**상태**: 🟢 Phase A 완료 (Gap-2 픽스 + ODD 커버리지 + 클러스터링)  
**최종 갱신**: 2026-06-04  
**방법론 근거**: `experiments/EXP-002/methodology_revision.md`

---

## 목차

1. [개요 및 설계 변경 이력](#1-개요-및-설계-변경-이력)
2. [사전 조건](#2-사전-조건)
3. [Phase A — 즉시 실행 (완료)](#3-phase-a--즉시-실행-완료)
4. [Phase B — 3~5일 (대기)](#4-phase-b--35일-대기)
5. [Phase C — 1~2주 (대기)](#5-phase-c--12주-대기)
6. [Phase D — 1~3개월 (미래)](#6-phase-d--13개월-미래)
7. [현재 결과 요약](#7-현재-결과-요약)
8. [산출물 위치](#8-산출물-위치)
9. [검증 기준](#9-검증-기준)
10. [비용 추정](#10-비용-추정)
11. [트러블슈팅](#11-트러블슈팅)

---

## 1. 개요 및 설계 변경 이력

### 원래 설계 (2026-06-02, 폐기)

| Axis | 방법 | 문제점 |
|------|------|--------|
| B | 7D 연속 ODD 벡터 (fog→0.12) | 수치 자체가 임의적, 재현 불가 |
| C | Standard Normalizing Flow (5D→7D) | 역매핑 없음 → 갭 → 클립 이름 변환 불가 |

### 재설계 (2026-06-04, `methodology_revision.md` 기반)

| Phase | 시점 | 핵심 변경 | 비용 |
|-------|------|----------|------|
| A | 즉시 | Gap-2 픽스 + ODD Coverage Matrix + HDBSCAN + Metric Space Magnitude | $0 |
| B | 3~5일 | SANFlow (per-cluster Gaussian NF) + LLM 시나리오 taxonomy | ~$0.50 |
| C | 1~2주 | T2SG 씬 그래프 기반 토폴로지 커버리지 | ~$1 |
| D | 1~3개월 | 갭 시나리오 합성 (ChatScene, UniSim, Scenario Dreamer) | 미정 |

**핵심 논거:**
- `fog=0.12` 수치는 임의적 → 재현 불가 → ODD Coverage Matrix(이산 조합 집계)로 대체
- Standard NF는 역매핑 없음 → SANFlow (클러스터별 Gaussian)로 대체
- Gap 탐지: 임베딩 공간 HDBSCAN → 소형 클러스터 = 희귀 시나리오

---

## 2. 사전 조건

### 환경 설치

```bash
uv sync   # anthropic, sklearn 1.8.0, umap-learn, normflows 포함
```

### API 키

```bash
# Phase A Step 3 LLM 레이블링 + eval set 구축 (gpt-4o-mini)
export OPENAI_API_KEY="sk-..."
```

### 필수 아티팩트

```
data/active/
  bm25s_index/       ← BM25 인덱스
  clip_ids.json      ← 299,180개 클립 ID
  embeddings.npy     ← (299180, 1024) bge-m3 임베딩
  hnsw.index         ← FAISS HNSW 인덱스
  odd_tags.json      ← 이산 ODD 태그

data/eval/
  queries_v2.json    ← 60개 쿼리 (L0~L4)
  eval_set_v2.json   ← LLM 레이블 평가셋 ✅
```

확인:
```bash
ls data/active/
# → bm25s_index  clip_ids.json  embeddings.npy  hnsw.index  odd_tags.json
```

---

## 3. Phase A — 즉시 실행 (완료)

### 전체 한 번에 실행

```bash
# 전체 실행 (LLM 레이블링 포함, ANTHROPIC_API_KEY 필요)
bash scripts/run_phase_a.sh

# LLM 레이블링 제외 (API 키 없을 때)
bash scripts/run_phase_a.sh --no-llm

# Recall@10 평가
bash scripts/run_phase_a.sh --top-k 10
```

### Step A-1: Hybrid 재평가 (Gap-2 픽스)

**배경**: 기존 `evaluate_v2.py`는 Hybrid 검색 시 `odd_filter=None`을 전달해
Hybrid가 항상 Embedding과 동일한 결과를 반환했다 (Gap-2 버그).

**픽스 내용** (`src/avdata/eval/evaluate_v2.py`):
- `extract_odd_hint(query)` 함수: 쿼리 텍스트에서 ODD 조건 키워드 추출
- Hybrid 호출 시 `odd_filter=odd_hint` 전달
- Gap-2 검증 블록 추가

```bash
uv run python -m avdata.eval.evaluate_v2 --top-k 5
```

**검증 출력 예시:**
```
── Gap-2 Fix Verification ──────────────────────────────────
  Queries with ODD hint : 53 / 60
    Hybrid ≠ Embedding  : 46  (86.8%)   ← 픽스 확인
    Hybrid == Embedding : 7   (fallback — no matching clips)
  ✓ Gap-2 FIXED
```

---

### Step A-2: ODD Coverage Matrix

**배경**: taxonomy 내 (weather × time_of_day × road_type × hazard_level) 560개 조합 중
실제 클립이 커버하는 조합 수를 집계. 갭 식별.

```bash
uv run python -m avdata.phase6.odd_coverage_matrix
```

**결과 확인:**
```bash
python3 -c "
import json
d = json.load(open('experiments/EXP-002/results/odd_coverage_matrix.json'))
print(f'커버리지: {d[\"covered_combinations\"]} / {d[\"possible_combinations\"]} ({d[\"coverage_rate\"]:.1%})')
print(f'제로 커버리지 갭: {d[\"zero_coverage_count\"]}개')
print()
for ax, dist in d['per_field_distribution'].items():
    top3 = list(dist.items())[:3]
    print(f'  {ax}: {top3}')
"
```

---

### Step A-3: 임베딩 클러스터링 + Metric Space Magnitude + LLM 레이블

**파이프라인**: embeddings.npy → PCA(50D) → UMAP(10D, 캐시) → HDBSCAN → Magnitude → LLM 레이블

```bash
# LLM 레이블링 포함 (ANTHROPIC_API_KEY 필요, ~$0.03)
uv run python -m avdata.phase6.embedding_cluster

# LLM 없이 클러스터링만
uv run python -m avdata.phase6.embedding_cluster --no-llm
```

**주요 파라미터** (`embedding_cluster.py` 내 수정):

| 파라미터 | 현재값 | 설명 |
|---------|-------|------|
| HDBSCAN `min_cluster_size` | 50 | 클러스터 최소 크기 |
| HDBSCAN `min_samples` | 10 | 핵심 포인트 최소 이웃 수 |
| UMAP `n_components` | 10 | 클러스터링용 차원 |
| UMAP `n_neighbors` | 30 | 지역 구조 보존 범위 |
| Magnitude `t` | 1.0 | 스케일 파라미터 |

**UMAP 캐시**: 최초 실행 시 `experiments/EXP-002/results/umap_10d.npy`에 저장.
이후 재실행 시 캐시를 로드해 UMAP 단계 생략.

**결과 확인:**
```bash
python3 -c "
import json
d = json.load(open('experiments/EXP-002/results/cluster_analysis.json'))
print(f'클러스터: {d[\"n_clusters\"]}개, 노이즈: {d[\"n_noise\"]:,} ({d[\"noise_rate\"]:.1%})')
print()
print('Bottom-10 갭 후보 (가장 희귀한 시나리오):')
for c in d['bottom_50_gap_candidates'][:10]:
    label = c['llm_label'] or '(no label)'
    print(f'  cluster {c[\"cluster_id\"]:4d}  n={c[\"size\"]:5d}  mag={c[\"magnitude\"]:.1f}  {label}')
"
```

---

## 4. Phase B — 3~5일 (대기)

### 개요

| 항목 | 내용 |
|------|------|
| 목적 | Standard NF (역매핑 불가) → SANFlow (클러스터별 Gaussian) 로 교체 |
| 근거 | `methodology_revision.md` Phase B 섹션 |
| 참조 논문 | `literature/papers/R4_SANFlow_NeurIPS2023.pdf` |

### 예정 작업

1. **SANFlow 구현** (`src/avdata/phase6/sanflow.py`)
   - 각 HDBSCAN 클러스터에 독립 Gaussian 베이스 분포 할당
   - per-cluster inverse mapping: 갭 좌표 → 클러스터 ID → 시나리오 이름

2. **LLM 시나리오 taxonomy** (`src/avdata/phase6/scenario_taxonomy.py`)
   - AIDE 패턴: 클러스터별 대표 캡션 3개 → GPT-4o-mini → 계층 레이블
   - 출력: `{cluster_id: {level1: str, level2: str, examples: [str]}}`

3. **갭 리포트 재작성** (`src/avdata/phase6/gap_report.py`)
   - 갭 좌표 → 가장 가까운 클러스터 → SANFlow 역매핑 → 시나리오 이름

### 실행 방법 (미구현)

```bash
# 예정
uv run python -m avdata.phase6.sanflow --clusters experiments/EXP-002/results/cluster_analysis.json
uv run python -m avdata.phase6.scenario_taxonomy --no-llm  # 드라이런
uv run python -m avdata.phase6.gap_report
```

---

## 5. Phase C — 1~2주 (대기)

### 개요

| 항목 | 내용 |
|------|------|
| 목적 | 에이전트 상호작용 위상 구조 기반 커버리지 분석 |
| 근거 | `methodology_revision.md` Phase C 섹션 |
| 참조 논문 | `literature/papers/R11_T2SG_CVPR2025.pdf` |

### 예정 작업

1. 10,000개 캡션 파일럿 → LLM으로 씬 그래프 JSON 추출
2. 씬 그래프 임베딩 (GNN 또는 LLM embedding)
3. HDBSCAN 위상 클러스터링
4. 커버리지 갭 리포트

```bash
# 예정 (~$1, GPT-4o-mini 10,000개)
uv run python -m avdata.phase6.scene_graph_extract --n 10000
uv run python -m avdata.phase6.topology_cluster
```

---

## 6. Phase D — 1~3개월 (미래)

갭 시나리오 합성 (현재 범위 외):

| 도구 | 용도 | 참조 |
|------|------|------|
| ChatScene | LLM + CARLA 시나리오 생성 | R14_ChatScene |
| UniSim | 신경 센서 시뮬레이터 | R15_UniSim |
| Scenario Dreamer | 잠재 확산 모델 생성 | R16_ScenarioDreamer |

---

## 7. 현재 결과 요약

### Step A-1: Hybrid 재평가 (2026-06-04 실행)

| 방법 | Recall@5 전체 | L0 | L1 | L2 | L3 | L4 | 지연(중앙값) |
|------|-------------|----|----|----|----|-----|------------|
| BM25 | **0.8533** | 0.930 | 0.940 | 0.707 | 0.900 | 0.720 | 0.9ms |
| Embedding | 0.8267 | 0.880 | 0.940 | 0.707 | 0.900 | 0.600 | 5.4ms |
| **Hybrid (픽스 후)** | 0.6600 | 0.720 | 0.920 | 0.573 | 0.520 | 0.440 | 125.6ms |
| (Hybrid 픽스 전) | ~~0.8267~~ | — | — | — | — | — | — |

**관찰:**
- Gap-2 FIXED: Hybrid가 이제 Embedding과 다른 결과를 반환 (53쿼리 중 46개에서 상이)
- Hybrid 성능이 Embedding보다 낮음: ODD 태그에 `unknown` 값이 많아 관련 클립이 필터에서 탈락
- → Phase B에서 SANFlow로 ODD 태그 품질 독립적인 클러스터 기반 갭 탐지로 전환

**Axis A 가설 체크:**

| 기준 | 결과 |
|------|------|
| L2 gap (Emb−BM25) > L0 gap | ✓ PASS: L2=+0.0000 > L0=−0.0500 |
| Embedding L2 MRR > BM25 L2 MRR | ✓ (Emb=0.9111, BM25=0.8222) |

### Step A-2: ODD Coverage Matrix (2026-06-04 실행)

| 지표 | 값 |
|------|-----|
| 전체 클립 | 299,180개 |
| Taxonomy 조합 수 | 560개 (weather×time×road×hazard) |
| 커버된 조합 | 338개 (60.4%) |
| 제로 커버리지 갭 | 222개 (39.6%) |
| weather `unknown` 비율 | 47.1% (140,937개) |
| time_of_day `unknown` 비율 | 37.3% (111,554개) |

**핵심 발견**: 전체 클립의 약 40%가 weather 태그 없음 → ODD 태그 재추출 여지 있음.

### Step A-3: 임베딩 클러스터링 (2026-06-04 실행)

| 지표 | 값 |
|------|-----|
| 클러스터 수 | 124개 |
| 노이즈 포인트 | 65,893개 (22.0%) |
| PCA 설명 분산 | 69.2% (50D) |
| UMAP 캐시 | `results/umap_10d.npy` ✅ |
| LLM 레이블링 | ❌ 미실행 (ANTHROPIC_API_KEY 필요) |

**상위 10개 갭 후보 (가장 작은 클러스터):**

| cluster | size | magnitude | mag/clip |
|---------|------|-----------|---------|
| 24 | 50 | 1.4 | 0.028 |
| 46 | 50 | 1.1 | 0.023 |
| 44 | 51 | 1.2 | 0.024 |
| 25 | 53 | 1.4 | 0.026 |
| 56 | 53 | 1.3 | 0.025 |

> `mag/clip` < 0.03: 클립 대비 유효 다양성이 매우 낮음 → 내부 중복이 많은 희귀 시나리오 군

---

## 8. 산출물 위치

```
data/eval/
  queries_v2.json                   ✅ 60개 쿼리 (L0~L4)
  eval_set_v2.json                  ✅ LLM 레이블 평가셋

data/active/
  embeddings.npy                    ✅ (299180, 1024)
  odd_tags.json                     ✅ 이산 ODD 태그

experiments/EXP-002/
  methodology_revision.md           ✅ 재설계 근거 문서
  RUNBOOK.md                        ✅ 이 파일
  results/
    experiment_002_results.csv      ✅ Phase A-1 평가 결과 (Gap-2 픽스 버전)
    summary.json                    ✅ 메서드별 요약 통계
    odd_coverage_matrix.json        ✅ Phase A-2 커버리지 분석
    umap_10d.npy                    ✅ UMAP 10D 좌표 (캐시)
    cluster_labels.npy              ✅ HDBSCAN 레이블 (N=299180)
    cluster_analysis.json           ✅ 클러스터별 통계 + 갭 후보
    nf_model.pkl                    ❌ Phase B 산출물 (미생성)
    gap_report.json                 ❌ Phase B 산출물 (미생성)

src/avdata/
  eval/evaluate_v2.py               ✅ Gap-2 픽스 + ODD 힌트 추출
  phase6/__init__.py                ✅
  phase6/odd_coverage_matrix.py     ✅ ODD 커버리지 분석
  phase6/embedding_cluster.py       ✅ 클러스터링 파이프라인

scripts/
  run_phase_a.sh                    ✅ Phase A 전체 오케스트레이션
```

---

## 9. 검증 기준

| 기준 | 목표 | 결과 |
|------|------|------|
| 평가셋 크기 | 쿼리 ≥ 60개, 정답 없는 쿼리 = 0 | ✅ 60개 |
| Gap-2 픽스 확인 | Hybrid ≠ Embedding for hinted queries | ✅ 86.8% 상이 |
| Axis A: L2 gap > L0 gap | L2 gap(Emb−BM25) > L0 gap | ✅ PASS (+0.000 > −0.050) |
| Axis A: 지연 | 중앙값 200ms 이하 | ✅ BM25 0.9ms, Emb 5.4ms, Hybrid 125.6ms |
| ODD Coverage | 커버리지율 계산 완료 | ✅ 60.4% (338/560) |
| 클러스터링 | 클러스터 ≥ 50개 발견 | ✅ 124개 |
| LLM 레이블링 | bottom-50 클러스터 레이블 | ❌ ANTHROPIC_API_KEY 필요 |
| Phase B: SANFlow | NF 역매핑으로 갭 → 시나리오 이름 | ❌ 미구현 |

---

## 10. 비용 추정

| 단계 | 항목 | 비용 | 시간 |
|------|------|------|------|
| Phase A-1 | Gap-2 픽스 + Hybrid 재평가 | 무료 | ~3분 |
| Phase A-2 | ODD Coverage Matrix | 무료 | ~5초 |
| Phase A-3 | PCA + UMAP + HDBSCAN + Magnitude | 무료 | ~20분 |
| Phase A-3 LLM | bottom-50 클러스터 레이블 (gpt-4o-mini) | ~$0.004 | ~2분 |
| Phase B | SANFlow 구현 + LLM taxonomy | ~$0.50 | 3~5일 |
| Phase C | T2SG 씬 그래프 (10k 파일럿) | ~$1.00 | 1~2주 |
| **현재까지 합계** | Phase A (LLM 제외) | **$0** | **~25분** |

---

## 11. 트러블슈팅

### OPENAI_API_KEY 미설정 (LLM 레이블링 실패)

```bash
export OPENAI_API_KEY="sk-..."
# 또는 --no-llm 플래그로 레이블링 건너뜀
uv run python -m avdata.phase6.embedding_cluster --no-llm
```

### UMAP 재실행 강제 (캐시 무효화)

```bash
rm experiments/EXP-002/results/umap_10d.npy
uv run python -m avdata.phase6.embedding_cluster --no-llm
```

### Hybrid 성능이 Embedding보다 낮은 이유

ODD 태그의 `unknown` 비율이 높아 (weather 47%, time_of_day 37%) ODD 필터가 관련 클립을 제외.
해결 방안:
1. ODD 태그 재추출 (`phase3.extract_odd_continuous` LLM refinement)
2. 또는 Phase B SANFlow로 ODD 태그 독립적인 클러스터 기반 접근 전환

### data/active 링크 없음

```bash
ln -sfn data/artifacts/exp-001 data/active
```

### HDBSCAN `FutureWarning: copy`

경고이므로 결과에 영향 없음. 억제하려면:
```python
HDBSCAN(min_cluster_size=50, min_samples=10, copy=True)
```

### normflows import 오류

```bash
uv sync
python3 -c "import normflows; print(normflows.__version__)"
```
