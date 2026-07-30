"""§5 leave-out 재현실험 하네스 — 논문의 척추(G4 증명) + 후속 실험 A·B.

가설: 제안 획득함수(Priority)로 데이터를 고르면 무작위/단일렌즈보다 성능이 빨리 회복된다.
      guided > random·coverage-only·uncertainty-only·diversity-only  → 정책 유효 + 두 렌즈 상호보완.

테스트베드 = 학습형 egomotion 예측기. 입력 = kinematics(6) + **PCA(임베딩,16) 장면 feature**
— 순수 kinematics면 모델이 날씨 같은 조건축을 학습할 통로가 없어 어떤 획득도 회복을 못 만든다
(smoke 진단). 임베딩=장면 content/condition → 모델이 조건별 동역학 학습 가능 = real 장면인지
모델의 정직한 대리. "성능"=고정 홀드아웃 test ADE. "획득"=training에 어떤 클립을 add하나.

두 결핍 시나리오(각각 독립 실험):
  adverse   : tail=weather=snow ∨ fog=present (ODD 조건축) — guided(ODD-aware) 유리 가설.
  kinematic : tail=고yaw·급기동(kinematic feature축) — uncertainty(error-aware) 유리 가설.
  → 각 렌즈가 관련 결핍에서 이기는지 대조. G4 = guided > coverage_only(ODD-only)·diversity_only(임베딩-only).

정책(candidate 순위):
  guided       : 클립 coarse셀 Priority(full 우선, 없으면 core) — 다섯 인자 종합.
  random       : 무작위(seed).
  coverage_only: ODD 11-tuple 셀 분산(round-robin) — 부재/희소 채우기, 임베딩 무시.
  uncertainty_only: 학습형 model_error per-clip 내림차순 — 오차만(원시 축).
  diversity_only  : 임베딩 farthest-point(greedy max-min cosine) — 기하 다양성만.
  emb_err_only : 성능신호를 임베딩 이웃(k-NN 평균 ADE)으로 재배치 — ODD 무시. ②(축) 격리용.
  guided_sep   : emb_err × soft ODD context([0.5,1] 넛지, 억제 불가) — 축분리 결합(guided 교정형).

후속 실험 (COMPLEMENTARITY_GAP.md §6·§8) — 기본 실행과 별개, 플래그로만 구동:
  --expA : ablation 배터리(결핍 다양화·파일럿·severity·capacity·ODD-feature). → leaveout_battery.json
  --expB : spread 결합(coverage⊕diversity: portfolio·stratified·mult) × 이질적 결핍 · worst-case.
           → leaveout_spread_combo.json

실행:  ../../../.venv/bin/python leaveout.py [--demo] [--quick] [--expA] [--expB]
       windows.npz(learned_surrogate 전체실행 산출) 필요.
"""
import os, sys, json, numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors

ROOT = os.path.dirname(os.path.abspath(__file__))
P0 = os.path.join(ROOT, '..', 'phase0', 'output')
OUT = os.path.join(ROOT, 'output')
SEEDS = [0, 1, 2, 3, 4]        # 다중 seed(test분할·MLP init·타이브레이크) → 순위 유의성
MAX_WIN_PER_CLIP = 2           # 클립당 창 상한(하네스 속도)
TEST_FRAC = 0.25
EMB_PCA = 16                   # 장면 feature: 임베딩 PCA 차원(모델이 조건 학습하는 통로)
BUDGETS = [0, 400, 800]
COMMON_MULT = 3                # mixed pool: candidate에 tail의 COMMON_MULT배 잉여 common 혼입(변별 시험)

# --- 실험 A·B 파라미터 (COMPLEMENTARITY_GAP.md §6·§8) ---
SEVERITY_PCTL = [98, 96, 92]                    # tail 상위 2/4/8% (연속축 결핍)
CAPACITY_SWEEP = [(16,), (32, 16), (128, 64)]   # A ①: surrogate 용량 스윕
# 기동축 결핍 후보(X 컬럼): 0=speed 1=a_long 2=a_lat 3=yaw_rate 4=curv(yaw/speed) 5=speed²
KIN_DEFICITS = {'yaw': 3, 'a_long': 1, 'a_lat': 2, 'speed': 0, 'curv': 4}
# ODD 조건축 결핍 후보(coarse cell label 부분문자열 매칭). 실제 vocab에 맞춰 내일 조정.
ODD_TOKENS = ['rural', 'national', 'urban', 'highway', 'rain', 'snow', 'fog']
PILOT_MIN_GAP = 0.01           # 파일럿: 이 이상 회복여지(=실재 결핍)면 채택
BUDGETS_B = [100, 200, 400, 800]   # 실험 B 예산 스윕(천장 전 구간 포착)
POLICIES_B = ['random', 'coverage_only', 'diversity_only',
              'cov_div_portfolio', 'cov_div_strat', 'cov_div_mult']


def per_clip_windows(grp, cap):
    """grp(창→클립) → {clip: [window row idx ≤cap]}."""
    d = {}
    for row, g in enumerate(grp):
        lst = d.setdefault(int(g), [])
        if len(lst) < cap:
            lst.append(row)
    return d


def rows_for(clips, c2w):
    idx = []
    for c in clips:
        idx.extend(c2w.get(int(c), ()))
    return np.array(idx, dtype=int)


def fit_eval(train_rows, test_rows_all, test_rows_tail, X, Y, quick, seed,
             hidden=None, max_iter=None):
    """base+add 학습 → test overall·tail ADE(canonical 거리).
    hidden/max_iter=None이면 기존 기본(quick 여부)으로 — 기존 호출 100% 보존."""
    if hidden is None:
        hidden = (24,) if quick else (32, 16)
    if max_iter is None:
        max_iter = 40 if quick else 60
    m = make_pipeline(StandardScaler(),
                      MLPRegressor(hidden_layer_sizes=hidden, max_iter=max_iter,
                                   early_stopping=True, n_iter_no_change=6, random_state=seed))
    m.fit(X[train_rows], Y[train_rows])

    def ade(rows):
        if len(rows) == 0:
            return float('nan')
        P = m.predict(X[rows]).reshape(-1, 6, 2)
        G = Y[rows].reshape(-1, 6, 2)
        return float(np.linalg.norm(P - G, axis=2).mean())
    return ade(test_rows_all), ade(test_rows_tail)


def farthest_point(cand, emb, k):
    """greedy max-min cosine FPS: 다양성 순으로 cand 정렬(앞 k만 의미)."""
    cand = list(cand)
    E = emb[cand]                                  # (C,1024) L2-norm=1
    picked = [0]
    mind = 1.0 - E @ E[0]
    order = [cand[0]]
    for _ in range(min(k, len(cand)) - 1):
        j = int(np.argmax(mind))
        order.append(cand[j]); picked.append(j)
        mind = np.minimum(mind, 1.0 - E @ E[j])
    rest = [c for i, c in enumerate(cand) if i not in set(picked)]
    return order + rest


def emb_neighborhood_error(clips, emb_pca, err_by_clip, k=20):
    """성능신호를 임베딩축에 재배치: 각 클립 = 임베딩 k-NN의 평균 per-clip ADE.
    ②'model_error는 ODD셀이 아니라 임베딩축에 산다'의 직접 구현."""
    V = emb_pca[clips]
    nn = NearestNeighbors(n_neighbors=min(k + 1, len(clips))).fit(V)
    _, idx = nn.kneighbors(V)
    out = {}
    for i, c in enumerate(clips):
        nbrs = [int(clips[j]) for j in idx[i] if j != i][:k]
        out[int(c)] = float(np.mean([err_by_clip[n] for n in nbrs])) if nbrs else err_by_clip[int(c)]
    return out


def coverage_order(cand, odd_keys, rng):
    """ODD 셀 round-robin: 셀별 큐를 교대로 뽑아 셀 분산 최대화."""
    from collections import defaultdict, deque
    buckets = defaultdict(list)
    for c in cand:
        buckets[odd_keys[c]].append(c)
    cells = list(buckets)
    rng.shuffle(cells)
    queues = [deque(buckets[k]) for k in cells]
    order = []
    while queues:
        nxt = []
        for q in queues:
            if q:
                order.append(q.popleft())
            if q:
                nxt.append(q)
        queues = nxt
    return order


# ---- 실험 B: coverage⊕diversity 결합의 3형태 (COMPLEMENTARITY_GAP.md §8.2) ----
def portfolio_order(cand, odd_keys, emb, rng):
    """포트폴리오: coverage 순위와 diversity 순위를 교대(round-robin) 병합 → 어느 prefix든 ~반반."""
    cov = coverage_order(cand, odd_keys, rng)
    div = farthest_point(cand, emb, len(cand))
    out, seen = [], set()
    for a, b in zip(cov, div):
        for c in (a, b):
            if c not in seen:
                seen.add(c); out.append(c)
    for c in cov:                                   # 안전 채움
        if c not in seen:
            seen.add(c); out.append(c)
    return out


def stratified_order(cand, odd_keys, emb, rng):
    """층화 결합: ODD 셀로 층화 → 각 셀 내부 FPS 정렬 → 셀 라운드로빈(ODD×임베딩 결합 공간)."""
    from collections import defaultdict, deque
    buckets = defaultdict(list)
    for c in cand:
        buckets[odd_keys[c]].append(c)
    cells = list(buckets)
    rng.shuffle(cells)
    queues = []
    for k in cells:
        b = buckets[k]
        queues.append(deque(farthest_point(b, emb, len(b)) if len(b) > 1 else b))
    order = []
    while queues:
        nxt = []
        for q in queues:
            if q:
                order.append(q.popleft())
            if q:
                nxt.append(q)
        queues = nxt
    return order


def mult_order(cand, odd_keys, emb, rng):
    """곱셈 융합(대조): coverage 순위점수 × diversity 순위점수 내림차순 = guided와 같은 억제 병리."""
    cand = list(cand)
    n = len(cand)
    cov = coverage_order(cand, odd_keys, rng)
    div = farthest_point(cand, emb, n)
    cs = {c: (n - i) / n for i, c in enumerate(cov)}   # 순위 높을수록 점수↑
    ds = {c: (n - i) / n for i, c in enumerate(div)}
    return sorted(cand, key=lambda c: (-(cs[c] * ds[c]), rng.random()))


def policy_orders(cand, guided_clip, err_clip, emberr_clip, sep_clip, emb, odd_keys, rng):
    """기존 7정책 순위(guided·random·coverage_only·uncertainty_only·emb_err_only·guided_sep·diversity_only)."""
    cand = list(cand)
    orders = {}
    orders['random'] = list(rng.permutation(cand))
    orders['guided'] = sorted(cand, key=lambda c: (-guided_clip[c], rng.random()))
    orders['uncertainty_only'] = sorted(cand, key=lambda c: (-err_clip[c], rng.random()))
    orders['emb_err_only'] = sorted(cand, key=lambda c: (-emberr_clip[c], rng.random()))
    orders['guided_sep'] = sorted(cand, key=lambda c: (-sep_clip[c], rng.random()))
    orders['diversity_only'] = farthest_point(cand, emb, max(BUDGETS))
    orders['coverage_only'] = coverage_order(cand, odd_keys, rng)
    return orders


POLICIES = ['guided', 'guided_sep', 'random', 'coverage_only',
            'uncertainty_only', 'emb_err_only', 'diversity_only']


def run_scenario_seed(is_tail, clips, c2w, X, Y, guided_by_clip, err_by_clip,
                      emberr_by_clip, sep_by_clip, emb, odd_keys, quick, seed, hidden=None):
    """한 시나리오·한 seed: 정책별 최종예산 tail 회복량 dict 반환. hidden=surrogate 용량 override."""
    rng = np.random.default_rng(seed)
    test_mask = np.zeros(len(clips), bool)
    for sub in (np.where(is_tail)[0], np.where(~is_tail)[0]):
        test_mask[rng.choice(sub, max(1, int(len(sub) * TEST_FRAC)), replace=False)] = True
    pool = clips[~test_mask]; pool_tail = is_tail[~test_mask]
    tail_clips = pool[pool_tail]
    common = pool[~pool_tail].copy(); rng.shuffle(common)
    # mixed pool: candidate = tail(유용) + 잉여 common(무용, base에 이미 충분) → 변별 시험
    n_cc = min(len(common) // 2, COMMON_MULT * len(tail_clips))
    cand_clips = np.concatenate([tail_clips, common[:n_cc]])
    base_clips = common[n_cc:]
    is_tail_cand = {int(c): True for c in tail_clips}          # candidate 중 tail 여부
    guided_c = {int(c): guided_by_clip[int(c)] for c in cand_clips}
    err_c = {int(c): err_by_clip[int(c)] for c in cand_clips}
    emberr_c = {int(c): emberr_by_clip[int(c)] for c in cand_clips}
    sep_c = {int(c): sep_by_clip[int(c)] for c in cand_clips}
    test_rows_all = rows_for(clips[test_mask], c2w)
    test_rows_tail = rows_for(clips[test_mask][is_tail[test_mask]], c2w)
    base_rows = rows_for(base_clips, c2w)
    budgets = [b for b in (BUDGETS[:2] if quick else BUDGETS) if b <= len(cand_clips)]

    orders = policy_orders(cand_clips, guided_c, err_c, emberr_c, sep_c, emb, odd_keys, rng)
    a0, t0 = fit_eval(base_rows, test_rows_all, test_rows_tail, X, Y, quick, seed, hidden)
    rec, tail_frac = {}, {}
    for pol in POLICIES:
        picked = orders[pol][:budgets[-1]]
        tail_frac[pol] = float(np.mean([is_tail_cand.get(int(c), False) for c in picked]))
        add_rows = rows_for(picked, c2w)
        _, t = fit_eval(np.concatenate([base_rows, add_rows]), test_rows_all, test_rows_tail,
                        X, Y, quick, seed, hidden)
        rec[pol] = t0 - t
    return {'baseline_tail': t0, 'n_cand': len(cand_clips), 'n_tail': len(tail_clips),
            'budget': budgets[-1], 'recover': rec, 'tail_frac_picked': tail_frac}


# ============================ 데이터 로딩 (main·A·B 공용) ============================
def load_data(quick=False):
    """windows·임베딩·신호·기본 tail 마스크를 한 번에 로드. main()과 exp A/B가 공유."""
    z = np.load(os.path.join(OUT, 'windows.npz'))
    X, Y, grp = z['X'], z['Y'], z['grp']
    labels = np.load(os.path.join(OUT, 'coarse_cell_per_clip.npy'), allow_pickle=True)
    odd = np.load(os.path.join(P0, 'odd_codes_compat_v2.npy'))
    emb_raw = np.load(os.path.join(P0, 'embeddings.npy'))
    ade_clip = np.load(os.path.join(OUT, 'learned_ade_per_clip.npy'))   # per-clip raw 오차
    pr = json.load(open(os.path.join(OUT, 'learned_ext_priority_ranking.json')))
    # cell_context = Priority에서 model_error 인자를 뺀 나머지(exposure×crit×deficit×headroom).
    context = {}
    for r in pr['ranking_core']:
        me = r['model_error'] or 1e-6
        base = (r['priority_full'] if r['priority_full'] is not None else r['priority_core'])
        context[r['cell']] = base / me
    odd_keys = ['-'.join(map(str, row)) for row in odd]

    emb_pca = PCA(n_components=EMB_PCA, random_state=0).fit_transform(emb_raw)
    Xaug = np.hstack([X, emb_pca[grp]]).astype(np.float32)
    c2w = per_clip_windows(grp, MAX_WIN_PER_CLIP)
    clips = np.array(sorted(c2w))

    # per-clip 신호: err=raw learned ADE(정규화), guided=cell_context×err
    fin = np.isfinite(ade_clip)
    lo, hi = np.nanpercentile(ade_clip[fin], [1, 99])
    err_by_clip = {int(c): float(np.clip((ade_clip[c] - lo) / (hi - lo + 1e-9), 0, 1)) if fin[c] else 0.0
                   for c in clips}
    guided_by_clip = {int(c): context.get(labels[c], 0.0) * err_by_clip[int(c)] for c in clips}
    emberr_by_clip = emb_neighborhood_error(clips, emb_pca, err_by_clip)
    cmax = max((context.get(labels[c], 0.0) for c in clips), default=0.0) or 1.0
    sep_by_clip = {int(c): emberr_by_clip[int(c)] * (0.5 + 0.5 * context.get(labels[c], 0.0) / cmax)
                   for c in clips}

    # 기본 tail 마스크(기존 두 시나리오)
    adverse = np.array([bool(labels[c]) and ('snow' in labels[c] or 'present' in labels[c]) for c in clips])
    yaw_by_clip = clip_feature_max(grp, X, 3, clips)
    kin = yaw_by_clip >= np.percentile(yaw_by_clip, 96)

    return dict(X=X, Y=Y, grp=grp, labels=labels, emb_raw=emb_raw, emb_pca=emb_pca,
                Xaug=Xaug, c2w=c2w, clips=clips, odd_keys=odd_keys,
                err_by_clip=err_by_clip, guided_by_clip=guided_by_clip,
                emberr_by_clip=emberr_by_clip, sep_by_clip=sep_by_clip,
                adverse=adverse, kin=kin)


def clip_feature_max(grp, X, col, clips):
    """per-window feature[col] → 클립별 max|·| (clips 순서 정렬). yaw tail 등 연속축 결핍용."""
    ci = {int(c): i for i, c in enumerate(clips)}
    agg = np.zeros(len(clips))
    for row, g in enumerate(grp):
        i = ci.get(int(g))
        if i is not None:
            agg[i] = max(agg[i], abs(X[row, col]))
    return agg


# ============================ 기본 실행 (기존 두-시나리오) ============================
def main(quick=False):
    D = load_data(quick)
    print(f"features: kinematics{D['X'].shape[1]}+emb_pca{EMB_PCA}={D['Xaug'].shape[1]}  seeds={SEEDS}")
    print(f"tail sizes: adverse={D['adverse'].sum()} kinematic={D['kin'].sum()}")

    seeds = SEEDS[:2] if quick else SEEDS
    out = {'params': {'seeds': seeds, 'test_frac': TEST_FRAC, 'budgets': BUDGETS,
                      'max_win_per_clip': MAX_WIN_PER_CLIP,
                      'features': 'kinematics(6)+emb_pca(16)',
                      'guided': 'cell_context(exposure×crit×deficit×headroom) × per-clip raw ADE',
                      'uncertainty': 'per-clip raw learned ADE',
                      'emb_err_only': 'per-clip ADE를 임베딩 k-NN(20)로 평균 = 성능신호 임베딩축',
                      'guided_sep': 'emb_err × soft ODD context([0.5,1]) = 축분리 결합'},
           'scenarios': {}}
    for name, mask in (('adverse', D['adverse']), ('kinematic', D['kin'])):
        per_seed = [run_scenario_seed(mask, D['clips'], D['c2w'], D['Xaug'], D['Y'],
                                      D['guided_by_clip'], D['err_by_clip'], D['emberr_by_clip'],
                                      D['sep_by_clip'], D['emb_raw'], D['odd_keys'], quick, s)
                    for s in seeds]
        agg = {pol: {'mean': float(np.mean([ps['recover'][pol] for ps in per_seed])),
                     'std': float(np.std([ps['recover'][pol] for ps in per_seed])),
                     'tail_frac': float(np.mean([ps['tail_frac_picked'][pol] for ps in per_seed]))}
               for pol in POLICIES}
        rank = sorted(POLICIES, key=lambda p: -agg[p]['mean'])
        g, cov, div = agg['guided']['mean'], agg['coverage_only']['mean'], agg['diversity_only']['mean']
        margin = max(agg['guided']['std'], agg['coverage_only']['std'], agg['diversity_only']['std'])
        out['scenarios'][name] = {
            'baseline_tail': float(np.mean([ps['baseline_tail'] for ps in per_seed])),
            'budget': per_seed[0]['budget'], 'n_cand': per_seed[0]['n_cand'],
            'recover_mean_std': agg, 'rank': rank,
            'G4_guided_gt_singlelens': bool(g > cov and g > div),
            'G4_significant_1sigma': bool(g - margin > cov and g - margin > div)}
        unc, emberr, sep = (agg['uncertainty_only']['mean'], agg['emb_err_only']['mean'],
                            agg['guided_sep']['mean'])
        out['scenarios'][name]['axis_diag'] = {
            'emb_err_gt_uncertainty': bool(emberr > unc),
            'guided_sep_gt_guided': bool(sep > g),
            'guided_sep_reaches_spread': bool(sep >= min(cov, div) - margin),
            'values': {'guided': g, 'guided_sep': sep, 'uncertainty': unc,
                       'emb_err': emberr, 'coverage': cov, 'diversity': div}}
        print(f"\n[{name}] baseline_tail={out['scenarios'][name]['baseline_tail']:.3f} "
              f"budget={per_seed[0]['budget']} cand={per_seed[0]['n_cand']}")
        for pol in rank:
            print(f"    {pol:<16} recover {agg[pol]['mean']:+.4f} ± {agg[pol]['std']:.4f}  tail_picked={agg[pol]['tail_frac']:.0%}")
        print(f"    순위: {' > '.join(rank)}  | G4={out['scenarios'][name]['G4_guided_gt_singlelens']}"
              f" (1σ유의={out['scenarios'][name]['G4_significant_1sigma']})")

    tag = 'quick_' if quick else ''
    json.dump(out, open(os.path.join(OUT, f'{tag}leaveout_results.json'), 'w'), ensure_ascii=False, indent=2)
    print("\n=== 요약 ===")
    for name, r in out['scenarios'].items():
        print(f"  {name:<10} {' > '.join(r['rank'])}  G4={r['G4_guided_gt_singlelens']} 1σ={r['G4_significant_1sigma']}")


# ============================ 실험 A: ablation 배터리 ============================
def candidate_masks(D):
    """결핍 후보 마스크 dict {name: bool[clips]}. 기동 sub(연속·severity 적용) + ODD sub(범주)."""
    out, meta = {}, {}
    for name, col in KIN_DEFICITS.items():
        agg = clip_feature_max(D['grp'], D['X'], col, D['clips'])
        for p in SEVERITY_PCTL:
            out[f'kin_{name}_p{100 - p}'] = agg >= np.percentile(agg, p)
            meta[f'kin_{name}_p{100 - p}'] = {'type': 'kinematic', 'axis': name, 'pctl': p}
    labels = D['labels']
    for tok in ODD_TOKENS:
        m = np.array([tok in str(labels[c]) for c in D['clips']])
        if m.sum() >= 50:                       # 너무 희소하면 제외
            out[f'odd_{tok}'] = m
            meta[f'odd_{tok}'] = {'type': 'odd', 'token': tok, 'n': int(m.sum())}
    return out, meta


def pilot_deficit_gap(mask, D, quick, seed=0):
    """실재 결핍 여부: base(=tail 제거)에서의 tail-ADE − full(=tail 포함)에서의 tail-ADE.
    >0 클수록 '메울 수 있는 실재 결핍'. adverse처럼 null이면 ≈0."""
    clips, c2w, X, Y = D['clips'], D['c2w'], D['Xaug'], D['Y']
    rng = np.random.default_rng(seed)
    test_mask = np.zeros(len(clips), bool)
    for sub in (np.where(mask)[0], np.where(~mask)[0]):
        test_mask[rng.choice(sub, max(1, int(len(sub) * TEST_FRAC)), replace=False)] = True
    tr = clips[~test_mask]; tr_tail = mask[~test_mask]
    test_rows_all = rows_for(clips[test_mask], c2w)
    test_rows_tail = rows_for(clips[test_mask][mask[test_mask]], c2w)
    base_rows = rows_for(tr[~tr_tail], c2w)                         # tail 제거
    full_rows = rows_for(tr, c2w)                                   # tail 포함
    _, base_tail = fit_eval(base_rows, test_rows_all, test_rows_tail, X, Y, quick, seed)
    _, full_tail = fit_eval(full_rows, test_rows_all, test_rows_tail, X, Y, quick, seed)
    return {'baseline_tail': base_tail, 'floor_tail': full_tail,
            'deficit_gap': base_tail - full_tail, 'n_tail': int(mask.sum())}


def odd_onehot_X(D):
    """A ②: coarse cell one-hot을 feature로 concat한 대체 입력(ODD를 모델이 볼 수 있게)."""
    labels, grp = D['labels'], D['grp']
    cats = sorted(set(str(labels[c]) for c in D['clips']))
    idx = {c: i for i, c in enumerate(cats)}
    OH = np.zeros((len(labels), len(cats)), np.float32)
    for c in range(len(labels)):
        s = str(labels[c])
        if s in idx:
            OH[c, idx[s]] = 1.0
    return np.hstack([D['Xaug'], OH[grp]]).astype(np.float32), len(cats)


def _run_battery_deficit(mask, D, quick, seeds, X=None, hidden=None):
    """한 결핍 마스크에 대해 7정책 회복 aggregate(재현성 판정용)."""
    X = D['Xaug'] if X is None else X
    ps = [run_scenario_seed(mask, D['clips'], D['c2w'], X, D['Y'], D['guided_by_clip'],
                            D['err_by_clip'], D['emberr_by_clip'], D['sep_by_clip'],
                            D['emb_raw'], D['odd_keys'], quick, s, hidden) for s in seeds]
    agg = {pol: {'mean': float(np.mean([p['recover'][pol] for p in ps])),
                 'std': float(np.std([p['recover'][pol] for p in ps])),
                 'tail_frac': float(np.mean([p['tail_frac_picked'][pol] for p in ps]))}
           for pol in POLICIES}
    rank = sorted(POLICIES, key=lambda p: -agg[p]['mean'])
    cov, div = agg['coverage_only']['mean'], agg['diversity_only']['mean']
    spread = max(cov, div)
    targ = max(agg['uncertainty_only']['mean'], agg['guided']['mean'])
    return {'baseline_tail': float(np.mean([p['baseline_tail'] for p in ps])),
            'recover_mean_std': agg, 'rank': rank,
            'spread_gt_targeting': bool(spread > targ),         # 재현성 핵심 지표
            'guided_loses': bool(agg['guided']['mean'] < agg['random']['mean'])}


def exp_A(quick=False):
    """ablation 배터리 — 파일럿 필터 → 재현성(severity 전반) → capacity·ODD-feature 견고성.
    구동: python leaveout.py --expA [--quick].  산출: leaveout_battery.json"""
    D = load_data(quick)
    seeds = SEEDS[:2] if quick else SEEDS
    cands, meta = candidate_masks(D)
    print(f"[expA] 후보 결핍 {len(cands)}종 · 파일럿(seed0)으로 실재성 필터")

    # 1) 파일럿 필터: deficit_gap > PILOT_MIN_GAP 인 것만 채택
    pilots, real = {}, []
    for name, m in cands.items():
        p = pilot_deficit_gap(m, D, quick)
        pilots[name] = {**p, **meta[name]}
        ok = p['deficit_gap'] > PILOT_MIN_GAP
        pilots[name]['is_real_deficit'] = bool(ok)
        if ok:
            real.append(name)
        print(f"    {name:<20} gap={p['deficit_gap']:+.4f} n_tail={p['n_tail']}  "
              f"{'REAL' if ok else 'null'}")

    # 2) 재현성: 파일럿 통과 결핍마다 7정책 회복 → spread>targeting·guided 패 유지되나
    replication = {}
    for name in real:
        replication[name] = _run_battery_deficit(cands[name], D, quick, seeds)
        r = replication[name]
        print(f"    [rep] {name:<20} rank1={r['rank'][0]:<14} "
              f"spread>targ={r['spread_gt_targeting']} guided_loses={r['guided_loses']}")

    # 3) 견고성 축 — yaw(기존 대표 결핍) 기준
    ref = 'kin_yaw_p4' if 'kin_yaw_p4' in cands else (real[0] if real else next(iter(cands)))
    robustness = {'ref_deficit': ref, 'capacity_sweep': {}, 'odd_feature': None}
    for h in CAPACITY_SWEEP:
        r = _run_battery_deficit(cands[ref], D, quick, seeds, hidden=h)
        robustness['capacity_sweep'][str(h)] = {
            'rank': r['rank'], 'spread_gt_targeting': r['spread_gt_targeting'],
            'recover_mean_std': r['recover_mean_std']}
        print(f"    [cap {str(h):<10}] rank1={r['rank'][0]:<14} spread>targ={r['spread_gt_targeting']}")
    Xodd, n_oh = odd_onehot_X(D)
    r = _run_battery_deficit(cands[ref], D, quick, seeds, X=Xodd)
    robustness['odd_feature'] = {'n_onehot': n_oh, 'rank': r['rank'],
                                 'spread_gt_targeting': r['spread_gt_targeting'],
                                 'recover_mean_std': r['recover_mean_std']}
    print(f"    [ODD-feat +{n_oh}dim] rank1={r['rank'][0]:<14} spread>targ={r['spread_gt_targeting']}")

    out = {'params': {'seeds': seeds, 'severity_pctl': SEVERITY_PCTL,
                      'capacity_sweep': [str(h) for h in CAPACITY_SWEEP],
                      'pilot_min_gap': PILOT_MIN_GAP},
           'pilot': pilots, 'real_deficits': real,
           'replication': replication, 'robustness': robustness}
    tag = 'quick_' if quick else ''
    json.dump(out, open(os.path.join(OUT, f'{tag}leaveout_battery.json'), 'w'),
              ensure_ascii=False, indent=2)
    print(f"[expA] → {tag}leaveout_battery.json  (실재 결핍 {len(real)}/{len(cands)}종)")
    return out


# ============================ 실험 B: spread 결합 ============================
def combo_orders(cand, odd_keys, emb, rng):
    """실험 B 6정책 순위."""
    return {'random': list(rng.permutation(list(cand))),
            'coverage_only': coverage_order(cand, odd_keys, rng),
            'diversity_only': farthest_point(cand, emb, max(BUDGETS_B)),
            'cov_div_portfolio': portfolio_order(cand, odd_keys, emb, rng),
            'cov_div_strat': stratified_order(cand, odd_keys, emb, rng),
            'cov_div_mult': mult_order(cand, odd_keys, emb, rng)}


def run_combo_seed(tailA, tailB, D, quick, seed):
    """이질적 결핍(2영역) 한 seed: 정책×예산별 영역A·B·worst-case 회복."""
    clips, c2w, X, Y = D['clips'], D['c2w'], D['Xaug'], D['Y']
    is_tail = tailA | tailB
    rng = np.random.default_rng(seed)
    test_mask = np.zeros(len(clips), bool)
    for sub in (np.where(is_tail)[0], np.where(~is_tail)[0]):
        test_mask[rng.choice(sub, max(1, int(len(sub) * TEST_FRAC)), replace=False)] = True
    pool = clips[~test_mask]; pool_tail = is_tail[~test_mask]
    tail_clips = pool[pool_tail]
    common = pool[~pool_tail].copy(); rng.shuffle(common)
    n_cc = min(len(common) // 2, COMMON_MULT * len(tail_clips))
    cand_clips = np.concatenate([tail_clips, common[:n_cc]])
    base_rows = rows_for(common[n_cc:], c2w)
    tset = clips[test_mask]
    test_all = rows_for(tset, c2w)
    test_A = rows_for(tset[tailA[test_mask]], c2w)
    test_B = rows_for(tset[tailB[test_mask]], c2w)
    budgets = [b for b in (BUDGETS_B[::2] if quick else BUDGETS_B) if b <= len(cand_clips)]

    def ade_regions(train_rows):
        m = make_pipeline(StandardScaler(),
                          MLPRegressor(hidden_layer_sizes=(24,) if quick else (32, 16),
                                       max_iter=40 if quick else 60, early_stopping=True,
                                       n_iter_no_change=6, random_state=seed))
        m.fit(X[train_rows], Y[train_rows])

        def ade(rows):
            if len(rows) == 0:
                return float('nan')
            P = m.predict(X[rows]).reshape(-1, 6, 2); G = Y[rows].reshape(-1, 6, 2)
            return float(np.linalg.norm(P - G, axis=2).mean())
        return ade(test_A), ade(test_B)

    base_A, base_B = ade_regions(base_rows)
    orders = combo_orders(cand_clips, D['odd_keys'], D['emb_raw'], rng)
    res = {}
    for pol in POLICIES_B:
        res[pol] = {}
        for b in budgets:
            add_rows = rows_for(orders[pol][:b], c2w)
            a, bb = ade_regions(np.concatenate([base_rows, add_rows]))
            recA, recB = base_A - a, base_B - bb
            res[pol][b] = {'recover_A': recA, 'recover_B': recB,
                           'recover_worst': float(min(recA, recB))}
    return {'baseline_A': base_A, 'baseline_B': base_B,
            'n_cand': int(len(cand_clips)), 'budgets': budgets, 'policies': res}


def exp_B(quick=False, tailA_spec=('kin', 2, 98), tailB_spec=('kin', 0, 92)):
    """spread 결합 × 이질적 결핍. spec=(kind, col, pctl).
    기본 = expA 검증으로 확정된 최반대선호 쌍:
      tailA=a_lat@p2(col2,pctl98) — diversity 우세(div>cov)
      tailB=speed@p8(col0,pctl92) — coverage 우세(cov≫div, div 최약)
    → coverage-only는 A영역, diversity-only는 B영역에서 각각 worst-case 취약 → 결합 헤지 시험(§8.3).
    구동: python leaveout.py --expB [--quick].  산출: leaveout_spread_combo.json"""
    D = load_data(quick)
    seeds = SEEDS[:2] if quick else SEEDS

    def build(spec):
        kind, col, pctl = (spec + (96,))[:3]     # pctl 생략 시 p4(=96)
        agg = clip_feature_max(D['grp'], D['X'], col, D['clips'])
        return agg >= np.percentile(agg, pctl)
    tailA, tailB = build(tailA_spec), build(tailB_spec)
    print(f"[expB] tailA={tailA_spec}({tailA.sum()}) tailB={tailB_spec}({tailB.sum()}) "
          f"overlap={int((tailA & tailB).sum())}")

    per_seed = [run_combo_seed(tailA, tailB, D, quick, s) for s in seeds]
    budgets = per_seed[0]['budgets']
    agg = {}
    for pol in POLICIES_B:
        agg[pol] = {}
        for b in budgets:
            for key in ('recover_A', 'recover_B', 'recover_worst'):
                vals = [ps['policies'][pol][b][key] for ps in per_seed]
                agg[pol].setdefault(b, {})[key] = {'mean': float(np.mean(vals)),
                                                   'std': float(np.std(vals))}
    # 판정: 최대 예산에서 결합(portfolio/strat)이 worst-case로 단일 spread 초과하나
    bmax = budgets[-1]
    baseA = float(np.mean([ps['baseline_A'] for ps in per_seed]))
    baseB = float(np.mean([ps['baseline_B'] for ps in per_seed]))
    worst = lambda p: agg[p][bmax]['recover_worst']['mean']
    # baseline 정규화 worst — 영역 난이도 불균형(R2) defuse: 각 영역 회복을 자기 baseline으로 나눔
    worst_n = lambda p: min(agg[p][bmax]['recover_A']['mean'] / baseA,
                            agg[p][bmax]['recover_B']['mean'] / baseB)
    single = max(worst('coverage_only'), worst('diversity_only'))
    single_n = max(worst_n('coverage_only'), worst_n('diversity_only'))
    verdict = {'budget': bmax,
               'portfolio_gt_single_worst': bool(worst('cov_div_portfolio') > single),
               'strat_gt_single_worst': bool(worst('cov_div_strat') > single),
               'mult_fails': bool(worst('cov_div_mult') < single),
               'worst_values': {p: worst(p) for p in POLICIES_B},
               'portfolio_gt_single_worst_norm': bool(worst_n('cov_div_portfolio') > single_n),
               'strat_gt_single_worst_norm': bool(worst_n('cov_div_strat') > single_n),
               'worst_values_norm': {p: worst_n(p) for p in POLICIES_B}}
    out = {'params': {'seeds': seeds, 'budgets': budgets,
                      'tailA_spec': list(tailA_spec), 'tailB_spec': list(tailB_spec),
                      'note': 'tailA/tailB는 실험 A 파일럿 통과 결핍으로 교체 권장(§8.3)'},
           'baseline': {'A': float(np.mean([ps['baseline_A'] for ps in per_seed])),
                        'B': float(np.mean([ps['baseline_B'] for ps in per_seed]))},
           'agg': agg, 'verdict': verdict}
    tag = 'quick_' if quick else ''
    json.dump(out, open(os.path.join(OUT, f'{tag}leaveout_spread_combo.json'), 'w'),
              ensure_ascii=False, indent=2)
    print(f"[expB] worst-case@{bmax}: " +
          " ".join(f"{p}={worst(p):+.4f}" for p in POLICIES_B))
    print(f"[expB] portfolio>single={verdict['portfolio_gt_single_worst']} "
          f"strat>single={verdict['strat_gt_single_worst']} mult_fails={verdict['mult_fails']}")
    print(f"[expB] → {tag}leaveout_spread_combo.json")
    return out


def demo():
    """rows_for·coverage·FPS·emb_nbhd_error + 실험 B 결합정책 형태 검증."""
    c2w = {1: [10, 11], 2: [20], 3: []}
    assert set(rows_for([1, 2, 3], c2w).tolist()) == {10, 11, 20}
    rng = np.random.default_rng(0)
    keys = {1: 'a', 2: 'a', 3: 'b', 4: 'c'}
    cov = coverage_order([1, 2, 3, 4], keys, rng)
    assert set(cov) == {1, 2, 3, 4}
    emb = np.eye(4).astype(float)
    fp = farthest_point([0, 1, 2, 3], emb, 3)
    assert set(fp) == {0, 1, 2, 3} and len(fp) == 4
    # 결합 정책: 셋 다 cand 전체의 순열이어야(중복·누락 없음)
    for fn in (lambda: portfolio_order([0, 1, 2, 3], {0: 'a', 1: 'a', 2: 'b', 3: 'c'}, emb, rng),
               lambda: stratified_order([0, 1, 2, 3], {0: 'a', 1: 'a', 2: 'b', 3: 'c'}, emb, rng),
               lambda: mult_order([0, 1, 2, 3], {0: 'a', 1: 'a', 2: 'b', 3: 'c'}, emb, rng)):
        o = fn()
        assert set(o) == {0, 1, 2, 3} and len(o) == 4, o
    # portfolio: 앞 2개는 coverage·diversity에서 각각 최소 1개(반반) — round-robin 병합
    clip_max = clip_feature_max(np.array([0, 0, 1, 2]), np.array([[5.], [1.], [3.], [9.]]), 0,
                                np.array([0, 1, 2]))
    assert clip_max.tolist() == [5.0, 3.0, 9.0]        # clip0 max(5,1)=5
    # emb_neighborhood_error
    ne = emb_neighborhood_error(np.array([0, 1, 2, 3]),
                                np.array([[0.0], [0.05], [10.0], [10.05]]),
                                {0: 1.0, 1: 0.0, 2: 1.0, 3: 1.0}, k=1)
    assert ne[0] == 0.0 and ne[1] == 1.0
    print("demo ✓  helpers + portfolio/strat/mult + clip_feature_max 검증 통과")


if __name__ == '__main__':
    q = '--quick' in sys.argv
    if '--demo' in sys.argv:
        demo()
    elif '--expA' in sys.argv:
        exp_A(q)
    elif '--expB' in sys.argv:
        exp_B(q)
    else:
        main(q)
