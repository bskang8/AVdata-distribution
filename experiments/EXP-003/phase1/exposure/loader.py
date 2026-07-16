"""EXP-003 Phase 1 · 1부(데이터 조달 계획) — 블록 CSV 로더 + 계약 검증기.

design.md §6 "CSV 계약"의 구현. 조달 산출물(sources/*.csv)을 블록별 조건부 확률표로
읽어 dict 테이블로 노출하고, tidy·prob-합=1 계약을 검증한다.

이 파일이 아는 유일한 것 = **파일명 → 블록·조건키 매핑**(BLOCKS). 소스 갈아끼우기 =
CSV 교체 한 번(코드 무변경). 2부(compose.py 등)는 여기서 나온 테이블만 소비한다.

의존: stdlib csv + PyYAML 뿐. phase0/외부 모듈 import 없음.
실행(self-check):  python3 loader.py
"""
import csv
import os

SOURCES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sources')
SUM_TOL = 0.01   # prob 합=1 허용오차 (손전사 반올림 흡수)

# 파일명 → 블록 구조. keys=조건키 컬럼, cat=분포되는 축 컬럼(None=독립축),
# 값=각 행의 마지막 컬럼. sum1=조건키 그룹 내 값 합이 1이어야 하는가.
BLOCKS = {
    'weather_P1.csv':    dict(block='P1_weather',  keys=['month', 'hour'],       cat='weather',    sum1=True),
    'fog_P1.csv':        dict(block='P1_fog',       keys=['month', 'hour'],       cat=None,         sum1=False),
    'vkt_weight.csv':    dict(block='w_vkt',        keys=[],                      cat='road_type',  sum1=True),
    'hourly_profile.csv':dict(block='w_hourly',     keys=['road_type'],           cat='hour',       sum1=True),
    'speed_P4.csv':      dict(block='P4_speed',     keys=['road_type', 'weather'],cat='speed',      sum1=True),
    'agent_P3.csv':      dict(block='P3_agent',     keys=['road_type', 'hour'],   cat='agent_type', sum1=True),
    'density_P3.csv':    dict(block='P3_density',   keys=['road_type', 'hour'],   cat='density',    sum1=True),
    'lighting_P5.csv':   dict(block='P5_lighting',  keys=['road_type', 'hour'],   cat='lighting',   sum1=True),
}


def _coerce(v):
    """숫자로 보이면 int, 아니면 문자열. 조건키/축 값 정규화용."""
    try:
        return int(v)
    except (ValueError, TypeError):
        return v


def load_block(fname, sources_dir=SOURCES_DIR):
    """CSV 한 장 → 중첩 dict 테이블 반환.

    cat 있으면  table[key_tuple][cat_value] = prob
    cat 없으면(독립축) table[key_tuple] = prob
    key_tuple = tuple(coerce(조건키 값)); keys=[] 이면 빈 튜플 ().
    """
    spec = BLOCKS[fname]
    keys, cat = spec['keys'], spec['cat']
    path = os.path.join(sources_dir, fname)
    with open(path, newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
        expected = keys + ([cat] if cat else []) + [_value_col(header, keys, cat)]
        if header != expected:
            raise ValueError(f"{fname}: 헤더 불일치\n  기대: {expected}\n  실제: {header}")
        val_idx = len(header) - 1
        table = {}
        for row in reader:
            if not row or all(c.strip() == '' for c in row):
                continue
            key = tuple(_coerce(row[header.index(k)]) for k in keys)
            prob = float(row[val_idx])
            if cat:
                table.setdefault(key, {})[_coerce(row[header.index(cat)])] = prob
            else:
                table[key] = prob
    return table


def _value_col(header, keys, cat):
    structural = set(keys) | ({cat} if cat else set())
    tail = [c for c in header if c not in structural]
    if len(tail) != 1:
        raise ValueError(f"값 컬럼을 하나로 특정 못함: {tail} (헤더 {header})")
    return tail[0]


def validate(sources_dir=SOURCES_DIR):
    """전체 블록을 계약 대비 검증. 위반 문자열 리스트 반환(빈 리스트=통과)."""
    violations = []
    for fname, spec in BLOCKS.items():
        path = os.path.join(sources_dir, fname)
        if not os.path.exists(path):
            violations.append(f"{fname}: 파일 없음 ({path})")
            continue
        try:
            table = load_block(fname, sources_dir)
        except (ValueError, OSError) as e:
            violations.append(str(e))
            continue
        if not spec['sum1']:
            continue
        for key, dist in table.items():
            s = sum(dist.values())
            if abs(s - 1.0) > SUM_TOL:
                violations.append(f"{fname}: 조건 {key} 의 prob 합={s:.4f} (≠1, tol={SUM_TOL})")
    return violations


def load_all(sources_dir=SOURCES_DIR):
    """검증 통과 시 {block_name: table} 반환. 위반 있으면 예외.

    2부 진입점: compose.py는 이 함수만 부르면 된다.
    """
    v = validate(sources_dir)
    if v:
        raise ValueError("CSV 계약 위반:\n  - " + "\n  - ".join(v))
    return {BLOCKS[f]['block']: load_block(f, sources_dir) for f in BLOCKS}


if __name__ == '__main__':
    viol = validate()
    if viol:
        print("[FAIL] CSV 계약 위반:")
        for x in viol:
            print("  -", x)
        raise SystemExit(1)
    tables = load_all()
    print(f"[OK] {len(tables)}개 블록 로드 및 계약 검증 통과:")
    for name, t in tables.items():
        print(f"  {name:14s} 조건 그룹 {len(t):3d}개  예: {next(iter(t.items()))}")
