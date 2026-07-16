"""집계 전사: raw/kma/asos_hourly.csv → sources/weather_P1.csv + fog_P1.csv.

raw는 관측소×매시간 낱개 기록 (tm,stn,ta,rn,vs). 이를 (월,시)별로 접어 확률표로 만든다:
  · weather_P1.csv (month,hour,weather,prob)  = P(weather | month,hour), (월,시)당 합=1
  · fog_P1.csv     (month,hour,fog_present_prob) = P(시정<1km | month,hour), 독립축(합≠1)

분류 규칙(mapping.yaml §5-1·§5-2 + ASOS 수치 센티넬 실측):
  · rn(강수): -9.0 = **무강수(건조)**, 0.0 = 측정된 무강수, >0 = 강수량(mm).
              (KMA RN 관례: 건조하면 -9 보고. -9를 미측정으로 빼면 강수율이 겨울 54%로 폭증 —
               실측 검증상 -9=건조가 맞음. 1월 6%·7월 16%로 현실적.)
  · ta(기온): -99.0 = 결측 → snow/rain 판정 불가시 rain으로(보수적)
  · vs(시정): 미터 단위, -9.0 = 결측 → fog 분모에서 제외 (전시각 측정돼 288칸 모두 채워짐)
  weather = snow(강수>0 & 기온≤0) / rain(강수>0) / clear(그 외)
  fog     = 1 if 시정 < 1000m else 0   (유효 관측만)

[겨울 강수 3시간 보고 아티팩트] KMA는 겨울철 비종관시각(h%3≠0)엔 비가 와도 rn>0을 아예
안 찍는다(measured=측정된 rn≥0 이 0건). 그 시각을 그대로 두면 가짜 100% clear가 된다.
→ measured가 0인 '강수-맹점' 셀만 **가장 가까운 종관시각(0/3/…/21)에서 분포 상속**한다
(강수상태는 1~2시간 자기상관 → 종관값이 최선 근사). 상속 셀은 실행 로그·COVERAGE.md에 노출.

실행:  python3 transcribe_weather.py   (이후 loader.py로 계약 검증)
# ponytail: (월,시) 288칸 전국 집계(v0). region 층화는 design §4대로 검증 후.
"""
import csv
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "raw", "kma", "asos_hourly.csv")
OUT_W = os.path.join(HERE, "sources", "weather_P1.csv")
OUT_F = os.path.join(HERE, "sources", "fog_P1.csv")

WEATHERS = ["clear", "rain", "snow"]   # 고정 출력 순서
FOG_VIS_M = 1000                        # 시정 임계(m), mapping.yaml §5-1
MISSING_TA = -90.0                      # ta ≤ -90 → 결측(-99 센티넬)
MIN_MEASURED = 100                      # measured가 이 미만이면 강수-맹점 → 종관시각 상속


def classify_weather(rn, ta):
    """강수·기온 → clear/rain/snow. rn·ta는 이미 float 또는 None. (-9=건조→clear)"""
    if rn is None or rn <= 0:                    # -9(건조)·0(무강수) → clear
        return "clear"
    if ta is not None and ta > MISSING_TA and ta <= 0:
        return "snow"                           # 강수 있고 영하
    return "rain"                               # 강수 있고 (영상 or 기온결측)


def nearest_synoptic(h):
    """비종관시각 → 가장 가까운 종관시각(0,3,…,21)."""
    return min(round(h / 3) * 3, 21)


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main():
    wcount = defaultdict(lambda: defaultdict(int))   # (m,h) -> {weather: n} (-9 포함, clear로)
    measured = defaultdict(int)                       # (m,h) -> rn≥0 측정 관측수(맹점 탐지용)
    fsum = defaultdict(int)                           # (m,h) -> 시정<1km 관측수
    fobs = defaultdict(int)                           # (m,h) -> 유효 시정 관측수
    n = 0
    with open(SRC) as f:
        for r in csv.DictReader(f):
            tm = r["tm"]
            if len(tm) < 10:
                continue
            m, h = int(tm[4:6]), int(tm[8:10])
            rn, ta, vs = _f(r["rn"]), _f(r["ta"]), _f(r["vs"])
            wcount[(m, h)][classify_weather(rn, ta)] += 1
            if rn is not None and rn >= 0:           # 측정된 rn(0 or >0) — 맹점 아님
                measured[(m, h)] += 1
            if vs is not None and vs >= 0:           # -9 결측 제외
                fobs[(m, h)] += 1
                if vs < FOG_VIS_M:
                    fsum[(m, h)] += 1
            n += 1

    # weather: 강수-맹점 셀(measured<임계)은 종관시각에서 분포 상속 → 정규화(합=1), 3종 출력
    wrows, inherited = [], []
    for m in range(1, 13):
        for h in range(24):
            src_h = h if measured[(m, h)] >= MIN_MEASURED else nearest_synoptic(h)
            if src_h != h:
                inherited.append((m, h, src_h))
            counts = wcount[(m, src_h)]
            tot = sum(counts.values()) or 1
            for w in WEATHERS:
                wrows.append((m, h, w, round(counts[w] / tot, 4)))

    with open(OUT_W, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["month", "hour", "weather", "prob"])
        w.writerows(wrows)

    # fog: (월,시)당 시정<1km 비율 (독립축, 전시각 측정)
    frows = [(m, h, round(fsum[(m, h)] / fobs[(m, h)], 4))
             for m in range(1, 13) for h in range(24) if fobs[(m, h)]]
    with open(OUT_F, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["month", "hour", "fog_present_prob"])
        w.writerows(frows)

    # 가드: weather (월,시)별 합=1
    chk = defaultdict(float)
    for m, h, _, p in wrows:
        chk[(m, h)] += p
    bad = {k: round(v, 3) for k, v in chk.items() if abs(v - 1) > 0.01}
    assert not bad, f"weather 합≠1: {list(bad.items())[:5]}"
    print(f"[OK] {n:,}행 집계 → weather {len(wrows)}행(288칸) / fog {len(frows)}칸")
    print(f"     ⚠ 강수 미측정으로 종관시각 상속한 셀: {len(inherited)}/288 "
          f"(겨울 비종관시각 — COVERAGE.md 한계 ⑤)")
    print(f"     {OUT_W}\n     {OUT_F}")


def _selfcheck():
    assert classify_weather(-9.0, -2.0) == "clear"     # -9 = 건조
    assert classify_weather(0.0, -2.0) == "clear"      # 측정된 무강수
    assert classify_weather(0.5, -2.0) == "snow"       # 강수 & 영하
    assert classify_weather(0.5, 5.0) == "rain"        # 강수 & 영상
    assert classify_weather(0.5, -99.0) == "rain"      # 강수 & 기온결측 → rain
    assert nearest_synoptic(8) == 9 and nearest_synoptic(7) == 6
    assert nearest_synoptic(1) == 0 and nearest_synoptic(23) == 21
    print("[OK] transcribe_weather self-check 통과")


if __name__ == "__main__":
    _selfcheck()
    main()
