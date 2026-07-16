"""EXP-003 Phase 1 · 1부 — 소스 정찰(reconnaissance) + 블록 게이팅.

4개 소스(KMA ASOS / KTDB / KoROAD / KASI)의 **대표 샘플**을 프로파일링해서
loader.BLOCKS(=§2 구조 prior)가 실데이터로 채워지는지 블록별로 게이팅한다.
구조를 *만들지* 않고 *검증·축소*만 한다 — 의존 그래프는 데이터가 못 주는 prior(비식별).

입력:  exposure/raw/<source>/*.csv|json   (사람이 손수 export한 샘플 1개면 충분)
출력:  exposure/recon/availability.json + recon_report.md
의존:  stdlib(csv,json,glob,statistics) + loader.BLOCKS. pandas·yaml·network 없음.
실행(self-check):  python3 recon.py
"""
import csv
import glob
import json
import os
from collections import defaultdict

import loader  # phase1 내부 — §2 구조 prior 재사용

# loader.BLOCKS는 파일명 keyed → 블록명 keyed로 뒤집어 재사용
BY_NAME = {spec['block']: spec for spec in loader.BLOCKS.values()}
HERE = os.path.dirname(os.path.abspath(__file__))
EDGE_TV_EPS = 0.05   # 부모 조건부 분포 차이 이 미만 → 엣지 삭제 후보

# needs_key → 이 role이 있으면 그 키를 만들 수 있음
YIELDS = {'month': {'time'}, 'hour': {'time', 'hour'},
          'road_type': {'grade'}, 'weather': {'precip'}}

# KTDB 도로등급 전체 모집단. itmsh_yearly 백엔드는 이 중 앞 2개(고속·일반국도)만 적재하고
# 지방도·국지도는 502(구조적 미제공) → vocab 커버리지로 그 한계를 게이트에 노출한다.
ROAD_UNIVERSE = ['고속도로', '일반도로', '지방도', '국가지원지방도']

# 소스-facing 스펙. loader.BLOCKS(CSV-facing)를 보완. roles 값=컬럼명 후보(부분일치).
REQUIREMENTS = {
    'P1_weather': dict(source='KMA_ASOS', raw_glob='raw/kma/*.csv',
                       roles={'time': ['tm'], 'precip': ['rn'], 'temp': ['ta']}),
    'P1_fog':     dict(source='KMA_ASOS', raw_glob='raw/kma/*.csv',
                       roles={'time': ['tm'], 'vis': ['vs']}),
    'w_vkt':      dict(source='KTDB', raw_glob='raw/ktdb/vkt_sample.csv',
                       roles={'grade': ['등급', 'grade'], 'share': ['구성비', 'share', 'vkt']},
                       vocab_role='grade', universe=ROAD_UNIVERSE),  # P(road_type)=등급별 관측교통량 구성비
    'w_hourly':   dict(source='KTDB', raw_glob='raw/ktdb/itmsh_sample.csv',
                       roles={'grade': ['등급', 'grade'], 'hour': ['시', 'hour'], 'share': ['교통량비', 'share']},
                       vocab_role='grade', universe=ROAD_UNIVERSE,
                       edge=('grade', 'hour', 'share')),
    'P4_speed':   dict(source='KTDB', raw_glob='raw/ktdb/*.csv',
                       roles={'grade': ['등급', 'grade'], 'speed': ['속도', 'speed']},
                       apriori='HAND_ANCHOR:weather-dim'),   # 등급속도=맑음만; weather=손계수
    'P3_agent':   dict(source='KoROAD', raw_glob='raw/koroad/*.csv',
                       roles={'ped': ['보행', 'ped']},
                       apriori='HAND_ANCHOR'),                # 보행노출=최약, 손앵커
    'P3_density': dict(source='KTDB', raw_glob='raw/ktdb/*.csv',
                       roles={'grade': ['등급', 'grade'], 'hour': ['시', 'hour'], 'vc': ['vc', '용량']},
                       apriori='HAND_ANCHOR:V/C=용량편람(문서) 산출·API 부재'),  # 재조사 확정
    'P5_lighting':dict(source='KASI', raw_glob='raw/kasi/*.json',
                       roles={'sunrise': ['sunrise'], 'sunset': ['sunset']},
                       apriori='HAND_ANCHOR:brightness'),     # 출몰시각만; 밝기재매핑=손저작
}


def detect_columns(columns, roles):
    """role → 매칭 컬럼명(부분일치, 대소문자 무시) 또는 None."""
    out = {}
    for role, cands in roles.items():
        hit = next((c for c in columns for cand in cands if cand.lower() in c.lower()), None)
        out[role] = hit
    return out


def read_sample(path):
    """샘플 1장 → (columns, records[dict])."""
    if path.endswith('.json'):
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, list):
            recs = data
        elif isinstance(data, dict):
            recs = next((v for v in data.values() if isinstance(v, list) and v and isinstance(v[0], dict)), [data])
        else:
            recs = []
        return (list(recs[0]) if recs else []), recs
    with open(path, newline='') as f:
        reader = csv.reader(f)
        header = next(reader, [])
        recs = [dict(zip(header, row)) for row in reader if row and any(c.strip() for c in row)]
    return header, recs


def _key_ok(k, detected, columns):
    if k in YIELDS:
        return bool(YIELDS[k] & detected)
    return any(k.lower() == c.lower() for c in columns)


def edge_max_tv(records, parent_col, axis_col, value_col):
    """부모값별 axis 분포의 최대 pairwise Total-Variation. 부모<2면 0."""
    dist = defaultdict(lambda: defaultdict(float))
    for r in records:
        try:
            dist[r[parent_col]][r[axis_col]] += float(r[value_col])
        except (KeyError, ValueError, TypeError):
            continue
    for p in dist:                       # 부모별 정규화
        s = sum(dist[p].values()) or 1.0
        for a in dist[p]:
            dist[p][a] /= s
    parents = list(dist)
    axes = {a for p in parents for a in dist[p]}
    best = 0.0
    for i in range(len(parents)):
        for j in range(i + 1, len(parents)):
            tv = 0.5 * sum(abs(dist[parents[i]].get(a, 0.0) - dist[parents[j]].get(a, 0.0)) for a in axes)
            best = max(best, tv)
    return best


def gate_block(name, base=HERE):
    req = REQUIREMENTS[name]
    keys = BY_NAME[name]['keys']
    res = dict(block=name, source=req['source'], gate=None,
               needs_keys=keys, achievable=None, missing=None,
               vocab_found=None, vocab_missing=None, edge_tv=None, note='')
    ap = req.get('apriori')
    files = sorted(glob.glob(os.path.join(base, req['raw_glob'])))

    if ap and ap.startswith('HAND_ANCHOR'):
        res['gate'] = 'HAND_ANCHOR'
        res['note'] = ap.split(':', 1)[1] if ':' in ap else '축 부재 → §11 민감도 스윕'
        return res
    if not files:
        res['gate'] = 'NOT_OBTAINED'
        res['note'] = f"샘플 없음: {req['raw_glob']}"
        return res

    columns, records = read_sample(files[0])
    cols = detect_columns(columns, req['roles'])
    detected = {r for r, c in cols.items() if c}
    missing_roles = [r for r, c in cols.items() if not c]
    if missing_roles:
        res['gate'] = 'INSUFFICIENT'
        res['note'] = f"컬럼 미검출 role={missing_roles} (헤더 {columns})"
        return res

    missing_keys = [k for k in keys if not _key_ok(k, detected, columns)]
    res['achievable'] = [k for k in keys if k not in missing_keys]
    res['missing'] = missing_keys
    res['gate'] = 'SUPPORTED' if not missing_keys else 'LOW_RES'

    if req.get('vocab_role') and cols.get(req['vocab_role']):
        col = cols[req['vocab_role']]
        seen = []
        for r in records:
            v = r.get(col)
            if v and v not in seen:
                seen.append(v)
        res['vocab_found'] = seen[:20]
        universe = req.get('universe')
        if universe:
            miss = [u for u in universe if u not in seen]
            res['vocab_missing'] = miss          # [] = 전 등급 커버
            if miss:                             # 구조는 채워지나 등급 모집단 일부 미확보
                cov = f"⚠ 등급 커버 {len(seen)}/{len(universe)} — 미확보 {miss} (itmsh_yearly 백엔드 미제공·502, 구조적 한계)"
                res['note'] = (res['note'] + '; ' if res['note'] else '') + cov
    if req.get('edge'):
        pr, ar, vr = req['edge']
        if all(cols.get(x) for x in (pr, ar, vr)):
            tv = edge_max_tv(records, cols[pr], cols[ar], cols[vr])
            res['edge_tv'] = round(tv, 4)
            edge_note = (f"edge {pr}→{ar}: TV={tv:.3f} "
                         + ("< eps → 조건부 삭제 후보(marginal 단순화)" if tv < EDGE_TV_EPS
                            else "≥ eps → 조건부 정당"))
            res['note'] = (res['note'] + '; ' if res['note'] else '') + edge_note
    return res


def run(base=HERE):
    return [gate_block(n, base) for n in REQUIREMENTS]


def write_outputs(results, base=HERE):
    outdir = os.path.join(base, 'recon')
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, 'availability.json'), 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    lines = ['# Phase 1 소스 정찰 리포트 (recon.py)', '',
             '블록별 게이트 — SUPPORTED=실데이터 지지 / LOW_RES=해상도 부족 /',
             'HAND_ANCHOR=축 부재(§11 스윕) / INSUFFICIENT=컬럼 미검출 / NOT_OBTAINED=샘플 없음', '',
             '| block | source | gate | achievable | missing | vocab / edge / note |',
             '|---|---|---|---|---|---|']
    for r in results:
        extra = []
        if r['vocab_found']:
            extra.append('vocab=' + ','.join(map(str, r['vocab_found'])))
        if r['edge_tv'] is not None:
            extra.append(f"edgeTV={r['edge_tv']}")
        if r['note']:
            extra.append(r['note'])
        lines.append(f"| {r['block']} | {r['source']} | **{r['gate']}** | "
                     f"{r['achievable'] or '-'} | {r['missing'] or '-'} | {'; '.join(extra) or '-'} |")
    partial = [f"{r['block']}(미확보 {r['vocab_missing']})"
               for r in results if r.get('vocab_missing')]
    lines += ['', '## 판정 요약',
              f"- SUPPORTED: {[r['block'] for r in results if r['gate']=='SUPPORTED']}",
              f"- ⚠ 등급 부분커버(SUPPORTED이나 모집단 일부 미확보·구조적 한계): "
              f"{partial or '없음'}",
              f"- 손앵커/저해상도(→§11 스윕·주의): "
              f"{[r['block'] for r in results if r['gate'] in ('HAND_ANCHOR','LOW_RES')]}",
              f"- 미확보/불충분(→샘플 확보·컬럼 확인): "
              f"{[r['block'] for r in results if r['gate'] in ('NOT_OBTAINED','INSUFFICIENT')]}",
              '', '## 다음 조치',
              '1. SUPPORTED 블록: sources/*.csv 실값 전사 → loader.py 계약 검증.',
              '2. LOW_RES/HAND_ANCHOR: loader.BLOCKS 조건키 trim 또는 §11 민감도 스윕 대상 표기.',
              '3. vocab_found로 mapping.yaml road_type taxonomy 확인(tunnel 부재 등).',
              '4. edge TV < eps 블록: 해당 조건부 삭제(marginal) 검토.']
    with open(os.path.join(outdir, 'recon_report.md'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    return outdir


def _selfcheck():
    import tempfile, shutil
    assert set(REQUIREMENTS) == set(BY_NAME), "REQUIREMENTS ↔ BLOCKS 불일치"

    # edge_max_tv 단위 검증: 부모별 프로파일 동일→0, 상이→>0
    same = [{'p': 'a', 'h': '8', 'v': '0.6'}, {'p': 'a', 'h': '9', 'v': '0.4'},
            {'p': 'b', 'h': '8', 'v': '0.6'}, {'p': 'b', 'h': '9', 'v': '0.4'}]
    diff = [{'p': 'a', 'h': '8', 'v': '0.9'}, {'p': 'a', 'h': '9', 'v': '0.1'},
            {'p': 'b', 'h': '8', 'v': '0.1'}, {'p': 'b', 'h': '9', 'v': '0.9'}]
    assert edge_max_tv(same, 'p', 'h', 'v') < 1e-9
    assert edge_max_tv(diff, 'p', 'h', 'v') > 0.7

    base = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(base, 'raw/kma'))
        os.makedirs(os.path.join(base, 'raw/ktdb'))
        with open(os.path.join(base, 'raw/kma/s.csv'), 'w', newline='') as f:
            w = csv.writer(f); w.writerow(['tm', 'ta', 'rn', 'vs'])
            w.writerow(['2023-01-01 08:00', '-2.0', '0.5', '800'])
        with open(os.path.join(base, 'raw/ktdb/vkt_sample.csv'), 'w', newline='') as f:
            w = csv.writer(f); w.writerow(['grade', 'share'])
            w.writerow(['고속도로', '0.55']); w.writerow(['일반도로', '0.45'])
        with open(os.path.join(base, 'raw/ktdb/itmsh_sample.csv'), 'w', newline='') as f:
            w = csv.writer(f); w.writerow(['grade', 'hour', 'share'])
            w.writerow(['고속도로', '8', '0.6']); w.writerow(['고속도로', '9', '0.4'])
            w.writerow(['일반도로', '8', '0.4']); w.writerow(['일반도로', '9', '0.6'])
        g = {r['block']: r['gate'] for r in run(base)}
        assert g['P1_weather'] == 'SUPPORTED', g
        assert g['P1_fog'] == 'SUPPORTED', g
        assert g['w_vkt'] == 'SUPPORTED', g           # vkt_sample: grade/share → P(road_type)
        assert g['w_hourly'] == 'SUPPORTED', g        # itmsh_sample: grade/hour/share
        assert g['P5_lighting'] == 'HAND_ANCHOR', g   # apriori(축 부재) 우선
        assert g['P3_agent'] == 'HAND_ANCHOR', g      # 샘플 없어도 apriori 우선
        assert g['P3_density'] == 'HAND_ANCHOR', g    # V/C=용량편람(문서), API 부재 → apriori
        shutil.rmtree(os.path.join(base, 'raw/kma'))
        assert {r['block']: r['gate'] for r in run(base)}['P1_weather'] == 'NOT_OBTAINED'
        # vocab 추출 + 모집단 커버리지 한계 노출 확인
        wv = next(r for r in run(base) if r['block'] == 'w_vkt')
        assert '고속도로' in wv['vocab_found'], wv
        assert wv['vocab_missing'] == ['지방도', '국가지원지방도'], wv  # 2/4 미확보가 게이트에 뜸
    finally:
        shutil.rmtree(base, ignore_errors=True)
    print('[OK] recon self-check 통과')


if __name__ == '__main__':
    _selfcheck()
    results = run()
    out = write_outputs(results)
    print(f"[recon] {len(results)}개 블록 게이팅 → {out}/")
    for r in results:
        print(f"  {r['block']:12s} {r['gate']:12s} {r['note'][:60]}")
