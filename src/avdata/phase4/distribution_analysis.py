"""
Phase 4 — Distribution Analysis
  1. UMAP 2D projection of clip embeddings
  2. KDE density map (identify long-tail scenarios)
  3. ODD coverage matrix (Chodowiec 2026 style)
  4. Interactive Plotly visualisation → data/index/distribution.html

Run:
  uv run python -m avdata.phase4.distribution_analysis
  uv run python -m avdata.phase4.distribution_analysis --sample 10000
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from avdata.config import (
    CLIP_IDS_PATH,
    EMBEDDINGS_NPY_PATH,
    INDEX_DIR,
    ODD_TAGS_PATH,
)


def load_data(sample: int | None = None):
    clip_ids   = json.loads(CLIP_IDS_PATH.read_text())
    embeddings = np.load(EMBEDDINGS_NPY_PATH)
    odd_tags   = json.loads(ODD_TAGS_PATH.read_text())

    if sample and sample < len(clip_ids):
        rng     = np.random.default_rng(42)
        indices = rng.choice(len(clip_ids), size=sample, replace=False)
        clip_ids   = [clip_ids[i]   for i in indices]
        embeddings = embeddings[indices]

    return clip_ids, embeddings, odd_tags


def umap_project(embeddings: np.ndarray) -> np.ndarray:
    import umap
    reducer = umap.UMAP(n_components=2, n_neighbors=15,
                        min_dist=0.1, metric="cosine", random_state=42)
    return reducer.fit_transform(embeddings)


def kde_density(xy: np.ndarray) -> np.ndarray:
    from sklearn.neighbors import KernelDensity
    kde = KernelDensity(kernel="gaussian", bandwidth=0.3)
    kde.fit(xy)
    return np.exp(kde.score_samples(xy))


def build_odd_coverage_matrix(odd_tags: dict, clip_ids: list[str]) -> pd.DataFrame:
    """
    Rows: (time_of_day × weather) combinations
    Cols: ego_action
    Values: clip count
    """
    rows = []
    for cid in clip_ids:
        tags = odd_tags.get(cid, {})
        tod  = tags.get("time_of_day", "unknown")
        wx   = tags.get("weather",     "unknown")
        acts = tags.get("ego_action",  ["straight"])
        if isinstance(acts, str):
            acts = [acts]
        for act in acts:
            rows.append({"time_weather": f"{tod}×{wx}", "ego_action": act})

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame()
    return df.groupby(["time_weather", "ego_action"]).size().unstack(fill_value=0)


def analyse(sample: int | None = None):
    print("Loading data …")
    clip_ids, embeddings, odd_tags = load_data(sample)
    print(f"  {len(clip_ids):,} clips  embeddings={embeddings.shape}")

    # ── 1. UMAP ────────────────────────────────────────────────────────
    print("Running UMAP …")
    xy = umap_project(embeddings)

    # ── 2. KDE density ────────────────────────────────────────────────
    print("Computing KDE density …")
    density = kde_density(xy)

    # ── 3. Build metadata DataFrame ───────────────────────────────────
    records = []
    for i, cid in enumerate(clip_ids):
        tags = odd_tags.get(cid, {})
        records.append({
            "clip_id":      cid,
            "x":            float(xy[i, 0]),
            "y":            float(xy[i, 1]),
            "density":      float(density[i]),
            "time_of_day":  tags.get("time_of_day", "unknown"),
            "weather":      tags.get("weather",     "unknown"),
            "road_type":    tags.get("road_type",   "unknown"),
            "hazard_level": tags.get("hazard_level","unknown"),
            "agent_type":   str(tags.get("agent_type", [])),
        })
    df = pd.DataFrame(records)

    # ── 4. Plotly visualisation ────────────────────────────────────────
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "UMAP coloured by density (low = long-tail)",
            "UMAP coloured by time of day",
            "UMAP coloured by hazard level",
            "ODD coverage matrix (time×weather vs action)",
        ],
        specs=[[{"type": "scatter"}, {"type": "scatter"}],
               [{"type": "scatter"}, {"type": "heatmap"}]],
    )

    # ── subplot 1: density ────────────────────────────────────────────
    fig.add_trace(
        go.Scatter(
            x=df["x"], y=df["y"],
            mode="markers",
            marker=dict(color=df["density"], colorscale="Viridis",
                        size=3, opacity=0.6,
                        colorbar=dict(title="density", x=0.46)),
            text=df["clip_id"], name="density",
        ),
        row=1, col=1,
    )

    # ── subplot 2: time_of_day ────────────────────────────────────────
    for tod in df["time_of_day"].unique():
        sub = df[df["time_of_day"] == tod]
        fig.add_trace(
            go.Scatter(x=sub["x"], y=sub["y"], mode="markers",
                       marker=dict(size=3, opacity=0.5),
                       name=tod, legendgroup=tod),
            row=1, col=2,
        )

    # ── subplot 3: hazard_level ───────────────────────────────────────
    color_map = {"high": "red", "medium": "orange",
                 "low": "green", "none": "lightblue", "unknown": "grey"}
    for hl in df["hazard_level"].unique():
        sub = df[df["hazard_level"] == hl]
        fig.add_trace(
            go.Scatter(x=sub["x"], y=sub["y"], mode="markers",
                       marker=dict(size=3, opacity=0.5,
                                   color=color_map.get(hl, "grey")),
                       name=hl, legendgroup=hl, showlegend=False),
            row=2, col=1,
        )

    # ── subplot 4: ODD coverage heatmap ──────────────────────────────
    cov = build_odd_coverage_matrix(odd_tags, clip_ids)
    if not cov.empty:
        fig.add_trace(
            go.Heatmap(
                z=cov.values,
                x=list(cov.columns),
                y=list(cov.index),
                colorscale="Blues",
                name="ODD coverage",
            ),
            row=2, col=2,
        )

    fig.update_layout(
        title="AV Data Distribution Analysis",
        height=1200,
        width=1600,
    )

    out_html = INDEX_DIR / "distribution.html"
    fig.write_html(str(out_html))
    print(f"  → Interactive plot: {out_html}")

    # ── 5. Long-tail report ────────────────────────────────────────────
    threshold     = np.percentile(density, 5)   # bottom 5%
    longtail_ids  = [clip_ids[i] for i, d in enumerate(density) if d < threshold]
    longtail_path = INDEX_DIR / "longtail_clips.json"
    longtail_path.write_text(json.dumps(longtail_ids, ensure_ascii=False))
    print(f"  → Long-tail clips (bottom 5% density): {len(longtail_ids):,}  → {longtail_path}")

    # ── 6. Save 2D coordinates ────────────────────────────────────────
    df.to_parquet(INDEX_DIR / "umap_coords.parquet", index=False)
    print(f"  → UMAP coords: {INDEX_DIR / 'umap_coords.parquet'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=None,
                        help="Subsample N clips for faster iteration")
    args = parser.parse_args()
    analyse(sample=args.sample)
