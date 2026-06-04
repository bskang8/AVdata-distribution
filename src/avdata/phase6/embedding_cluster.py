"""
Phase 6 Step 3: Embedding Clustering + Metric Space Magnitude + LLM labeling

Pipeline:
  1. Load embeddings.npy (N, 1024) from data/active/
  2. PCA(50D) dimensionality reduction
  3. UMAP(10D) structure-preserving projection (cached to umap_10d.npy)
  4. HDBSCAN clustering
  5. Metric Space Magnitude per cluster (diversity measure)
  6. LLM label bottom-50 clusters by size (rarest = potential gaps)

Run:
  uv run python -m avdata.phase6.embedding_cluster
  uv run python -m avdata.phase6.embedding_cluster --no-llm
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np

from avdata.config import (
    ACTIVE_DIR,
    CAPTIONS_DIR,
    CAPTION_SUFFIX,
    CLUSTER_ANALYSIS_PATH,
    CLUSTER_LABELS_PATH,
    CLUSTER_UMAP_PATH,
)


def metric_space_magnitude(X: np.ndarray, t: float = 1.0) -> float:
    """Effective number of distinct points: Mag(X,t) = Σwᵢ where Z·w = 1, Z[i,j] = exp(-t·d(i,j))."""
    dists = np.linalg.norm(X[:, None] - X[None, :], axis=-1)
    Z = np.exp(-t * dists)
    try:
        w = np.linalg.solve(Z, np.ones(len(X)))
        return float(np.sum(w))
    except np.linalg.LinAlgError:
        return float(len(X))


def load_captions(clip_ids: list[str], n: int = 3) -> list[str]:
    texts = []
    for cid in clip_ids[:n * 3]:  # try more in case some are missing
        p = CAPTIONS_DIR / f"{cid}{CAPTION_SUFFIX}"
        if p.exists():
            texts.append(p.read_text(encoding="utf-8").strip()[:400])
            if len(texts) == n:
                break
    return texts


def llm_label_clusters(clusters_to_label: list[dict]) -> dict[int, str]:
    from openai import OpenAI
    client = OpenAI()  # OPENAI_API_KEY 자동 읽음
    labels: dict[int, str] = {}

    for i, c in enumerate(clusters_to_label):
        captions = load_captions(c["clip_ids_sample"])
        if not captions:
            labels[c["cluster_id"]] = "unknown (no captions)"
            continue

        caption_block = "\n".join(f"- {cap}" for cap in captions)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=64,
            messages=[{
                "role": "user",
                "content": (
                    "You are an autonomous driving scenario analyst. "
                    "Based on these driving scenario captions, output a concise 5-10 word label "
                    "describing the scenario type (e.g. 'highway merging in heavy fog at night'). "
                    "Only output the label.\n\n"
                    f"Captions:\n{caption_block}"
                ),
            }],
        )
        label = resp.choices[0].message.content.strip()
        labels[c["cluster_id"]] = label
        print(f"  [{i+1:2d}/{len(clusters_to_label)}] cluster {c['cluster_id']:4d} "
              f"(n={c['size']:5d}): {label}")
        time.sleep(0.05)

    return labels


def run(use_llm: bool = True) -> None:
    print("Step 1: Loading embeddings …")
    X = np.load(str(ACTIVE_DIR / "embeddings.npy")).astype(np.float32)
    clip_ids: list[str] = json.loads((ACTIVE_DIR / "clip_ids.json").read_text())
    N = len(X)
    print(f"  {N:,} embeddings, dim={X.shape[1]}")

    print("Step 2: PCA(50D) …")
    from sklearn.decomposition import PCA
    pca = PCA(n_components=50, random_state=42)
    X_pca = pca.fit_transform(X)
    print(f"  Explained variance: {pca.explained_variance_ratio_.sum():.3f}")

    print("Step 3: UMAP(10D) …")
    if CLUSTER_UMAP_PATH.exists():
        X_umap = np.load(str(CLUSTER_UMAP_PATH))
        print(f"  Loaded from cache: {CLUSTER_UMAP_PATH}")
    else:
        import umap as umap_lib
        reducer = umap_lib.UMAP(
            n_components=10, n_neighbors=30, min_dist=0.0, metric="cosine",
            random_state=42, low_memory=True,
        )
        X_umap = reducer.fit_transform(X_pca).astype(np.float32)
        CLUSTER_UMAP_PATH.parent.mkdir(parents=True, exist_ok=True)
        np.save(str(CLUSTER_UMAP_PATH), X_umap)
        print(f"  Saved → {CLUSTER_UMAP_PATH}")

    print("Step 4: HDBSCAN clustering …")
    from sklearn.cluster import HDBSCAN
    hdb = HDBSCAN(min_cluster_size=50, min_samples=10)
    labels_arr = hdb.fit_predict(X_umap)
    CLUSTER_LABELS_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.save(str(CLUSTER_LABELS_PATH), labels_arr)

    unique_labels = [l for l in sorted(set(labels_arr)) if l >= 0]
    n_noise = int((labels_arr == -1).sum())
    print(f"  Clusters: {len(unique_labels)},  Noise: {n_noise:,} ({n_noise/N:.1%})")

    print("Step 5: Metric Space Magnitude per cluster …")
    rng = np.random.default_rng(42)
    cluster_stats: list[dict] = []

    for lbl in unique_labels:
        idx = np.where(labels_arr == lbl)[0]
        members = [clip_ids[i] for i in idx]
        X_c = X_umap[idx]

        # Sample up to 200 for magnitude (O(n²) solve)
        if len(X_c) > 200:
            s_idx = rng.choice(len(X_c), 200, replace=False)
            X_sample = X_c[s_idx]
            sample_ids = [members[i] for i in s_idx]
        else:
            X_sample = X_c
            sample_ids = members

        mag = metric_space_magnitude(X_sample, t=1.0)
        cluster_stats.append({
            "cluster_id":      int(lbl),
            "size":            len(members),
            "magnitude":       round(mag, 4),
            "mag_per_clip":    round(mag / max(len(X_sample), 1), 4),
            "clip_ids_sample": sample_ids[:10],
            "llm_label":       "",
        })

    cluster_stats.sort(key=lambda x: x["size"])
    print(f"  Computed for {len(cluster_stats)} clusters")

    bottom_50 = cluster_stats[:50]

    if use_llm and bottom_50:
        print(f"Step 6: LLM labeling {len(bottom_50)} smallest clusters …")
        llm_labels = llm_label_clusters(bottom_50)
        for c in cluster_stats:
            if c["cluster_id"] in llm_labels:
                c["llm_label"] = llm_labels[c["cluster_id"]]

    output = {
        "n_total":    N,
        "n_clusters": len(unique_labels),
        "n_noise":    n_noise,
        "noise_rate": round(n_noise / N, 4),
        "clusters":   cluster_stats,
        "bottom_50_gap_candidates": bottom_50,
    }
    CLUSTER_ANALYSIS_PATH.parent.mkdir(parents=True, exist_ok=True)
    CLUSTER_ANALYSIS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n→ {CLUSTER_ANALYSIS_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-llm", action="store_true")
    args = parser.parse_args()
    run(use_llm=not args.no_llm)
