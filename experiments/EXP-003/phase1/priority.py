"""획득함수 Priority(c) 통합 랭킹 — 다섯 인자의 곱 (방법론 §2).

    Priority(c) = criticality(c) × exposure(c) × deficit(c) × model_error(c) × headroom(c)

공통 셀 c = coarse 관측조합 (road_type × weather × fog) — exposure 결정공간이자
이름주소화 가능(수집발주는 이름으로, §3). 다섯 인자를 이 셀에 모두 표현:
  criticality : 축 승수 곱(road_type·weather·fog) — criticality.json multipliers. 관측 3축만
                (lighting·agent·speed는 per-clip 미태깅 → 부분 심각도, 정직).
  exposure    : P_ext (road_surface marginalize). ⚠️ 한계① — road_type 2/4(highway·national_road)만.
  deficit     : 과소수집 log(P_ext/P_self). exposure 정의 셀만.
  model_error : 셀 mean ADE의 클립수 가중 CDF ∈[0,1] (phase1 egomotion, coarse 재집계).
  headroom    : 셀 mean uniqueness_weight(=비중복 여력) 정규화 — 임베딩 포화 게이트.

각 인자 [0,1] 정규화 후 곱. 두 랭킹 산출:
  Priority_core = criticality × model_error × headroom  (관측 셀 전부 계산가능)
  Priority_full = ×exposure×deficit                     (exposure 정의 셀만; 한계① 노출)

per-clip coarse 라벨은 pself.axes_of 재사용(축정합 보장), 첫 실행 ODD json 재파싱 ~80s→캐시.
실행:  ../../../.venv/bin/python priority.py [--demo]
"""
import os, sys, json, numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
P0   = os.path.join(ROOT, '..', 'phase0', 'output')
EXPO = os.path.join(ROOT, '..', 'phase0_2', 'exposure')
OUT  = os.path.join(ROOT, 'output')
CACHE = os.path.join(OUT, 'coarse_cell_per_clip.npy')
MIN_CELL = 20
EPS = 1e-9


def coarse_labels(clip_ids):
    """각 클립 → 'road_type|weather|fog' (pself 축정합). 캐시."""
    if os.path.exists(CACHE):
        return np.load(CACHE, allow_pickle=True)
    sys.path.insert(0, os.path.join(EXPO, 'select'))
    sys.path.insert(0, EXPO)
    from pself import axes_of                      # noqa
    from step_a_odd_coverage import _flatten_final  # noqa
    from config import ODD_DIR                       # noqa
    import json as _j
    out = np.empty(len(clip_ids), dtype=object)
    for i, cid in enumerate(clip_ids):
        try:
            d = _j.load(open(os.path.join(ODD_DIR, f'{cid}.json')))
            ax = axes_of(_flatten_final(d['odd_final'])) if d.get('odd_final') else None
        except (OSError, ValueError, KeyError):
            ax = None
        out[i] = None if ax is None else '|'.join(ax[a] for a in ('road_type', 'weather', 'fog'))
        if (i + 1) % 20000 == 0:
            print(f"  labeled {i+1}/{len(clip_ids)}")
    np.save(CACHE, out)
    return out


def minmax(d):
    """dict value → [0,1] min-max (동일값이면 전부 1)."""
    vals = np.array(list(d.values()), float)
    lo, hi = vals.min(), vals.max()
    if hi - lo < EPS:
        return {k: 1.0 for k in d}
    return {k: float((v - lo) / (hi - lo)) for k, v in d.items()}


def weighted_cdf(means, counts):
    order = np.argsort(means); cum = np.cumsum(counts[order]); tot = cum[-1]
    cdf = np.empty_like(means, float); prev = 0
    for rank, idx in enumerate(order):
        cdf[idx] = (prev + cum[rank]) / 2.0 / tot; prev = cum[rank]
    return cdf


def crit_of(cell, mult):
    rt, we, fo = cell.split('|')
    return mult['road_type'].get(rt, 1.0) * mult['weather'].get(we, 1.0) * mult['fog'].get(fo, 1.0)


def pext_coarse(fname='P_ext.json'):
    """P_ext (rt|weather|fog|surface) → rt|weather|fog 로 marginalize.
    fname='P_ext_extended.json' → urban/rural 손앵커 확장판(한계① 해소)."""
    px = json.load(open(os.path.join(EXPO, 'output', fname)))['P_ext']
    out = {}
    for k, p in px.items():
        rt, we, fo, _rs = k.split('|')
        out[f'{rt}|{we}|{fo}'] = out.get(f'{rt}|{we}|{fo}', 0.0) + p
    return out


def compute(ade, labels, uniq, mult, P_ext, P_self, min_cell=MIN_CELL):
    """다섯 인자 → 셀별 rows. P_ext를 갈아끼워 exposure 스윕 재사용(extend_exposure.py)."""
    ok = np.isfinite(ade)
    cells = {}
    for i in np.nonzero(ok)[0]:
        c = labels[i]
        if c and 'unknown' not in c:
            cells.setdefault(c, []).append(i)
    cells = {c: np.array(ix) for c, ix in cells.items() if len(ix) >= min_cell}
    keys = list(cells)

    crit_raw = {c: crit_of(c, mult) for c in keys}
    cmean = {c: float(ade[cells[c]].mean()) for c in keys}
    ccnt = np.array([cells[c].size for c in keys], float)
    me = dict(zip(keys, weighted_cdf(np.array([cmean[c] for c in keys]), ccnt)))
    head_raw = {c: float(uniq[cells[c]].mean()) for c in keys}
    expo_raw = {c: P_ext[c] for c in keys if c in P_ext}
    deficit_raw = {c: float(np.log((P_ext[c] + EPS) / (P_self.get(c, 0.0) + EPS)))
                   for c in keys if c in P_ext}

    crit_n, head_n = minmax(crit_raw), minmax(head_raw)
    expo_n = minmax(expo_raw) if expo_raw else {}
    def_n = minmax(deficit_raw) if deficit_raw else {}

    rows = []
    for c in keys:
        core = crit_n[c] * me[c] * head_n[c]
        full = core * expo_n[c] * def_n[c] if c in expo_n else None
        rows.append({
            'cell': c, 'n': int(cells[c].size),
            'priority_core': round(core, 5),
            'priority_full': round(full, 5) if full is not None else None,
            'criticality': round(crit_raw[c], 2), 'criticality_n': round(crit_n[c], 3),
            'model_error': round(me[c], 3),
            'headroom_n': round(head_n[c], 3), 'mean_uniqueness': round(head_raw[c], 4),
            'exposure_Pext': round(expo_raw[c], 6) if c in expo_raw else None,
            'deficit_logr': round(deficit_raw[c], 3) if c in deficit_raw else None,
            'mean_ade': round(cmean[c], 3),
        })
    return rows


def load_inputs(prefix=''):
    clip_ids = np.load(os.path.join(P0, 'clip_ids.npy'), allow_pickle=True)
    ade = np.load(os.path.join(ROOT, 'output', f'{prefix}ade_per_clip.npy'))
    uniq = np.load(os.path.join(P0, 'uniqueness_weight.npy'))
    labels = coarse_labels(clip_ids)
    mult = json.load(open(os.path.join(EXPO, 'output', 'criticality.json')))['multipliers']
    P_self = json.load(open(os.path.join(EXPO, 'output', 'P_self.json')))['P_self']
    return ade, labels, uniq, mult, P_self


def main(prefix='', pext_file='P_ext.json'):
    # prefix='learned_' → 학습형 model_error. pext_file='P_ext_extended.json' → 확장 exposure.
    ade, labels, uniq, mult, P_self = load_inputs(prefix)
    P_ext = pext_coarse(pext_file)
    rows = compute(ade, labels, uniq, mult, P_ext, P_self)
    keys = [r['cell'] for r in rows]
    ext_tag = 'ext_' if pext_file != 'P_ext.json' else ''
    core_rank = sorted(rows, key=lambda r: -r['priority_core'])
    full_rows = [r for r in rows if r['priority_full'] is not None]
    full_rank = sorted(full_rows, key=lambda r: -r['priority_full'])

    json.dump({
        'note': 'Priority(c)=criticality×exposure×deficit×model_error×headroom, 셀=road_type|weather|fog',
        'unit': 'coarse 관측조합(exposure 결정공간). 인자 각 min-max[0,1] 후 곱.',
        'min_cell': MIN_CELL, 'n_cells': len(keys),
        'exposure_source': pext_file,
        'exposure_limit': f'priority_full 정의 {len(full_rows)}/{len(keys)}셀 (P_ext 정의 셀만).'
                          + (' urban/rural=손앵커 확장(한계① 해소, extend_exposure.py).' if ext_tag else ' P_ext는 road_type 2/4만(한계①).'),
        'ranking_core': core_rank,
        'ranking_full': full_rank,
    }, open(os.path.join(OUT, f'{prefix}{ext_tag}priority_ranking.json'), 'w'), ensure_ascii=False, indent=2)

    print(f"관측 셀 {len(keys)}개(n>={MIN_CELL}), priority_full 정의 {len(full_rows)}개")
    print("\n=== Priority_core top 8 (criticality×model_error×headroom) ===")
    for r in core_rank[:8]:
        print(f"  {r['priority_core']:.4f}  {r['cell']:<28} n={r['n']:5d} crit={r['criticality']:5.1f} ME={r['model_error']:.2f} head={r['headroom_n']:.2f} ADE={r['mean_ade']}")
    if full_rank:
        print(f"\n=== Priority_full top (×exposure×deficit; {len(full_rows)}/{len(keys)}셀 정의) ===")
        for r in full_rank[:8]:
            print(f"  {r['priority_full']:.4f}  {r['cell']:<28} n={r['n']:5d} Pext={r['exposure_Pext']} logr={r['deficit_logr']} ME={r['model_error']:.2f}")


def demo():
    """minmax·weighted_cdf·crit_of 자기검증."""
    assert minmax({'a': 1, 'b': 3, 'c': 2}) == {'a': 0.0, 'b': 1.0, 'c': 0.5}
    assert minmax({'a': 5, 'b': 5}) == {'a': 1.0, 'b': 1.0}
    e = weighted_cdf(np.array([1., 2., 3.]), np.array([10., 10., 10.]))
    assert np.all(np.diff(e) > 0) and 0 < e.min() and e.max() < 1
    m = {'road_type': {'highway': 2.0}, 'weather': {'snow': 2.5}, 'fog': {'present': 2.0}}
    assert abs(crit_of('highway|snow|present', m) - 10.0) < 1e-9
    print("demo ✓  minmax·cdf·crit 검증 통과")


if __name__ == '__main__':
    if '--demo' in sys.argv:
        demo()
    else:
        main('learned_' if '--learned' in sys.argv else '',
             'P_ext_extended.json' if '--ext' in sys.argv else 'P_ext.json')
