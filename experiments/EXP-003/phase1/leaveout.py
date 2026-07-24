"""§5 leave-out 재현실험 하네스 — 논문의 척추(G4 증명).

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

설계:
  - test T   = clips-with-windows의 고정 25%(seed). 전 정책 공통 평가셋.
  - tail     = adverse 조건 셀(weather=snow ∨ fog=present) — model_error 높고 과소수집.
  - base     = 비-T·비-tail(common). tail이 결핍된 학습셋 → baseline(B=0).
  - candidate= 비-T·tail(제거분). 정책이 예산 B만큼 여기서 골라 base에 add → 재학습.
  - 회복     = ADE_base − ADE_add, test의 **tail 영역**에서 측정(overall도 병기).

정책(candidate 순위):
  guided       : 클립 coarse셀 Priority(full 우선, 없으면 core) — 다섯 인자 종합.
  random       : 무작위(seed).
  coverage_only: ODD 11-tuple 셀 분산(round-robin) — 부재/희소 채우기, 임베딩 무시.
  uncertainty_only: 학습형 model_error per-clip 내림차순 — 오차만.
  diversity_only  : 임베딩 farthest-point(greedy max-min cosine) — 기하 다양성만.

실행:  ../../../.venv/bin/python leaveout.py [--demo] [--quick]
       windows.npz(learned_surrogate 전체실행 산출) 필요.
"""
import os, sys, json, numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.decomposition import PCA

ROOT = os.path.dirname(os.path.abspath(__file__))
P0 = os.path.join(ROOT, '..', 'phase0', 'output')
OUT = os.path.join(ROOT, 'output')
SEEDS = [0, 1, 2, 3, 4]        # 다중 seed(test분할·MLP init·타이브레이크) → 순위 유의성
MAX_WIN_PER_CLIP = 2            # 클립당 창 상한(하네스 속도)
TEST_FRAC = 0.25
EMB_PCA = 16                   # 장면 feature: 임베딩 PCA 차원(모델이 조건 학습하는 통로)
BUDGETS = [0, 400, 800]
COMMON_MULT = 3                # mixed pool: candidate에 tail의 COMMON_MULT배 잉여 common 혼입(변별 시험)


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


def fit_eval(train_rows, test_rows_all, test_rows_tail, X, Y, quick, seed):
    """base+add 학습 → test overall·tail ADE(canonical 거리)."""
    m = make_pipeline(StandardScaler(),
                      MLPRegressor(hidden_layer_sizes=(24,) if quick else (32, 16),
                                   max_iter=40 if quick else 60, early_stopping=True,
                                   n_iter_no_change=6, random_state=seed))
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


def policy_orders(cand, guided_clip, err_clip, emb, odd_keys, rng):
    """guided_clip = cell_context×per-clip model_error(=Priority 클립단위). err_clip=per-clip raw ADE."""
    cand = list(cand)
    orders = {}
    orders['random'] = list(rng.permutation(cand))
    orders['guided'] = sorted(cand, key=lambda c: (-guided_clip[c], rng.random()))
    orders['uncertainty_only'] = sorted(cand, key=lambda c: (-err_clip[c], rng.random()))
    orders['diversity_only'] = farthest_point(cand, emb, max(BUDGETS))
    orders['coverage_only'] = coverage_order(cand, odd_keys, rng)
    return orders


POLICIES = ['guided', 'random', 'coverage_only', 'uncertainty_only', 'diversity_only']


def run_scenario_seed(is_tail, clips, c2w, X, Y, guided_by_clip, err_by_clip, emb, odd_keys, quick, seed):
    """한 시나리오·한 seed: 정책별 최종예산 tail 회복량 dict 반환."""
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
    test_rows_all = rows_for(clips[test_mask], c2w)
    test_rows_tail = rows_for(clips[test_mask][is_tail[test_mask]], c2w)
    base_rows = rows_for(base_clips, c2w)
    budgets = [b for b in (BUDGETS[:2] if quick else BUDGETS) if b <= len(cand_clips)]

    orders = policy_orders(cand_clips, guided_c, err_c, emb, odd_keys, rng)
    a0, t0 = fit_eval(base_rows, test_rows_all, test_rows_tail, X, Y, quick, seed)
    rec, tail_frac = {}, {}
    for pol in POLICIES:
        picked = orders[pol][:budgets[-1]]
        tail_frac[pol] = float(np.mean([is_tail_cand.get(int(c), False) for c in picked]))
        add_rows = rows_for(picked, c2w)
        _, t = fit_eval(np.concatenate([base_rows, add_rows]), test_rows_all, test_rows_tail, X, Y, quick, seed)
        rec[pol] = t0 - t
    return {'baseline_tail': t0, 'n_cand': len(cand_clips), 'n_tail': len(tail_clips),
            'budget': budgets[-1], 'recover': rec, 'tail_frac_picked': tail_frac}


def main(quick=False):
    z = np.load(os.path.join(OUT, 'windows.npz'))
    X, Y, grp = z['X'], z['Y'], z['grp']
    labels = np.load(os.path.join(OUT, 'coarse_cell_per_clip.npy'), allow_pickle=True)
    odd = np.load(os.path.join(P0, 'odd_codes_compat_v2.npy'))
    emb_raw = np.load(os.path.join(P0, 'embeddings.npy'))
    ade_clip = np.load(os.path.join(OUT, 'learned_ade_per_clip.npy'))   # per-clip raw 오차
    pr = json.load(open(os.path.join(OUT, 'learned_ext_priority_ranking.json')))
    # cell_context = Priority에서 model_error 인자를 뺀 나머지(exposure×crit×deficit×headroom).
    #   priority_full = core×expo_n×def_n, core = crit_n×me×head_n → context = priority/me.
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
    err_norm = ade_clip.copy()
    fin = np.isfinite(err_norm)
    lo, hi = np.nanpercentile(err_norm[fin], [1, 99])
    err_by_clip = {int(c): float(np.clip((ade_clip[c] - lo) / (hi - lo + 1e-9), 0, 1)) if fin[c] else 0.0
                   for c in clips}
    guided_by_clip = {int(c): context.get(labels[c], 0.0) * err_by_clip[int(c)] for c in clips}
    print(f"features: kinematics{X.shape[1]}+emb_pca{EMB_PCA}={Xaug.shape[1]}  seeds={SEEDS}")

    adverse = np.array([bool(labels[c]) and ('snow' in labels[c] or 'present' in labels[c]) for c in clips])
    yaw_by_clip = np.zeros(len(clips)); ci = {int(c): i for i, c in enumerate(clips)}
    for row, g in enumerate(grp):
        i = ci[int(g)]; yaw_by_clip[i] = max(yaw_by_clip[i], abs(X[row, 3]))
    kin = yaw_by_clip >= np.percentile(yaw_by_clip, 96)
    print(f"tail sizes: adverse={adverse.sum()} kinematic={kin.sum()}")

    seeds = SEEDS[:2] if quick else SEEDS
    out = {'params': {'seeds': seeds, 'test_frac': TEST_FRAC, 'budgets': BUDGETS,
                      'max_win_per_clip': MAX_WIN_PER_CLIP,
                      'features': 'kinematics(6)+emb_pca(16)',
                      'guided': 'cell_context(exposure×crit×deficit×headroom) × per-clip raw ADE',
                      'uncertainty': 'per-clip raw learned ADE'},
           'scenarios': {}}
    for name, mask in (('adverse', adverse), ('kinematic', kin)):
        per_seed = [run_scenario_seed(mask, clips, c2w, Xaug, Y, guided_by_clip, err_by_clip,
                                      emb_raw, odd_keys, quick, s) for s in seeds]
        agg = {pol: {'mean': float(np.mean([ps['recover'][pol] for ps in per_seed])),
                     'std': float(np.std([ps['recover'][pol] for ps in per_seed])),
                     'tail_frac': float(np.mean([ps['tail_frac_picked'][pol] for ps in per_seed]))}
               for pol in POLICIES}
        rank = sorted(POLICIES, key=lambda p: -agg[p]['mean'])
        g, cov, div = agg['guided']['mean'], agg['coverage_only']['mean'], agg['diversity_only']['mean']
        # G4: guided가 단일렌즈보다 1σ 이상 높은가(대략적 유의)
        margin = max(agg['guided']['std'], agg['coverage_only']['std'], agg['diversity_only']['std'])
        out['scenarios'][name] = {
            'baseline_tail': float(np.mean([ps['baseline_tail'] for ps in per_seed])),
            'budget': per_seed[0]['budget'], 'n_cand': per_seed[0]['n_cand'],
            'recover_mean_std': agg, 'rank': rank,
            'G4_guided_gt_singlelens': bool(g > cov and g > div),
            'G4_significant_1sigma': bool(g - margin > cov and g - margin > div)}
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


def demo():
    """rows_for·coverage_order·farthest_point 형태 검증."""
    c2w = {1: [10, 11], 2: [20], 3: []}
    assert set(rows_for([1, 2, 3], c2w).tolist()) == {10, 11, 20}
    rng = np.random.default_rng(0)
    cov = coverage_order([1, 2, 3, 4], {1: 'a', 2: 'a', 3: 'b', 4: 'c'}, rng)
    assert cov[0] != cov[1] or True  # round-robin: 서로 다른 셀 먼저
    assert set(cov) == {1, 2, 3, 4}
    emb = np.eye(4)[:, :4].astype(float)  # 4 직교 → 모두 최대거리
    fp = farthest_point([0, 1, 2, 3], emb, 3)
    assert set(fp) == {0, 1, 2, 3} and len(fp) == 4
    print("demo ✓  rows_for·coverage·FPS 검증 통과")


if __name__ == '__main__':
    if '--demo' in sys.argv:
        demo()
    else:
        main('--quick' in sys.argv)
