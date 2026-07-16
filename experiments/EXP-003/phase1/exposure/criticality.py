"""§10 criticality — 안전-위험 손 위험모델 + 수집 사각지대 진단.

design §10 + coverage-vs-sufficiency.md "Criticality 손 위험표". exposure 누적영역(§8)은
저빈도 안전-critical 조합을 놓친다 → crit로 전체 공간을 랭킹하고, 그중 데이터가 부족/미관측
인 조합을 수집·합성 타겟으로 뽑는다.

crit(c) = likelihood × severity = ∏(블록별 배수). **published multiplier 앵커**(숫자 지어내기
금지) + **상관 차원은 블록으로 묶어 배수 하나**(악천후 이중계산 방지, design 경고). forbidden=0.
축은 crit 관련 + phase0 관측가능한 6개: {road_type, weather, fog, lighting, agent_type,
traffic_density}. (speed는 phase0 compat에 없어 v1 제외 → 고속 severity 과소, 한계로 표기.)

수집 사각지대 = crit 상위 ∧ P_self 표본 부족(꼬리)/미관측. 미관측은 v1에선 "coverage=0 고crit"
로 flag(정식 이웃-외삽은 situation-coverage-grid.md, v2).

입력: phase0 clips(P_self coverage 재집계, 캐시 output/P_self_crit.json)
출력: output/criticality.json + stdout   실행: python3 criticality.py
"""
import itertools
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
PHASE0 = os.path.abspath(os.path.join(HERE, "..", "..", "phase0"))
sys.path.insert(0, PHASE0)

# ── 값별 배수 = published 통계 앵커 (coverage-vs-sufficiency.md) ──────────────
# likelihood 블록 (지각저하·충돌기하). severity 블록 (운동에너지·취약성).
ROAD_TYPE = {"urban": 1.0, "rural": 1.2, "national_road": 1.5, "highway": 2.0}   # severity: 에너지
# weather·road_surface는 상관(비→젖음) → 한 블록 배수 하나 (FHWA weather-crash)
WEATHER = {"clear": 1.0, "rain": 1.5, "snow": 2.5}                               # likelihood
FOG = {"none": 1.0, "present": 2.0}                                              # likelihood, 독립
LIGHTING = {"well_lit": 1.0, "moderate": 1.5, "poorly_lit": 2.5}                 # NHTSA 야간
AGENT = {"cars_only": 1.0, "mixed": 1.5, "cyclists": 3.0, "pedestrians": 4.0,    # Rosén&Sander VRU
         "emergency": 2.0}                                                        # severity
DENSITY = {"sparse": 1.0, "moderate": 1.3, "dense": 1.6}                         # 충돌점 수
SPEED = {"low": 1.0, "mid": 2.0, "high": 4.0}                                    # severity ∝ v² (v2 추가)
CRIT_CAP = 500.0   # 다요인 누적 상한(design "cap/log 감쇠"). 에너지블록 감쇠 후 최대곱 ~400 → 안 물려

# 관측 6축 = phase0가 태깅함 → coverage 교차 대상. speed는 클립 미태깅(연속·비태깅, §12-R)
# → crit 랭킹엔 넣되 coverage는 6축 투영(combo[:N_OBS])으로 본다.
OBS_AXES = ["road_type", "weather", "fog", "lighting", "agent_type", "traffic_density"]
AXES = OBS_AXES + ["speed"]
TABLES = [ROAD_TYPE, WEATHER, FOG, LIGHTING, AGENT, DENSITY, SPEED]
N_OBS = len(OBS_AXES)


def crit(combo, tables=TABLES):
    """crit = (∏ 독립블록) × ENERGY(road_type, speed). forbidden=0, CRIT_CAP 상한.

    잔여상관 감쇠: road_type·speed 둘 다 운동에너지 severity라 상관(고속도로↔고속) →
    곱하면 '고에너지'를 이중계산. 대신 **가법 결합** ENERGY = m_road_type + m_speed − 1:
      · 한쪽 baseline(=1)이면 다른쪽으로 환원 (urban×high→speed만, highway×low→road만)
      · 겹치는 highway×high만 감쇠 (2×4=8 → 2+4−1=5)
    나머지 5블록(weather·fog·lighting·agent·density)은 독립이라 그대로 곱.
    (TABLES 순서 [road_type, w,f,l,ag,de, speed] 가정 — 위 정의부와 일치.)
    tables 주입 가능(sweep용)."""
    rt, ag = combo[0], combo[4]
    if rt == "highway" and ag in ("pedestrians", "cyclists"):   # forbidden(법·물리)
        return 0.0
    energy = tables[0][combo[0]] + tables[-1][combo[-1]] - 1.0  # road_type ⊕ speed (감쇠)
    prod = energy
    for i in range(1, 6):                                        # weather·fog·lighting·agent·density (독립)
        prod *= tables[i][combo[i]]
    return min(prod, CRIT_CAP)


def pself_coverage():
    """phase0 clips → crit 6축 clean 조합 카운트. 캐시."""
    cache = os.path.join(OUT, "P_self_crit.json")
    if os.path.exists(cache):
        d = json.load(open(cache))
        return {tuple(k.split("|")): v for k, v in d["counts"].items()}, d["n_clips"]
    from step_a_odd_coverage import _flatten_final    # phase0 무수정 재사용
    from config import ODD_DIR
    wmap = {"none": "clear", "rain": "rain", "snow": "snow"}
    cnt = Counter()
    n = 0
    for fn in sorted(os.listdir(ODD_DIR)):
        if not fn.endswith(".json"):
            continue
        try:
            d = json.load(open(os.path.join(ODD_DIR, fn)))
        except (json.JSONDecodeError, OSError):
            continue
        if not d.get("odd_final"):
            continue
        f = _flatten_final(d["odd_final"])
        n += 1
        key = (f.get("road_type", "unknown"), wmap.get(f.get("precipitation"), "unknown"),
               f.get("fog", "unknown"), f.get("lighting_condition", "unknown"),
               f.get("road_user_types", "unknown"), f.get("traffic_density", "unknown"))
        if "unknown" not in key:
            cnt[key] += 1
    os.makedirs(OUT, exist_ok=True)
    json.dump({"axes": OBS_AXES, "n_clips": n,          # 관측 6축(speed 미포함)
               "counts": {"|".join(k): v for k, v in cnt.most_common()}},
              open(cache, "w"), ensure_ascii=False, indent=2)
    return dict(cnt), n


def main():
    cov, n_clips = pself_coverage()
    combos = [c for c in itertools.product(*[t.keys() for t in TABLES]) if crit(c) > 0]
    # coverage는 관측 6축 투영(combo[:N_OBS]) — speed는 클립 미태깅이라 speed별 구분 불가
    scored = sorted(((crit(c), cov.get(c[:N_OBS], 0), c) for c in combos), key=lambda x: -x[0])

    print(f"=== §10 criticality ({len(combos)}개 유효조합, forbidden 제외) ===")
    print(f"  P_self coverage: {n_clips:,}클립, 관측된 crit조합 {sum(1 for _,n,_ in scored if n>0)}/{len(combos)}")
    print("\n  ── 상위 crit 조합 (배수·관측클립수) ──")
    for cr, obs, c in scored[:12]:
        flag = "  🚩미관측" if obs == 0 else ("  ⚠️꼬리" if obs < 50 else "")
        print(f"    crit={cr:5.1f}  n={obs:6d}  {'×'.join(c)}{flag}")

    # 수집 사각지대 = crit 상위 ∧ 표본부족/미관측
    THRESH = 50
    blind = [(cr, obs, c) for cr, obs, c in scored if cr >= 8.0 and obs < THRESH]
    unobs = [(cr, c) for cr, obs, c in scored if obs == 0 and cr >= 6.0]
    print(f"\n  ── 🚩 수집·합성 타겟 (crit≥8 ∧ 관측<{THRESH}) : {len(blind)}개 ──")
    for cr, obs, c in blind[:10]:
        print(f"    crit={cr:5.1f}  n={obs:4d}  {'×'.join(c)}")

    report = {
        "n_valid_combos": len(combos), "n_clips": n_clips,
        "multipliers": {a: t for a, t in zip(AXES, TABLES)}, "crit_cap": CRIT_CAP,
        "top_crit": [dict(crit=round(cr, 2), n_self=obs, combo=dict(zip(AXES, c)))
                     for cr, obs, c in scored[:30]],
        "collection_targets": [dict(crit=round(cr, 2), n_self=obs, combo=dict(zip(AXES, c)))
                               for cr, obs, c in blind],
        "unobserved_high_crit": [dict(crit=round(cr, 2), combo=dict(zip(AXES, c)))
                                 for cr, c in unobs],
        "note": "최종 수집타겟 = analyze §8 exposure 누적영역 ∪ 위 collection_targets. "
                "v2: speed축 추가(severity∝v²) + road_type⊕speed 에너지블록 가법감쇠(이중계산 제거). "
                "단 phase0 클립이 speed 미태깅 → coverage(n_self)는 관측 6축 투영값이라 obs>0라도 "
                "해당 speed 보유 보장 못 함(§12-R speed 관측불가). 이웃 확률외삽은 후속(situation-coverage-grid).",
    }
    json.dump(report, open(os.path.join(OUT, "criticality.json"), "w"), ensure_ascii=False, indent=2)
    print(f"\n[OK] → output/criticality.json (top30 + 타겟 {len(blind)} + 미관측 {len(unobs)})")


def _selfcheck():
    # 단조성: VRU>차량, 눈>맑음, 야간>주간, 고속>저속 (7축, 끝에 speed)
    base = ("urban", "clear", "none", "well_lit", "cars_only", "sparse", "low")
    assert crit(("urban", "clear", "none", "well_lit", "pedestrians", "sparse", "low")) > crit(base)
    assert crit(("urban", "snow", "none", "well_lit", "cars_only", "sparse", "low")) > crit(base)
    assert crit(("urban", "clear", "none", "poorly_lit", "cars_only", "sparse", "low")) > crit(base)
    assert crit(("urban", "clear", "none", "well_lit", "cars_only", "sparse", "high")) > crit(base)
    # 잔여상관 감쇠: highway×high = 2+4−1=5 (곱 8 아님). urban×high = 1+4−1=4 (speed만).
    hh = ("highway", "clear", "none", "well_lit", "cars_only", "sparse", "high")
    uh = ("urban", "clear", "none", "well_lit", "cars_only", "sparse", "high")
    assert abs(crit(hh) - 5.0) < 1e-9, crit(hh)
    assert abs(crit(uh) - 4.0) < 1e-9, crit(uh)
    assert crit(hh) < ROAD_TYPE["highway"] * SPEED["high"], "감쇠 안 됨(곱=8)"
    # forbidden
    assert crit(("highway", "clear", "none", "well_lit", "pedestrians", "sparse", "high")) == 0.0
    # cap
    assert crit(("national_road", "snow", "present", "poorly_lit", "pedestrians", "dense", "high")) <= CRIT_CAP
    print("[OK] criticality self-check 통과")


if __name__ == "__main__":
    _selfcheck()
    main()
