"""
EXP-002 Axis C — Gap detection in 7D ODD space using the trained NF.

Gap score:
  gap_score = (1 / density) × hazard_proximity × real_world_freq_weight

real_world_freq_weight: domain-knowledge prior for each ODD region.
  High weight = rare in real-world but important to cover.
  e.g. (fog + highway) has high weight; (clear + parking) has low weight.

Run:
  uv run python -m avdata.phase5.detect_gaps
  uv run python -m avdata.phase5.detect_gaps --hazard-threshold 0.5 --top-n 200
"""
import argparse
import json
import pickle
from pathlib import Path

import numpy as np

from avdata.config import (
    EXP002_RESULTS_DIR,
    GAP_REPORT_PATH,
    NF_MODEL_PATH,
    ODD_CONTINUOUS_PATH,
)

ODD_DIMS = [
    "visibility_level",
    "precipitation_intensity",
    "traffic_density_cont",
    "hazard_proximity",
    "agent_density",
    "lighting_level",
    "road_type_encoded",
]

# Real-world frequency weight: lower visibility + higher road speed → higher weight.
# Encodes domain prior: these gaps are dangerous AND under-represented in datasets.
def _freq_weight(vec: np.ndarray) -> float:
    vis   = float(vec[0])   # visibility_level
    precip= float(vec[1])   # precipitation_intensity
    road  = float(vec[6])   # road_type_encoded (highway ≈ 0.92)
    # Fog on highway: very dangerous, should be high weight
    # Clear parking lot: not dangerous, low weight
    return (1.0 - vis) * 0.4 + precip * 0.3 + road * 0.3


def load_nf_model(path: Path = NF_MODEL_PATH):
    import torch
    import normflows as nf

    with open(path, "rb") as f:
        bundle = pickle.load(f)

    dim     = len(ODD_DIMS)
    n_flows = bundle["n_flows"]
    hidden  = bundle["hidden_features"]

    flows = []
    for _ in range(n_flows):
        flows.append(nf.flows.MaskedAffineAutoregressive(dim, hidden))
        flows.append(nf.flows.LULinearPermute(dim))

    base  = nf.distributions.DiagGaussian(dim)
    model = nf.NormalizingFlow(base, flows)

    state = {k: torch.tensor(v) for k, v in bundle["model_state"].items()}
    model.load_state_dict(state)
    model.eval()
    return model, bundle


def detect(
    hazard_threshold: float = 0.7,
    top_n: int = 100,
    output_path: Path = GAP_REPORT_PATH,
):
    if not NF_MODEL_PATH.exists():
        print(f"[ERROR] NF model not found: {NF_MODEL_PATH}")
        print("  Run first: uv run python -m avdata.phase5.fit_normalizing_flow")
        return

    if not ODD_CONTINUOUS_PATH.exists():
        print(f"[ERROR] ODD continuous vectors not found: {ODD_CONTINUOUS_PATH}")
        return

    import torch

    print(f"Loading NF model from {NF_MODEL_PATH} …")
    model, bundle = load_nf_model()
    print(f"  Model: {bundle['n_flows']} flows, "
          f"trained on {bundle['n_train']:,} clips")

    # ── Load all ODD vectors ───────────────────────────────────────────
    print(f"Loading ODD vectors from {ODD_CONTINUOUS_PATH} …")
    data = json.loads(ODD_CONTINUOUS_PATH.read_text())
    clip_ids, rows = [], []
    for cid, vec in data.items():
        row = [vec.get(k) for k in ODD_DIMS]
        if any(v is None for v in row):
            continue
        rows.append(row)
        clip_ids.append(cid)

    X = np.array(rows, dtype=np.float32)
    print(f"  {len(X):,} fully-observed clips")

    # ── Conditional filter: hazard_proximity > threshold ──────────────
    hazard_idx = ODD_DIMS.index("hazard_proximity")
    hazard_mask = X[:, hazard_idx] >= hazard_threshold
    X_hazard     = X[hazard_mask]
    ids_hazard   = [clip_ids[i] for i, m in enumerate(hazard_mask) if m]
    print(f"  High-hazard clips (≥{hazard_threshold}): {len(X_hazard):,}")

    if len(X_hazard) == 0:
        print("[WARN] No clips meet hazard threshold. Lower --hazard-threshold.")
        return

    # ── Compute log-density for high-hazard clips ─────────────────────
    with torch.no_grad():
        X_t     = torch.tensor(X_hazard, dtype=torch.float32)
        log_dens = model.log_prob(X_t).numpy()  # shape: (N,)

    # ── Gap score ─────────────────────────────────────────────────────
    # gap_score = (1/density) × hazard_proximity × freq_weight
    # Use -log_density as the "rarity" signal (more negative log_dens = rarer)
    density_rank = -log_dens  # higher = rarer in the overall ODD distribution

    gap_scores = np.array([
        density_rank[i]
        * X_hazard[i, hazard_idx]
        * _freq_weight(X_hazard[i])
        for i in range(len(X_hazard))
    ])

    top_idx = np.argsort(gap_scores)[::-1][:top_n]

    # ── Build report ──────────────────────────────────────────────────
    gap_clips = []
    for rank, i in enumerate(top_idx):
        vec = X_hazard[i]
        gap_clips.append({
            "rank":            rank + 1,
            "clip_id":         ids_hazard[i],
            "gap_score":       round(float(gap_scores[i]), 4),
            "log_density":     round(float(log_dens[i]),   4),
            "odd": {
                dim: round(float(vec[j]), 3)
                for j, dim in enumerate(ODD_DIMS)
            },
        })

    # Cluster summary: characterize gap regions by dominant ODD features
    def _describe_region(clips: list[dict]) -> dict:
        mean_odd = {}
        for dim in ODD_DIMS:
            vals = [c["odd"][dim] for c in clips]
            mean_odd[dim] = round(float(np.mean(vals)), 3)
        return mean_odd

    top20 = gap_clips[:20]
    region_desc = _describe_region(top20)

    report = {
        "config": {
            "hazard_threshold": hazard_threshold,
            "top_n": top_n,
            "nf_train_clips": bundle["n_train"],
            "nf_test_loglik":  bundle["nf_test_loglik"],
            "kde_test_loglik": bundle["kde_test_loglik"],
        },
        "stats": {
            "total_clips":       len(X),
            "high_hazard_clips": len(X_hazard),
            "gap_score_max":     round(float(gap_scores.max()), 4),
            "gap_score_mean":    round(float(gap_scores.mean()), 4),
        },
        "top_gap_region_mean_odd": region_desc,
        "gap_clips": gap_clips,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    print(f"\n  ── Top Gap Clips (ODD mean, rank 1–20) ──")
    for dim, val in region_desc.items():
        print(f"    {dim:<30} {val:.3f}")
    print(f"\n  → Gap report: {output_path}  ({len(gap_clips)} clips)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hazard-threshold", type=float, default=0.7)
    parser.add_argument("--top-n",            type=int,   default=100)
    parser.add_argument("--output",           type=Path,  default=GAP_REPORT_PATH)
    args = parser.parse_args()
    detect(
        hazard_threshold=args.hazard_threshold,
        top_n=args.top_n,
        output_path=args.output,
    )
