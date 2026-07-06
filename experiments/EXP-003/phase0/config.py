"""Phase 0 전역 설정 — 경로와 알고리즘 파라미터만 관리"""

import os

# ── 경로 (여기만 수정) ──────────────────────────────────────
CAPTIONS_DIR = '/Data1/home/bskang/cds-data/caption_v3/captions'
# 출력 디렉터리: 이 파일 위치 기준 → 실행 위치와 무관하게 항상 같은 경로
OUTPUT_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
# ──────────────────────────────────────────────────────────────

# 0-A: FAISS k-NN
K_KNN = 50                    # LID 안정성용 (Ma et al. ICLR 2018: k ≥ 20 권장)

# 0-B: Effective N + Vendi
K_UNIQUENESS        = 20      # soft_commonness 측정 반경 (중복성)
K_DENSITY           = 10      # local_density 측정 반경 (즉각적 밀집도)
VENDI_ANCHOR_GLOBAL = 2000    # Nyström 앵커 수 (run당)

# 0-B: Vendi 반복 샘플링 — Sequential Stopping Rule (Law & Kelton 2000)
VENDI_MIN_RUNS       = 5     # 최소 실행 횟수 (파일럿)
VENDI_MAX_RUNS       = 30    # 안전 상한
VENDI_TARGET_CV      = 0.02  # 평균 상대 표준오차 수렴 기준 (2%)
VENDI_SUPPRESSION_HIGH = 2.0  # 억압 계수 이 값 이상 → COLLECT_HIGH_PRIORITY 승격

# 0-C: LID
K_LID                = 20     # Ma et al. MLE 추정에 사용하는 이웃 수
LID_RELIABLE_RMAX    = 0.6    # r_max_dist 상한 (초과 시 LID 불안정 → Q4/Q5)

# 0-D: 6-분류 Action Map
ISOLATION_THRESHOLD  = 0.8    # Q4 고립 진단 (r_max_dist > 이 값 = 임베딩 공간 고립)
BOUNDARY_MARGIN_LID  = 0.15   # lid_margin ±15% → lid_boundary_zone

# 0-D-val: FLIPD 트리거
K_SENSITIVE_THRESHOLD  = 0.05
Q3_BOUNDARY_THRESHOLD  = 0.3

# 0-E-1: 시나리오 의미 지도
VENDI_ANCHOR_SCENARIO  = 200
SIL_K_CANDIDATES       = [6, 8, 10, 12, 15]
SIL_FLAT_THRESHOLD     = 0.02   # 실루엣 점수 범위 < 이 값이면 K=12 도메인 지식 폴백
K_SCENARIO_FALLBACK    = 12
MIN_HEALTHY_SIZE       = 500    # Phase B null hypothesis 안정성 최소 클립 수
MIN_Q0_PCT             = 40     # healthy_scenarios Q0 지배도 최소 비율
BOUNDARY_MARGIN_SCENARIO = 0.05 # 시나리오 mean 임계값 민감 판정 ±5%
Q5_CONCENTRATION_MULT  = 2.0    # Q5 집중 판정 (전역 Q5 비율 × 이 배수)
PRUNE_DOMINANT_MULT    = 1.5    # PRUNE 우세 판정 (전역 Q1+Q5 비율 × 이 배수)

# ODD 다양성 분석 (0-B 전역, 0-E-1 시나리오별)
ODD_DIR            = '/Data1/home/bskang/cds-data/caption_v3/odd'
ODD_DIMS           = ['road_type', 'weather', 'traffic_density', 'agent_type',
                      'lighting', 'scene_ambiguity', 'road_divider']
ODD_SPEARMAN_PAIRS = 5000  # 임베딩–ODD 정렬 검증용 샘플 쌍 수

# 0-E-2: 갭 슬라이스
GAP_RATIO_HIGH_PRIORITY = 0.4  # 시나리오 내 갭 비율 초과 → COLLECT_HIGH_PRIORITY
LID_UNCERTAIN_RATIO     = 0.4  # lid_reliable 비율 미만 → UNCERTAIN_CHECK_SEMANTIC
MIN_GAP_SIZE            = 50   # LID MLE k=20 기반 안정적 mean_lid 최소 클립 수
