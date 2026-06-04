"""
Project-wide paths and constants.
All scripts import from here — change paths in ONE place.
"""
from pathlib import Path

# ── Data sources ──────────────────────────────────────────────────────────────
DATA_ROOT       = Path("/Data1/home/bskang/cds-data")
VIDEOS_DIR      = DATA_ROOT / "front_camera_videos"
CAPTIONS_DIR    = DATA_ROOT / "captions"

# Caption filename suffix  →  {uuid}.camera_front_wide_120fov.txt
CAPTION_SUFFIX  = ".camera_front_wide_120fov.txt"
VIDEO_SUFFIX    = ".camera_front_wide_120fov.mp4"

# ── Project outputs ────────────────────────────────────────────────────────────
PROJECT_ROOT    = Path(__file__).parents[2]          # repo root
DATA_DIR        = PROJECT_ROOT / "data"
INDEX_DIR       = DATA_DIR / "index"
TAGS_DIR        = DATA_DIR / "tags"
EVAL_DIR        = DATA_DIR / "eval"
EXPERIMENTS_DIR = PROJECT_ROOT / "experiments"

for _d in (INDEX_DIR, TAGS_DIR, EVAL_DIR, EXPERIMENTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ── Pipeline build paths (phase1~4 write here) ────────────────────────────────
# 실험 파이프라인은 항상 data/index/, data/tags/ 에 씀.
# 완료 후 scripts/snapshot_artifacts.sh 로 data/artifacts/exp-NNN/ 에 스냅샷.
BM25_INDEX_DIR      = INDEX_DIR / "bm25s_index"
CLIP_IDS_PATH       = INDEX_DIR / "clip_ids.json"
EMBEDDINGS_NPY_PATH = INDEX_DIR / "embeddings.npy"
FAISS_INDEX_PATH    = INDEX_DIR / "hnsw.index"
ODD_TAGS_PATH       = TAGS_DIR  / "odd_tags.json"
EVAL_SET_PATH       = EVAL_DIR  / "eval_set.json"

# ── EXP-002 paths ──────────────────────────────────────────────────────────────
EXP002_DIR              = EXPERIMENTS_DIR / "EXP-002"
EXP002_RESULTS_DIR      = EXP002_DIR / "results"
QUERIES_V2_PATH         = EVAL_DIR / "queries_v2.json"
EVAL_SET_V2_PATH        = EVAL_DIR / "eval_set_v2.json"
ODD_CONTINUOUS_PATH     = TAGS_DIR / "odd_continuous.json"
NF_MODEL_PATH           = EXP002_RESULTS_DIR / "nf_model.pkl"
GAP_REPORT_PATH         = EXP002_RESULTS_DIR / "gap_report.json"

for _d in (EXP002_RESULTS_DIR,):
    _d.mkdir(parents=True, exist_ok=True)

# ── Phase 6 (EXP-002 Phase A) output paths ────────────────────────────────────
ODD_COVERAGE_PATH    = EXP002_RESULTS_DIR / "odd_coverage_matrix.json"
CLUSTER_UMAP_PATH    = EXP002_RESULTS_DIR / "umap_10d.npy"
CLUSTER_LABELS_PATH  = EXP002_RESULTS_DIR / "cluster_labels.npy"
CLUSTER_ANALYSIS_PATH = EXP002_RESULTS_DIR / "cluster_analysis.json"

# ── Active artifact paths (Searcher + API read from here) ─────────────────────
# data/active 는 data/artifacts/exp-NNN 을 가리키는 심볼릭 링크.
# 실험 전환: ln -sfn artifacts/exp-NNN data/active  (서버 재시작 불필요)
ACTIVE_DIR          = DATA_DIR / "active"

# ── Embedding model ────────────────────────────────────────────────────────────
EMBED_MODEL_NAME    = "BAAI/bge-m3"          # multilingual, 8192-token
EMBED_BATCH_SIZE    = 32                     # 64 still OOM with 5k-token captions (O(n²) attn)
EMBED_DIM           = 1024                   # bge-m3 output dim

# ── Faiss HNSW ────────────────────────────────────────────────────────────────
HNSW_M              = 32
HNSW_EF_CONSTRUCTION = 200
HNSW_EF_SEARCH      = 128

# ── ODD taxonomy (for tag extraction & coverage matrix) ───────────────────────
ODD_FIELDS = {
    "time_of_day":    ["day", "night", "dawn", "dusk"],
    "weather":        ["clear", "cloudy", "rain", "snow", "fog"],
    "road_type":      ["highway", "urban", "intersection", "parking_lot",
                       "rural", "tunnel", "bridge"],
    "traffic_density":["free", "moderate", "congested"],
    "agent_type":     ["pedestrian", "cyclist", "motorcycle", "truck",
                       "bus", "emergency_vehicle", "animal", "none"],
    "hazard_level":   ["none", "low", "medium", "high"],
    "ego_action":     ["straight", "left_turn", "right_turn", "uturn",
                       "lane_change", "braking", "stopping", "reversing"],
}
