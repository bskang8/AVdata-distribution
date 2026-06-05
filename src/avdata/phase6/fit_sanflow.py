"""
EXP-002 Phase B — SANFlow: Semantic-Aware Normalizing Flow on 10D UMAP space

표준 NF(단일 Gaussian base) 대신 Phase A HDBSCAN 클러스터별 Gaussian을 base로 사용.
각 클립 x는 자신이 속한 클러스터 k의 N(μ_k, Σ_k) 로 매핑됨 → 갭 탐지 후 클러스터
역추적으로 시나리오 이름 출력 가능.

Loss = -E_x[ log p_{z_k(x)}(f⁻¹(x)) + log|det J_{f⁻¹}(x)| ]

입력 공간: umap_10d.npy  (299180, 10) — Phase A UMAP 10D
클러스터:  cluster_labels.npy         — HDBSCAN (-1=noise → bucket K)
레이블:    cluster_analysis.json      — LLM 시나리오 레이블 (50/124개)

Run:
  uv run python -m avdata.phase6.fit_sanflow
  uv run python -m avdata.phase6.fit_sanflow --epochs 50 --limit 50000
  uv run python -m avdata.phase6.fit_sanflow --no-train   # 저장된 모델로 갭만 재탐지
"""
import argparse
import json
import pickle
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from torch.distributions import Normal

from avdata.config import (
    CLIP_IDS_PATH,
    CLUSTER_ANALYSIS_PATH,
    CLUSTER_LABELS_PATH,
    CLUSTER_UMAP_PATH,
    EXP002_RESULTS_DIR,
    SANFLOW_GAP_PATH,
    SANFLOW_MODEL_PATH,
)


# ════════════════════════════════════════════════════════════════════════════════
# Cluster-aware base distribution
# ════════════════════════════════════════════════════════════════════════════════

class ClusterGaussianBase(nn.Module):
    """
    SANFlow base: 클러스터 k마다 독립적인 대각 Gaussian N(μ_k, diag(σ_k²)).
    μ_k, log σ_k 는 학습 파라미터 — NF 와 함께 joint fine-tune.
    """

    def __init__(self, means: torch.Tensor, log_stds: torch.Tensor):
        super().__init__()
        self.means    = nn.Parameter(means)     # (K, D)
        self.log_stds = nn.Parameter(log_stds)  # (K, D)

    @property
    def K(self) -> int:
        return self.means.shape[0]

    def log_prob(self, z: torch.Tensor, cids: torch.Tensor) -> torch.Tensor:
        """(N, D), (N,) → (N,)  — 각 샘플에 할당된 클러스터의 log p(z)"""
        mu  = self.means[cids]                      # (N, D)
        std = self.log_stds[cids].exp() + 1e-6      # (N, D)
        return Normal(mu, std).log_prob(z).sum(-1)  # (N,)

    def nearest(self, z: torch.Tensor) -> torch.Tensor:
        """(N, D) → (N,)  — z 에서 가장 가까운 클러스터 인덱스"""
        dists = torch.cdist(z.cpu(), self.means.cpu())  # (N, K)
        return dists.argmin(dim=1)


# ════════════════════════════════════════════════════════════════════════════════
# Flow utilities
# ════════════════════════════════════════════════════════════════════════════════

def _eval_direction(flows: nn.ModuleList, x: torch.Tensor):
    """
    데이터 x → latent z  (평가 방향, normflows convention).
    flows 는 생성 방향(z→x)으로 정의되므로 역순으로 inverse() 적용.
    반환: (z, log_det)  log_det = log|det ∂z/∂x|
    """
    z = x
    log_det = torch.zeros(len(x), device=x.device)
    for flow in reversed(list(flows)):
        z, ld = flow.inverse(z)
        log_det = log_det + ld
    return z, log_det


# ════════════════════════════════════════════════════════════════════════════════
# Data loading
# ════════════════════════════════════════════════════════════════════════════════

def load_data(limit: int | None = None):
    print("Loading Phase A outputs …")
    X        = np.load(str(CLUSTER_UMAP_PATH))          # (N, 10)
    labels   = np.load(str(CLUSTER_LABELS_PATH))         # (N,)  -1..123
    clip_ids = json.loads(CLIP_IDS_PATH.read_text())

    if limit:
        rng  = np.random.default_rng(42)
        idx  = rng.choice(len(X), limit, replace=False)
        X, labels = X[idx], labels[idx]
        clip_ids  = [clip_ids[i] for i in idx]

    K = int(labels.max()) + 1   # 0..123 → K=124
    # noise(-1) → 별도 bucket K (index 124)
    labels_mapped = labels.copy()
    labels_mapped[labels_mapped == -1] = K

    n_noise = (labels == -1).sum()
    print(f"  clips={len(X):,}  K={K} clusters  noise={n_noise:,}")
    return X.astype(np.float32), labels_mapped, clip_ids, K


# ════════════════════════════════════════════════════════════════════════════════
# Cluster Gaussian initialization
# ════════════════════════════════════════════════════════════════════════════════

def build_cluster_gaussians(
    X: np.ndarray, labels: np.ndarray, K_total: int
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    K_total = K(클러스터) + 1(noise bucket).
    데이터 수 < 5인 클러스터는 전체 통계로 폴백.
    """
    D = X.shape[1]
    means    = np.zeros((K_total, D), dtype=np.float32)
    log_stds = np.zeros((K_total, D), dtype=np.float32)

    global_mean = X.mean(0)
    global_std  = X.std(0) + 1e-6

    for k in range(K_total):
        mask = labels == k
        if mask.sum() < 5:
            means[k]    = global_mean
            log_stds[k] = np.log(global_std)
        else:
            Xk          = X[mask]
            means[k]    = Xk.mean(0)
            log_stds[k] = np.log(Xk.std(0) + 1e-6)

    return torch.tensor(means), torch.tensor(log_stds)


# ════════════════════════════════════════════════════════════════════════════════
# Training
# ════════════════════════════════════════════════════════════════════════════════

def train_sanflow(
    X_train: np.ndarray,
    cids_train: np.ndarray,
    K_total: int,
    n_flows: int = 6,
    hidden: int = 128,
    epochs: int = 100,
    batch_size: int = 1024,
    lr: float = 1e-3,
) -> tuple[nn.ModuleList, ClusterGaussianBase]:
    import normflows as nf

    dim    = X_train.shape[1]   # 10
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  device={device}  dim={dim}  K_total={K_total}  "
          f"flows={n_flows}  hidden={hidden}  epochs={epochs}")

    # ── Base distribution ────────────────────────────────────────────────────
    means, log_stds = build_cluster_gaussians(X_train, cids_train, K_total)
    base = ClusterGaussianBase(means, log_stds).to(device)

    # ── MAF layers (생성 방향: z → x) ───────────────────────────────────────
    flow_list = nn.ModuleList()
    for _ in range(n_flows):
        flow_list.append(nf.flows.MaskedAffineAutoregressive(dim, hidden))
        flow_list.append(nf.flows.LULinearPermute(dim))
    flow_list = flow_list.to(device)

    # ── Optimizer: flow + base μ/σ joint ────────────────────────────────────
    optimizer = torch.optim.Adam(
        list(flow_list.parameters()) + list(base.parameters()), lr=lr,
        weight_decay=1e-5,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, epochs)

    # ── DataLoader ───────────────────────────────────────────────────────────
    loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(
            torch.tensor(X_train, dtype=torch.float32),
            torch.tensor(cids_train, dtype=torch.long),
        ),
        batch_size=batch_size, shuffle=True, pin_memory=(device.type == "cuda"),
    )

    # ── Training loop ────────────────────────────────────────────────────────
    best_loss, best_state = float("inf"), None

    for epoch in range(1, epochs + 1):
        flow_list.train(); base.train()
        ep_loss = 0.0

        for bx, bc in loader:
            bx, bc = bx.to(device), bc.to(device)
            optimizer.zero_grad()

            z, log_det = _eval_direction(flow_list, bx)
            log_p      = base.log_prob(z, bc)
            loss       = -(log_p + log_det).mean()

            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                list(flow_list.parameters()) + list(base.parameters()), 5.0
            )
            optimizer.step()
            ep_loss += loss.item() * len(bx)

        scheduler.step()
        avg = ep_loss / len(X_train)
        if avg < best_loss:
            best_loss = avg
            best_state = {
                "flows": {k: v.cpu().clone() for k, v in flow_list.state_dict().items()},
                "base":  {k: v.cpu().clone() for k, v in base.state_dict().items()},
            }

        if epoch % 10 == 0 or epoch == 1:
            print(f"    epoch {epoch:3d}/{epochs}  loss={avg:.4f}  best={best_loss:.4f}")

    # best checkpoint 복원
    flow_list.cpu(); base.cpu()
    flow_list.load_state_dict(best_state["flows"])
    base.load_state_dict(best_state["base"])
    flow_list.eval(); base.eval()
    print(f"  best loss={best_loss:.4f}")
    return flow_list, base


# ════════════════════════════════════════════════════════════════════════════════
# Gap detection + cluster backtracking
# ════════════════════════════════════════════════════════════════════════════════

def detect_gaps(
    flow_list: nn.ModuleList,
    base: ClusterGaussianBase,
    X_sc: np.ndarray,
    clip_ids: list[str],
    labels_mapped: np.ndarray,
    cluster_analysis: dict,
    top_n: int = 200,
) -> list[dict]:
    """
    전체 데이터셋에 대해 log-density 계산 → 하위 top_n = 갭 후보.

    역추적 전략 (후보 C — HDBSCAN 우선 + UMAP nearest 보완):
      - original_cluster != -1 → HDBSCAN 레이블 직접 사용 (재학습 불필요)
      - original_cluster == -1 → UMAP(X_sc) 공간 nearest cluster 탐색
    log_density 계산은 latent z 공간 (SANFlow 본래 목적) 그대로 유지.
    """
    label_map: dict[int, str] = {
        c["cluster_id"]: c["llm_label"] or f"cluster_{c['cluster_id']}"
        for c in cluster_analysis["clusters"]
    }
    K_clusters = base.K - 1   # noise bucket은 마지막 인덱스 (= K)

    flow_list.eval(); base.eval()

    # ── UMAP 공간 클러스터 중심 (noise 포인트 역추적용) ──────────────────────────
    # noise bucket(K_clusters) 제외, 클러스터 0..K_clusters-1 의 X_sc 평균
    cluster_means_umap = np.stack([
        X_sc[labels_mapped == k].mean(axis=0)
        for k in range(K_clusters)
    ])  # (K_clusters, D)

    # ── log-density 배치 계산 ────────────────────────────────────────────────────
    CHUNK = 8192
    log_dens_list = []

    with torch.no_grad():
        for start in range(0, len(X_sc), CHUNK):
            bx = torch.tensor(X_sc[start:start + CHUNK], dtype=torch.float32)
            z, ld = _eval_direction(flow_list, bx)
            nk    = base.nearest(z)          # z 공간 nearest (log_prob 계산 전용)
            lp    = base.log_prob(z, nk)
            log_dens_list.append((lp + ld).numpy())

    log_dens = np.concatenate(log_dens_list)   # (N,)
    gap_idx  = np.argsort(log_dens)[:top_n]

    # ── noise 갭 포인트에 대해 UMAP-space nearest cluster 일괄 계산 ─────────────
    noise_mask = labels_mapped[gap_idx] == K_clusters
    noise_positions = X_sc[gap_idx[noise_mask]]   # (n_noise, D)

    if len(noise_positions) > 0:
        dists = np.linalg.norm(
            noise_positions[:, None, :] - cluster_means_umap[None, :, :],
            axis=-1,
        )  # (n_noise, K_clusters)
        umap_nearest = dists.argmin(axis=1)   # (n_noise,)
    else:
        umap_nearest = np.array([], dtype=int)

    # ── 결과 조립 ────────────────────────────────────────────────────────────────
    noise_ptr = 0
    results = []
    for rank, i in enumerate(gap_idx):
        orig_lbl = int(labels_mapped[i])
        is_noise = (orig_lbl == K_clusters)

        if is_noise:
            assigned_k = int(umap_nearest[noise_ptr])
            noise_ptr += 1
        else:
            assigned_k = orig_lbl   # HDBSCAN 레이블이 곧 정답

        results.append({
            "rank":             rank + 1,
            "clip_id":          clip_ids[i],
            "log_density":      round(float(log_dens[i]), 4),
            "nearest_cluster":  assigned_k,
            "scenario_name":    label_map.get(assigned_k, f"cluster_{assigned_k}"),
            "original_cluster": -1 if is_noise else orig_lbl,
            "is_noise":         bool(is_noise),
        })

    return results


# ════════════════════════════════════════════════════════════════════════════════
# Model I/O helpers
# ════════════════════════════════════════════════════════════════════════════════

def save_model(
    flow_list, base, scaler, meta: dict,
    path: Path = SANFLOW_MODEL_PATH,
):
    bundle = {
        "flows_state": {k: v.numpy() for k, v in flow_list.state_dict().items()},
        "base_state":  {k: v.numpy() for k, v in base.state_dict().items()},
        "scaler":      scaler,
        **meta,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(bundle, f)
    print(f"  → model: {path}")


def load_model(path: Path = SANFLOW_MODEL_PATH):
    import normflows as nf

    with open(path, "rb") as f:
        bundle = pickle.load(f)

    dim, K_total, n_flows, hidden = (
        bundle["dim"], bundle["K_total"],
        bundle["n_flows"], bundle["hidden"],
    )

    flow_list = nn.ModuleList()
    for _ in range(n_flows):
        flow_list.append(nf.flows.MaskedAffineAutoregressive(dim, hidden))
        flow_list.append(nf.flows.LULinearPermute(dim))

    means    = torch.tensor(bundle["base_state"]["means"])
    log_stds = torch.tensor(bundle["base_state"]["log_stds"])
    base = ClusterGaussianBase(means, log_stds)

    flow_list.load_state_dict(
        {k: torch.tensor(v) for k, v in bundle["flows_state"].items()}
    )
    base.load_state_dict(
        {k: torch.tensor(v) for k, v in bundle["base_state"].items()}
    )
    flow_list.eval(); base.eval()
    return flow_list, base, bundle["scaler"], bundle


# ════════════════════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════════════════════

def run(
    limit: int | None = None,
    n_flows: int = 6,
    hidden: int = 128,
    epochs: int = 100,
    test_ratio: float = 0.05,
    top_n: int = 200,
    no_train: bool = False,
):
    # ── 1. 데이터 로드 ────────────────────────────────────────────────────────
    X, cids, clip_ids, K = load_data(limit=limit)
    K_total = K + 1   # 클러스터 124 + noise bucket 1 = 125

    # ── 2. 정규화 ─────────────────────────────────────────────────────────────
    scaler = StandardScaler().fit(X)
    X_sc   = scaler.transform(X).astype(np.float32)

    # ── 3. Train / test split ─────────────────────────────────────────────────
    rng = np.random.default_rng(42)
    idx = rng.permutation(len(X_sc))
    n_test = max(1, int(len(X_sc) * test_ratio))
    idx_te, idx_tr = idx[:n_test], idx[n_test:]

    X_tr, cids_tr = X_sc[idx_tr], cids[idx_tr]
    X_te, cids_te = X_sc[idx_te], cids[idx_te]
    print(f"  train={len(X_tr):,}  test={len(X_te):,}")

    # ── 4. 학습 or 로드 ───────────────────────────────────────────────────────
    if no_train and SANFLOW_MODEL_PATH.exists():
        print("Loading existing model …")
        flow_list, base, scaler, _ = load_model()
    else:
        print("\nTraining SANFlow …")
        t0 = time.time()
        flow_list, base = train_sanflow(
            X_tr, cids_tr, K_total,
            n_flows=n_flows, hidden=hidden, epochs=epochs,
        )
        print(f"  elapsed: {time.time() - t0:.0f}s")

    # ── 5. 평가: SANFlow vs DiagGaussian baseline ─────────────────────────────
    print("\nEvaluating …")
    flow_list.eval(); base.eval()
    with torch.no_grad():
        X_te_t = torch.tensor(X_te, dtype=torch.float32)
        z_te, ld_te = _eval_direction(flow_list, X_te_t)
        nk_te = base.nearest(z_te)
        # SANFlow log p(x) = log p_{cluster_k}(z) + log|det J^{-1}(x)|
        sanflow_ll = float((base.log_prob(z_te, nk_te) + ld_te).mean())

    # Baseline: KDE (data space 직접 비교, 공정한 비교)
    from sklearn.neighbors import KernelDensity
    n_tr, d_tr = X_tr.shape
    h = n_tr ** (-1.0 / (d_tr + 4))   # Silverman's rule
    kde = KernelDensity(kernel="gaussian", bandwidth=h).fit(X_tr)
    baseline_ll = float(kde.score_samples(X_te).mean())

    print(f"\n  ── Test log-likelihood (data space) ──")
    print(f"     SANFlow (cluster NF) : {sanflow_ll:.4f}")
    print(f"     KDE baseline         : {baseline_ll:.4f}")
    if sanflow_ll > baseline_ll:
        print("     ✓ PASS: SANFlow > KDE")
    else:
        print("     △ NOTE: SANFlow <= KDE — 더 많은 epoch 또는 전체 데이터 필요")

    # ── 6. 갭 탐지 (전체 데이터셋) ───────────────────────────────────────────
    print(f"\nDetecting gaps (top {top_n}) …")
    ca    = json.loads(CLUSTER_ANALYSIS_PATH.read_text())
    gaps  = detect_gaps(flow_list, base, X_sc, clip_ids, cids, ca, top_n=top_n)

    print(f"\n  Top-10 gap clips:")
    print(f"  {'rank':>4}  {'log_dens':>9}  {'cluster':>8}  scenario")
    print(f"  {'----':>4}  {'---------':>9}  {'-------':>8}  --------")
    for g in gaps[:10]:
        print(f"  {g['rank']:>4}  {g['log_density']:>9.3f}  "
              f"  {g['nearest_cluster']:>6}  {g['scenario_name'][:60]}")

    # noise 비율 요약
    n_noise_gaps = sum(1 for g in gaps if g["is_noise"])
    print(f"\n  gaps에서 noise 비율: {n_noise_gaps}/{len(gaps)} "
          f"({n_noise_gaps/len(gaps):.1%})")

    # ── 7. 저장 ───────────────────────────────────────────────────────────────
    save_model(flow_list, base, scaler, {
        "K_total":       K_total,
        "K_clusters":    K,
        "dim":           X.shape[1],
        "n_flows":       n_flows,
        "hidden":        hidden,
        "epochs":        epochs,
        "sanflow_ll":    sanflow_ll,
        "kde_baseline_ll": baseline_ll,
        "n_train":       len(X_tr),
        "n_test":        len(X_te),
    })

    SANFLOW_GAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    SANFLOW_GAP_PATH.write_text(json.dumps(gaps, indent=2, ensure_ascii=False))
    print(f"  → gaps : {SANFLOW_GAP_PATH}  ({len(gaps)} clips)")

    # eval 요약 저장
    eval_path = EXP002_RESULTS_DIR / "sanflow_eval.json"
    eval_path.write_text(json.dumps({
        "sanflow_ll":      sanflow_ll,
        "kde_baseline_ll": baseline_ll,
        "pass":            sanflow_ll > baseline_ll,
        "n_train":     len(X_tr),
        "n_test":      len(X_te),
        "n_flows":     n_flows,
        "epochs":      epochs,
        "top_n_gaps":  top_n,
        "gap_noise_rate": n_noise_gaps / len(gaps),
    }, indent=2))
    print(f"  → eval : {eval_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",    type=int,   default=None,
                        help="학습에 사용할 클립 수 (기본=전체)")
    parser.add_argument("--flows",    type=int,   default=6,
                        help="MAF 블록 수 (기본=6, 각 블록=MAF+LULinear)")
    parser.add_argument("--hidden",   type=int,   default=128,
                        help="MAF hidden units (기본=128)")
    parser.add_argument("--epochs",   type=int,   default=100)
    parser.add_argument("--top-n",    type=int,   default=200,
                        help="출력할 갭 클립 수")
    parser.add_argument("--no-train", action="store_true",
                        help="저장된 모델 로드 후 갭 탐지만 수행")
    args = parser.parse_args()
    run(
        limit=args.limit,
        n_flows=args.flows,
        hidden=args.hidden,
        epochs=args.epochs,
        top_n=args.top_n,
        no_train=args.no_train,
    )
