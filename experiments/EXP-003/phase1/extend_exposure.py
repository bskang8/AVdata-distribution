"""exposure를 urban/rural로 확장 — 손앵커 + 민감도 스윕 (한계① 해소).

배경: P_ext(vkt_weight.csv)는 KTDB itmsh가 highway·national_road만 제공(rural 502·urban
미조사, sources/COVERAGE.md). → Priority_full이 그 2등급 셀만 정의됐다. 저자는 "보완 안 함"
으로 남겨뒀고(COVERAGE.md), 본 스크립트가 그 결정을 **손앵커 + 스윕**으로 갱신한다.

방법(정직한 최소):
  - 관측 hw:nr 비율(0.41465:0.58535, KTDB)은 **보존**(SUPPORTED). total-VKT 구성만 손앵커.
  - 손앵커 = {trunk(hw+nr), urban, rural}의 전체 VKT 점유율. 근사값(국토교통통계연보 VKT
    계열 order-of-magnitude) — **관측 아닌 설계자 앵커**(P3/P4/P5 HAND_ANCHOR와 동급).
  - road_type ⟂ weather라 compose가 P_ext=vkt[rt]×Pwf(we,fo)로 factorize. urban/rural의
    hourly_profile은 미조달 → national_road 프로파일을 proxy 주입(문서화).
  - compose.compose를 그대로 재사용(원 코드 무수정), w_vkt·w_hourly만 확장.

민감도 스윕: 앵커 (T,U,R)을 격자로 흔들어 (a) road_type별 deficit 부호(과/소수집 판정)와
  (b) Priority_full 랭킹이 앵커에 견고한지 보고. 견고하면 앵커 불확실성에도 결론 유지.

산출: exposure/output/P_ext_extended.json(중심 앵커) + output/exposure_sweep.json(스윕 보고).
실행:  ../../../.venv/bin/python extend_exposure.py [--demo]
"""
import os, sys, json, numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
EXPO = os.path.join(ROOT, '..', 'phase0_2', 'exposure')
OUT = os.path.join(ROOT, 'output')
sys.path.insert(0, EXPO)
import loader, compose                                  # noqa: E402  원 코드 무수정 재사용
from priority import load_inputs, compute, minmax       # noqa: E402

HW_NR = (0.41465, 0.58535)          # 관측 hw:nr (KTDB, 보존)
# 손앵커 스윕 격자: (trunk, urban, rural) total-VKT 점유율. 중심=첫 행.
ANCHORS = [
    ('central',     0.45, 0.40, 0.15),
    ('urban_heavy', 0.35, 0.45, 0.20),
    ('trunk_heavy', 0.55, 0.30, 0.15),
    ('rural_heavy', 0.45, 0.30, 0.25),
    ('rural_light', 0.50, 0.40, 0.10),
]


def vkt_full(trunk, urban, rural):
    """total-VKT 앵커 → {road_type: share}, 관측 hw:nr 보존."""
    hw, nr = HW_NR
    return {'highway': trunk * hw, 'national_road': trunk * nr,
            'urban': urban, 'rural': rural}


def build_pext(tables, trunk, urban, rural):
    """w_vkt·w_hourly 확장(urban/rural=national_road hourly proxy) → compose → P_ext dict."""
    t = dict(tables)
    t['w_vkt'] = {(): vkt_full(trunk, urban, rural)}
    hourly = dict(tables['w_hourly'])
    hourly[('urban',)] = tables['w_hourly'][('national_road',)]   # proxy
    hourly[('rural',)] = tables['w_hourly'][('national_road',)]
    t['w_hourly'] = hourly
    return compose.compose(t)                                     # {(rt,we,fo,rs): p}


def to_json_pext(P):
    ser = {f'{rt}|{we}|{fo}|{rs}': round(p, 8) for (rt, we, fo, rs), p in
           sorted(P.items(), key=lambda x: -x[1])}
    return {'axes': ['road_type', 'weather', 'fog', 'road_surface'],
            'note': 'urban/rural=손앵커(central) 확장. hw:nr=KTDB 관측 보존, urban/rural hourly=national proxy. '
                    '값은 관측 아닌 설계자 앵커(extend_exposure.py). 스윕 견고성=output/exposure_sweep.json',
            'n_cells': len(ser), 'sum': round(sum(P.values()), 6), 'P_ext': ser}


def coarse(P):
    out = {}
    for (rt, we, fo, _rs), p in P.items():
        out[f'{rt}|{we}|{fo}'] = out.get(f'{rt}|{we}|{fo}', 0.0) + p
    return out


def main():
    tables = loader.load_all()
    ade, labels, uniq, mult, P_self = load_inputs('learned_')   # 학습형 model_error 기준

    sweep, rank_by_anchor, roadtype_deficit = [], {}, {}
    for name, T, U, R in ANCHORS:
        P = build_pext(tables, T, U, R)
        if name == 'central':
            json.dump(to_json_pext(P),
                      open(os.path.join(EXPO, 'output', 'P_ext_extended.json'), 'w'),
                      ensure_ascii=False, indent=2)
        P_ext_c = coarse(P)
        rows = compute(ade, labels, uniq, mult, P_ext_c, P_self)
        full = [r for r in rows if r['priority_full'] is not None]
        full.sort(key=lambda r: -r['priority_full'])
        rank_by_anchor[name] = [r['cell'] for r in full]
        # road_type별 집계 deficit(과/소수집): P_ext_marg vs P_self_marg
        pe_rt, ps_rt = {}, {}
        for c, p in P_ext_c.items():
            pe_rt[c.split('|')[0]] = pe_rt.get(c.split('|')[0], 0.0) + p
        for c, p in P_self.items():
            ps_rt[c.split('|')[0]] = ps_rt.get(c.split('|')[0], 0.0) + p
        rt_def = {rt: round(float(np.log((pe_rt.get(rt, 0) + 1e-9) / (ps_rt.get(rt, 0) + 1e-9))), 2)
                  for rt in ['highway', 'national_road', 'urban', 'rural']}
        roadtype_deficit[name] = rt_def
        sweep.append({'anchor': name, 'trunk': T, 'urban': U, 'rural': R,
                      'n_full_cells': len(full), 'top5_full': rank_by_anchor[name][:5],
                      'roadtype_deficit_logr': rt_def})

    # 견고성: 중심 대비 top-5 Jaccard, 전체 full 랭킹 Spearman
    base = rank_by_anchor['central']
    robust = {}
    for name, rk in rank_by_anchor.items():
        common = [c for c in base if c in rk]
        rb = [base.index(c) for c in common]; rr = [rk.index(c) for c in common]
        sp = float(np.corrcoef(rb, rr)[0, 1]) if len(common) > 2 else 1.0
        j = len(set(base[:5]) & set(rk[:5])) / len(set(base[:5]) | set(rk[:5]))
        robust[name] = {'spearman_vs_central': round(sp, 3), 'top5_jaccard': round(j, 2)}

    # road_type 과/소수집 부호가 앵커 전반에 안정한가
    sign_stable = {rt: len({np.sign(roadtype_deficit[a][rt]) for a in rank_by_anchor}) == 1
                   for rt in ['highway', 'national_road', 'urban', 'rural']}

    json.dump({'note': 'exposure 손앵커 민감도 스윕. hw:nr=관측보존, {trunk,urban,rural}=앵커격자.',
               'anchors': sweep, 'robustness_vs_central': robust,
               'roadtype_over_under_sign_stable': sign_stable},
              open(os.path.join(OUT, 'exposure_sweep.json'), 'w'), ensure_ascii=False, indent=2)

    print("=== road_type 과/소수집 deficit logr (부호<0=과대수집=프루닝, >0=과소=수집) ===")
    print(f"  {'anchor':<12} " + " ".join(f'{rt[:8]:>9}' for rt in ['highway', 'national_road', 'urban', 'rural']))
    for name in rank_by_anchor:
        d = roadtype_deficit[name]
        print(f"  {name:<12} " + " ".join(f"{d[rt]:>9.2f}" for rt in ['highway', 'national_road', 'urban', 'rural']))
    print(f"\n부호(과/소수집 판정) 앵커 전반 안정: {sign_stable}")
    print(f"\n중심 앵커 Priority_full top-5:\n  " + "\n  ".join(base[:5]))
    print("\n견고성(중심 대비):")
    for name, r in robust.items():
        print(f"  {name:<12} spearman={r['spearman_vs_central']:+.2f} top5_jaccard={r['top5_jaccard']}")


def demo():
    """vkt_full 합=1·hw:nr 비율 보존 검증."""
    v = vkt_full(0.45, 0.40, 0.15)
    assert abs(sum(v.values()) - 1.0) < 1e-9, v
    assert abs(v['highway'] / v['national_road'] - HW_NR[0] / HW_NR[1]) < 1e-9
    assert abs(v['urban'] - 0.40) < 1e-9 and abs(v['rural'] - 0.15) < 1e-9
    print(f"demo ✓  vkt_full={ {k: round(x, 3) for k, x in v.items()} } 합=1·hw:nr 보존")


if __name__ == '__main__':
    demo() if '--demo' in sys.argv else main()
