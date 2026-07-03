# EXP-003 설계 — 분포 분석 기반 학습 데이터 큐레이션

**작성일**: 2026-06-30  
**수정일**: 2026-07-02  
**상태**: 🟡 설계 확정 → 구현 준비  
**관련 논문**: Dimlioglu et al. (2026) MOSAIC · Sorscher et al. (NeurIPS 2022) · Eyuboglu et al. (ICLR 2022) · Xia et al. (ICML 2024) · Gadre et al. (NeurIPS 2024) · Ma et al. (ICLR 2018) · Friedman & Dieng (TMLR 2023) · Abbas et al. (2023) SemDeDup · Yao et al. (ACL 2024) SoftDedup · Xie et al. (NeurIPS 2023) DoReMi · Ruppik et al. (NeurIPS 2025) · Cresswell et al. (NeurIPS 2024) FLIPD  
**관련 갭**: Gap-4 (분포 편향: 정상 과다, 희귀 과소)

---

## 1. 실험 동기

자율주행 학습 데이터(83k 클립)는 분포가 불균등하다: 정상 주행 시나리오가 과대 표현되고, 야간·우천·교차로 등 희귀 시나리오는 과소 표현된다(Gap-4). 단순히 "어디에 갭이 있는가"를 찾는 것만으로는 불충분하다 — "얼마나 더 수집해야 하는가"(ROI)와 "D_train 전체 구조가 어떤 상태인가"라는 질문이 남는다. EXP-003은 D_train 분포를 다차원으로 프로파일링하고(Phase 0), 스케일링 법칙 기반 수집 우선순위를 정량화하는(Phase A~C) 독립 실험이다. 이 접근은 D_train 전체의 구조적 편향을 이해하고 최적 구성을 결정하는 DISC(Distribution-Informed Smart Curation) 패러다임을 따른다.

### 패러다임 전환 요약

| 항목 | 기존 접근 (MOSAIC 직접 적용) | 새 방향 (DISC) |
|------|---------------------------|----------------|
| 출발점 | D_pool에서 무엇을 추가할지 선택 | D_train 분포 자체를 먼저 이해 |
| 핵심 질문 | "어떤 클립이 가장 가치 있는가?" | "D_train이 어떤 분포를 가지는가?" |
| 갭 정의 | 성능 여지(a_i) 기반 | 밀도 갭 × 성능 여지 × 커버리지 결합 |
| 프루닝 | 고려 없음 | 중복·저가치 클립 먼저 제거 |
| 이론 근거 | MOSAIC 스케일링 법칙 | DataComp + Sorscher + MOSAIC |

> 이론적 배경 및 패러다임 분석은 [`research_synthesis.md`](research_synthesis.md) 참조.

---

## 2. 가설

**초기 가설 (2026-06-30 v1)**:
> "83k 캡션을 TF-IDF로 클러스터링하면 밀도 갭(저밀도·고LID 클립)이 특정 시나리오 클러스터에 집중되어 있을 것이며,
> 그 클러스터의 스케일링 법칙을 추정하면 추가 수집 필요량을 정량화할 수 있다."

**날카로운 가설 (2026-07-02 v3 — Phase 0 최신 논문 반영 재정립)**:
> "D_train의 독립 정보량(Effective N / Vendi Score), 밀도 구조, 국소 내재 차원(LID)을 동시에 고려하지 않으면,
> 갭만 보고 수집하거나 성능 여지만 보고 수집하는 단일 신호 전략은 비효율적이다.
> 개정된 4차원 결합 우선순위:
> `priority_i = a_i × (1 - density_i) × LID_i_normalized × collectability_i`
> 로 정의된 수집 전략이 단일 신호보다 더 적은 클립으로 더 높은 도메인별 Recall@5를 달성한다.
> 특히 LID를 포함함으로써 '갭이 있는 곳'과 '수집해도 다양성이 느는 곳'이 다를 수 있음을 처음으로 구분한다."

> DISC 4차원 우선순위 공식의 이론적 근거는 [`research_synthesis.md §2.5`](research_synthesis.md) 참조.

---

## 3. 실험 설계

### Phase 0: D_train 멀티차원 분포 프로파일링 [신규]

**입력**: 83k 캡션 텍스트 (EXP-001/002 코드 독립, bge-m3 재인코딩)  
**목적**: FAISS k-NN 단일 계산 위에 4개의 해석 레이어를 쌓아 D_train의 분포 구조를 전방위로 정량화  
**상태**: 🔲 미시작

> **설계 원칙**: 0-A의 k-NN 구조 하나에서 모든 분석이 파생된다. 중복 계산 없음.  
> 각 서브 실험이 이전 실험의 맹점을 채우는 체인 구조:  
> 0-A → "이웃 구조" → 0-B → "얼마나 중복됐나" → 0-C → "어떤 종류의 희소함인가(+LID 신뢰도+k-민감도)" → 0-D → "무엇을 해야 하나(6분류+경계 구역 정량화)" → **[조건부] 0-D-val → "Q3 결정 FLIPD 검증"** → 0-E-1 → "전체 의미 지도(83k, 분포 형태 포함)" → 0-E-2 → "갭 정밀 분석 및 수집 전략(판정 근거 명시)"
>
> **설계 전제 (외부 타당성 한계)**: Phase 0 전체는 캡션이 시각 데이터를 충실히 반영한다는 가정에 의존한다. 캡션 품질이 낮거나 시각-텍스트 불일치가 체계적으로 존재하면 LID·밀도·시나리오 분류가 왜곡될 수 있다. 첫 교차 검증 신호는 Phase B 파일럿 — 캡션 기반 클러스터와 실제 주행 성능 갭이 불일치하면 bge-m3 재인코딩 품질 또는 캡션 생성 파이프라인 점검 필요.  
>
> **v2 변경점 (유지)**: (1) LID 신뢰도 플래그(Q4) (2) 0-E를 0-E-1/0-E-2로 분리 (3) mean_lid 직접 사용  
> **v3 변경점 (유지)**: (1) 0-D: BIC K=1~3 + brentq 실제 교차점 임계값 (2) 0-E-1: TF-IDF KMeans — 임베딩과 독립 공간 (3) 0-E-1: per-scenario Vendi 200앵커 고정 (4) 0-E-2: COLLECT_HIGH_PRIORITY / GAP_RATIO_HIGH_PRIORITY 파라미터화  
> **v4 변경점 (유지)**:  
> (1) 0-A: `embeddings.npy` 저장 추가 — 0-B·0-E-1 독립 실행 지원  
> (2) 0-E-1: Q1×Vendi 피드백 → `caution_scenarios.json` 별도 출력 추가 (prune_flag 다운스트림 연결)  
> (3) 0-B: density(k=10) vs uniqueness(k=20) k 차이 명시  
> (4) 0-E-1: `VENDI_ANCHOR` 루프 외부로 이동, K=12 실루엣 검증 코드 추가  
> **v5 변경점 (유지)**:  
> (1) 0-B: `diversity_profile.json` 저장 누락 수정 (§7 산출물 목록과 불일치 해소)  
> (2) 0-D: `len(captions)` → `len(density_per_clip)` (독립 실행 시 NameError 수정)  
> (3) 0-E-2: JSON 로드 후 키 타입 str→int 변환 — `{int(kk): vv for kk, vv in ...}` (KeyError 수정)  
> (4) 0-E-1: `toarray()` 제거 + `best_models` dict로 검증 모델 재사용 (메모리 ~2GB 절약, KMeans 5회 재학습 제거)  
> (5) 0-B + 0-E-1: Vendi 앵커 선택에 `np.random.default_rng(42)` / `default_rng(42+k)` 시드 추가 (재현성)  
> **v6 변경점 (유지)**:  
> (1) 0-C: `lid_stats.json` 저장 누락 수정 — 0-B/0-D와 동일 패턴  
> (2) 0-D: `quadrant_profile.json` 저장 누락 수정 — 동일 패턴  
> (3) 0-B: `len(captions)` → `len(knn_sim)` 2곳 (독립 실행 NameError 해소)  
> (4) 0-E-1: `joblib.dump(tfidf_e1, ...)` 추가 + `healthy_scenarios.json` Q0 기준점 추출  
> (5) 0-E-2: `joblib.load` + `tfidf_e1.transform(captions)` 로 X_tfidf 재생성 — 독립 실행 지원 (기존 코멘트만 있던 구조 해소) + 미사용 변수 `gap_idx` 제거  
> **v7 변경점 (유지)**:  
> (1) 0-B: `density_quartile.npy` 저장 추가 — 0-D 이진 임계값의 분포 맥락 제공 (미사용 변수 → 저장)  
> (2) 0-C: `lid_quartile.npy` 저장 추가 — 동일 패턴  
> (3) 0-E-2: `collect_candidates` 필드 재설계 — `query_terms` 병합 → `scenario_context`+`gap_specifics` 분리 + `gap_count`·`mean_lid` 추가 (Phase D LLM 쿼리 생성 맥락 구조 보존)  
> **v8 변경점 (유지)**:  
> (1) 0-A: `os.makedirs('phase0', exist_ok=True)` 추가 — 첫 실행 시 FileNotFoundError 해소 (v1~v7 전 버전 잠재 버그)  
> (2) 0-E-2: `gap_slices[k]`에 `prune_flag` 필드 추가 — COLLECT·PRUNE 신호 공존 시 맥락 보존  
> (3) 0-E-2: `collect_candidates`에 `prune_flag` 전달 — Phase D에서 PRUNE 후보 내 갭 케이스 별도 처리 지원  
> (4) 0-E-2: `synthetic_candidates`에 `gap_count`·`mean_lid` 추가 — EXP-004 합성 생성 단일 파일 완결  
> **v9 변경점 (유지)**:  
> (1) 0-D: Q5 `PRUNE_UNCERTAIN` 추가 (고밀도+저LID 판정이지만 LID 불신뢰) — 신뢰도 없는 PRUNE 결정 방지  
> (2) 0-E-1: `density_quartile_dist`·`lid_quartile_dist` 시나리오 프로파일 추가 — mean만으로 숨겨지는 양극 분포 포착  
> (3) 0-E-1: `silhouette_scores.json` 저장 추가 — K 선택 근거 추적 가능  
> (4) 0-E-2: `uncertain_candidates` 상세 필드 추가 (top_terms, size, gap_count, quadrant_distribution) — 수동 검토 효율 향상  
> (5) 0-E-2: `collect_candidates` priority+mean_lid 기준 정렬 — Phase D 진입 순서 명확화  
> **v10 변경점 (유지)**:  
> (1) Phase 0 진입점 코드 블록 추가 — `captions` + `clip_ids` 로드 (v1 이래 구조적 공백 해소)  
> (2) 0-E-1 `prune_flag`: Q5_pct 합산 + `Q5_UNCERTAIN` 플래그 추가 — Q5 우세 시나리오 누락 방지  
> (3) 0-E-1 `caution_scenarios`: `Q5_UNCERTAIN` 포함 — 수동 검토 대상 완전 수집  
> (4) 0-E-1 `healthy_scenarios`: `MIN_HEALTHY_SIZE = 500` 조건 추가 — Phase B null hypothesis 통계 안정성  
> (5) 0-E-2 `gap_slices`: `gap_quadrant_composition`·`gap_q2_ratio` 추가 — COLLECT vs SYNTHETIC 판정 근거 명시  
> (6) 0-B·0-C 출력 명세 불일치 수정 — 저장 파일 목록과 코드 일치화  
> **v11 변경점 (유지)**:  
> (1) 0-D 목적 텍스트 "5가지" → "6가지" — 제목과 내용 일치화  
> (2) 0-E-1 `healthy_scenarios`: `MIN_Q0_PCT = 40` 조건 추가 — Q0 지배도 보장 (dominant만으로 부족)  
> (3) 0-E-1 `caution_scenarios`: `_caution_note()` 함수로 케이스 A/B 분리 — 수동 검토자 맥락 제공  
> (4) Phase 0 통합 산출물: 다운스트림 연결표 추가 — Phase 0 → Phase A~D 산출물 흐름 명시  
> **v12 변경점 (최신)**:  
> (1) 0-C: k-민감도 분석 추가 (`lid_k15/k25`, `k_sensitive_rate`, `flipd_recommended`) — "MLE로 충분" 주장의 실증 근거 확보  
> (2) 0-D: `lid_margin`·`lid_boundary_zone` 연산 추가 + `thresholds.json`에 `q3_boundary_rate` 저장 — 경계 구역 정량화  
> (3) 0-D-val: Targeted FLIPD 검증 서브 실험 추가 (조건부: `flipd_recommended=True` OR `q3_boundary_rate > 0.3`) — Q3 결정 신뢰도 FLIPD 보정

---

#### Phase 0 진입점: captions 로드

**모든 서브 실험 실행 전 1회 수행.** `captions`와 `clip_ids`는 0-A, 0-E-1, 0-E-2에서 공통으로 참조된다.

```python
import os, json
import numpy as np

CAPTIONS_DIR = '/Data1/home/bskang/cds-data/captions/'

captions = []
clip_ids = []
for fname in sorted(os.listdir(CAPTIONS_DIR)):
    if not fname.endswith('.jsonl'):
        continue
    with open(os.path.join(CAPTIONS_DIR, fname), encoding='utf-8') as f:
        for line in f:
            item = json.loads(line.strip())
            captions.append(item['caption'])
            clip_ids.append(item['clip_id'])

print(f"로드 완료: {len(captions)}개 캡션")
# clip_ids 저장 — 분석 결과(index) → 실제 클립 역추적 필수
os.makedirs('phase0', exist_ok=True)
np.save('phase0/clip_ids.npy', np.array(clip_ids, dtype=object))
```

> **파일 포맷 주의**: 위는 `.jsonl` 기준. 실제 포맷(csv/txt/parquet 등)에 따라 로드 코드 수정.  
> `clip_ids.npy`는 이후 모든 `.npy` 인덱스(quadrant_assignment, scenario_labels 등)의 역추적 키다.

---

#### Sub-exp 0-A: FAISS k-NN Foundation (계산 앵커)

**역할**: 이후 4개 서브 실험의 유일한 무거운 연산. k=50은 LID 추정 안정성을 위해 필요하다 (Ma et al. ICLR 2018: k ≥ 20 권장).

```python
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os

os.makedirs('phase0', exist_ok=True)   # 첫 실행 시 디렉토리 생성 — 하위 모든 서브 실험 저장 경로 보장

model = SentenceTransformer('BAAI/bge-m3')
embeddings = model.encode(captions, batch_size=256, normalize_embeddings=True)
embeddings_f32 = embeddings.astype(np.float32)

K = 50
index = faiss.IndexFlatIP(embeddings_f32.shape[1])
index.add(embeddings_f32)

sim_with_self, idx_with_self = index.search(embeddings_f32, K + 1)
knn_sim = sim_with_self[:, 1:]    # (N, 50) — cosine similarity (정규화 임베딩: IP = cosine)
knn_idx = idx_with_self[:, 1:]    # (N, 50)

np.savez('phase0/knn_foundation.npz', knn_sim=knn_sim, knn_idx=knn_idx)
# embeddings_f32 저장 — 0-B(Vendi) · 0-E-1(per-scenario Vendi)에서 독립 로드 필요
# 83k × 1024 float32 ≈ 325MB. 디스크 여유 확인 후 실행.
np.save('phase0/embeddings.npy', embeddings_f32)
```

**출력**: `knn_foundation.npz`, `embeddings.npy`  
**이후 서브 실험은 이 두 파일만 로드. 추가 임베딩 인코딩 없음.**

---

#### Sub-exp 0-B: Effective N + Vendi Score + 연속 밀도장

**목적**: D_train 독립 정보량을 두 가지 보완적 지표로 정량화

**왜 두 지표인가**: Effective N은 cosine sim > 0.95인 near-duplicate만 잡는다. 0.7~0.9 구간의 "유사하지만 다른" 클립들이 기여하는 부분 다양성은 포착하지 못한다. Vendi Score (Friedman & Dieng, TMLR 2023)는 전체 고유값 스펙트럼으로 이를 보완한다.

```python
import json

knn_sim = np.load('phase0/knn_foundation.npz')['knn_sim']
embeddings_f32 = np.load('phase0/embeddings.npy')    # Vendi Score 계산용 (0-A에서 저장)

# --- Effective N: SoftDedup(ACL 2024) 방향 — 이진 임계값 → 연속 soft weight ---
# k=20: "더 넓은 이웃 반경에서 얼마나 복제됐는가" → 중복성(uniqueness) 측정
# k=10 (local_density, 아래): "즉각적 이웃이 얼마나 빽빽한가" → 밀도 측정
# 두 k는 다른 개념을 측정하므로 의도적으로 다름; 0-D에서 각각 사용됨
soft_commonness = knn_sim[:, :20].mean(axis=1)       # 높을수록 고중복
uniqueness_weight = 1.0 - soft_commonness             # 낮을수록 독립적
uniqueness_weight = np.clip(uniqueness_weight, 0, 1)
effective_N = float(uniqueness_weight.sum())

# 비교용 hard 버전 (기존 방식, 0.95 임계값)
near_dup_hard = (knn_sim[:, :20] > 0.95).sum(axis=1)
uniqueness_hard = 1.0 / (1.0 + near_dup_hard.astype(float))
effective_N_hard = float(uniqueness_hard.sum())

# --- Vendi Score: Nyström 근사로 N²→ O(N·m) ---
# 전체 유사도 행렬 고유값 스펙트럼의 지수 엔트로피 → 실질 다양성 차원 수
m = 2000
rng = np.random.default_rng(42)
anchor_idx = rng.choice(len(embeddings_f32), m, replace=False)
anchors = embeddings_f32[anchor_idx]
K_mm = (anchors @ anchors.T).astype(np.float64)
eigenvalues = np.linalg.eigvalsh(K_mm)
eigenvalues = np.maximum(eigenvalues, 0)
ev_norm = eigenvalues / (eigenvalues.sum() + 1e-12)
vendi_score = float(np.exp(-np.sum(ev_norm * np.log(ev_norm + 1e-12))))
vendi_diversity_ratio = vendi_score / len(knn_sim)

# --- 연속 밀도장: k-NN 기반 (UMAP 왜곡 없는 원래 임베딩 공간 밀도) ---
# k=10: 즉각적 이웃 밀도 (uniqueness의 k=20보다 좁은 반경 — 0-D 분류 기준)
local_density = knn_sim[:, :10].mean(axis=1)         # 10-NN 평균 유사도
density_quartile = np.digitize(
    local_density,
    np.percentile(local_density, [25, 50, 75])
)  # 0=희소(하위25%), 3=조밀(상위25%)

result_B = {
    'effective_N_soft': effective_N,
    'effective_N_hard': effective_N_hard,
    'redundancy_ratio': 1 - effective_N / len(knn_sim),
    # grey_zone_contribution: SoftDedup이 HardDedup보다 독립으로 인정하는 추가 클립 기여량
    # = cosine sim 0.95 미만이지만 0.7~0.95 구간의 "부분 중복" 클립들의 soft uniqueness 합
    # 클 수록 D_train에 완전 중복은 아니지만 매우 유사한 클립이 많음
    # → Q1 프루닝 임계값 설정 시 이 값이 크면 보수적으로 접근할 것
    'grey_zone_contribution': round(effective_N - effective_N_hard, 1),
    'vendi_score': vendi_score,
    'vendi_diversity_ratio': vendi_diversity_ratio,
    'density_p10': float(np.percentile(local_density, 10)),
    'density_median': float(np.median(local_density)),
    'density_p75': float(np.percentile(local_density, 75)),
}
with open('phase0/diversity_profile.json', 'w') as f:
    json.dump(result_B, f, indent=2, ensure_ascii=False)
np.save('phase0/density_per_clip.npy', local_density)
np.save('phase0/density_quartile.npy', density_quartile)   # 4분위 등급 — 0-D 이진 임계값의 분포 맥락 제공
np.save('phase0/uniqueness_weight.npy', uniqueness_weight)  # 0-D에서 재사용
```

**Effective N vs Vendi Score 비교**:

| | Effective N (soft) | Vendi Score |
|---|---|---|
| 포착 범위 | 전 유사도 구간 (연속 가중치) | 전 유사도 스펙트럼 (고유값) |
| 0.7~0.9 유사 클립 기여 | 부분 반영 | 고유값에 정확히 반영 |
| 계산 복잡도 | O(N·k) FAISS | O(N·m) Nyström 근사 |
| 해석 | 중복 제거 후 독립 클립 수 | 정보 다양성의 유효 차원 수 |

**출력**: `diversity_profile.json`, `density_per_clip.npy`, `density_quartile.npy`, `uniqueness_weight.npy`  
**근거**: Friedman & Dieng (TMLR 2023) Vendi Score · Abbas et al. (ICLR 2023 Workshop) SemDeDup · Yao et al. (ACL 2024) SoftDedup · Sorscher et al. (NeurIPS 2022)

---

#### Sub-exp 0-C: Local Intrinsic Dimensionality (LID)

**목적**: 각 클립 주변에 "진짜 변화 방향이 몇 개 존재하는가"를 측정  
**맹점 해소**: 0-B는 "중복이 얼마나 많은가"를 알려주지만, 희소 지역이 "다양한 시나리오가 존재하지만 아직 수집 안 됐는가"인지 "본질적으로 단조로운 공간인가"인지 구분하지 못한다. LID가 이 차이를 측정한다.

LID가 높은 클립 → 주변에 다양한 방향의 변주 존재 → 탐색 시 다양한 클립 발견 가능  
LID가 낮은 클립 → 주변이 본질적으로 1~2차원 구조 → 더 수집해도 유사 클립만 늘어남

```python
import json

def compute_lid_mle(knn_sim, k_lid=20):
    """
    Ma et al. (ICLR 2018) MLE 추정량 — 극값 이론(Extreme Value Theory) 기반
    LID(x) = -[ (1/m) Σ_{j=1}^{m} log(r_j / r_m) ]^{-1}
    r_j = j번째 이웃까지의 거리 (코사인 거리 = 1 - cosine_sim, 정규화 임베딩)

    근거: NeurIPS 2025 "Less is More" (Ruppik et al.) — bge-m3 같은
    언어 모델 임베딩에서 LID가 일반화 능력과 직접 연결됨을 실증.
    캡션 임베딩 위 LID 계산의 해석적 타당성이 최신 연구로 확인됨.
    (NeurIPS 2024 Spotlight FLIPD는 이 공식의 확장이며 LID가 현재진행형
    연구임을 방증. 우리 케이스는 Ma et al. 원본 MLE 공식으로 충분.)
    """
    knn_dist = 1.0 - knn_sim[:, :k_lid]            # similarity → distance
    r_max = knn_dist[:, -1:] + 1e-10               # k번째(최원) 이웃 거리
    log_ratios = np.log(knn_dist / r_max + 1e-10)  # log(r_j/r_max) ≤ 0
    mean_log = log_ratios.mean(axis=1)
    lid = -1.0 / (mean_log + 1e-10)
    return np.clip(lid, 1.0, 200.0)

knn_sim = np.load('phase0/knn_foundation.npz')['knn_sim']
lid_per_clip = compute_lid_mle(knn_sim, k_lid=20)

lid_quartile = np.digitize(lid_per_clip, np.percentile(lid_per_clip, [25, 50, 75]))
lid_stats = {
    'mean': float(lid_per_clip.mean()),
    'median': float(np.median(lid_per_clip)),
    'p10': float(np.percentile(lid_per_clip, 10)),
    'p90': float(np.percentile(lid_per_clip, 90)),
}
np.save('phase0/lid_per_clip.npy', lid_per_clip)
np.save('phase0/lid_quartile.npy', lid_quartile)            # 4분위 등급 — 0-D 이진 임계값의 분포 맥락 제공

# LID 신뢰도 플래그: 20번째 이웃이 너무 멀면 log(r_j/r_max) 비율 분산 폭발
# 저밀도 영역에서 Q2/Q3 구분이 노이즈 기반이 될 수 있는 케이스를 명시
r_max_dist = 1.0 - knn_sim[:, 19]        # 20번째 이웃까지 코사인 거리
lid_reliable = r_max_dist < 0.6           # 0.6 이상 = 이웃이 너무 멀어 LID 불안정
lid_stats['lid_reliable_ratio'] = round(float(lid_reliable.mean()), 3)
np.save('phase0/lid_reliable.npy', lid_reliable)

# --- k-민감도 분석 (Tier 0): 추정기 안정성 정량화 — 0-D-val 실행 필요성 사전 판단 ---
# k 변동(15·20·25)에서 Q3 분류 후보가 Q2로 바뀌는 비율을 측정
# 원리: boundary effect는 k가 클수록 원거리 이웃까지 포함해 과소추정이 줄어듦
#       k=20 기준 저LID인데 k=15·25에서 고LID로 바뀌는 클립 = MLE에 민감한 케이스
# 전제: density_per_clip.npy (0-B 산출물) 존재
lid_k15 = compute_lid_mle(knn_sim, k_lid=15)
lid_k25 = compute_lid_mle(knn_sim, k_lid=25)
np.save('phase0/lid_k15.npy', lid_k15)
np.save('phase0/lid_k25.npy', lid_k25)

_density_0c       = np.load('phase0/density_per_clip.npy')
lid_approx_thresh = float(np.median(lid_per_clip))      # 0-D GMM 실행 전 중앙값 근사
den_approx_thresh = float(np.median(_density_0c))
low_d_approx      = _density_0c < den_approx_thresh     # 저밀도(Q2/Q3 후보) 근사 마스크

# k=20 기준 Q3 방향(저LID)인데 k=15 또는 k=25 기준으로 Q2(고LID)로 바뀌는 클립
flip_k15 = (lid_per_clip < lid_approx_thresh) & (lid_k15 >= lid_approx_thresh)
flip_k25 = (lid_per_clip < lid_approx_thresh) & (lid_k25 >= lid_approx_thresh)
flip_any  = (flip_k15 | flip_k25) & low_d_approx & lid_reliable
k_sensitive_rate  = float(flip_any.mean())

lid_stats['k_sensitive_rate']  = round(k_sensitive_rate, 4)
lid_stats['flipd_recommended'] = bool(k_sensitive_rate > 0.05)
lid_stats['k_sensitivity_note'] = (
    'k_sensitive_rate < 0.02 → MLE 충분 실증 완료, 0-D-val 생략 가능'
    if k_sensitive_rate < 0.02 else
    '0.02~0.05 구간 → 0-D-val 실행 후 q3_boundary_rate 확인 권고'
    if k_sensitive_rate < 0.05 else
    'k_sensitive_rate > 0.05 → 0-D-val FLIPD 실행 필요 (thresholds.json 참조)'
)
print(f"k-민감도: {k_sensitive_rate:.4f} → flipd_recommended={lid_stats['flipd_recommended']}")

with open('phase0/lid_stats.json', 'w') as f:
    json.dump(lid_stats, f, indent=2)
```

**LID 해석 (AV 캡션 맥락)**:

| LID 범위 | 의미 | 수집 전략 |
|---------|------|---------|
| LID > 10 | 복합 시나리오 교차점 (야간+우천+교차로 등 조합 다양) | 탐색 시 ROI 높음 |
| 3 < LID ≤ 10 | 단일 시나리오 변주 존재 | 제한적 탐색 가능 |
| LID ≤ 3 | 본질적으로 단조로운 공간 | 탐색 ROI 낮음 → 합성 고려 |

**출력**: `lid_per_clip.npy`, `lid_reliable.npy`, `lid_stats.json`, `lid_quartile.npy`, `lid_k15.npy`, `lid_k25.npy`  
**lid_reliable 기준**: r_max_dist < 0.6 — 20번째 이웃 거리가 0.6 초과하면 LID 추정 불안정으로 분류  
**k_sensitive_rate 해석**: < 0.02 → MLE 분류 안정(0-D-val 생략 가능) · 0.02~0.05 → q3_boundary_rate 추가 확인 · > 0.05 → 0-D-val FLIPD 실행  
**근거**: Ma et al. (ICLR 2018) MLE 추정량 · Ruppik et al. (NeurIPS 2025 "Less is More") · Cresswell et al. (NeurIPS 2024 Spotlight FLIPD)

---

#### Sub-exp 0-D: 6-분류 분포 액션 맵 (Density × LID × 신뢰도, 자연 임계값 기반)

**목적**: 0-B 밀도장과 0-C LID를 교차해 클립별 역할을 6가지로 분류 → 구체적 행동 지도 생성  
**임계값 설계**: BIC로 K=1~3 비교 후 최적 K를 선택. K≥2이면 두 모드 실제 교차점을 임계값으로 계산(brentq). K=1 최적(단봉 분포)이면 median으로 폴백 — 단봉 분포 자체가 "편향 없음" 진단이다. 구 `means_.mean()`은 두 성분 가중치가 비대칭이면 교차점과 어긋나므로 실제 교차점으로 대체.

```python
import json
from sklearn.mixture import GaussianMixture
from scipy import optimize

density_per_clip = np.load('phase0/density_per_clip.npy')
lid_per_clip = np.load('phase0/lid_per_clip.npy')
uniqueness_weight = np.load('phase0/uniqueness_weight.npy')
lid_reliable = np.load('phase0/lid_reliable.npy')

# BIC로 K=1~3 비교 → 최적 K 선택 → K≥2이면 두 모드 실제 교차점을 임계값으로 반환
# 구 means_.mean()은 가중치 비대칭 시 교차점과 어긋남 → brentq로 실제 교차점 계산
def gmm_threshold(data, max_k=3):
    """BIC 최적 K 선택 후 이진 임계값 반환.
    K=1: np.median 폴백(단봉 분포). K=2: 두 성분 교차점.
    K=3: BIC 개선 ≥ 3%이면 인접 성분 중 PDF 최솟값이 가장 낮은 쌍의 교차점,
    미달이면 K=2 폴백 (세 번째 성분 = 분포 꼬리 흡수, 이진 분리에 불필요)."""
    data_2d = data.reshape(-1, 1)
    gmms, bics = {}, {}
    for k in range(1, max_k + 1):
        g = GaussianMixture(n_components=k, random_state=42, n_init=5).fit(data_2d)
        bics[k] = g.bic(data_2d)
        gmms[k] = g
    best_k = min(bics, key=bics.get)
    if best_k == 1:               # 단봉 분포 → 임계값 의미 없음, median 폴백
        return float(np.median(data)), 1, bics

    # K=3 최적이어도 이진 임계값에는 "주요 분리선" 하나만 필요
    # BIC(K=3) - BIC(K=2) 개선이 3% 이상이면 K=3 첫 번째 밸리 사용
    # 3% 미만이면 K=2 폴백 — 세 번째 성분은 꼬리 흡수 역할로 판단
    use_k3 = (best_k == 3 and
              (bics[2] - bics[3]) / max(abs(bics[2]), 1.0) >= 0.03)
    if use_k3:
        g3 = gmms[3]
        means3   = g3.means_.flatten()
        stds3    = np.sqrt(g3.covariances_.flatten())
        weights3 = g3.weights_.flatten()
        idx3     = np.argsort(means3)
        best_thresh, best_pdf_min = None, np.inf
        for i in range(len(idx3) - 1):
            ma, sa, wa = means3[idx3[i]],   stds3[idx3[i]],   weights3[idx3[i]]
            mb, sb, wb = means3[idx3[i+1]], stds3[idx3[i+1]], weights3[idx3[i+1]]
            def _diff(x, ma=ma, sa=sa, wa=wa, mb=mb, sb=sb, wb=wb):
                return wa/sa*np.exp(-0.5*((x-ma)/sa)**2) - wb/sb*np.exp(-0.5*((x-mb)/sb)**2)
            def _sum(x, ma=ma, sa=sa, wa=wa, mb=mb, sb=sb, wb=wb):
                return wa/sa*np.exp(-0.5*((x-ma)/sa)**2) + wb/sb*np.exp(-0.5*((x-mb)/sb)**2)
            try:
                t = optimize.brentq(_diff, ma, mb)
                v = _sum(t)
                if v < best_pdf_min:
                    best_pdf_min, best_thresh = v, t
            except ValueError:
                pass
        if best_thresh is not None:
            return float(best_thresh), best_k, bics
        # 교차점 없음 → K=2 폴백

    g2 = gmms[2]                  # K=2 기준 주요 분리선 (K=3 BIC 미달·교차점 없음 폴백 포함)
    means   = g2.means_.flatten()
    stds    = np.sqrt(g2.covariances_.flatten())
    weights = g2.weights_.flatten()
    idx = np.argsort(means)
    m1, s1, w1 = means[idx[0]], stds[idx[0]], weights[idx[0]]
    m2, s2, w2 = means[idx[1]], stds[idx[1]], weights[idx[1]]
    def pdf_diff(x):
        p1 = w1 / s1 * np.exp(-0.5 * ((x - m1) / s1) ** 2)
        p2 = w2 / s2 * np.exp(-0.5 * ((x - m2) / s2) ** 2)
        return p1 - p2
    try:
        threshold = optimize.brentq(pdf_diff, m1, m2)
    except ValueError:            # 두 성분이 완전 분리 → 교차점 없음 → 폴백
        threshold = float(np.mean([m1, m2]))
    return float(threshold), best_k, bics

density_threshold, d_best_k, d_bics = gmm_threshold(density_per_clip)
lid_threshold,     l_best_k, l_bics = gmm_threshold(lid_per_clip)

# K=1 단봉 분포 경고 — median 이진 임계값은 분포 구조가 아닌 50:50 분할이므로 해석 주의
# LID K=1: Q2/Q3 구분이 임의적 → 0-E-2 COLLECT/SYNTHETIC 판정의 신뢰도 저하
# Density K=1: 편향 없는 균등 분포 가능성 → 고/저밀도 절대값보다 상대적 위치로 해석
if l_best_k == 1:
    print("[경고] LID 분포 단봉(K=1 최적) — Q2/Q3 구분이 median 기반 50:50 분할. "
          "LID가 연속적으로 퍼진 단일 분포이므로 '고LID vs 저LID' 이진 분리 자체가 약함. "
          "0-E-2 COLLECT/SYNTHETIC 결과 해석 시 lid_threshold_unimodal=True 확인 필요.")
if d_best_k == 1:
    print("[경고] 밀도 분포 단봉(K=1 최적) — 고/저밀도 분리 구조 없음. "
          "D_train이 상대적으로 균등 분포일 가능성. 절대 임계값보다 사분위 수준에서 판단 권고.")

high_d = density_per_clip >= density_threshold
high_l = lid_per_clip >= lid_threshold

quadrant = np.full(len(density_per_clip), -1, dtype=int)
quadrant[high_d & high_l]                          = 0   # KEEP
quadrant[high_d & ~high_l & lid_reliable]           = 1   # PRUNE (신뢰 LID 기반)
quadrant[high_d & ~high_l & ~lid_reliable]          = 5   # PRUNE_UNCERTAIN (고밀도+저LID이지만 LID 불신뢰 — 수동 검토)
quadrant[~high_d & high_l & lid_reliable]           = 2   # COLLECT (저밀도+고LID+신뢰)
quadrant[~high_d & ~high_l & lid_reliable]          = 3   # EVALUATE → 0-E-2 판단
quadrant[~high_d & ~lid_reliable]                   = 4   # LID_UNCERTAIN → 0-E-1 의미로만 판단

quadrant_profile = {}
for q in range(6):
    mask = quadrant == q
    quadrant_profile[q] = {
        'count': int(mask.sum()),
        'pct': round(float(mask.sum()) / len(density_per_clip) * 100, 1),
        'effective_n_contribution': float(uniqueness_weight[mask].sum()),
        'mean_density': float(density_per_clip[mask].mean()),
        'mean_lid': float(lid_per_clip[mask].mean()),
    }
np.save('phase0/quadrant_assignment.npy', quadrant)
with open('phase0/quadrant_profile.json', 'w') as f:
    json.dump({str(q): v for q, v in quadrant_profile.items()}, f, indent=2)

# Q4 이질성 진단: "경계 불신뢰" vs "완전 고립" 분리
# r_max_dist = 0.61(간신히 불신뢰)과 r_max_dist = 0.95(20번째 이웃도 멀리 고립)는
# 둘 다 Q4이지만 원인이 다름 — 후자는 임베딩 품질 문제나 레이블 오류 가능성
ISOLATION_THRESHOLD = 0.8   # 20번째 이웃 거리 > 0.8 = 사실상 임베딩 공간 고립
r_max_dist_all = 1.0 - knn_sim[:, 19]
q4_mask = quadrant == 4
q4_isolated_count = int((q4_mask & (r_max_dist_all > ISOLATION_THRESHOLD)).sum())
# q4_isolated_count > Q4 전체의 30%이면 bge-m3 임베딩 불균질 가능성 → 임베딩 품질 점검 권고
# (Q4+Q5 비율 5% 경고보다 정밀한 진단: 비율이 낮아도 고립이 집중되면 문제)

# 임계값 + GMM 검증 정보 저장 — 0-E-2에서 로드해 재사용
# best_k=1이면 단봉 분포(편향 없음), BIC 값 차이로 모드 분리 강도 확인 가능
with open('phase0/thresholds.json', 'w') as f:
    json.dump({
        'density_threshold': density_threshold, 'lid_threshold': lid_threshold,
        'density_gmm_best_k': d_best_k,         'lid_gmm_best_k': l_best_k,
        'density_bics': {str(k): round(v, 1) for k, v in d_bics.items()},
        'lid_bics':     {str(k): round(v, 1) for k, v in l_bics.items()},
        'lid_threshold_unimodal':     l_best_k == 1,  # True이면 Q2/Q3 구분이 median 50:50 분할 — 이진 분리 신뢰도 낮음
        'density_threshold_unimodal': d_best_k == 1,  # True이면 밀도 편향 구조 없음 — 절대값보다 상대 위치로 해석
        'q4_isolated_clip_count': q4_isolated_count,
        'q4_isolation_threshold': ISOLATION_THRESHOLD,
        # q4_isolated_clip_count / quadrant_profile[4]['count'] > 0.3 이면 임베딩 품질 점검 권고
    }, f, indent=2)

# --- lid_margin + 경계 구역 정량화 (Tier 1) — lid_threshold 확정 후 계산 ---
# lid_margin: 임계값 대비 정규화 거리 → Q2/Q3 결정의 신뢰 스펙트럼
# lid_boundary_zone: 임계값 ±15% 이내 저밀도+신뢰 클립 = FLIPD가 분류를 바꿀 수 있는 범위
lid_margin = (lid_per_clip - lid_threshold) / np.maximum(lid_threshold, 1.0)
BOUNDARY_MARGIN_LID = 0.15   # ±15%: 임계값 소폭 변동 시 Q2↔Q3 역전 가능 구간
lid_boundary_zone = (
    (np.abs(lid_margin) < BOUNDARY_MARGIN_LID) &
    lid_reliable & ~high_d    # 저밀도(Q2/Q3 후보) + 신뢰 LID 클립만 (Q4/Q5 제외)
)
np.save('phase0/lid_margin.npy', lid_margin)
np.save('phase0/lid_boundary_zone.npy', lid_boundary_zone)

# thresholds.json에 경계 구역 통계 추가 — 0-D-val 실행 여부 판단 기준
_thresh = json.load(open('phase0/thresholds.json'))
_q3_boundary = int(((quadrant == 3) & lid_boundary_zone).sum())
_q3_total    = int((quadrant == 3).sum())
_thresh.update({
    'q3_boundary_count': _q3_boundary,
    'q3_total_count':    _q3_total,
    'q3_boundary_rate':  round(_q3_boundary / max(_q3_total, 1), 4),
    # q3_boundary_rate > 0.3: Q3→SYNTHETIC 결정의 30%가 FLIPD 재검증 대상
    # lid_stats.json의 flipd_recommended와 합산해 0-D-val 실행 여부 결정
})
with open('phase0/thresholds.json', 'w') as f:
    json.dump(_thresh, f, indent=2)
print(f"경계 구역: Q3 {_q3_total}개 중 {_q3_boundary}개({_q3_boundary/max(_q3_total,1):.1%}) FLIPD 재검증 후보")

# --- k-민감도 GMM 임계값 기반 재계산 — 0-C 중앙값 근사 보정 ---
# 0-C에서 median(lid_per_clip)을 임시 임계값으로 사용했으나,
# 여기서 0-D가 확정한 GMM BIC 교차점 lid_threshold로 재계산하여 lid_stats.json 갱신
_lid_k15 = np.load('phase0/lid_k15.npy')
_lid_k25 = np.load('phase0/lid_k25.npy')
_low_d_gmm    = ~high_d                             # GMM 확정 밀도 기준 저밀도
flip_k15_gmm  = (lid_per_clip < lid_threshold) & (_lid_k15 >= lid_threshold)
flip_k25_gmm  = (lid_per_clip < lid_threshold) & (_lid_k25 >= lid_threshold)
flip_any_gmm  = (flip_k15_gmm | flip_k25_gmm) & _low_d_gmm & lid_reliable
k_sensitive_rate_gmm = float(flip_any_gmm.mean())
_lid_stats_upd = json.load(open('phase0/lid_stats.json'))
_lid_stats_upd['k_sensitive_rate_approx'] = _lid_stats_upd.get('k_sensitive_rate', None)
_lid_stats_upd['k_sensitive_rate']        = round(k_sensitive_rate_gmm, 4)
_lid_stats_upd['flipd_recommended']       = bool(k_sensitive_rate_gmm > 0.05)
_lid_stats_upd['k_sensitive_rate_source'] = 'GMM BIC 교차점 기반 (0-D 확정 임계값)'
with open('phase0/lid_stats.json', 'w') as f:
    json.dump(_lid_stats_upd, f, indent=2)
print(f"k-민감도 GMM 재계산: rate={k_sensitive_rate_gmm:.4f} "
      f"(중앙값 근사={_lid_stats_upd['k_sensitive_rate_approx']:.4f} → "
      f"GMM 확정={k_sensitive_rate_gmm:.4f}) flipd_recommended={_lid_stats_upd['flipd_recommended']}")
```

**5+1-분류 Action Map**:

| 사분면 | 밀도 | LID | LID 신뢰 | 의미 | 행동 | 근거 |
|--------|------|-----|---------|------|------|------|
| Q0 | 높음 | 높음 | — | 많고 다양함 | **유지** | — |
| Q1 | 높음 | 낮음 | 신뢰 | 많지만 단조로움 | **프루닝 후보** → 0-E-1에서 시나리오 확인 | Sorscher NeurIPS 2022 |
| Q2 | 낮음 | 높음 | 신뢰 | 적지만 다양성 잠재 높음 | **수집 최우선** | Ma et al. ICLR 2018 |
| Q3 | 낮음 | 낮음 | 신뢰 | 적고 단조로움 | **0-E-2에서 판정** | Sorscher NeurIPS 2022 |
| Q4 | 낮음 | — | 불신뢰 | LID 추정 불안정 | **0-E-1 의미로 판단** | [신규 v2] |
| Q5 | 높음 | 낮음 | 불신뢰 | 많지만 LID 불안정 | **PRUNE_UNCERTAIN → 수동 검토** | [신규 v9] |

**출력**: `quadrant_assignment.npy`, `quadrant_profile.json`, `thresholds.json`, `lid_margin.npy`, `lid_boundary_zone.npy`  
**Q4+Q5 비율이 5% 초과 시**: bge-m3 임베딩 품질 점검 권고 — 임베딩 공간이 고르지 않을 수 있음  
**Q5(PRUNE_UNCERTAIN) 처리**: LID 불신뢰이므로 PRUNE 확정 불가 — 0-E-1 prune_flag=CAUTION과 동일 경로로 수동 검토  
**임계값 해석**: density_threshold와 lid_threshold가 모두 중앙값 근방이면 분포가 균등함(편향 없음). 크게 벗어나면 실제 편향 구조가 있는 것.  
**q3_boundary_rate 해석**: `thresholds.json`에 저장 — > 0.3이면 0-D-val FLIPD 실행 권고 (Q3 SYNTHETIC 결정의 신뢰 구역 이탈 경고)

---

#### Sub-exp 0-D-val: Targeted FLIPD 검증 [조건부]

**실행 조건** (둘 중 하나 충족 시):
- `lid_stats.json` → `flipd_recommended = True` (`k_sensitive_rate > 0.05`)
- `thresholds.json` → `q3_boundary_rate > 0.3`

**목적**: Q3(SYNTHETIC 분류) 클립 중 LID 경계 구역에만 FLIPD를 적용해 Ma et al. MLE의 boundary effect 보정 — 전체 83k 재처리 없이 결정-민감 클립만 선별 검증

**배경**: Ma et al. MLE는 매니폴드 경계 근방에서 LID를 체계적으로 과소추정한다. 이 오류는 **Q3 ← (진짜 Q2)** 방향만 발생한다 — SYNTHETIC으로 잘못 분류된 클립이 실제로는 COLLECT 대상일 수 있다. 반대(Q2→Q3 오류)는 boundary effect로 발생하지 않으므로 Q3 결정이 리스크의 유일한 집중점이다.

> **`lid_reliable` 필터와의 관계**: 0-C의 r_max_dist < 0.6 필터가 가장 심한 경계 케이스(Q4/Q5)를 이미 걸러냄. 0-D-val은 필터를 통과한 "신뢰 LID이지만 임계값 근방" 클립에만 적용 — 잔여 boundary effect 보정이므로 계산 범위가 제한적.
>
> **독립 실행 필수 파일**: `phase0/lid_boundary_zone.npy` (0-D), `phase0/lid_stats.json` (0-C), `phase0/thresholds.json` (0-D), `phase0/knn_foundation.npz` (0-A). 0-D-val은 0-D 완료 후에만 실행 가능하다.

```python
import json, numpy as np

# --- 실행 조건 확인 ---
_lid_stats  = json.load(open('phase0/lid_stats.json'))
_thresholds = json.load(open('phase0/thresholds.json'))
flipd_needed = (
    _lid_stats.get('flipd_recommended', False) or
    _thresholds.get('q3_boundary_rate', 0.0) > 0.3
)
if not flipd_needed:
    print("0-D-val SKIP: k_sensitive_rate ≤ 0.05 and q3_boundary_rate ≤ 0.3 → MLE 분류 안정")
    # SKIP 시에도 감사 기록 — 다운스트림이 실행 여부를 flipd_applied 필드로 구분 가능
    with open('phase0/flipd_validation.json', 'w') as f:
        json.dump({
            'flipd_applied':    False,
            'skip_reason':      'k_sensitive_rate ≤ 0.05 and q3_boundary_rate ≤ 0.3',
            'k_sensitive_rate': _lid_stats.get('k_sensitive_rate', None),
            'q3_boundary_rate': _thresholds.get('q3_boundary_rate', None),
        }, f, indent=2)
else:
    print(f"0-D-val 실행: flipd_recommended={_lid_stats.get('flipd_recommended')}, "
          f"q3_boundary_rate={_thresholds.get('q3_boundary_rate', 0):.4f}")

    quadrant          = np.load('phase0/quadrant_assignment.npy')
    lid_boundary_zone = np.load('phase0/lid_boundary_zone.npy')
    knn_sim_all       = np.load('phase0/knn_foundation.npz')['knn_sim']  # (83k, 50) — 전체 공간
    lid_threshold     = _thresholds['lid_threshold']

    # FLIPD 적용 대상: Q3 + lid_boundary_zone (lid_reliable & 저밀도 & ±15% 이내)
    target_mask    = (quadrant == 3) & lid_boundary_zone
    target_indices = np.where(target_mask)[0]
    print(f"FLIPD 적용: {len(target_indices)}개 클립 "
          f"(전체 {len(target_indices)/len(quadrant):.1%}, Q3의 {len(target_indices)/max(int((quadrant==3).sum()),1):.1%})")

    # 원본 83k 공간의 kNN 거리 추출 (k=20) — 재계산 없음
    # 핵심: target 클립끼리만 kNN을 구성하면 전체 공간 맥락이 소실되어
    #       boundary effect가 측정되지 않음. 0-A knn_foundation이 이미 83k 전체 기준이므로
    #       해당 행만 슬라이싱하면 올바른 맥락에서 FLIPD 보정 가능.
    knn_dist_target = 1.0 - knn_sim_all[target_indices, :20]  # (|target|, 20), cosine distance

    def compute_flipd_lid(knn_dist, k=20):
        """
        FLIPD (Cresswell et al. NeurIPS 2024) — Poisson 과정 기반 경계 보정 LID
        boundary_correction = 1 + (2/k) Σ_j [ j · (r_j/r_k)^mle_lid ]
        경계 근방에서 보정항이 MLE의 과소추정을 위쪽으로 조정 (MLE ≤ FLIPD 항상 성립)
        입력: knn_dist — 원본 83k 공간에서 계산된 k-NN 거리 (N, k), 자기 자신 이미 제외
        """
        r     = knn_dist                    # (N, k)
        r_k   = r[:, -1:] + 1e-10          # (N, 1), k번째 이웃 거리
        log_r = np.log(r / r_k + 1e-10)
        mle   = np.clip(-1.0 / (log_r.mean(axis=1) + 1e-10), 1.0, 50.0)
        j_arr = np.arange(1, k+1, dtype=float)
        bc    = 1.0 + (2.0 / k) * np.sum(j_arr * (r / r_k) ** mle.reshape(-1, 1), axis=1)
        return np.clip(mle * bc, 1.0, 200.0), mle

    flipd_lid, mle_lid = compute_flipd_lid(knn_dist_target, k=20)

    upgraded_mask   = flipd_lid >= lid_threshold
    upgrade_rate    = float(upgraded_mask.mean())
    upgraded_global = target_indices[upgraded_mask]

    flipd_result = {
        'flipd_applied':           True,
        'knn_source':              'knn_foundation.npz — 83k 전체 공간 맥락 사용',
        'target_clip_count':       len(target_indices),
        'upgraded_count':          int(upgraded_mask.sum()),
        'upgrade_rate':            round(upgrade_rate, 4),
        'median_flipd_correction': round(float(np.median(flipd_lid - mle_lid)), 4),
        # upgrade_rate 해석:
        # < 0.05 → MLE 분류 실질 안정 — quadrant 변경 없음
        # 0.05~0.15 → 소규모 Q3→Q2 재분류 권고
        # > 0.15 → lid_threshold 하향 보정 검토 + 재분류 (systematic underestimation 심각)
        'recommended_action': (
            'quadrant 변경 없음 — MLE 분류 안정 확인' if upgrade_rate < 0.05 else
            'Q3→Q2 재분류 반영 권고'                  if upgrade_rate < 0.15 else
            'lid_threshold 하향 보정 검토 + Q3→Q2 재분류'
        ),
        'quadrant_updated': upgrade_rate >= 0.05,
    }

    if upgrade_rate >= 0.05:
        np.save('phase0/quadrant_assignment_pre_flipd.npy', quadrant.copy())  # 재현성 추적
        quadrant[upgraded_global] = 2
        np.save('phase0/quadrant_assignment.npy', quadrant)
        np.save('phase0/flipd_upgraded_clips.npy', upgraded_global)
        print(f"quadrant_assignment.npy 업데이트: {len(upgraded_global)}개 Q3→Q2")

    with open('phase0/flipd_validation.json', 'w') as f:
        json.dump(flipd_result, f, indent=2)
    print(f"FLIPD 결과: upgrade_rate={upgrade_rate:.3f} → {flipd_result['recommended_action']}")
```

**결정 흐름**:

```
0-C k_sensitive_rate  +  0-D q3_boundary_rate
    ├─ 둘 다 기준 미달 → 0-D-val SKIP → MLE 분류 그대로 0-E-1 진입
    └─ 하나라도 초과 → FLIPD 실행
            ├─ upgrade_rate < 0.05 → 변경 없음, MLE 신뢰 실증 완료
            ├─ 0.05~0.15 → Q3→Q2 재분류 반영 후 0-E-1
            └─ > 0.15 → lid_threshold 하향 보정 권고 + 재분류 + 0-D 재실행 고려
```

**출력** (실행 시): `flipd_validation.json`, `flipd_upgraded_clips.npy`, `quadrant_assignment_pre_flipd.npy` (upgrade_rate ≥ 0.05 시)  
**0-E-1/0-E-2 영향**: `quadrant_assignment.npy` 업데이트가 있으면 0-E-1/0-E-2가 재분류된 Q2 클립을 자동 반영  
**재현성**: `quadrant_assignment_pre_flipd.npy` — FLIPD 적용 전 원본 보존. 0-D-val 스킵 경로와 실행 경로의 quadrant를 구분 추적 가능  
**근거**: Cresswell et al. (NeurIPS 2024 Spotlight FLIPD) · Ma et al. (ICLR 2018) boundary effect 분석

---

#### Sub-exp 0-E-1: 전체 시나리오 의미 지도 (TF-IDF 공간, 83k 전체)

**목적**: 0-D(임베딩 공간 기하학)와 독립적인 TF-IDF 텍스트 공간에서 시나리오 클러스터링 → 기하학 × 의미 교차표 생성  
**핵심 변경 (v3)**: 임베딩 GMM → **TF-IDF KMeans** — 임베딩 공간(기하학)과 TF-IDF 공간(의미)은 같은 텍스트를 처리하지만 포착하는 구조가 다르다. 임베딩은 문장 전체 의미론적 유사도, TF-IDF는 특정 키워드 출현 패턴. 두 공간이 독립적 관점을 제공하므로 교차표에서 진정한 새 정보가 나온다.  
**추가 (v3)**: 시나리오별 Vendi Score 독립 측정 — Vendi는 비가산적(`VS(A∪B) ≠ VS(A)+VS(B)`)이므로 "글로벌 분해"가 아닌 각 시나리오 클립의 임베딩 공간 다양성을 독립 측정. 앵커 200개 고정으로 시나리오 간 비교 가능하게 표준화.  
**Phase A 관계**: 0-E-1(K=12)은 Phase A(K=6)의 세밀한 선행 분석. Phase A는 스케일링 파일럿 독립성 가정에 최적화된 K=6 클러스터를 별도로 수행하며, 0-E-1 시나리오 프로파일이 Phase A 클러스터 해석을 지원한다.

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, normalized_mutual_info_score, adjusted_rand_score
import json
import joblib

quadrant          = np.load('phase0/quadrant_assignment.npy')
uniqueness_weight = np.load('phase0/uniqueness_weight.npy')
density_per_clip  = np.load('phase0/density_per_clip.npy')
density_quartile  = np.load('phase0/density_quartile.npy')  # 0-B 저장 — 시나리오 내 분포 형태용
lid_per_clip      = np.load('phase0/lid_per_clip.npy')
lid_quartile      = np.load('phase0/lid_quartile.npy')      # 0-C 저장 — 시나리오 내 분포 형태용
lid_reliable      = np.load('phase0/lid_reliable.npy')
embeddings_f32    = np.load('phase0/embeddings.npy')        # per-scenario Vendi용 (0-A에서 저장)

# TF-IDF 공간 클러스터링 — 임베딩 공간(0-D)과 독립적 의미 분석
# sparse TF-IDF + KMeans: 고차원 저주 없음, 어휘 기반 시나리오 구분에 적합
tfidf_e1 = TfidfVectorizer(max_features=3000, ngram_range=(1, 2),
                            stop_words='english', min_df=3)
X_tfidf = tfidf_e1.fit_transform(captions)      # sparse (N, vocab)
feature_names = np.array(tfidf_e1.get_feature_names_out())

# K 실루엣 검증: K=6,8,10,12,15 비교 후 최적 K 선택 → 검증 모델 재사용
# (Phase A K=6은 독립성 가정 최적화용 — 0-E-1은 세밀 프로파일링 목적이므로 별도 검증)
# toarray() 제거: 83k×3000 dense → ~2GB 불필요. sparse 직접 사용.
best_models = {}
sil_scores = {}
for k_try in [6, 8, 10, 12, 15]:
    km_try = KMeans(n_clusters=k_try, random_state=42, n_init=10).fit(X_tfidf)
    sil_scores[k_try] = silhouette_score(X_tfidf, km_try.labels_,
                                          sample_size=5000, random_state=42)
    best_models[k_try] = km_try
SIL_FLAT_THRESHOLD = 0.02   # 최고-최저 실루엣 차이가 이 이하이면 "평탄"으로 판정
sil_range = max(sil_scores.values()) - min(sil_scores.values())
if sil_range < SIL_FLAT_THRESHOLD:
    K_scenario = 12          # 평탄하면 도메인 지식 우선 — 시나리오 과분할/과통합 방지
    flat_fallback = True
else:
    K_scenario = max(sil_scores, key=sil_scores.get)
    flat_fallback = False
print(f"실루엣 검증 결과: {sil_scores} → K_scenario={K_scenario} (flat_fallback={flat_fallback})")
with open('phase0/silhouette_scores.json', 'w') as f:
    json.dump({
        'scores': {str(k): round(v, 4) for k, v in sil_scores.items()},
        'K_selected': K_scenario,
        'sil_range': round(sil_range, 4),
        'flat_fallback': flat_fallback,
        'note': f'sil_range < {SIL_FLAT_THRESHOLD}이면 K=12 도메인 지식 폴백 (자동 적용됨)',
    }, f, indent=2)

kmeans_e1 = best_models[K_scenario]   # 검증 모델 재사용 — KMeans 재학습 없음
scenario_labels = kmeans_e1.labels_
np.save('phase0/scenario_labels.npy', scenario_labels)

VENDI_ANCHOR = 200   # 루프 외부 정의 — 시나리오 간 비교 가능하도록 앵커 수 고정

scenario_profiles = {}
for k in range(K_scenario):
    k_mask = scenario_labels == k
    total = int(k_mask.sum())

    # 사분면 분포: 이 TF-IDF 시나리오가 임베딩 기하학 사분면에서 어떻게 분포하는가
    # → 두 독립 공간의 교차 — 여기서 진정한 새 인사이트 발생 (Q5 포함 6분류)
    q_dist = {f'Q{q}': int((quadrant[k_mask] == q).sum()) for q in range(6)}
    q_pct  = {f'Q{q}_pct': round(q_dist[f'Q{q}'] / total * 100, 1) for q in range(6)}
    dominant_q = int(max(q_dist, key=q_dist.get).replace('Q', ''))

    # 시나리오 대표 어휘: KMeans 중심점 기반 (차분 TF-IDF 대비 해석 안정적)
    centroid = kmeans_e1.cluster_centers_[k]
    top_idx = centroid.argsort()[-12:][::-1]
    top_terms = list(feature_names[top_idx])

    # Effective N: 이 시나리오의 실질 독립 정보량
    eff_n = float(uniqueness_weight[k_mask].sum())

    # 시나리오별 Vendi Score: TF-IDF 시나리오 내 클립들의 임베딩 공간 다양성 독립 측정
    # Vendi 비가산적: 글로벌 값과 합산 불가 — 시나리오 간 상대 비교용
    k_emb = embeddings_f32[k_mask]
    n_k = len(k_emb)
    rng_vendi = np.random.default_rng(42 + k)   # 시나리오별 독립 시드
    vendi_anchor_used = min(n_k, VENDI_ANCHOR)   # 실제 사용 앵커 수 — 시나리오 크기 < VENDI_ANCHOR이면 앵커 축소
    anc_idx = rng_vendi.choice(n_k, vendi_anchor_used, replace=False)
    k_anchors = k_emb[anc_idx]
    K_kk = (k_anchors @ k_anchors.T).astype(np.float64)
    ev_k = np.maximum(np.linalg.eigvalsh(K_kk), 0)
    ev_k_norm = ev_k / (ev_k.sum() + 1e-12)
    vendi_k = float(np.exp(-np.sum(ev_k_norm * np.log(ev_k_norm + 1e-12))))

    # 분포 형태: density/LID의 평균만으로 숨겨지는 양극 vs 균일 구조 포착
    # density_quartile: 0=희소(하위25%), 3=조밀(상위25%)
    # lid_quartile: 양극화 여부 — 0+3 비율 높으면 mean LID 해석 주의 필요
    dq = density_quartile[k_mask]
    lq = lid_quartile[k_mask]

    scenario_profiles[k] = {
        'size': total,
        'top_terms': top_terms,
        'quadrant_distribution': {**q_dist, **q_pct},
        'dominant_quadrant': f'Q{dominant_q}',
        'effective_n': round(eff_n, 1),
        'global_redundancy_in_dtrain': round(1.0 - eff_n / total, 3),  # 전역 k-NN 기반 — 이 시나리오 내부 중복도가 아니라 D_train 전체 관점에서의 중복 기여율
        'mean_density': round(float(density_per_clip[k_mask].mean()), 4),
        'density_quartile_dist': {str(q): round(float((dq == q).mean()), 3) for q in range(4)},
        'mean_lid': round(float(lid_per_clip[k_mask].mean()), 2),
        'lid_quartile_dist': {str(q): round(float((lq == q).mean()), 3) for q in range(4)},
        'lid_reliable_ratio': round(float(lid_reliable[k_mask].mean()), 3),
        'vendi_score': round(vendi_k, 1),
        'vendi_anchor_used': vendi_anchor_used,          # 실제 사용 앵커 수
        'vendi_reliable': vendi_anchor_used >= VENDI_ANCHOR,  # False이면 타 시나리오와 직접 비교 주의
    }

# 프루닝 신호 플래그: Q1(신뢰 기반 단조) + Q5(불신뢰 기반 단조) 합산
# prune_flag 종류:
#   CAUTION      — Q1+Q5 우세이고 Vendi 높음 → LID/Vendi 불일치, 수동 검토 필수
#   Q5_UNCERTAIN — Q5 비율 높음 → LID 자체가 불신뢰, PRUNE 확정 불가, 수동 검토 필수
#   OK           — Q1 우세 + Vendi 낮음 → 표준 프루닝 후보 (두 신호 일치)
#   None         — 프루닝 신호 없음

# Q5 임계값: 전역 Q5 비율(0-D 산출물) 대비 2배 집중 OR 절대값 15% 중 큰 값
# 전역 Q5가 5%이면 시나리오 Q5 10%만 돼도 2배 집중 → 절대값 15%보다 민감하게 반응
# 전역 Q5가 20%이면 30%가 돼야 플래그 — 데이터 전체가 Q5 많은 환경에서 과검출 방지
_q_profile = json.load(open('phase0/quadrant_profile.json'))
global_q5_pct = _q_profile['5']['pct']
Q5_CONCENTRATION_THRESHOLD = max(15.0, 2.0 * global_q5_pct)

# prune_dominant 임계값: 전역 Q1+Q5 기준선 반영
# 고정 40%는 전역 비율이 높을 때 과검출, 낮을 때 과소검출 문제 발생
# → 전역 대비 1.5배 초과 OR 절대값 40% 중 큰 값으로 상대화
# 전역 Q1+Q5=10%: max(40, 15)=40% (4배 집중) · 전역 30%: max(40, 45)=45% (1.5배)
# 전역 50%: max(40, 75)=75% — 전체가 Q1+Q5 환경에서 일반 시나리오를 과검출하지 않음
global_q1_pct = _q_profile['1']['pct']
global_prune_pct = global_q1_pct + global_q5_pct
PRUNE_DOMINANT_THRESHOLD = max(40.0, 1.5 * global_prune_pct)

median_vendi = float(np.median([scenario_profiles[k]['vendi_score'] for k in range(K_scenario)]))
for k in range(K_scenario):
    prof = scenario_profiles[k]
    q1_pct = prof['quadrant_distribution']['Q1_pct']
    q5_pct = prof['quadrant_distribution']['Q5_pct']
    prune_signal_pct = q1_pct + q5_pct   # Q1(단조·신뢰) + Q5(단조·불신뢰) 합산
    is_prune_dominant = prune_signal_pct > PRUNE_DOMINANT_THRESHOLD

    if is_prune_dominant and q5_pct > Q5_CONCENTRATION_THRESHOLD and prof['vendi_score'] > median_vendi:
        # Q5 비율 집중 + Vendi도 높음 → LID 불신뢰 + 다양성 불일치 이중 불확실성
        prof['prune_flag'] = 'CAUTION'
    elif is_prune_dominant and q5_pct > Q5_CONCENTRATION_THRESHOLD:
        # Q5 비율 집중 → LID 불신뢰 기반 단조 판정 → PRUNE 확정 불가
        prof['prune_flag'] = 'Q5_UNCERTAIN'
    elif is_prune_dominant and prof['vendi_score'] > median_vendi:
        # Q1 우세이지만 Vendi 높음 → 임베딩 기하학(단조) vs 내부 다양성 불일치
        prof['prune_flag'] = 'CAUTION'
    elif is_prune_dominant:
        # Q1 우세 + Vendi 낮음 → 두 신호 모두 "단조" → 표준 프루닝 후보
        prof['prune_flag'] = 'OK'
    else:
        prof['prune_flag'] = None

with open('phase0/scenario_profiles.json', 'w') as f:
    json.dump(scenario_profiles, f, indent=2, ensure_ascii=False)

# 수동 검토 필요 시나리오 추출: CAUTION + Q5_UNCERTAIN 모두 포함
# Phase B/C 프루닝 결정 시 이 파일을 먼저 확인 — 자동 프루닝 금지
_PRUNE_REVIEW_FLAGS = ('CAUTION', 'Q5_UNCERTAIN')

def _caution_note(prof):
    flag = prof['prune_flag']
    q5   = prof['quadrant_distribution']['Q5_pct']
    if flag == 'Q5_UNCERTAIN':
        return 'Q5 비율 집중 — LID 불신뢰로 단조 판정 불확실. PRUNE 확정 불가. 수동 검토 필요.'
    if flag == 'CAUTION' and q5 > Q5_CONCENTRATION_THRESHOLD:
        return 'Q5 비율 집중 + Vendi 높음 — LID 불신뢰 + 다양성 불일치 이중 불확실성. 반드시 수동 검토.'
    return 'Q1 우세이지만 Vendi 높음 — 임베딩 단조 vs 내부 다양성 불일치. 프루닝 전 수동 검토.'

caution_scenarios = [
    {
        'scenario_id': k,
        'scenario_terms': scenario_profiles[k]['top_terms'],
        'q1_pct': scenario_profiles[k]['quadrant_distribution']['Q1_pct'],
        'q5_pct': scenario_profiles[k]['quadrant_distribution']['Q5_pct'],
        'vendi_score': scenario_profiles[k]['vendi_score'],
        'size': scenario_profiles[k]['size'],
        'prune_flag': scenario_profiles[k]['prune_flag'],
        'note': _caution_note(scenario_profiles[k]),
    }
    for k in range(K_scenario)
    if scenario_profiles[k]['prune_flag'] in _PRUNE_REVIEW_FLAGS
]
with open('phase0/caution_scenarios.json', 'w') as f:
    json.dump(caution_scenarios, f, indent=2, ensure_ascii=False)

# Q0 우세 + 충분 크기 + Q0 지배도 조건 → Phase B null hypothesis (기준 클러스터)
# MIN_HEALTHY_SIZE : Phase B 파일럿 최대 포인트(n=400)보다 충분히 커야 피팅 안정
# MIN_Q0_PCT      : dominant이어도 Q0=28%면 기준점으로 약함 — 40% 이상 요구
MIN_HEALTHY_SIZE = 500
MIN_Q0_PCT       = 40
healthy_scenarios = [
    {
        'scenario_id': k,
        'scenario_terms': scenario_profiles[k]['top_terms'],
        'q0_pct': scenario_profiles[k]['quadrant_distribution']['Q0_pct'],
        'q2_pct': scenario_profiles[k]['quadrant_distribution']['Q2_pct'],  # 건강 시나리오 내 수집 가능 갭 비율
        'vendi_score': scenario_profiles[k]['vendi_score'],
        'effective_n': scenario_profiles[k]['effective_n'],
        'size': scenario_profiles[k]['size'],
    }
    for k in range(K_scenario)
    if scenario_profiles[k]['dominant_quadrant'] == 'Q0'
    and scenario_profiles[k]['quadrant_distribution']['Q0_pct'] >= MIN_Q0_PCT
    and scenario_profiles[k]['size'] >= MIN_HEALTHY_SIZE
]
with open('phase0/healthy_scenarios.json', 'w') as f:
    json.dump(healthy_scenarios, f, indent=2, ensure_ascii=False)

# tfidf_vectorizer 저장 — 0-E-2 독립 실행 지원 (X_tfidf 재생성 가능)
joblib.dump(tfidf_e1, 'phase0/tfidf_vectorizer.joblib')

# 시나리오 간 Vendi 분산 집계
# "전역 Vendi가 높다"는 것이 "모든 시나리오가 고르게 다양한가" vs "특정 시나리오에 다양성이 집중되는가"를 구분 불가
# → Gini 계수와 CV로 다양성 불균등도를 단일 지표로 요약
vendi_arr = np.array([scenario_profiles[k]['vendi_score'] for k in range(K_scenario)])
vendi_mean = float(vendi_arr.mean())
vendi_std  = float(vendi_arr.std())
sorted_v = np.sort(vendi_arr)
n_s = len(sorted_v)
gini_vendi = float((2 * np.sum(np.arange(1, n_s + 1) * sorted_v)) / (n_s * sorted_v.sum()) - (n_s + 1) / n_s)
# TF-IDF 시나리오 레이블 vs 임베딩 사분면 독립성 검증 (NMI/ARI)
# 두 공간이 독립적이어야 교차표에서 진정한 새 정보가 발생한다는 설계 전제를 실증
# NMI > 0.15 또는 ARI > 0.1 이면 두 공간이 강하게 공유 구조 → 교차표 신규 정보량 제한적
nmi_scenario_quadrant = float(normalized_mutual_info_score(scenario_labels, quadrant))
ari_scenario_quadrant = float(adjusted_rand_score(scenario_labels, quadrant))

scenario_diversity_summary = {
    'vendi_mean': round(vendi_mean, 1),
    'vendi_std':  round(vendi_std, 1),
    'vendi_cv':   round(vendi_std / (vendi_mean + 1e-6), 3),   # 변동계수 — 규모 독립적 불균등도
    'vendi_gini': round(max(gini_vendi, 0.0), 3),               # 0=균등, 1=극단 집중
    'vendi_max_scenario': int(np.argmax(vendi_arr)),
    'vendi_min_scenario': int(np.argmin(vendi_arr)),
    # vendi_unreliable_count: 앵커 축소로 인해 타 시나리오와 직접 비교가 불가능한 시나리오 수
    # vendi_min_scenario가 unreliable이면 "다양성 최소" 해석을 신뢰하지 말 것
    'vendi_unreliable_count': int(sum(
        1 for k in range(K_scenario)
        if not scenario_profiles[k]['vendi_reliable']
    )),
    'nmi_scenario_vs_quadrant': round(nmi_scenario_quadrant, 4),  # TF-IDF 시나리오 ↔ 임베딩 사분면 공유 정보량
    'ari_scenario_vs_quadrant': round(ari_scenario_quadrant, 4),  # 우연 보정 일치도
    'two_space_independence_ok': nmi_scenario_quadrant < 0.15 and ari_scenario_quadrant < 0.1,
    # False이면 두 공간이 강하게 공유 구조 — 교차표 신규 정보량 제한적, 설계 전제 재검토 필요
    'note': (
        'vendi_cv > 0.5 또는 vendi_gini > 0.3이면 다양성이 특정 시나리오에 집중 → '
        '수집 우선순위 설계 시 저Vendi 시나리오(vendi_min_scenario)를 별도 확인. '
        'vendi_unreliable_count > 0이면 min/max 시나리오가 소규모(앵커 축소)일 수 있음 — scenario_profiles의 vendi_reliable 확인. '
        'two_space_independence_ok=False이면 TF-IDF 시나리오와 임베딩 사분면이 강하게 공유 구조 — 교차표 설계 전제 재검토.'
    ),
}
with open('phase0/scenario_diversity_summary.json', 'w') as f:
    json.dump(scenario_diversity_summary, f, indent=2, ensure_ascii=False)
print(f"시나리오 Vendi CV={scenario_diversity_summary['vendi_cv']:.3f}, Gini={scenario_diversity_summary['vendi_gini']:.3f}, unreliable={scenario_diversity_summary['vendi_unreliable_count']}")

# 임계값 민감 시나리오: mean_density 또는 mean_lid가 전역 임계값 ±5% 이내
# 0-D 임계값이 조금만 달라져도 이 시나리오들의 사분면 구성이 역전될 수 있음
# → 0-D ↔ 0-E-1 피드백 루프 역할: 임계값 적절성 검증에 활용
_thresholds = json.load(open('phase0/thresholds.json'))
_d_thresh = _thresholds['density_threshold']
_l_thresh = _thresholds['lid_threshold']
BOUNDARY_MARGIN = 0.05   # ±5%: 이 구간 내 mean은 임계값 변동에 민감

boundary_sensitive = [
    {'scenario_id': k,
     'scenario_terms': scenario_profiles[k]['top_terms'][:5],
     'mean_density': scenario_profiles[k]['mean_density'],
     'mean_lid': scenario_profiles[k]['mean_lid'],
     'density_near_threshold': abs(scenario_profiles[k]['mean_density'] - _d_thresh) < BOUNDARY_MARGIN,
     'lid_near_threshold': abs(scenario_profiles[k]['mean_lid'] - _l_thresh) < BOUNDARY_MARGIN,
     'note': '임계값 ±5% 이내 — density/lid_threshold 소폭 변동 시 action이 역전될 수 있음. 임계값 보정 후 재확인 권고.'}
    for k in range(K_scenario)
    if (abs(scenario_profiles[k]['mean_density'] - _d_thresh) < BOUNDARY_MARGIN or
        abs(scenario_profiles[k]['mean_lid'] - _l_thresh) < BOUNDARY_MARGIN)
]
with open('phase0/boundary_sensitive_scenarios.json', 'w') as f:
    json.dump(boundary_sensitive, f, indent=2, ensure_ascii=False)
print(f"임계값 민감 시나리오: {len(boundary_sensitive)}개")
```

**0-E-1 핵심 산출물 — 시나리오(TF-IDF) × 사분면(임베딩) 교차표**:

```
시나리오 | 대표 키워드                   | 크기  | Q0%  | Q1%  | Q2%  | Q5%  | gap%  | Eff.N | Vendi | prune_flag   | 판단
--------|------------------------------|------|------|------|------|------|-------|-------|-------|--------------|------
S0      | highway straight clear day   | 9100 | 38%  | 51%  | 5%   | 0%   | 10%   | 2800  | 68    | OK           | ⚠ Q1 우세+저Vendi → 표준 프루닝 후보
S3      | urban intersection complex   | 2100 | 22%  | 44%  | 18%  | 0%   | 29%   | 1600  | 195   | CAUTION      | ⚠ Q1+고Vendi → 두 트랙 불일치, 수동 검토
S4      | parking lot low speed urban  | 1800 | 15%  | 18%  | 10%  | 25%  | 21%   | 900   | 80    | Q5_UNCERTAIN | ⚠ Q5 우세 → LID 불신뢰, PRUNE 확정 불가
S1      | rainy night intersection     | 1200 | 18%  | 8%   | 52%  | 2%   | 60%   | 780   | 95    | None         | ✓ 갭+고다양 → 수집 1순위
S2      | fog low visibility highway   | 640  | 12%  | 4%   | 28%  | 1%   | 37%   | 510   | 35    | None         | △ 갭+저다양 → 합성 고려
...
```
> `gap%` = Q2+Q3+Q4 합산 비율. 시나리오 전체에서 저밀도 갭이 차지하는 비중을 한눈에 파악 → gap_ratio 임계값(0.4) 보정 참고값.

**density_quartile_dist / lid_quartile_dist 해석 예시**:
- `density_quartile_dist: {"0": 0.65, "1": 0.20, "2": 0.10, "3": 0.05}` → 65%가 글로벌 밀도 하위 25% — 이 시나리오는 D_train 전체에서 희소 지역에 집중됨
- `lid_quartile_dist: {"0": 0.45, "1": 0.08, "2": 0.07, "3": 0.40}` → 0+3 합계 85%, 양극 분포 — mean_lid=5.0이어도 실제론 LID≈1 클립 45% + LID≈15 클립 40%로 구성됨. COLLECT와 SYNTHETIC이 혼재하는 시나리오 신호.

`prune_flag=CAUTION`: Q1+Q5 우세이지만 Vendi가 시나리오 중앙값 이상 — LID는 단조를 가리키지만 임베딩 다양성이 높은 불일치 케이스. 자동 프루닝 금지, 수동 검토 필요.  
`prune_flag=Q5_UNCERTAIN`: Q5(고밀도+LID 불신뢰) 비율 높음 — PRUNE이 맞는지 판단 불가. 수동 검토 필요.

**출력**: `scenario_labels.npy`, `scenario_profiles.json`, `silhouette_scores.json`, `caution_scenarios.json`, `healthy_scenarios.json`, `tfidf_vectorizer.joblib`  
**근거**: Eyuboglu et al. (ICLR 2022 Domino) 의미 슬라이스 철학 · TF-IDF 공간의 독립성 — Phase A(K=6, 스케일링용)와 상보적 역할

---

#### Sub-exp 0-E-2: 저밀도 갭 슬라이스 정밀 분석

**목적**: Q2+Q3+Q4 저밀도 클립을 0-E-1 시나리오 단위로 그룹화 → 수집 전략 결정  
**핵심 변경**: Q2 비율(0-D 정보 반복) → **mean_lid 직접 사용**으로 순환성 제거  
**0-E-2가 해결하는 문제**: 0-E-1이 시나리오를 식별했지만 "그 시나리오 안에서 어떤 클립이 갭인가"의 세부 분석은 0-E-2가 담당

```python
import json
import numpy as np
import joblib

# 파일 기반 로드 (0-E-1과 동일 세션이면 이미 메모리에 있으므로 생략 가능)
quadrant          = np.load('phase0/quadrant_assignment.npy')
lid_per_clip      = np.load('phase0/lid_per_clip.npy')
lid_reliable      = np.load('phase0/lid_reliable.npy')
uniqueness_weight = np.load('phase0/uniqueness_weight.npy')   # q2_effective_n 계산용 (0-B 저장)
scenario_labels   = np.load('phase0/scenario_labels.npy')
scenario_profiles_raw = json.load(open('phase0/scenario_profiles.json'))
scenario_profiles = {int(kk): vv for kk, vv in scenario_profiles_raw.items()}  # str→int 키 변환
K_scenario = len(scenario_profiles)

# captions: 동일 세션이면 메모리에 있음. 독립 실행 시 진입점과 동일 패턴으로 재로드.
if 'captions' not in dir():
    import os
    CAPTIONS_DIR = '/Data1/home/bskang/cds-data/captions/'
    captions = []
    for fname in sorted(os.listdir(CAPTIONS_DIR)):
        if not fname.endswith('.jsonl'):
            continue
        with open(os.path.join(CAPTIONS_DIR, fname), encoding='utf-8') as _f:
            for line in _f:
                captions.append(json.loads(line.strip())['caption'])
    print(f"[0-E-2 독립 실행] captions 재로드: {len(captions)}개")

# X_tfidf + feature_names: 0-E-1이 저장한 vectorizer로 재생성
tfidf_e1 = joblib.load('phase0/tfidf_vectorizer.joblib')
X_tfidf = tfidf_e1.transform(captions)
feature_names = np.array(tfidf_e1.get_feature_names_out())

thresholds = json.load(open('phase0/thresholds.json'))
lid_threshold = thresholds['lid_threshold']     # 0-D BIC GMM 교차점 임계값

# 0-E-1 boundary_sensitive 정보 로드 — gap_slices에 플래그로 전달
# Phase D에서 COLLECT/SYNTHETIC 판정이 임계값 민감인 시나리오를 수동 조인 없이 즉시 식별
_boundary_raw = json.load(open('phase0/boundary_sensitive_scenarios.json'))
_boundary_ids = {b['scenario_id'] for b in _boundary_raw}

GAP_RATIO_HIGH_PRIORITY = 0.4   # 캘리브레이션 파라미터 — 실험 후 gap_in_scenario_ratio 분포 보고 조정
MIN_GAP_SIZE = 50               # 통계 안정성 최소 기준 — LID MLE는 k=20 이웃 거리의 로그 비율로 추정되므로
                                # 클립 수가 작을수록 mean_lid 분산이 커진다. 30개는 분산 폭발을 막는 최솟값이지만
                                # 안정적인 mean_lid 추정을 위해서는 50개 이상이 필요. (30→50 상향)
                                # gap_q2_ratio, mean_lid, collect_confidence 모두 이 임계값 이하에서 신뢰 불가

gap_mask = np.isin(quadrant, [2, 3, 4])   # Q2+Q3+Q4 전체 저밀도

gap_slices = {}
for k in range(K_scenario):
    k_gap_mask = gap_mask & (scenario_labels == k)
    if k_gap_mask.sum() < MIN_GAP_SIZE:
        continue

    total_in_scenario = int((scenario_labels == k).sum())
    gap_in_scenario_ratio = float(k_gap_mask.sum() / total_in_scenario)
    mean_lid_gap = float(lid_per_clip[k_gap_mask].mean())
    lid_rel_ratio = float(lid_reliable[k_gap_mask].mean())

    # 수집 전략 결정 (v3): mean_lid + gap_in_scenario_ratio 결합
    if lid_rel_ratio < 0.4:
        # Q4 클립 다수 → LID 불신뢰 → 0-E-1 시나리오 프로파일로 수동 판단
        action = 'UNCERTAIN_CHECK_SEMANTIC'
    elif mean_lid_gap >= lid_threshold:
        # gap_in_scenario_ratio: 이 시나리오 내 저밀도 클립 비율
        # > 0.4: 시나리오 자체가 D_train에서 갭 → 대규모 탐색 필요
        # ≤ 0.4: 시나리오 일부만 저밀도 → 보완적 탐색으로 충분
        action = 'COLLECT_HIGH_PRIORITY' if gap_in_scenario_ratio > GAP_RATIO_HIGH_PRIORITY else 'COLLECT'
    else:
        action = 'SYNTHETIC_OR_ACCEPT'

    # 갭 클립 내 Q2/Q3/Q4 구성비 — COLLECT vs SYNTHETIC 판정 근거 명시
    # mean_lid는 Q2(고LID)+Q3(저LID) 혼합 평균 → 비율 정보 없으면 판정 근거 불투명
    gap_quadrant_counts = {f'Q{q}': int((quadrant[k_gap_mask] == q).sum()) for q in [2, 3, 4]}
    gap_q2_ratio = gap_quadrant_counts['Q2'] / max(int(k_gap_mask.sum()), 1)
    # gap_q2_ratio 높을수록 COLLECT 신뢰도 높음; 낮을수록 SYNTHETIC/UNCERTAIN 고려

    # 갭 클립 특이 어휘: 이 시나리오 전체 대비 저밀도 클립에서 두드러지는 어휘
    # (동일 TF-IDF 공간 내 차분 — 0-E-1 재사용)
    cluster_gap_tfidf = X_tfidf[k_gap_mask].mean(axis=0).A1
    cluster_all_tfidf = X_tfidf[scenario_labels == k].mean(axis=0).A1
    diff_idx = (cluster_gap_tfidf - cluster_all_tfidf).argsort()[-8:][::-1]
    gap_specific_terms = list(feature_names[diff_idx])

    # Q2 클립들의 effective_n 기여량 — "이 갭을 수집하면 Effective N이 얼마나 느는가"의 추정치
    # uniqueness_weight는 전역 k-NN 기반이므로 D_train 전체 관점에서의 독립 정보량
    q2_mask_k = (scenario_labels == k) & (quadrant == 2)
    q2_effective_n = float(uniqueness_weight[q2_mask_k].sum())

    scenario_mean_lid = scenario_profiles[k]['mean_lid']
    # lid_context_caution: 갭 클립 mean_lid는 임계값 이상(COLLECT 판정)이지만
    # 시나리오 전체 mean_lid는 임계값 미만 — 갭 외 클립이 LID를 끌어내리는 구조
    # COLLECT 판정이 갭 내 소수 고LID 클립에 의존하는 경우 Phase D 진입 전 수동 확인 권고
    lid_context_caution = bool(
        scenario_mean_lid < lid_threshold and mean_lid_gap >= lid_threshold
    )

    gap_slices[k] = {
        'scenario_id': k,
        'scenario_terms': scenario_profiles[k]['top_terms'],
        'gap_specific_terms': gap_specific_terms,
        'gap_count': int(k_gap_mask.sum()),
        'gap_in_scenario_ratio': round(gap_in_scenario_ratio, 3),
        'gap_quadrant_composition': gap_quadrant_counts,  # Q2/Q3/Q4 구성비 — 판정 근거 추적
        'gap_q2_ratio': round(gap_q2_ratio, 3),           # 높을수록 COLLECT 신뢰도 높음
        'q2_effective_n': round(q2_effective_n, 1),       # 현재 Q2 클립들의 독립 정보량 (D_pool 수집 후 실제 증가량은 Phase D에서 측정)
        'mean_lid': round(mean_lid_gap, 2),
        'scenario_mean_lid': round(scenario_mean_lid, 2),  # 시나리오 전체 평균 LID — 갭 클립 맥락 해석용
        'lid_context_caution': lid_context_caution,        # True이면 갭만 COLLECT 기준 충족, 시나리오 전체는 저LID — 소수 고LID 클립에 의존
        'lid_reliable_ratio': round(lid_rel_ratio, 3),
        'action': action,
        'prune_flag': scenario_profiles[k].get('prune_flag'),
        # prune_flag='OK'/'CAUTION' + action='COLLECT' 공존 가능 — 시나리오 전체는 과잉이지만 일부 갭 존재
        'boundary_sensitive': k in _boundary_ids,
        # True이면 mean_density/mean_lid가 전역 임계값 ±5% 이내 → action 역전 가능성
        # Phase D 진입 전 0-D 임계값 보정 검토 권고 (boundary_sensitive_scenarios.json 참조)
    }

# 스킵된 시나리오 기록 — gap_count > 0이지만 MIN_GAP_SIZE 미달로 분석 제외된 케이스
# 희귀 시나리오(작은 k 클러스터)가 통계 불안정을 이유로 조용히 누락되는 것을 방지
skipped_gaps = [
    {'scenario_id': k,
     'gap_count': int((gap_mask & (scenario_labels == k)).sum()),
     'scenario_size': int((scenario_labels == k).sum()),
     'reason': 'below_min_gap_size'}
    for k in range(K_scenario)
    if 0 < (gap_mask & (scenario_labels == k)).sum() < MIN_GAP_SIZE
]
with open('phase0/skipped_small_gaps.json', 'w') as f:
    json.dump(skipped_gaps, f, indent=2)

# COLLECT_HIGH_PRIORITY와 COLLECT를 우선순위 필드로 통합
# scenario_context / gap_specifics 분리 유지 — LLM 쿼리 생성 시 맥락 구조 보존
# "이것은 [scenario_context] 장면인데 [gap_specifics] 요소가 부족합니다" 구조
def _collect_confidence(gap_q2_ratio):
    """gap_q2_ratio: COLLECT 판정의 Q2(저밀도+고LID+신뢰) 기반 비율
    LOW이면 Q3(저LID) 또는 Q4(LID 불신뢰) 클립이 갭 대부분을 차지 → 실제 수집 ROI 불확실"""
    if gap_q2_ratio >= 0.5:
        return 'HIGH'    # 갭의 절반 이상이 신뢰 Q2 → COLLECT 판정 확실
    if gap_q2_ratio >= 0.3:
        return 'MED'     # Q2 혼재 — 부분적으로 신뢰
    return 'LOW'         # 갭의 대부분이 Q3/Q4 → 수집 ROI 불확실, Phase D 진입 전 수동 확인 권고

collect_candidates = [
    {'scenario_id': k,
     'scenario_context': v['scenario_terms'][:5],    # 시나리오 배경 맥락 (TF-IDF centroid 상위 5)
     'gap_specifics': v['gap_specific_terms'],        # 갭 내 특이 속성 (시나리오 전체 대비 저밀도 구간 차분)
     'priority': 'HIGH' if v['action'] == 'COLLECT_HIGH_PRIORITY' else 'NORMAL',
     'gap_count': v['gap_count'],                     # D_train 내 갭 클립 수 — 수집 목표 참고값
     'q2_effective_n': v['q2_effective_n'],           # 수집 시 Effective N 증가 추정치 — 수집 ROI 정량화 핵심
     'mean_lid': v['mean_lid'],                       # 탐색 ROI 참고값 — Phase D 우선순위 보조
     'gap_q2_ratio': v['gap_q2_ratio'],               # COLLECT 판정 신뢰도 원값
     'collect_confidence': _collect_confidence(v['gap_q2_ratio']),  # HIGH/MED/LOW — Phase D 진입 판단 보조
     'lid_context_caution': v.get('lid_context_caution', False),    # True이면 갭만 고LID, 시나리오 전체는 저LID — 소수 클립에 의존, Phase D 진입 전 수동 확인 권고
     'prune_flag': v['prune_flag']}                   # PRUNE 후보이지만 갭 존재하는 케이스 — Phase D에서 별도 처리
    for k, v in gap_slices.items() if v['action'] in ('COLLECT_HIGH_PRIORITY', 'COLLECT')
]
# Phase D 진입 순서: HIGH 우선 → lid_context_caution=False 우선(갭 내 소수 고LID 의존 케이스 하위) → q2_effective_n 내림차순 → mean_lid 내림차순
collect_candidates.sort(
    key=lambda x: (x['priority'] == 'HIGH', not x.get('lid_context_caution', False), x['q2_effective_n'], x['mean_lid']),
    reverse=True
)
synthetic_candidates = [
    {'scenario_id': k,
     'scenario_terms': v['scenario_terms'],
     'gap_count': v['gap_count'],              # 합성 목표량 참고값 (얼마나 만들어야 하는가)
     'mean_lid': v['mean_lid'],                # LID 낮음 확인 — 합성 선택 근거 (탐색 ROI 없음)
     # mean_lid < lid_threshold이어도 gap 내 Q2 클립이 존재할 수 있음
     # → partial_collect_flag=True이면 EXP-004 합성 전 Q2 클립만 분리 수집 검토
     'partial_collect_flag': v['gap_q2_ratio'] >= 0.2,
     'q2_effective_n': v['q2_effective_n'],    # Q2 클립 독립 정보량 — 부분 수집 ROI 추정치
     'gap_q2_ratio': v['gap_q2_ratio'],        # 부분 수집 규모 참고값
     'note': ('Q2 클립 존재 — EXP-004 합성 전 Q2 클립 별도 수집 검토'
              if v['gap_q2_ratio'] >= 0.2 else 'Q2 클립 미미 — 합성으로 충분')}
    for k, v in gap_slices.items() if v['action'] == 'SYNTHETIC_OR_ACCEPT'
]
uncertain_candidates = [
    {
        'scenario_id': k,
        'top_terms': scenario_profiles[k]['top_terms'][:5],
        'size': scenario_profiles[k]['size'],
        'gap_count': v['gap_count'],
        'lid_reliable_ratio': v['lid_reliable_ratio'],
        'gap_specific_terms': v['gap_specific_terms'],   # 갭 클립 특이 어휘 — 수동 검토 시 즉시 맥락 파악용
        'quadrant_distribution': scenario_profiles[k]['quadrant_distribution'],
        'boundary_sensitive': v['boundary_sensitive'],   # 임계값 민감 여부 — 수동 검토 우선순위 보조
        'note': 'LID 불신뢰 — 0-E-1 시나리오 프로파일 수동 확인',
    }
    for k, v in gap_slices.items() if v['action'] == 'UNCERTAIN_CHECK_SEMANTIC'
]

with open('phase0/gap_slices.json', 'w') as f:
    json.dump(gap_slices, f, indent=2, ensure_ascii=False)
with open('phase0/collect_candidates.json', 'w') as f:
    json.dump(collect_candidates, f, indent=2, ensure_ascii=False)
with open('phase0/synthetic_candidates.json', 'w') as f:
    json.dump(synthetic_candidates, f, indent=2, ensure_ascii=False)
with open('phase0/uncertain_candidates.json', 'w') as f:
    json.dump(uncertain_candidates, f, indent=2, ensure_ascii=False)

```

**COLLECT vs SYNTHETIC 판정 기준 (개정)**:

| 조건 | 판정 | gap_q2_ratio 해석 | 근거 |
|------|------|-----------------|------|
| lid_reliable_ratio < 0.4 | UNCERTAIN_CHECK_SEMANTIC | 해당 없음 | LID 신뢰도 불충분 — 0-E-1 프로파일로 수동 판단 |
| mean_lid ≥ lid_threshold AND gap_ratio > 0.4 | **COLLECT_HIGH_PRIORITY** | 높을수록 신뢰도 ↑ | 시나리오 전체가 갭 → 대규모 탐색 |
| mean_lid ≥ lid_threshold AND gap_ratio ≤ 0.4 | COLLECT | 높을수록 신뢰도 ↑ | 시나리오 일부 갭 → 보완적 탐색 |
| mean_lid < lid_threshold | SYNTHETIC_OR_ACCEPT | 낮을수록 합성 확신 ↑ | LID 낮음 → 탐색 ROI 없음 → 합성 고려 |

> `gap_q2_ratio`는 action 결정에 쓰이지 않고 gap_slices에 기록만 한다. mean_lid가 임계값 경계에 걸릴 때 판정 신뢰도를 수동으로 보정하는 참고 지표.

**출력**: `gap_slices.json`, `collect_candidates.json`, `synthetic_candidates.json`, `uncertain_candidates.json`  
**근거**: Eyuboglu et al. (ICLR 2022 Domino) · Ma et al. (ICLR 2018) LID 직접 사용 · Semantic-Drive (arXiv 2024) — VLM 기반 검증은 원시 비디오 확보 후 다음 단계

---

#### Phase 0 통합 산출물

```json
{
  "effective_N_soft": 38400,
  "effective_N_hard": 31200,
  "redundancy_ratio": 0.538,
  "vendi_score": 4820,
  "vendi_diversity_ratio": 0.058,
  "density_median": 0.724,
  "lid_median": 6.3,
  "lid_mean": 7.1,
  "lid_reliable_ratio": 0.84,
  "quadrant_counts": {"Q0": 18600, "Q1": 12000, "Q2": 14200, "Q3": 18700, "Q4": 15000, "Q5": 4500},
  "scenario_count": 12,
  "overrepresented_scenarios": [0, 3, 7],
  "gap_scenarios_collect": [1, 4, 9],
  "gap_scenarios_synthetic": [2, 6],
  "gap_scenarios_uncertain": [5, 8, 11],
  "prune_candidates": 16500,
  "collect_priority_pool": 14200
}
```

**Phase 0 산출물 → 다운스트림 연결표**:

| Phase 0 산출물 | 소비 단계 | 역할 |
|--------------|---------|------|
| `healthy_scenarios.json` | Phase B 파일럿 | Q0 우세(≥40%)+크기(≥500) 시나리오 → null hypothesis 기준 클러스터 |
| `caution_scenarios.json` | Phase B/C 프루닝 결정 | CAUTION·Q5_UNCERTAIN 시나리오 → 자동 프루닝 금지 목록 |
| `collect_candidates.json` | Phase D 쿼리 생성 | priority(HIGH→NORMAL)+mean_lid 정렬 → LLM 갭 쿼리 입력 순서 |
| `synthetic_candidates.json` | EXP-004 합성 생성 | LID 낮음 확인 + gap_count 목표량 → 합성 클립 생성 명세 |
| `uncertain_candidates.json` | 수동 검토 | top_terms+quadrant_distribution 포함 → 단일 파일로 검토 완결 |
| `quadrant_profile.json` | Q4+Q5 진단 | Q4+Q5 비율 > 5% → bge-m3 임베딩 품질 점검 트리거 |
| `thresholds.json` | 0-E-2 재사용 · 0-D-val 조건 판단 | lid_threshold(BIC 교차점) → gap_slices action 판정 기준 · q3_boundary_rate → 0-D-val 실행 트리거 |
| `flipd_validation.json` | (0-D-val 실행 시) 감사 기록 | upgrade_rate + recommended_action → Q3 분류 신뢰도 실증 결과, quadrant_updated=True이면 0-E-1/0-E-2 재반영 |
| `scenario_profiles.json` | Phase A 클러스터 해석 | TF-IDF×사분면 교차표 → Phase A K=6 클러스터 의미 설명 |

**산출물 → 우선순위 공식 연결표**:

| 공식 항 | 소스 서브 실험 | 핵심 지표 |
|--------|--------------|---------|
| `a_i` | Phase B (파일럿 이후) | 스케일링 법칙 최대 이득 |
| `(1 - density_i)` | 0-B local_density | 클러스터 내 클립 평균 밀도 역수 |
| `LID_i_normalized` | 0-C × 0-D | 클러스터 내 Q2 클립 평균 LID 정규화 (신뢰 클립만) |
| `collectability_i` | **0-E-2** gap_slices.action | COLLECT=1, SYNTHETIC=0, UNCERTAIN=0.5 (보수 추정) |

**개정된 우선순위 공식**:

```
priority_i = a_i × (1 - density_i) × LID_i_normalized × collectability_i
```

**v2 개선점**:
- `collectability_i`가 mean_lid 직접 판정으로 Q2 비율 순환성 해소
- UNCERTAIN 슬라이스는 0.5 보수값으로 처리 — 과도한 우선순위 부여 방지
- 0-E-1 시나리오 프로파일이 Q1 프루닝 대상을 의미 수준에서 설명 가능

---

### Phase A: Caption TF-IDF 클러스터링 [기존 유지]

**입력**: 83k 캡션 텍스트 (`/Data1/home/bskang/cds-data/captions/`)  
**상태**: 🔲 미시작

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

tfidf = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words='english')
X = tfidf.fit_transform(captions)  # sparse, 메모리 효율적

# K=6 고정 (Q2 결정 참조)
kmeans = KMeans(n_clusters=6, random_state=42)
labels = kmeans.fit_predict(X)
```

**출력 분석**:
- 클러스터별 top 10 uni-gram/bi-gram (Table 3 스타일)
- 클러스터별 클립 수 분포 및 희귀 시나리오 클러스터 식별
- Phase 0 Q2(COLLECT) 클립의 클러스터 소속 분포 → "갭이 몰린 클러스터" 식별 (Phase B 우선순위 결정)

---

### Phase B: 클러스터별 스케일링 파일럿 [기존 유지]

**목적**: 각 클러스터에서 데이터를 추가할 때 Recall@5가 어떻게 변하는지 측정  
**상태**: 🔲 미시작

```
각 클러스터에서 n = [50, 100, 200, 400] 샘플 추가 시 Recall@5 측정
→ (a_i, τ_i) 피팅: ΔU_i(n) ≈ a_i × (1 - e^{-n/τ_i})
→ a_i 높고 현재 수 적은 클러스터 = 최우선 수집 대상
```

파일럿 방식: 클러스터별 독립 서브인덱스 (Q4 결정 참조)  
출력: `scaling_fits.json` — 클러스터별 `(a_i, τ_i)` 파라미터

---

### Phase C: 다중 메트릭 분리 평가 [기존 유지]

**목적**: 단일 aggregate 메트릭이 숨기는 도메인별 트레이드오프 측정  
**상태**: 🔲 미시작

```python
domain_queries = {
    'night': [...],        # 야간 관련 쿼리
    'rain': [...],         # 우천 관련 쿼리
    'pedestrian': [...],   # 보행자 관련 쿼리
    'highway': [...],      # 고속도로 관련 쿼리
    'intersection': [...], # 교차로 관련 쿼리
}
# 희귀 도메인에 높은 weight
weights = {'night': 3, 'rain': 3, 'pedestrian': 2, 'highway': 1, 'intersection': 2}
U = weighted_recall(domain_queries, weights)
```

출력: `domain_recall.json` — 도메인별 Recall@5 비교표

---

### Phase D: 타겟 탐색 효율 측정 [신규]

**목적**: 갭 명세 → 검색 쿼리 → 탐색 효율 정량화  
**상태**: 🔲 미시작

#### ① 갭 명세 → 자연어 쿼리 생성

LLM으로 갭 명세를 검색 쿼리로 변환:

```python
gap_spec = "야간 + 우천 + 교차로 + 보행자 돌출"
queries = llm.generate_queries(gap_spec, n=10)
# 출력 예: ["night rainy intersection pedestrian crossing",
#            "heavy rain crossroads person stepping out", ...]
```

#### ② D_pool 내 타겟 검색

```python
results = [retrieval_system.search(q, top_k=20) for q in queries]
```

#### ③ 탐색 효율(Search ROI) 계산

```python
search_roi_i = n_relevant_found_i / n_queries_i
# n_relevant_found: 실제 해당 갭에 속하는 클립 수 (수동 검증 또는 LLM 분류)
```

#### ④ 탐색 종료 기준

Phase B에서 추정한 스케일링 파라미터를 역산해 필요 수집량 산출:

```
n_target = τ_i × ln(a_i / ε)    ε = 0.01 (목표 성능 여지 1% 이하)
```

출력: `search_roi.json`, `target_counts.json`

---

## 4. 파이프라인 대응표 (DISC 확장판)

| MOSAIC 단계 | EXP-003 Phase | 추가 근거 논문 | 상태 |
|------------|---------------|--------------|------|
| (없음) | Phase 0: D_train 분포 프로파일링 (0-A~0-E) | Ma et al. ICLR 2018 · Friedman TMLR 2023 · SoftDedup ACL 2024 · Domino ICLR 2022 · Sorscher NeurIPS 2022 | 🔲 미시작 |
| Cluster & Rank | Phase A: TF-IDF 클러스터링 | MOSAIC, Coverage Coreset | 🔲 미시작 |
| Estimate Scaling | Phase B: 스케일링 파일럿 | MOSAIC · LESS (대안) · DoReMi NeurIPS 2023 (희귀 도메인 Minimax 대안) | 🔲 미시작 |
| Multi-metric Utility | Phase C: 도메인별 Recall | Domino, Chodowiec | 🔲 미시작 |
| Iterative Mining | Phase D: 탐색 효율 측정 | TypiClust, active collection | 🔲 미시작 |

---

## 5. 결정 사항

| # | 질문 | 결정 | 근거 |
|---|------|------|------|
| Q1 | 클러스터링 알고리즘 | **KMeans** | MOSAIC 독립성 근사(Eq.3)는 클러스터가 명확히 분리될수록 정확. HDBSCAN은 노이즈 포인트와 경계 중첩이 독립성 가정을 약화시킴 |
| Q2 | 클러스터 수 K | **K=6, 의미 일관성 검증** | 논문이 caption 기반으로 K=6 사용. K가 작으면 클러스터 내 이질성 증가 → Eq.3 오차 증가. K가 크면 파일럿 비용 증가. 각 클러스터 top 키워드로 의미 순수도 수동 확인 후 K 조정 |
| Q3 | Utility 함수 | **도메인별 가중 Recall** | 지표들이 경쟁하지 않으면 MOSAIC 프레임워크 자체가 불필요해짐. 희귀(야간/우천) vs 일반 쿼리 Recall은 실제로 경쟁함 — 희귀 클립 추가는 희귀 Recall↑, 전체 Recall에는 희석 효과 |
| Q4 | Phase B 파일럿 방식 | **클러스터별 서브인덱스** | 전체 재구축은 K×4번 반복 시 비용 과다. 클러스터별 독립 서브인덱스로 증분 평가. 파일럿 포인트: n = [50, 100, 200, 400] (2파라미터 피팅에 4포인트면 충분) |
| Q5 | 수집 우선순위 공식 설계 | **개정 4차원 결합 우선순위 공식** | `priority_i = a_i × (1 - density_i) × LID_i_normalized × collectability_i`. 각 항: a_i(Phase B), density_i(0-B k-NN), LID_i(0-C Ma et al. 2018), collectability_i(0-E-2 gap_slices.action). 모든 항이 클립 단위 → 클러스터 집계 일관 |
| Q6 | 저가치 클립 프루닝 여부 | **0-D Q1 사분면 완료 후 판단** | 기준: Q1 사분면(고밀도+저LID) 클립 = 많지만 단조로운 복제 클립. 근거: Sorscher et al. (NeurIPS 2022) — redundant 클립 제거가 갭 채우기보다 선행되어야 효율적 |
| Q7 | 탐색 종료 기준 | **스케일링 법칙 역산** | `n_target = τ_i × ln(a_i / ε)`, ε = 0.01 (목표 성능 여지 1% 이하). EXP-003 Phase B에서 추정된 (a_i, τ_i) 값 사용 |

### Q5 결합 공식 설명

```
priority_i = a_i  ×  (1 - density_i)  ×  LID_i_norm  ×  collectability_i
              ↑            ↑                  ↑                 ↑
           Phase B        0-B              0-C × 0-D            0-E
          (성능 여지)   (밀도 갭)     (다양성 잠재량)      (수집 가능 여부)
         클러스터 단위  클립→클러스터  클립→클러스터    슬라이스→클러스터
```

**항별 계산 방식 (클립 단위 → 클러스터 단위 집계)**:
- `density_i` = Phase A 클러스터 i의 클립 평균 local_density (0-B)
- `LID_i_norm` = 클러스터 i의 Q2 클립 비율 × mean_lid / global_lid_max (0-C × 0-D)
- `collectability_i` = 클러스터 i 저밀도 클립들의 COLLECT 슬라이스 비율 (0-E)

| 케이스 | a_i | density_i | LID_i | collectability_i | 우선순위 | 해석 |
|--------|-----|-----------|-------|----------------|---------|------|
| 진짜 수집 대상 | 높음 | 낮음 | 높음 | 1 | **최고** | 갭 있고 다양하고 탐색 가능 |
| 포화된 갭 | 낮음 | 낮음 | 높음 | 1 | 낮음 | 갭이지만 성능 여지 없음 |
| 자연 희귀 | 높음 | 낮음 | 낮음 | 0 | **최저** | LID 낮아 탐색 ROI 없음 → 합성 |
| Q1 중복 과잉 | 높음 | 높음 | 낮음 | — | 낮음 | 프루닝 먼저 (Q6 액션) |
| 무관심 | 낮음 | 높음 | 낮음 | — | 최저 | 많고 단조롭고 효과도 없음 |

---

## 6. EXP-004 계획 (간략)

**가설**: "D_train에서 중복/저가치 클립을 제거하고 갭 클립 비율을 높이면, 총 클립 수를 늘리지 않고도 도메인별 Recall@5 분산이 감소한다."

**선행 조건**: EXP-003 Phase 0 완료 + Phase B (a_i, τ_i) 추정 완료

### Phase A: 데이터 가치 평가

- 중복 클립 식별 (cosine sim > 0.95)
- LESS 방식 gradient influence 추정
- 가치 하위 10% 목록 추출

### Phase B: 구성 비교 실험

| 조건 | 구성 | 크기 |
|------|------|------|
| Baseline | D_train 전체 | 83k |
| Pruned | D_train - 가치 하위 10% | ~75k |
| Rebalanced | Pruned + 갭 클립 오버샘플링 | ~80k |

각각 도메인별 Recall@5 측정.

### 핵심 메트릭

- 도메인별 Recall@5 평균 (희귀 도메인 향상 확인)
- 도메인별 Recall@5 분산 (낮을수록 균등 — 주 목표)

---

## 7. 예상 산출물

```
experiments/EXP-003/
├── design.md                      ← 이 파일 (실험 설계)
├── research_synthesis.md          ← 이론적 배경 문서 [신규]
├── RUNBOOK.md                     ← 실행 명령어 (설계 확정 후 작성)
└── results/
    ├── phase0/
    │   ├── clip_ids.npy               # 진입점: 클립 ID 배열 — 모든 인덱스의 역추적 키
    │   ├── knn_foundation.npz         # 0-A: FAISS k-NN (knn_sim, knn_idx) — 계산 앵커
    │   ├── embeddings.npy             # 0-A: bge-m3 임베딩 (0-B Vendi, 0-E-1 per-scenario Vendi용)
    │   ├── diversity_profile.json     # 0-B: Effective N (soft/hard), Vendi Score
    │   ├── density_per_clip.npy       # 0-B: 클립별 k=10 연속 밀도 (0-D 분류 기준)
    │   ├── density_quartile.npy       # 0-B: 클립별 밀도 4분위 등급 (0-E-1 density_quartile_dist용)
    │   ├── uniqueness_weight.npy      # 0-B: 클립별 k=20 soft uniqueness (0-D effective_n용)
    │   ├── lid_per_clip.npy           # 0-C: 클립별 LID (Ma et al. MLE)
    │   ├── lid_quartile.npy           # 0-C: 클립별 LID 4분위 등급 (0-E-1 lid_quartile_dist용)
    │   ├── lid_reliable.npy           # 0-C: LID 신뢰 플래그 (r_max_dist < 0.6)
    │   ├── lid_stats.json             # 0-C: LID 분포 통계 + lid_reliable_ratio
    │   ├── quadrant_assignment.npy    # 0-D: 클립별 6분류 (Q0~Q5, Q5=PRUNE_UNCERTAIN)
    │   ├── quadrant_profile.json      # 0-D: 사분면별 통계 (count/pct/effective_n/density/lid)
    │   ├── thresholds.json            # 0-D: density_threshold, lid_threshold + BIC 검증 정보
    │   ├── scenario_labels.npy        # 0-E-1: 클립별 시나리오 ID (83k 전체, K=실루엣 최적)
    │   ├── silhouette_scores.json     # 0-E-1: K별 실루엣 점수 + K_selected — K 선택 근거 추적
    │   ├── scenario_profiles.json     # 0-E-1: 시나리오별 프로파일 (키워드+사분면+quartile_dist+prune_flag)
    │   ├── caution_scenarios.json     # 0-E-1: CAUTION+Q5_UNCERTAIN 시나리오 — 수동 검토 대상 완전 수집
    │   ├── healthy_scenarios.json     # 0-E-1: Q0 우세+size≥500 시나리오 — Phase B null hypothesis
    │   ├── scenario_diversity_summary.json  # 0-E-1: 시나리오 간 Vendi 분산 집계 (CV, Gini, unreliable_count) — 다양성 불균등도
    │   ├── boundary_sensitive_scenarios.json # 0-E-1: 전역 임계값 ±5% 이내 시나리오 — 0-D 임계값 민감성 피드백
    │   ├── tfidf_vectorizer.joblib    # 0-E-1: 저장된 TF-IDF vectorizer — 0-E-2 독립 실행 지원
    │   ├── gap_slices.json            # 0-E-2: 시나리오 단위 갭 분석 (Q2/Q3/Q4 구성비 포함)
    │   ├── collect_candidates.json    # 0-E-2: COLLECT → Phase D 쿼리 입력 (priority 정렬)
    │   ├── synthetic_candidates.json  # 0-E-2: SYNTHETIC → EXP-004 합성 입력
    │   ├── uncertain_candidates.json  # 0-E-2: UNCERTAIN → 수동 검토 목록 (상세 필드 포함)
    │   ├── skipped_small_gaps.json   # 0-E-2: gap_count > 0이지만 MIN_GAP_SIZE(50) 미달로 분석 제외된 시나리오
    │   └── distribution_profile.json # 통합 요약 (priority 공식 4개 항 완성)
    ├── cluster_analysis.json          # Phase A: 클러스터별 top 키워드 + 클립 수
    ├── gap_cluster_mapping.json       # Phase A: Phase 0 Q2(COLLECT) 클립 → Phase A 클러스터 소속
    ├── scaling_fits.json              # Phase B: (a_i, τ_i) 파라미터
    ├── domain_recall.json             # Phase C: 도메인별 Recall@5
    ├── search_roi.json                # Phase D: 탐색 효율
    └── target_counts.json             # Phase D: 클러스터별 목표 수집량
```

---

## 8. 참조 문서

- **이론적 배경 전체**: [`research_synthesis.md`](research_synthesis.md)
  - MOSAIC 핵심 공헌 4개 상세 분석
  - E2E AD 학습 패러다임 (Tesla, Waymo, NVIDIA)
  - 관련 최신 연구 (Sorscher, Eyuboglu, Xia, Gadre 등)
  - DISC 통합 프레임워크 — Phase별 이론 근거
- **관련 논문**: `literature/papers/dimlioglu-2026-scaling-aware-data-selection.pdf`

---

## 9. 변경 이력

| 날짜 | 변경 내용 |
|------|---------|
| 2026-06-30 | 초안 작성 — MOSAIC 논문 분석 기반 |
| 2026-06-30 | §2.5 추가 — 논문 핵심 공헌 4레이어 분석 |
| 2026-06-30 | 가설 v2 — SANFlow × MOSAIC 결합 공식 중심 재정립 |
| 2026-06-30 | Q1~Q5 결정 완료 (KMeans K=6, 가중 Recall, 서브인덱스, 결합 우선순위) |
| 2026-06-30 | §2.6 추가 — E2E AD 학습 패러다임 |
| 2026-07-02 | 파일 분리: 이론 내용 → research_synthesis.md 이동 |
| 2026-07-02 | Phase 0 (D_train 분포 프로파일링) 신규 추가 — 초안 ①②③④ 구조 |
| 2026-07-02 | Phase 0 전면 재설계 — 5개 서브 실험 (0-A~0-E) 으로 교체 |
| 2026-07-02 | Phase 0 최신 논문 반영 재설계 — 단일 k-NN 앵커 + LID + Vendi Score + 4-사분면 |
| 2026-07-02 | 우선순위 공식 개정 v3 — coverage_gap/redundancy → LID_norm/collectability |
| 2026-07-02 | 관련 논문 추가 — Ma ICLR 2018 · Friedman TMLR 2023 · SoftDedup ACL 2024 · DoReMi NeurIPS 2023 · Ruppik NeurIPS 2025 · FLIPD NeurIPS 2024 |
| 2026-07-02 | Phase D (타겟 탐색 효율 측정) 신규 추가 |
| 2026-07-02 | Q6 (프루닝 여부), Q7 (탐색 종료 기준) 신규 추가 |
| 2026-07-02 | 가설 v2 → 4차원 결합 공식으로 업데이트 |
| 2026-07-02 | EXP-004 계획 간략 추가 |
| 2026-07-02 | 최종 검토 수정: 0-B `uniqueness_weight.npy` 저장 추가, 0-D `uniqueness_weight` 로드 추가 (미정의 변수 버그 수정) |
| 2026-07-02 | §7 산출물 목록에 `uniqueness_weight.npy` 추가 |
| 2026-07-02 | §4 파이프라인 대응표 Phase B에 DoReMi 연결 추가 |
| 2026-07-02 | Phase 0 v2 재설계 — LID 신뢰도 플래그 추가, 0-E를 0-E-1/0-E-2로 분리 |
| 2026-07-02 | Phase 0 v3 재설계 — 0-D 임계값(median→GMM2), 0-E-1(임베딩GMM→TF-IDF KMeans), Vendi 시나리오 분해, gap_ratio 활용 |
| 2026-07-02 | 0-D: GMM K=2 자연 임계값 도입, thresholds.json 저장 추가 |
| 2026-07-02 | 0-E-1: TF-IDF 공간 KMeans K=12 + 시나리오별 Vendi Score 계산 |
| 2026-07-02 | 0-E-2: lid_threshold 로드, COLLECT_HIGH_PRIORITY 추가, variable names 정리 |
| 2026-07-02 | 0-C: lid_reliable.npy 신규 — r_max_dist < 0.6 임계값 기반 신뢰도 플래그 |
| 2026-07-02 | 0-D: Q4(LID_UNCERTAIN) 신규 — 4분류 → 5분류로 확장 |
| 2026-07-02 | 0-E-1 신규: 전체 83k GMM K=12 + 시나리오×사분면 교차표 — Q1 과잉 시나리오 식별 |
| 2026-07-02 | 0-E-2: Q2 비율 → mean_lid 직접 사용으로 순환성 제거, uncertain_candidates.json 추가 |
| 2026-07-02 | Phase 0 v4 시너지 보강 — 5개 구조 문제 수정 |
| 2026-07-02 | 0-D: GMM K=2 고정 → BIC K=1~3 비교 + brentq 실제 교차점 계산으로 교체 (means_.mean() 부정확 수정) |
| 2026-07-02 | 0-D: thresholds.json 확장 — density/lid_gmm_best_k + BIC 값 저장 (검증 가능) |
| 2026-07-02 | 0-E-1: per-scenario Vendi 앵커 수 500→200 고정 (시나리오 간 비교 가능하게 표준화) |
| 2026-07-02 | 0-E-1: Vendi "분해" → "독립 측정"으로 표현 교정 (Vendi 비가산성 명시) |
| 2026-07-02 | 0-E-1: Q1 × Vendi 피드백 루프 추가 — Q1 우세+고Vendi 시나리오에 prune_flag=CAUTION 부여 |
| 2026-07-02 | 0-E-2: 명시적 변수 로드 추가 (독립 실행 지원, NameError 방지) |
| 2026-07-02 | 0-E-2: 0.4 하드코딩 → GAP_RATIO_HIGH_PRIORITY 상수화 (캘리브레이션 파라미터 명시) |
| 2026-07-02 | Phase 0 v5 재현성·완성도 보강 — 6개 문제 수정 |
| 2026-07-02 | 0-A: embeddings.npy 저장 추가 — 0-B·0-E-1 독립 실행 지원 (knn만 저장했던 버그 수정) |
| 2026-07-02 | 0-B: embeddings_f32 명시적 로드 추가 (0-A 메모리 암묵 의존 제거) |
| 2026-07-02 | 0-B: density(k=10) vs uniqueness(k=20) 주석 명시 — 각기 다른 개념 측정임을 문서화 |
| 2026-07-02 | 0-E-1: embeddings_f32 명시적 로드 추가 (0-A 메모리 암묵 의존 제거) |
| 2026-07-02 | 0-E-1: VENDI_ANCHOR=200 루프 외부로 이동 (루프 내 상수 재정의 제거) |
| 2026-07-02 | 0-E-1: K=12 → 실루엣 검증 코드 추가 (K=6,8,10,12,15 비교 후 최적 K 자동 선택) |
| 2026-07-02 | 0-E-1: caution_scenarios.json 출력 추가 (prune_flag=CAUTION 다운스트림 연결) |
| 2026-07-02 | §7 산출물 목록: embeddings.npy + caution_scenarios.json 추가, density/uniqueness k 명시 |
| 2026-07-02 | 설계 원칙 블록: v3 기준 → v4 변경점 갱신 (BIC+brentq, embeddings, caution_scenarios) |
| 2026-07-02 | Phase 0 v5 코드 실행 레벨 버그 수정 — 5개 |
| 2026-07-02 | 0-B: `diversity_profile.json` 저장 누락 수정 (§7 산출물 목록 선언 후 실제 저장 코드 없던 버그) |
| 2026-07-02 | 0-B: `import json` 추가 (diversity_profile.json 저장 코드 추가에 따라) |
| 2026-07-02 | 0-D: `len(captions)` → `len(density_per_clip)` 2곳 수정 (독립 실행 시 NameError 해소) |
| 2026-07-02 | 0-E-2: JSON 로드 후 str→int 키 변환 추가 (`scenario_profiles = {int(kk): vv for ...}`) — 독립 실행 시 KeyError 해소 |
| 2026-07-02 | 0-E-1: `X_tfidf.toarray()` 제거 + `best_models` dict로 검증 모델 재사용 — 메모리 ~2GB 절약, KMeans 5회 재학습 제거 |
| 2026-07-02 | 0-B: Vendi 앵커 `np.random.default_rng(42).choice(...)` 시드 고정 (재현성) |
| 2026-07-02 | 0-E-1: per-scenario Vendi 앵커 `np.random.default_rng(42+k).choice(...)` 시나리오별 독립 시드 (prune_flag 재현성) |
| 2026-07-02 | Phase 0 v6 코드 실행 버그 수정 + 구조적 독립 실행 지원 + 인사이트 보강 |
| 2026-07-02 | 0-C: `lid_stats.json` 저장 누락 수정 + `import json` 추가 (0-B/0-D와 동일 패턴 버그) |
| 2026-07-02 | 0-D: `quadrant_profile.json` 저장 누락 수정 (`{str(q): v ...}` 키 변환 포함) |
| 2026-07-02 | 0-B: `len(captions)` → `len(knn_sim)` 2곳 수정 (독립 실행 시 NameError 해소) |
| 2026-07-02 | 0-E-1: `joblib.dump(tfidf_e1, 'phase0/tfidf_vectorizer.joblib')` 추가 — 0-E-2 독립 실행 지원 |
| 2026-07-02 | 0-E-1: `import joblib` 추가 |
| 2026-07-02 | 0-E-1: `healthy_scenarios.json` 추출 추가 — Q0 우세 시나리오 → Phase B 건강 기준점 baseline |
| 2026-07-02 | 0-E-2: 로드 블록 교체 — 코멘트 제거, `joblib.load` + `tfidf_e1.transform(captions)` 실제 코드로 대체 |
| 2026-07-02 | 0-E-2: `import joblib` 추가 |
| 2026-07-02 | 0-E-2: 미사용 변수 `gap_idx = np.where(gap_mask)[0]` 제거 |
| 2026-07-02 | §7 산출물 목록: `healthy_scenarios.json` + `tfidf_vectorizer.joblib` 추가, `lid_stats.json`/`quadrant_profile.json` 설명 보강 |
| 2026-07-02 | Phase 0 v7 미사용 변수 저장 + collect_candidates 필드 재설계 |
| 2026-07-02 | Phase 0 v14 서브 실험 시너지 4개 추가 보강 |
| 2026-07-02 | 0-E-1: 실루엣 평탄 감지(`sil_range < 0.02`) → K=12 자동 폴백 코드 추가 (`flat_fallback` 플래그 기록) |
| 2026-07-02 | 0-E-2: `MIN_GAP_SIZE = 30` 상수 추가 — 갭 클립 30개 미만 시나리오 스킵 (5 → 30, mean_lid/gap_q2_ratio 통계 안정성) |
| 2026-07-02 | 0-B: `diversity_profile.json`에 `grey_zone_contribution` 추가 — soft/hard Effective N 차이, Q1 프루닝 보수성 판단 기준 |
| 2026-07-02 | 0-E-2: `uniqueness_weight` 로드 추가 + 루프 내 `q2_effective_n` 계산 → `gap_slices`·`collect_candidates`에 전달 |
| 2026-07-02 | 0-E-2: `collect_candidates` 정렬 기준 `mean_lid` 단일 → `q2_effective_n → mean_lid` 2단계 업그레이드 |
| 2026-07-02 | Phase 0 v13 서브 실험 시너지 4개 보강 |
| 2026-07-02 | 0-E-2: 독립 실행 시 `captions` NameError 수정 — `if 'captions' not in dir():` 조건부 재로드 블록 추가 |
| 2026-07-02 | 0-E-1: Q5 플래그 임계값 `15` 절대값 → `max(15, 2 × global_q5_pct)` 상대화 — `quadrant_profile.json` 참조 (0-D↔0-E-1 연결) |
| 2026-07-02 | 0-E-1: `_caution_note()` 내 `q5 > 15` 동일 패턴 `Q5_CONCENTRATION_THRESHOLD` 교체 |
| 2026-07-02 | 0-E-2: `_collect_confidence()` 함수 추가 + `collect_candidates`에 `collect_confidence` 필드 (HIGH/MED/LOW) — `gap_q2_ratio` actionable 처리 |
| 2026-07-02 | 0-E-1: 시나리오 Vendi 분산 집계 추가 → `scenario_diversity_summary.json` (CV, Gini, max/min 시나리오) — 0-B 전역 Vendi 맹점 보완 |
| 2026-07-02 | §7 산출물: `scenario_diversity_summary.json` 추가 |
| 2026-07-02 | Phase 0 v12 누락 필드 보강 + EXP-003 완전 독립 구조 확정 |
| 2026-07-02 | 0-E-2: `collect_candidates`에 `gap_q2_ratio` 필드 추가 — COLLECT 판정 신뢰도 직접 기록 |
| 2026-07-02 | 0-E-1: `healthy_scenarios`에 `q2_pct` 필드 추가 — 건강 시나리오 내 잠재 갭 비율 파악 |
| 2026-07-02 | 0-E-1: 교차표에 `gap%` 컬럼 추가 (Q2+Q3+Q4 합산) — gap_ratio 임계값 보정 참고값 |
| 2026-07-02 | EXP-003 독립화: EXP-001/002 결과 의존 코드 전면 제거 (EXP-002 crossval 블록 삭제, SANFlow 갭 참조 제거) |
| 2026-07-02 | §1: 실험 동기를 EXP-002 후속이 아닌 독립 분포 분석 실험으로 재작성 |
| 2026-07-02 | §2: 가설 v1 SANFlow 참조 → D_train 내부 밀도 갭 기반 표현으로 교체 |
| 2026-07-02 | §5 Q5: "SANFlow 갭과의 통합" → "수집 우선순위 공식 설계"로 질문 재명명 |
| 2026-07-02 | Phase A: 출력 분석에서 SANFlow 갭 소속 분포 제거 → Phase 0 Q2 클립 소속 분포로 대체 |
| 2026-07-02 | §7: gap_cluster_mapping.json 설명 교정 (SANFlow → Phase 0 Q2), exp002_gap_crossval.json 삭제 |
| 2026-07-02 | §8: 참조 문서에서 EXP-002 선행 실험 링크 제거 |
| 2026-07-02 | 0-B: `density_quartile.npy` 저장 추가 — 미사용 변수 → 파일 저장 (0-D 이진 임계값 분포 맥락 제공) |
| 2026-07-02 | 0-C: `lid_quartile.npy` 저장 추가 — 동일 패턴 |
| 2026-07-02 | 0-E-2: `collect_candidates` 재설계 — `query_terms` 병합 제거 → `scenario_context`+`gap_specifics` 분리, `gap_count`·`mean_lid` 추가 (Phase D LLM 쿼리 생성 맥락 구조 보존) |
| 2026-07-02 | §7 산출물 목록: `density_quartile.npy`·`lid_quartile.npy` 추가 |
| 2026-07-02 | Phase 0 v8 실행 환경 버그 수정 + 출력 완성도 보강 |
| 2026-07-02 | 0-A: `import os` + `os.makedirs('phase0', exist_ok=True)` 추가 — v1 이래 잠재된 첫 실행 FileNotFoundError 해소 |
| 2026-07-02 | 0-E-2: `gap_slices[k]`에 `'prune_flag'` 필드 추가 — COLLECT·PRUNE 신호 공존 시 맥락 보존 |
| 2026-07-02 | 0-E-2: `collect_candidates`에 `prune_flag` 전달 — Phase D PRUNE 후보 내 갭 케이스 처리 지원 |
| 2026-07-02 | 0-E-2: `synthetic_candidates`에 `gap_count`·`mean_lid` 추가 — EXP-004 합성 생성 단일 파일 완결 |
| 2026-07-02 | Phase 0 v15 해석 오류 방지 + 누락 기록 보완 |
| 2026-07-02 | 0-E-1: `vendi_per_clip` 제거 — 시나리오 크기 편향(소규모 시나리오 과대평가) 유발, `vendi_score` 절대값으로 충분 |
| 2026-07-02 | 0-E-1: `internal_redundancy` → `global_redundancy_in_dtrain` 명칭 교정 — 전역 k-NN 기반 지표임을 명시 (시나리오 내부 중복도 오해 방지) |
| 2026-07-02 | 0-E-2: `q2_effective_n` 주석 교정 — "수집 후 증가량" 오독 방지 → "현재 Q2 독립 정보량, 실제 증가량은 Phase D 측정"으로 명확화 |
| 2026-07-02 | 0-E-2: 스킵 시나리오 기록 추가 — `skipped_small_gaps.json` (gap>0 이지만 MIN_GAP_SIZE 미달로 분석 제외된 케이스 전수 추적) |
| 2026-07-02 | §7 산출물 목록: `skipped_small_gaps.json` 추가 |
| 2026-07-02 | Phase 0 v16 해석 맹점 3개 해소 |
| 2026-07-02 | 0-E-1: `vendi_anchor_used` + `vendi_reliable` 추가 — 소규모 시나리오 앵커 축소 시 비교 불가 상태 표기 (vendi_min_scenario 오해 방지) |
| 2026-07-02 | 0-E-1: `scenario_diversity_summary`에 `vendi_unreliable_count` 추가 — min/max 시나리오가 unreliable일 때 경보 |
| 2026-07-02 | 0-E-1: `boundary_sensitive_scenarios.json` 신규 — 전역 임계값 ±5% 이내 시나리오 추출 (0-D↔0-E-1 피드백 루프) |
| 2026-07-02 | 0-E-2: `synthetic_candidates`에 `partial_collect_flag`·`q2_effective_n`·`gap_q2_ratio`·`note` 추가 — mean_lid 집계에 묻히는 Q2 클립 부분 수집 가능성 보존 |
| 2026-07-02 | §7 산출물: `boundary_sensitive_scenarios.json` 추가, `scenario_diversity_summary.json` 설명에 `unreliable_count` 명시 |
| 2026-07-02 | Phase 0 v17 체인 단절 3개 해소 |
| 2026-07-02 | 0-D: Q4 완전 고립 클립 집계 추가 (`ISOLATION_THRESHOLD=0.8`) → `thresholds.json`에 `q4_isolated_clip_count` 저장 — 경계 불신뢰 vs 완전 고립 이질성 진단 |
| 2026-07-02 | 0-E-2: `_boundary_ids` 로드 추가 + `gap_slices`에 `boundary_sensitive` 플래그 전달 — `boundary_sensitive_scenarios.json`과 수동 조인 없이 Phase D에서 직접 식별 가능 |
| 2026-07-02 | 0-E-2: `uncertain_candidates`에 `gap_specific_terms`·`boundary_sensitive` 추가 — 수동 검토 시 `gap_slices.json` 별도 조회 없이 즉시 판단 |
