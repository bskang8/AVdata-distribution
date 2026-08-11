"""
두 렌즈(ODD × 임베딩)의 상호보완성 실증 — 양방향 직교성 증명
================================================================

■ 이 스크립트가 답하는 질문
   Phase 0는 데이터셋을 두 가지 렌즈로 진단했다.
     - ODD 렌즈   : 이산 조합 격자(11필드 튜플) — "어떤 '조건'에서 달렸나"
     - 임베딩 렌즈 : bge-m3 캡션 임베딩의 밀도/다양성 — "무슨 '장면'이 벌어졌나"
   슬라이드 §3의 주장 = "두 렌즈는 중복도 잡음도 아닌 상호보완"이다.
   그런데 상관계수 하나(ρ=0.221)로는 이 주장을 증명할 수 없다 — 낮은 상관은
     (a) 상호보완일 수도, (b) 임베딩이 그냥 노이즈일 수도 있어 둘을 못 가른다.
   이 스크립트는 상관 대신 **양방향 구성적 증거**로 (b)를 반박하고 (a)를 증명한다.

■ 증명 논리 (양방향 잔차)
   한 렌즈를 '고정'했을 때 다른 렌즈의 다양성이 얼마나 살아남는지를 잰다.
     - 실증① : ODD 튜플이 '완전 동일'한 클립들(=ODD 다양성 0) 안에서 임베딩 Vendi를 잰다.
               임베딩이 ODD로 결정된다면 Vendi는 1로 붕괴해야 한다.
               → 크게 남으면(≈전역값) 임베딩 방향은 ODD 셀과 '직교'.
     - 실증② : 임베딩상 최근접(코사인 높음=임베딩이 '같다'고 본) 이웃들 안에서 ODD 분산을 잰다.
               임베딩이 ODD를 완전히 담는다면 이웃의 ODD Hamming은 0이어야 한다.
               → 크게 남으면 ODD는 임베딩이 뭉갠 구분을 해상.
   둘 다 큰 잔차가 남으면 = 양방향 blind spot = 진짜 상호보완(개념이 아니라 관측).

■ 슬라이드(§3, 13·14p)에 실린 산출 숫자
     실증① : ODD-동일 6,578클립 → 임베딩 Vendi 3.17 = 무작위 동일크기(3.53)의 89.9%
     실증② : 임베딩 20-NN(코사인 0.939) → ODD Hamming 0.165 vs 무작위 0.297 = 56% 보존,
             가장 닮은 이웃 20개 묶음이 평균 ~11개 ODD 조합에 걸침
   → 비대칭(90% vs 56%) 자체가 인사이트: 임베딩은 ODD를 일부(≈44%)만 잡고,
     ODD는 임베딩 변주를 거의(≈10%만) 못 본다.

■ 입력 (전부 Phase 0가 이미 만든 산출물, 재집계 없음)
     output/clip_ids.npy          : 행 순서 ↔ 클립 UUID
     output/embeddings.npy        : (N,1024) L2-정규화 캡션 임베딩 (행=clip_ids)
     output/knn_foundation.npz    : knn_idx·knn_sim (N,50) 임베딩 최근접이웃
     ODD_DIR/<uuid>.json          : 클립별 ODD 원태그 → step_a 크로스워크로 compat_v2 튜플
     CAPTIONS_DIR/<uuid>.*.txt    : 실증① 하위그룹 명명(TF-IDF)용

■ 재현
     ../../../.venv/bin/python analysis_two_lens.py      (numpy≥2, scikit-learn 필요)
   첫 실행은 ODD 태그 10만 파일을 읽어 ~80초. 이후는 output/odd_codes_compat_v2.npy 캐시로 빠름.

관련: docs/wiki/evaluation/coverage-vs-sufficiency.md(개념틀),
      experiments/EXP-003/phase0/output/methodology_direction_analysis.md §0.5(주장 정리),
      slides/deck.md §3(이 숫자가 실린 곳).
"""
import os
import sys
import json
import numpy as np
from collections import Counter

# 이 파일이 있는 phase0 디렉터리를 import 경로에 추가 → CWD와 무관하게 동작
PHASE0 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PHASE0)
# 위험한 ODD 크로스워크는 step_a에 단일 출처로 두고 '재사용'만 한다(복제 금지).
# step_a는 __main__ 가드가 있어 import해도 파이프라인이 돌지 않는다.
from step_a_odd_coverage import _to_compat_v2, _flatten_final, COMPAT_V2_DIMS  # noqa: E402
from config import ODD_DIR, CAPTIONS_DIR                                        # noqa: E402

OUTPUT = os.path.join(PHASE0, 'output')
SEED = 0  # 앵커·무작위 대조군 재현용 고정 시드


# ─────────────────────────────────────────────────────────────────────────────
# 공통 로딩 — 임베딩 · 클립ID · 각 클립의 ODD(compat_v2) 튜플/정수코드
# ─────────────────────────────────────────────────────────────────────────────
def load_common():
    """embeddings·clip_ids와, 각 클립의 compat_v2 표현을 두 형태로 만든다.
       - tuples : 원본 문자열 튜플 리스트 (실증①에서 '가장 흔한 셀' 식별·명명에 사용)
       - codes  : (N,11) 정수 코드 배열   (실증②에서 Hamming 거리 계산에 사용)
       codes는 첫 실행 때만 계산하고 output/에 캐시(10만 json 재파싱 회피)."""
    clip_ids = np.load(os.path.join(OUTPUT, 'clip_ids.npy'), allow_pickle=True)
    emb = np.load(os.path.join(OUTPUT, 'embeddings.npy'))   # (N,1024), 각 행 L2-norm=1
    N = len(clip_ids)
    assert emb.shape[0] == N, '임베딩과 clip_ids 행 수 불일치'

    def tuple_for(cid):
        # 클립 1개의 ODD 원태그 → 플래튼 → AV성능 11필드(compat_v2) → 값 튜플
        with open(os.path.join(ODD_DIR, cid + '.json')) as f:
            d = json.load(f)
        rec = _to_compat_v2(_flatten_final(d['odd_final']))
        return tuple(rec[k] for k in COMPAT_V2_DIMS)

    tuples = [tuple_for(c) for c in clip_ids]   # 행 정렬 = clip_ids = emb

    cache = os.path.join(OUTPUT, 'odd_codes_compat_v2.npy')
    if os.path.exists(cache):
        codes = np.load(cache)
    else:
        # 필드마다 등장 값에 정수 id를 부여(값 자체는 무의미, '같다/다르다'만 필요)
        vocab = [{} for _ in COMPAT_V2_DIMS]
        codes = np.zeros((N, 11), dtype=np.int16)
        for i, t in enumerate(tuples):
            for j, v in enumerate(t):
                codes[i, j] = vocab[j].setdefault(v, len(vocab[j]))
        np.save(cache, codes)
    return clip_ids, emb, tuples, codes


# ─────────────────────────────────────────────────────────────────────────────
# Vendi Score — "실질적으로 몇 개의 독립 방향인가"
#   커널(코사인 유사도) 행렬 고유값 분포의 엔트로피를 지수화(= Hill number).
#   임베딩이 L2-정규화라 A@A.T가 곧 코사인 유사도 행렬.
#   파이프라인(step_b)과 동일하게 2000 앵커로 근사하고 여러 run 평균.
# ─────────────────────────────────────────────────────────────────────────────
def vendi_once(A):
    A = A.astype(np.float64)
    K = A @ A.T                                    # (m,m) 코사인 유사도
    ev = np.maximum(np.linalg.eigvalsh(K), 0)      # 고유값(음수는 수치오차 → 0)
    p = ev / (ev.sum() + 1e-12)                     # 확률분포로 정규화
    return float(np.exp(-np.sum(p * np.log(p + 1e-12))))   # exp(엔트로피)


def vendi_pool(pool, rng, n_anchor=2000, runs=10):
    """pool에서 n_anchor개를 여러 번 뽑아 Vendi 평균±표준편차."""
    s = [vendi_once(pool[rng.choice(len(pool), min(n_anchor, len(pool)), replace=False)])
         for _ in range(runs)]
    return float(np.mean(s)), float(np.std(s))


# ─────────────────────────────────────────────────────────────────────────────
# 실증① — ODD가 '한 상황'이라는 셀 안에서 임베딩은 몇 방향을 보는가
#   가장 흔한 ODD 튜플(→ 그 셀의 ODD 다양성은 정의상 0)을 골라, 그 클립들만의
#   임베딩 Vendi를 무작위 동일크기 대조군과 비교한다.
# ─────────────────────────────────────────────────────────────────────────────
def analysis1_within_cell(clip_ids, emb, tuples, rng):
    N = len(clip_ids)
    top_tuple, top_n = Counter(tuples).most_common(1)[0]
    cell_idx = np.array([i for i, t in enumerate(tuples) if t == top_tuple])
    cell_emb = emb[cell_idx]

    print('\n' + '=' * 70)
    print('실증① — ODD-동일 셀 안의 임베딩 다양성')
    print('=' * 70)
    print(f'가장 흔한 ODD 조합 = {top_n} 클립 (ODD 튜플 완전 동일 → ODD entropy=0.000)')
    print('  ', dict(zip(COMPAT_V2_DIMS, top_tuple)))

    v_cell, sd_cell = vendi_pool(cell_emb, rng)
    rand_pool = emb[rng.choice(N, len(cell_idx), replace=False)]   # 동일크기 무작위
    v_rand, sd_rand = vendi_pool(rand_pool, rng)
    print(f'\n  셀 내부 임베딩 Vendi   = {v_cell:.3f} ± {sd_cell:.3f}')
    print(f'  무작위 동일크기 Vendi  = {v_rand:.3f} ± {sd_rand:.3f}  (전역 random≈3.53)')
    print(f'  → 다양성 보존율 = {v_cell / v_rand:.1%}  '
          f'(임베딩∼ODD였다면 Vendi→1이어야; 크게 남음 = 임베딩 ⊥ ODD 셀)')

    # 이웃 유사도로 '동일 복제가 아님'을 확인 (퍼져 있어야 위 Vendi가 의미 있음)
    sub = cell_emb[rng.choice(len(cell_emb), 1500, replace=False)]
    sims = sub @ sub.T
    np.fill_diagonal(sims, -1)
    print(f'  셀 내부 최근접 코사인 median = {np.median(sims.max(axis=1)):.3f} (복제 아님)')

    _name_subgroups(clip_ids, cell_idx, cell_emb, rng)


def _name_subgroups(clip_ids, cell_idx, cell_emb, rng):
    """셀 내부 하위그룹을 캡션 TF-IDF 상위어로 명명 → '남은 변주'가 이름 붙는
       실제 장면구분(=content)임을 보인다. ODD 11축엔 없는 축."""
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    from sklearn.feature_extraction.text import TfidfVectorizer

    # 자연 클러스터 수 K를 실루엣으로 선택 (2000 표본에서)
    Xs = cell_emb[rng.choice(len(cell_emb), 2000, replace=False)]
    best_k, best_s = 2, -1.0
    for k in (2, 3, 4, 5, 6):
        lbl = KMeans(k, n_init=4, random_state=SEED).fit(Xs).labels_
        s = silhouette_score(Xs, lbl)
        if s > best_s:
            best_k, best_s = k, s
    labels = KMeans(best_k, n_init=8, random_state=SEED).fit(cell_emb).labels_

    def caption(cid):
        p = os.path.join(CAPTIONS_DIR, cid + '.camera_front_wide_120fov.txt')
        return open(p).read() if os.path.exists(p) else ''

    caps = [caption(clip_ids[i]) for i in cell_idx]
    # ego·vehicle·road 등 셀 전체 공통어는 stop 처리(변별력 없음)
    stop = ('the a an and or of to in on at with was were is are ego vehicle '
            'road lane its along traveled travels').split()
    vec = TfidfVectorizer(stop_words=stop, max_features=4000, ngram_range=(1, 2), min_df=5)
    X = vec.fit_transform(caps)
    terms = np.array(vec.get_feature_names_out())
    print(f'\n  하위그룹 명명 (K={best_k}, silhouette={best_s:.3f} — 낮으면 연속 스펙트럼):')
    for c in range(best_k):
        m = labels == c
        centroid = np.asarray(X[m].mean(axis=0)).ravel()
        top = ', '.join(terms[centroid.argsort()[::-1][:8]])
        print(f'    그룹{c} (n={int(m.sum()):>4}): {top}')


# ─────────────────────────────────────────────────────────────────────────────
# 실증② — 임베딩이 '같다'고 본 이웃 안에서 ODD가 갈리는가 (실증①의 대칭)
#   임베딩 최근접이웃(코사인 높음)의 ODD Hamming 거리를 무작위 대조군과 비교.
# ─────────────────────────────────────────────────────────────────────────────
def analysis2_within_neighborhood(clip_ids, codes, rng, K=20, n_anchor=4000):
    z = np.load(os.path.join(OUTPUT, 'knn_foundation.npz'))
    knn_idx, knn_sim = z['knn_idx'], z['knn_sim']    # (N,50): 임베딩 최근접 50이웃
    N = len(clip_ids)

    def hamming(a, b):   # 정규화 Hamming(0~1): 11필드 중 다른 비율
        return (a != b).mean(axis=-1)

    anchors = rng.choice(N, n_anchor, replace=False)
    nn_h, rand_h, nn_sim = [], [], []
    for a in anchors:
        nbr = knn_idx[a, 1:K + 1]                      # 자기(col0) 제외, 임베딩 20-NN
        nn_h.append(hamming(codes[a], codes[nbr]).mean())      # 이웃의 ODD 차이
        nn_sim.append(knn_sim[a, 1:K + 1].mean())              # 이웃의 임베딩 유사도
        rand_h.append(hamming(codes[a], codes[rng.choice(N, K, replace=False)]).mean())
    nn_h, rand_h = np.array(nn_h), np.array(rand_h)

    print('\n' + '=' * 70)
    print('실증② — 임베딩 이웃 안의 ODD 분산 (대칭 증거)')
    print('=' * 70)
    print(f'  임베딩 20-NN 평균 코사인 = {np.mean(nn_sim):.3f} (임베딩상 "거의 같음")')
    print(f'  그 이웃의 ODD Hamming    = {nn_h.mean():.3f}')
    print(f'  무작위 20개의 ODD Hamming = {rand_h.mean():.3f}')
    print(f'  → ODD 분산 보존율 = {nn_h.mean() / rand_h.mean():.1%}  '
          f'(임베딩이 "같다"는 이웃도 ODD는 이만큼 갈림)')

    # 가장 닮은 이웃 20개 묶음이 몇 개의 서로 다른 ODD 조합에 걸치나(1=완전정렬)
    # 위 55% 보존과 동일한 '상위 20 이웃' 집합을 써서 기준을 하나로 통일(0.95 컷 안 씀).
    spans = [len({tuple(r) for r in np.vstack([codes[a], codes[knn_idx[a, 1:K + 1]]])})
             for a in anchors]
    print(f'  가장 닮은 이웃 20개 묶음당 서로 다른 ODD 조합 수 = 평균 {np.mean(spans):.2f}개')

    _show_counterexamples(clip_ids, codes, knn_idx, knn_sim, rng)


def _show_counterexamples(clip_ids, codes, knn_idx, knn_sim, rng, n=6):
    """임베딩상 거의 동일(코사인>0.95)한데 ODD가 다른 실제 쌍 — 어느 안전축이
       갈리는지 보인다(clear↔fog, urban↔rural 등)."""
    def raw(i):
        with open(os.path.join(ODD_DIR, clip_ids[i] + '.json')) as f:
            d = json.load(f)
        rec = _to_compat_v2(_flatten_final(d['odd_final']))
        return {k: rec[k] for k in COMPAT_V2_DIMS}

    print('\n  반례 (cos>0.95인데 ODD 갈리는 쌍 — 갈리는 축):')
    shown = 0
    for a in rng.permutation(len(clip_ids)):
        j = int(knn_idx[a, 1])
        if knn_sim[a, 1] > 0.95 and (codes[a] != codes[j]).any():
            ta, tj = raw(a), raw(j)
            diff = {k: (ta[k], tj[k]) for k in ta if ta[k] != tj[k]}
            print(f'    cos={knn_sim[a, 1]:.3f}  {diff}')
            shown += 1
            if shown >= n:
                break


# ─────────────────────────────────────────────────────────────────────────────
# 실증③(심화) — 가장 흔한 ODD 셀의 임베딩 이웃은 같은/다른 조합으로 새는가
#   실증②의 '셀-특화 하드라벨' 버전. 6,578클립 각각의 임베딩 k-NN이 같은 ODD
#   조합인지 세되, 반드시 '무작위 이웃이 같을 확률(기저율)' 대비 lift로 해석한다
#   (top 셀은 6.55%를 차지 → 통제 없이는 same 비율이 부풀려져 거짓 정렬로 보임).
#   추가로 (필드-flip 분포)로 '얼마나' 다른지, (혼동 구조)로 '어디로/어느 축이'
#   새는지를 이름으로 뽑는다 → 임베딩이 무시하는 ODD 축을 정량 지목.
# ─────────────────────────────────────────────────────────────────────────────
def analysis3_top_cell_neighbors(clip_ids, codes, knn_idx, K=20):
    N = len(clip_ids)

    def raw_rec(i):   # 코드→사람이 읽는 값 매핑 (명명용, 대표 클립 몇 개만 읽음)
        with open(os.path.join(ODD_DIR, clip_ids[i] + '.json')) as f:
            d = json.load(f)
        return _to_compat_v2(_flatten_final(d['odd_final']))

    # top 셀 = codes에서 가장 흔한 행
    uniq, cnt = np.unique(codes, axis=0, return_counts=True)
    top_c = uniq[cnt.argmax()]
    cell_idx = np.where((codes == top_c).all(axis=1))[0]
    base = (len(cell_idx) - 1) / (N - 1)      # 무작위 이웃이 same-combo일 확률(기저율)

    nbr = knn_idx[cell_idx, 1:K + 1]          # (M,K) 임베딩 k-NN (자기 제외)
    nbr_codes = codes[nbr]                     # (M,K,11)
    same = (nbr_codes == top_c).all(axis=2)    # (M,K) 이웃이 same-combo?
    same_frac = float(same.mean())
    same_k1 = float((codes[knn_idx[cell_idx, 1]] == top_c).all(axis=1).mean())

    print('\n' + '=' * 70)
    print('실증③ — top ODD 셀의 임베딩 이웃 혼동 구조 (기저율 통제)')
    print('=' * 70)
    print(f'  셀 크기 {len(cell_idx)} / 전체 {N}  → 기저율(무작위 same) = {base:.1%}')
    print(f'  임베딩 {K}-NN 중 same-combo 비율 = {same_frac:.1%}  '
          f'(lift = {same_frac / base:.1f}×)')
    print(f'  최근접 1개 same-combo 비율      = {same_k1:.1%}  (lift = {same_k1 / base:.1f}×)')
    print(f'  → 정렬은 있으나(lift>1) 최근접 이웃의 {1 - same_k1:.0%}가 여전히 다른 조합')

    # (1) 필드-flip 분포: 이웃이 top 셀과 몇 개 필드 다른가 (0=same combo)
    fdiff = (nbr_codes != top_c).sum(axis=2).ravel()
    hist = np.bincount(fdiff, minlength=12)
    print('\n  [필드-flip 분포] 이웃이 top 셀과 다른 필드 수 (전체 {}쌍):'.format(fdiff.size))
    for d in range(6):
        print(f'    {d}필드 차이: {hist[d]:>6} ({hist[d] / fdiff.size:>5.1%})'
              + ('  ← same combo' if d == 0 else ''))
    print(f'    6+필드      : {hist[6:].sum():>6} ({hist[6:].sum() / fdiff.size:>5.1%})')

    # (2) 혼동 구조: different 이웃이 향하는 상위 조합 + 대표 클립 명명
    diff_pos = ~same
    diff_codes = nbr_codes[diff_pos]
    diff_clip = nbr[diff_pos]
    du, du_idx, du_cnt = np.unique(diff_codes, axis=0, return_index=True, return_counts=True)
    top_vals = raw_rec(cell_idx[0])
    print('\n  [혼동 구조] 다른 조합 이웃이 향하는 상위 조합 (갈리는 축):')
    for r in du_cnt.argsort()[::-1][:8]:
        vals = raw_rec(int(diff_clip[du_idx[r]]))
        diff = {k: f'{top_vals[k]}→{vals[k]}' for k in COMPAT_V2_DIMS if top_vals[k] != vals[k]}
        print(f'    n={du_cnt[r]:>5} ({du_cnt[r] / diff_codes.shape[0]:>5.1%})  {diff}')

    # (3) 축별 flip율: 다른 조합 이웃 중 각 필드가 top 셀과 다른 비율 (임베딩 무시 축)
    axis_flip = (diff_codes != top_c).mean(axis=0)
    print('\n  [축별 flip율] 다른 조합 이웃에서 각 ODD 축이 갈리는 비율 (높을수록 임베딩이 무시):')
    for j in np.argsort(axis_flip)[::-1]:
        print(f'    {COMPAT_V2_DIMS[j]:<22} {axis_flip[j]:>5.1%}  (top 셀 값={top_vals[COMPAT_V2_DIMS[j]]})')


# ─────────────────────────────────────────────────────────────────────────────
# 실증④ — η²: ODD 셀 소속이 임베딩 분산을 몇 % '설명'하나 (엄밀 전체 수치)
#   실증①의 단일-셀 Vendi 잔존율을 '전체·분산 기반'으로 못 박는다.
#   η² = SS_between / SS_total (급간/전체 제곱합). 1-η² = ODD 밖 잔여.
#   셀 2,070개(싱글톤 다수) → 무작위 그룹도 우연히 설명 → 순열 귀무로 보정.
#   임베딩이 unit-norm이라 SS_total = Σ||xᵢ−x̄||² = N − N·||x̄||².
# ─────────────────────────────────────────────────────────────────────────────
def analysis4_eta_squared(clip_ids, emb, codes, rng, n_perm=5, min_n=50):
    from scipy.sparse import csr_matrix
    N, D = emb.shape
    x = emb.astype(np.float64)
    gmean = x.mean(axis=0)
    ss_total = N - N * float(gmean @ gmean)          # Σ||xᵢ−x̄||²  (unit-norm)

    def ss_between(lab):
        K = int(lab.max()) + 1
        oh = csr_matrix((np.ones(N), (np.arange(N), lab)), shape=(N, K))
        gsum = oh.T @ x                               # (K,D) 셀별 합
        cnt = np.bincount(lab, minlength=K)
        # Σ_g n_g||x̄_g||² = Σ_g ||gsum_g||²/n_g ; SS_between = 그것 − N||x̄||²
        return float(((gsum ** 2).sum(axis=1) / cnt).sum()) - N * float(gmean @ gmean)

    _, labels = np.unique(codes, axis=0, return_inverse=True)
    labels = labels.astype(np.int64)
    eta_obs = ss_between(labels) / ss_total

    perms = [ss_between(rng.permutation(labels)) / ss_total for _ in range(n_perm)]
    eta_null = float(np.mean(perms))
    eta_adj = (eta_obs - eta_null) / (1 - eta_null)   # 우연 이상으로 ODD가 설명하는 몫

    print('\n' + '=' * 70)
    print('실증④ — η²: ODD가 설명하는 임베딩 분산 비율 (전체·엄밀)')
    print('=' * 70)
    n_cells = len(np.unique(labels))
    print(f'  셀 {n_cells}개 · 클립 {N}')
    print(f'  η²(관측)        = {eta_obs:.1%}   ODD 셀 소속이 설명하는 임베딩 분산')
    print(f'  η²(무작위 귀무) = {eta_null:.1%}   같은 조각화의 의미없는 그룹이 우연히 설명')
    print(f'  η²(보정)        = {eta_adj:.1%}   ← 우연 이상 ODD 순수 기여 (obs−null)/(1−null)')
    print(f'  → ODD 밖(설명 안 됨) = {1 - eta_obs:.1%}(관측 기준) / {1 - eta_adj:.1%}(보정 기준)')

    # 강건성: 잘 채워진 셀(≥min_n)만, 싱글톤 인플레 제거
    cnt_all = np.bincount(labels)
    keep = cnt_all[labels] >= min_n
    xs, ls = x[keep], labels[keep]
    ns = keep.sum()
    gm = xs.mean(axis=0)
    sst = ns - ns * float(gm @ gm)
    _, ls = np.unique(ls, return_inverse=True)
    from scipy.sparse import csr_matrix as _csr
    oh = _csr((np.ones(ns), (np.arange(ns), ls)), shape=(ns, ls.max() + 1))
    gs = oh.T @ xs
    c = np.bincount(ls)
    ssb = float(((gs ** 2).sum(axis=1) / c).sum()) - ns * float(gm @ gm)
    print(f'  [강건성] ≥{min_n}클립 셀만({ls.max()+1}셀 · {ns}클립): η² = {ssb / sst:.1%}')


def main():
    rng = np.random.default_rng(SEED)
    clip_ids, emb, tuples, codes = load_common()
    print(f'[로드] {len(clip_ids)}클립 · 임베딩 {emb.shape} · ODD 11필드 코드')
    knn_idx = np.load(os.path.join(OUTPUT, 'knn_foundation.npz'))['knn_idx']
    analysis1_within_cell(clip_ids, emb, tuples, rng)
    analysis2_within_neighborhood(clip_ids, codes, rng)
    analysis3_top_cell_neighbors(clip_ids, codes, knn_idx)
    analysis4_eta_squared(clip_ids, emb, codes, rng)
    print('\n' + '=' * 70)
    print('종합 — ODD 고정→임베딩 90% 잔존 / 임베딩 고정→ODD 56% 잔존')
    print('     양방향 큰 잔차 = 진짜 상호보완(양자화기 ODD × 잔차 임베딩)')
    print('=' * 70)


if __name__ == '__main__':
    main()
