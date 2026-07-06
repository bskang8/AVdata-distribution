"""Phase 0 공용 유틸리티 — 순수 함수만 포함, 부작용 없음"""

import json
import math
import os
from collections import Counter
import numpy as np
from config import OUTPUT_DIR, CAPTIONS_DIR


def P(fname):
    """OUTPUT_DIR 기준 파일 경로 반환"""
    return os.path.join(OUTPUT_DIR, fname)


def require_files(*fnames, step=''):
    """필수 입력 파일 존재 확인 — 없으면 명확한 오류 메시지"""
    missing = [f for f in fnames if not os.path.exists(P(f))]
    if missing:
        hint = f"\n  → 이전 단계를 먼저 실행하세요." + (f" [{step}]" if step else "")
        raise FileNotFoundError(f"필수 파일 없음: {missing}{hint}")


def already_done(step_name, *fnames):
    """출력 파일이 모두 존재하면 스킵 메시지 출력 후 True 반환"""
    if all(os.path.exists(P(f)) for f in fnames):
        print(f"[{step_name}] 스킵: 출력 파일 이미 존재 (force=True로 재실행)")
        return True
    return False


def load_captions():
    """캡션 텍스트와 clip_id 로드.
    파일 포맷: {clip_id}.camera_front_wide_120fov.txt (평문 캡션)
    """
    captions, clip_ids = [], []
    for fname in sorted(os.listdir(CAPTIONS_DIR)):
        if not fname.endswith('.txt'):
            continue
        clip_id = fname.split('.')[0]
        with open(os.path.join(CAPTIONS_DIR, fname), encoding='utf-8') as f:
            caption = f.read().strip()
        if not caption:
            continue
        captions.append(caption)
        clip_ids.append(clip_id)
    return captions, clip_ids


def compute_lid_mle(knn_sim_arr, k_lid=20):
    """Ma et al. (ICLR 2018) MLE — 극값 이론 기반 LID 추정.
    LID(x) = -[ (1/k) Σ log(r_j / r_k) ]^{-1}
    """
    knn_dist   = 1.0 - knn_sim_arr[:, :k_lid]
    r_max      = knn_dist[:, -1:] + 1e-10
    log_ratios = np.log(knn_dist / r_max + 1e-10)
    lid        = -1.0 / (log_ratios.mean(axis=1) + 1e-10)
    return np.clip(lid, 1.0, 200.0)


def load_odd_compat(clip_ids, odd_dir):
    """clip_ids 각각에 대해 odd_compat dict 로드 — 없으면 None"""
    records = []
    for cid in clip_ids:
        try:
            with open(os.path.join(odd_dir, f"{cid}.json")) as f:
                records.append(json.load(f).get('odd_compat') or None)
        except (FileNotFoundError, json.JSONDecodeError):
            records.append(None)
    return records


def odd_diversity_stats(odd_records, dims):
    """odd_compat 리스트 → 다양성 통계 dict (per-dim 엔트로피 + 고유 조합 수)"""
    valid = [r for r in odd_records if r is not None]
    found_ratio = round(len(valid) / max(len(odd_records), 1), 4)
    if not valid:
        return {'found_ratio': found_ratio, 'n_clips': 0}
    per_dim = {}
    for dim in dims:
        vals = [r.get(dim, 'unknown') for r in valid]
        n = len(vals)
        counts = Counter(vals)
        entropy = -sum((c / n) * math.log2(c / n + 1e-12) for c in counts.values())
        max_h = math.log2(len(counts)) if len(counts) > 1 else 1.0
        per_dim[dim] = {
            'entropy':      round(entropy, 3),
            'norm_entropy': round(entropy / (max_h + 1e-12), 3),
            'n_unique':     len(counts),
        }
    combos = [tuple(r.get(d, 'unknown') for d in dims) for r in valid]
    combo_counts = Counter(combos)
    n = len(combos)
    combo_entropy = -sum((cnt / n) * math.log2(cnt / n + 1e-12)
                         for cnt in combo_counts.values())
    odd_effective_n = round(float(2 ** combo_entropy), 3)

    for dim, v in per_dim.items():
        v['effective_n'] = round(float(2 ** v['entropy']), 3)

    return {
        'found_ratio':       found_ratio,
        'n_clips':           len(valid),
        'n_unique_combos':   len(combo_counts),
        'odd_effective_n':   odd_effective_n,   # exp2(H) — 실질 ODD 조합 다양성
        'mean_norm_entropy': round(
            sum(v['norm_entropy'] for v in per_dim.values()) / max(len(dims), 1), 3),
        'per_dim':           per_dim,
    }


def gmm_threshold(data, max_k=3):
    """BIC 최적 K → brentq 실제 교차점 임계값 반환.
    K=1: median 폴백. K=2: 두 성분 교차점. K=3: BIC 개선 ≥3%이면 최솟값 쌍 교차점.
    반환: (threshold, best_k, bics_dict)
    """
    from sklearn.mixture import GaussianMixture
    from scipy import optimize

    data_2d = data.reshape(-1, 1)
    gmms, bics = {}, {}
    for k in range(1, max_k + 1):
        g = GaussianMixture(n_components=k, random_state=42, n_init=5).fit(data_2d)
        bics[k]  = g.bic(data_2d)
        gmms[k]  = g
    best_k = min(bics, key=bics.get)

    if best_k == 1:
        return float(np.median(data)), 1, bics

    use_k3 = (best_k == 3 and
               (bics[2] - bics[3]) / max(abs(bics[2]), 1.0) >= 0.03)
    if use_k3:
        g3       = gmms[3]
        means3   = g3.means_.flatten()
        stds3    = np.sqrt(g3.covariances_.flatten())
        weights3 = g3.weights_.flatten()
        idx3     = np.argsort(means3)
        best_thresh, best_pdf_min = None, np.inf
        for i in range(len(idx3) - 1):
            ma, sa, wa = means3[idx3[i]],   stds3[idx3[i]],   weights3[idx3[i]]
            mb, sb, wb = means3[idx3[i+1]], stds3[idx3[i+1]], weights3[idx3[i+1]]
            def _diff(x, ma=ma, sa=sa, wa=wa, mb=mb, sb=sb, wb=wb):
                return (wa/sa*np.exp(-0.5*((x-ma)/sa)**2) -
                        wb/sb*np.exp(-0.5*((x-mb)/sb)**2))
            def _sum(x, ma=ma, sa=sa, wa=wa, mb=mb, sb=sb, wb=wb):
                return (wa/sa*np.exp(-0.5*((x-ma)/sa)**2) +
                        wb/sb*np.exp(-0.5*((x-mb)/sb)**2))
            try:
                t = optimize.brentq(_diff, ma, mb)
                v = _sum(t)
                if v < best_pdf_min:
                    best_pdf_min, best_thresh = v, t
            except ValueError:
                pass
        if best_thresh is not None:
            return float(best_thresh), best_k, bics

    # K=2 기준 교차점 (K=3 BIC 미달 또는 교차점 없음 폴백 포함)
    g2      = gmms[2]
    means   = g2.means_.flatten()
    stds    = np.sqrt(g2.covariances_.flatten())
    weights = g2.weights_.flatten()
    idx     = np.argsort(means)
    m1, s1, w1 = means[idx[0]], stds[idx[0]], weights[idx[0]]
    m2, s2, w2 = means[idx[1]], stds[idx[1]], weights[idx[1]]

    def pdf_diff(x):
        return (w1/s1*np.exp(-0.5*((x-m1)/s1)**2) -
                w2/s2*np.exp(-0.5*((x-m2)/s2)**2))
    try:
        threshold = optimize.brentq(pdf_diff, m1, m2)
    except ValueError:
        threshold = float(np.mean([m1, m2]))
    return float(threshold), best_k, bics
