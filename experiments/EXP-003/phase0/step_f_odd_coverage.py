"""Phase 0-F: ODD 커버리지 분석
odd_schema.md 기준 이론적 조합 수 대비 실제 클립 커버율 분석.
출력: output/odd_coverage.json
"""

import json
import os
from collections import Counter

from config import ODD_DIR
from utils import P, already_done

# ── odd_schema.md 허용 값 정의 ────────────────────────────────────────
# odd_final 19 필드 (4그룹 플래팅, unknown 포함)
FINAL_DIMS = [
    'road_type', 'lanes_ego_direction', 'lanes_opposite', 'road_divider',
    'lane_marking_quality', 'junction_proximity',
    'lighting_condition', 'precipitation', 'fog', 'road_surface', 'backlight',
    'traffic_density', 'road_user_types', 'construction_zone', 'special_event',
    'occlusion_level', 'visibility_range', 'scene_ambiguity', 'unexpected_element',
]

FINAL_SCHEMA = {
    'road_type':            ['highway', 'national_road', 'urban', 'rural', 'unknown'],
    'lanes_ego_direction':  ['1', '2', '3+', 'unknown'],
    'lanes_opposite':       ['0', '1', '2+', 'unknown'],
    'road_divider':         ['none', 'dashed', 'solid', 'barrier', 'unknown'],
    'lane_marking_quality': ['clear', 'faint', 'absent', 'unknown'],
    'junction_proximity':   ['none', 'approaching', 'in_junction', 'post_junction', 'unknown'],
    'lighting_condition':   ['well_lit', 'moderate', 'poorly_lit', 'unknown'],
    'precipitation':        ['none', 'rain', 'snow', 'unknown'],
    'fog':                  ['none', 'present', 'unknown'],
    'road_surface':         ['dry', 'wet', 'unknown'],
    'backlight':            ['none', 'present', 'unknown'],
    'traffic_density':      ['sparse', 'moderate', 'dense', 'unknown'],
    'road_user_types':      ['cars_only', 'mixed', 'pedestrians', 'cyclists', 'emergency', 'unknown'],
    'construction_zone':    ['none', 'present', 'unknown'],
    'special_event':        ['none', 'accident', 'obstacle', 'emergency', 'unknown'],
    'occlusion_level':      ['low', 'medium', 'high', 'unknown'],
    'visibility_range':     ['good', 'moderate', 'poor', 'unknown'],
    'scene_ambiguity':      ['low', 'medium', 'high', 'unknown'],
    'unexpected_element':   ['none', 'present', 'unknown'],
}

# odd_compat 9개 독립 필드 (lane_summary는 파생 필드 → 이론 조합 계산 제외)
COMPAT_DIMS = [
    'road_type', 'weather', 'traffic_density', 'agent_type',
    'lanes_ego_direction', 'lanes_opposite', 'road_divider',
    'lighting', 'scene_ambiguity',
]

COMPAT_SCHEMA = {
    'road_type':           ['highway', 'national_road', 'urban', 'rural', 'unknown'],
    'weather':             ['clear', 'rain', 'snow', 'unknown'],
    'traffic_density':     ['sparse', 'moderate', 'dense', 'unknown'],
    'agent_type':          ['cars_only', 'mixed', 'pedestrians', 'cyclists', 'emergency', 'unknown'],
    'lanes_ego_direction': ['1', '2', '3+', 'unknown'],
    'lanes_opposite':      ['0', '1', '2+', 'unknown'],
    'road_divider':        ['none', 'dashed', 'solid', 'barrier', 'unknown'],
    'lighting':            ['well_lit', 'moderate', 'poorly_lit', 'unknown'],
    'scene_ambiguity':     ['low', 'medium', 'high', 'unknown'],
}

# odd_compat_v2: AV 성능 관점 11개 필드 (odd_final에서 파생)
# 선택 기준: 지각·예측·계획 난이도에 직접 영향을 주는 필드
COMPAT_V2_DIMS = [
    'road_type',          # 시나리오 맥락
    'weather',            # 센서 저하 통합 (precipitation + fog 병합)
    'lighting',           # 카메라 지각 난이도
    'agent_type',         # VRU 존재 여부 — 안전 임계값
    'traffic_density',    # 다중 에이전트 예측 복잡도
    'junction_proximity', # 교차로 근접 — 행동 전략 분기 지점
    'road_surface',       # 차량 동역학 (제동·조향) 핵심 변수
    'occlusion_level',    # 지각 품질 직접 지표
    'visibility_range',   # planning horizon 결정
    'special_event',      # 사고·장애물 — 안전 크리티컬 롱테일
    'lane_marking_quality',  # 차선 탐지 모델 직접 실패 원인
]

COMPAT_V2_SCHEMA = {
    'road_type':            ['highway', 'national_road', 'urban', 'rural', 'unknown'],
    # fog는 precipitation과 독립 조건이므로 별도 값으로 분리
    'weather':              ['clear', 'rain', 'snow', 'fog', 'unknown'],
    'lighting':             ['well_lit', 'moderate', 'poorly_lit', 'unknown'],
    'agent_type':           ['cars_only', 'mixed', 'pedestrians', 'cyclists', 'emergency', 'unknown'],
    'traffic_density':      ['sparse', 'moderate', 'dense', 'unknown'],
    'junction_proximity':   ['none', 'approaching', 'in_junction', 'post_junction', 'unknown'],
    # snow/snow-dusted → snow로 통합; uneven/dirt 등 비포장 계열 → unknown
    'road_surface':         ['dry', 'wet', 'snow', 'unknown'],
    'occlusion_level':      ['low', 'medium', 'high', 'unknown'],
    'visibility_range':     ['good', 'moderate', 'poor', 'unknown'],
    'special_event':        ['none', 'accident', 'obstacle', 'emergency', 'unknown'],
    'lane_marking_quality': ['clear', 'faint', 'absent', 'unknown'],
}

_SURFACE_MAP = {
    'dry': 'dry', 'wet': 'wet',
    'snow': 'snow', 'snow-dusted': 'snow',
}


def _to_compat_v2(flat: dict) -> dict:
    """odd_final 플래트 레코드 → odd_compat_v2 레코드 변환."""
    prec = flat.get('precipitation', 'unknown')
    fog  = flat.get('fog', 'unknown')
    if prec in ('rain', 'snow'):
        weather = prec
    elif fog == 'present':
        weather = 'fog'
    elif prec == 'none' and fog == 'none':
        weather = 'clear'
    else:
        weather = 'unknown'

    return {
        'road_type':            flat.get('road_type', 'unknown'),
        'weather':              weather,
        'lighting':             flat.get('lighting_condition', 'unknown'),
        'agent_type':           flat.get('road_user_types', 'unknown'),
        'traffic_density':      flat.get('traffic_density', 'unknown'),
        'junction_proximity':   flat.get('junction_proximity', 'unknown'),
        'road_surface':         _SURFACE_MAP.get(flat.get('road_surface', 'unknown'), 'unknown'),
        'occlusion_level':      flat.get('occlusion_level', 'unknown'),
        'visibility_range':     flat.get('visibility_range', 'unknown'),
        'special_event':        flat.get('special_event', 'unknown'),
        'lane_marking_quality': flat.get('lane_marking_quality', 'unknown'),
    }


def _flatten_final(odd_final: dict) -> dict:
    flat = {}
    for group in odd_final.values():
        if isinstance(group, dict):
            flat.update(group)
    return flat


def _per_field_stats(records: list, dims: list, schema: dict) -> dict:
    n = len(records)
    stats = {}
    for dim in dims:
        vals = [r.get(dim, 'unknown') for r in records]
        cnt = Counter(vals)
        unk = cnt.get('unknown', 0)
        schema_vals = schema.get(dim, [])
        missing = [v for v in schema_vals if v != 'unknown' and v not in cnt]
        stats[dim] = {
            'counts':          dict(sorted(cnt.items(), key=lambda x: -x[1])),
            'n_values_seen':   len(cnt),
            'n_schema_vals':   len(schema_vals),
            'missing_vals':    missing,
            'unknown_count':   unk,
            'unknown_ratio':   round(unk / max(n, 1), 4),
        }
    return stats


def _combo_coverage(records: list, dims: list, schema: dict) -> dict:
    combos = [tuple(r.get(d, 'unknown') for d in dims) for r in records]
    observed = Counter(combos)

    n_theoretical = 1
    for d in dims:
        n_theoretical *= len(schema.get(d, ['unknown']))

    # unknown이 하나도 없는 클린 조합
    clean = [c for c in combos if 'unknown' not in c]
    n_clean_obs = len(set(clean))
    n_theoretical_clean = 1
    for d in dims:
        no_unk = [v for v in schema.get(d, []) if v != 'unknown']
        n_theoretical_clean *= max(len(no_unk), 1)

    return {
        'n_clips':              len(records),
        'n_observed':           len(observed),
        'n_theoretical':        n_theoretical,
        'coverage_ratio':       round(len(observed) / max(n_theoretical, 1), 6),
        'n_clean_observed':     n_clean_obs,
        'n_theoretical_clean':  n_theoretical_clean,
        'coverage_ratio_clean': round(n_clean_obs / max(n_theoretical_clean, 1), 6),
        'singleton_combos':     sum(1 for v in observed.values() if v == 1),
        'top100_combos': [
            {'combo': dict(zip(dims, k)), 'count': v}
            for k, v in sorted(observed.items(), key=lambda x: -x[1])[:100]
        ],
    }


def run(force=False):
    OUT = 'odd_coverage.json'
    if not force and already_done('0-F', OUT):
        return

    print('[0-F] ODD 커버리지 분석 중...')

    # ── 전체 ODD JSON 로드 ────────────────────────────────────────────
    final_recs, compat_recs = [], []
    n_total = n_loaded = 0
    for fname in sorted(os.listdir(ODD_DIR)):
        if not fname.endswith('.json'):
            continue
        n_total += 1
        try:
            with open(os.path.join(ODD_DIR, fname)) as f:
                data = json.load(f)
            if data.get('odd_final'):
                final_recs.append(_flatten_final(data['odd_final']))
            if data.get('odd_compat'):
                compat_recs.append(data['odd_compat'])
            n_loaded += 1
        except (json.JSONDecodeError, KeyError):
            pass

    print(f'  로드: {n_loaded}/{n_total}')

    # ── 분석 ─────────────────────────────────────────────────────────
    print('  [odd_final]    필드 분포·커버리지 계산...')
    final_fields = _per_field_stats(final_recs, FINAL_DIMS, FINAL_SCHEMA)
    final_combos = _combo_coverage(final_recs, FINAL_DIMS, FINAL_SCHEMA)

    print('  [odd_compat]   필드 분포·커버리지 계산...')
    compat_fields = _per_field_stats(compat_recs, COMPAT_DIMS, COMPAT_SCHEMA)
    compat_combos = _combo_coverage(compat_recs, COMPAT_DIMS, COMPAT_SCHEMA)

    print('  [odd_compat_v2] 필드 분포·커버리지 계산 (AV 성능 11개 필드)...')
    v2_recs = [_to_compat_v2(r) for r in final_recs]
    v2_fields = _per_field_stats(v2_recs, COMPAT_V2_DIMS, COMPAT_V2_SCHEMA)
    v2_combos = _combo_coverage(v2_recs, COMPAT_V2_DIMS, COMPAT_V2_SCHEMA)

    result = {
        'n_total_files':  n_total,
        'n_loaded':       n_loaded,
        'odd_final':      {'fields': final_fields,  'combos': final_combos},
        'odd_compat':     {'fields': compat_fields, 'combos': compat_combos},
        'odd_compat_v2':  {'fields': v2_fields,     'combos': v2_combos},
    }

    with open(P(OUT), 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # ── 콘솔 요약 ─────────────────────────────────────────────────────
    fc, cc = final_combos, compat_combos
    print(f'\n  ━━ odd_final (19 필드) ━━')
    print(f'  관측 조합: {fc["n_observed"]:>8,} / 이론 {fc["n_theoretical"]:,}  '
          f'({fc["coverage_ratio"]:.4%})')
    print(f'  클린 조합: {fc["n_clean_observed"]:>8,} / 이론 {fc["n_theoretical_clean"]:,}  '
          f'({fc["coverage_ratio_clean"]:.4%})  (unknown 없는 조합)')
    print(f'  싱글톤   : {fc["singleton_combos"]:>8,}  (1회만 등장한 조합)')

    print(f'\n  ━━ odd_compat (9 필드) ━━')
    print(f'  관측 조합: {cc["n_observed"]:>8,} / 이론 {cc["n_theoretical"]:,}  '
          f'({cc["coverage_ratio"]:.4%})')
    print(f'  클린 조합: {cc["n_clean_observed"]:>8,} / 이론 {cc["n_theoretical_clean"]:,}  '
          f'({cc["coverage_ratio_clean"]:.4%})')

    v2c = v2_combos
    print(f'\n  ━━ odd_compat_v2 (11 필드, AV 성능 기준) ━━')
    print(f'  관측 조합: {v2c["n_observed"]:>8,} / 이론 {v2c["n_theoretical"]:,}  '
          f'({v2c["coverage_ratio"]:.4%})')
    print(f'  클린 조합: {v2c["n_clean_observed"]:>8,} / 이론 {v2c["n_theoretical_clean"]:,}  '
          f'({v2c["coverage_ratio_clean"]:.4%})')
    print(f'  싱글톤   : {v2c["singleton_combos"]:>8,}')
    print(f'  필드별 미관측 값:')
    for dim in COMPAT_V2_DIMS:
        missing = v2_fields[dim]['missing_vals']
        if missing:
            print(f'    {dim:25s}: {missing}')

    print(f'\n  ━━ 필드별 미관측 스키마 값 (odd_final) ━━')
    for dim in FINAL_DIMS:
        missing = final_fields[dim]['missing_vals']
        if missing:
            print(f'  {dim:25s}: 미관측 {missing}')

    print(f'\n  ━━ 필드별 값 분포 (odd_compat) ━━')
    for dim in COMPAT_DIMS:
        s = compat_fields[dim]
        top = list(s['counts'].items())[:5]
        top_str = '  '.join(f'{v}={c:,}' for v, c in top)
        unk_info = f'  [unknown={s["unknown_count"]:,}]' if s['unknown_count'] else ''
        print(f'  {dim:22s}: {top_str}{unk_info}')

    print(f'\n  저장: {P(OUT)}')


if __name__ == '__main__':
    run(force=True)
