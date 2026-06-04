"""
EXP-002 Axis C — Fit a Masked Autoregressive Flow (MAF) on the 7D ODD space.

Compares NF vs KDE log-likelihood on a held-out test split (Axis C validation).

Run:
  # Fit MAF and compare against KDE baseline
  uv run python -m avdata.phase5.fit_normalizing_flow

  # Fit on subset (quick smoke test)
  uv run python -m avdata.phase5.fit_normalizing_flow --limit 5000 --epochs 20
"""
import argparse
import json
import pickle
import time
from pathlib import Path

import numpy as np

from avdata.config import (
    EXP002_RESULTS_DIR,
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


def load_odd_vectors(
    path: Path = ODD_CONTINUOUS_PATH,
    limit: int | None = None,
) -> tuple[np.ndarray, list[str]]:
    """Return (X, clip_ids) with only fully-observed rows."""
    data = json.loads(path.read_text())
    clip_ids, rows = [], []
    for cid, vec in data.items():
        row = [vec.get(k) for k in ODD_DIMS]
        if any(v is None for v in row):
            continue
        rows.append(row)
        clip_ids.append(cid)
        if limit and len(rows) >= limit:
            break
    X = np.array(rows, dtype=np.float32)
    print(f"  Loaded {len(X):,} fully-observed 7D ODD vectors")
    return X, clip_ids


def _train_maf(
    X_train: np.ndarray,
    n_flows: int = 8,
    hidden_features: int = 64,
    epochs: int = 100,
    batch_size: int = 512,
    lr: float = 1e-3,
) -> object:
    import torch
    import normflows as nf

    dim = X_train.shape[1]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  Training MAF on {device}  (dim={dim}, flows={n_flows}, epochs={epochs})")

    # Masked Autoregressive Flow
    flows = []
    for _ in range(n_flows):
        flows.append(nf.flows.MaskedAffineAutoregressive(dim, hidden_features))
        flows.append(nf.flows.LULinearPermute(dim))

    base = nf.distributions.DiagGaussian(dim)
    model = nf.NormalizingFlow(base, flows).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, epochs)

    X_t = torch.tensor(X_train, dtype=torch.float32, device=device)
    dataset = torch.utils.data.TensorDataset(X_t)
    loader  = torch.utils.data.DataLoader(
        dataset, batch_size=batch_size, shuffle=True
    )

    model.train()
    best_loss = float("inf")
    best_state = None

    for epoch in range(1, epochs + 1):
        epoch_loss = 0.0
        for (batch,) in loader:
            optimizer.zero_grad()
            loss = model.forward_kld(batch)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
            epoch_loss += loss.item() * len(batch)

        scheduler.step()
        avg_loss = epoch_loss / len(X_train)

        if avg_loss < best_loss:
            best_loss = avg_loss
            best_state = {k: v.cpu() for k, v in model.state_dict().items()}

        if epoch % 20 == 0 or epoch == 1:
            print(f"    epoch {epoch:3d}/{epochs}  loss={avg_loss:.4f}")

    model.load_state_dict(best_state)
    model.eval().cpu()
    return model


def _eval_nf_loglik(model, X: np.ndarray) -> float:
    import torch
    with torch.no_grad():
        X_t = torch.tensor(X, dtype=torch.float32)
        log_prob = model.log_prob(X_t)
    return float(log_prob.mean().item())


def _eval_kde_loglik(X_train: np.ndarray, X_test: np.ndarray) -> float:
    from sklearn.neighbors import KernelDensity
    # Silverman's rule bandwidth for 7D
    n, d = X_train.shape
    h = n ** (-1.0 / (d + 4))
    kde = KernelDensity(kernel="gaussian", bandwidth=h).fit(X_train)
    log_dens = kde.score_samples(X_test)
    return float(log_dens.mean())


def fit(
    limit: int | None = None,
    n_flows: int = 8,
    hidden: int = 64,
    epochs: int = 100,
    test_ratio: float = 0.1,
    output_path: Path = NF_MODEL_PATH,
):
    if not ODD_CONTINUOUS_PATH.exists():
        print(f"[ERROR] {ODD_CONTINUOUS_PATH} not found.")
        print("  Run first: uv run python -m avdata.phase3.extract_odd_continuous")
        return

    X, clip_ids = load_odd_vectors(limit=limit)
    if len(X) < 100:
        print(f"[ERROR] Only {len(X)} vectors — too few to fit NF. "
              "Run extract_odd_continuous first.")
        return

    # Train / test split
    rng  = np.random.default_rng(42)
    idx  = rng.permutation(len(X))
    n_test  = max(1, int(len(X) * test_ratio))
    idx_test, idx_train = idx[:n_test], idx[n_test:]
    X_train, X_test = X[idx_train], X[idx_test]
    ids_train = [clip_ids[i] for i in idx_train]
    print(f"  Train: {len(X_train):,}  Test: {len(X_test):,}")

    # ── Fit MAF ───────────────────────────────────────────────────────
    t0 = time.time()
    model = _train_maf(X_train, n_flows=n_flows, hidden_features=hidden, epochs=epochs)
    elapsed = time.time() - t0
    print(f"  MAF training: {elapsed:.0f}s")

    # ── Evaluate ──────────────────────────────────────────────────────
    nf_loglik  = _eval_nf_loglik(model, X_test)
    kde_loglik = _eval_kde_loglik(X_train, X_test)

    print(f"\n  ── Axis C Evaluation (test log-likelihood per sample) ──")
    print(f"     MAF : {nf_loglik:.4f}")
    print(f"     KDE : {kde_loglik:.4f}")
    if nf_loglik > kde_loglik:
        print("     ✓ PASS: MAF > KDE (NF is more accurate density estimator)")
    else:
        print("     ✗ FAIL: MAF <= KDE — check data scale / training config")

    # ── Save model bundle ─────────────────────────────────────────────
    bundle = {
        "model_state": {k: v.numpy() for k, v in model.state_dict().items()},
        "clip_ids_train": ids_train,
        "odd_dims": ODD_DIMS,
        "n_flows": n_flows,
        "hidden_features": hidden,
        "nf_test_loglik": nf_loglik,
        "kde_test_loglik": kde_loglik,
        "n_train": len(X_train),
        "n_test": len(X_test),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump(bundle, f)
    print(f"\n  → Model: {output_path}")

    # ── Save evaluation summary ────────────────────────────────────────
    eval_path = EXP002_RESULTS_DIR / "nf_eval.json"
    eval_path.write_text(json.dumps({
        "nf_test_loglik":  nf_loglik,
        "kde_test_loglik": kde_loglik,
        "pass": nf_loglik > kde_loglik,
        "n_train": len(X_train),
        "n_test":  len(X_test),
        "n_flows": n_flows,
        "epochs":  epochs,
    }, indent=2))
    print(f"  → Eval : {eval_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",   type=int, default=None)
    parser.add_argument("--flows",   type=int, default=8)
    parser.add_argument("--hidden",  type=int, default=64)
    parser.add_argument("--epochs",  type=int, default=100)
    args = parser.parse_args()
    fit(
        limit=args.limit,
        n_flows=args.flows,
        hidden=args.hidden,
        epochs=args.epochs,
    )
