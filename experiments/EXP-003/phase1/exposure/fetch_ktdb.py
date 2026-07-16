"""KTDB 상시 교통량(apis.data.go.kr KictTmsStat/itmsh_yearly) → raw/ktdb/itmsh_sample.csv.

itmsh_yearly = 지점·방향별 시간대별(time_type1..24) 연간 교통량. dtype별로 합산·정규화해
두 산출물을 만든다:
  · itmsh_sample.csv (grade,hour,share)  = recon w_hourly / hourly_profile 재료
  · vkt_sample.csv   (grade,share)       = recon w_vkt = P(road_type) 구성비

필수 파라미터(스웨거): serviceKey, spot_id(=all), year, dtype, numOfRows(1~100), pageNo(0부터).
dtype 1:고속도로 2:일반도로 3:지방도 5:국가지원지방도.

인증키: 환경변수 DATAGO_API_KEY.  실행 전:  set -a; . <project>/.env; set +a
실행:  python3 fetch_ktdb.py
# ponytail: w_hourly(등급×시간)·w_vkt(등급 구성비) 둘 다 이 API의 total_count로 커버.
#           연장·AADT '수치'는 여전히 API 밖(→통계연보)이나 구성비는 관측교통량으로 산출됨.
#           P3_density(V/C)만 용량편람(문서) 방법론 산출값 → recon HAND_ANCHOR로 남음.
# [한계·고정] itmsh_yearly 백엔드는 dtype 1·2(고속·일반국도)만 적재. dtype 3·5(지방도·
#           국가지원지방도)는 연도·포맷·numOfRows 무관하게 즉시 502(백엔드 미제공, 구조적).
#           → w_vkt·w_hourly는 4등급 중 2등급만 커버. 방침상 타 소스로 보완하지 않음(그 한계
#           그대로 두고 recon vocab_missing으로 노출). 지방도 필요 시 통계연보 별도 조달.
"""
import csv
import json
import os
import time
import urllib.parse
import urllib.request

BASE = "https://apis.data.go.kr/1613000/KictTmsStat/itmsh_yearly"
YEAR = 2023
DTYPE = {1: "고속도로", 2: "일반도로", 3: "지방도", 5: "국가지원지방도"}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw", "ktdb")


def _get(url, tries=4):
    """일시적 5xx/네트워크 플레이크는 백오프 재시도 (apihub 게이트웨이 502 잦음)."""
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=40) as r:
                return json.loads(r.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            code = getattr(e, "code", None)
            if i == tries - 1 or (code and code < 500 and code != 429):
                raise
            time.sleep(1.5 * (i + 1))


def fetch_dtype(dtype, key):
    """dtype 전 지점·방향 레코드를 페이지네이션으로 모아 반환."""
    recs, page = [], 0
    while True:
        q = urllib.parse.urlencode(dict(
            serviceKey=key, spot_id="all", year=YEAR, dtype=dtype,
            output="json", numOfRows=100, pageNo=page))
        d = _get(f"{BASE}?{q}")
        batch = d.get("traffic") or []
        recs += batch
        if len(recs) >= int(d.get("count", 0)) or not batch:
            break
        page += 1
    return recs


def main():
    key = os.environ.get("DATAGO_API_KEY")
    if not key:
        raise SystemExit("DATAGO_API_KEY 없음.  set -a; . <project>/.env; set +a 후 재실행")
    os.makedirs(OUT, exist_ok=True)
    rows = []
    grade_tot = {}                             # 등급별 연간 관측교통량 = w_vkt 구성비 재료
    for dtype, name in DTYPE.items():
        try:
            recs = fetch_dtype(dtype, key)
        except Exception as e:                 # 특정 도로종류 게이트웨이 오류는 스킵
            print(f"  dtype={dtype} {name:8s}: [skip] {e}")
            continue
        # 시간대별(1..24) 전 지점·방향 합산
        hourly = [0] * 24
        for rec in recs:
            for h in range(24):
                hourly[h] += int(rec.get(f"time_type{h+1}", 0) or 0)
        tot = sum(hourly) or 1
        grade_tot[name] = tot
        for h in range(24):
            rows.append(dict(grade=name, hour=h, share=round(hourly[h] / tot, 5)))
        print(f"  dtype={dtype} {name:8s}: {len(recs):4d}지점 · 합계 {tot:,}")
    if not rows:
        raise SystemExit("전 도로종류 실패 — 나중에 재시도")
    path = os.path.join(OUT, "itmsh_sample.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["grade", "hour", "share"])
        w.writeheader()
        w.writerows(rows)
    # 가드: 등급별 share 합=1
    import collections
    s = collections.defaultdict(float)
    for r in rows:
        s[r["grade"]] += r["share"]
    bad = {g: round(v, 3) for g, v in s.items() if abs(v - 1) > 0.01}
    assert not bad, f"등급별 share 합≠1: {bad}"
    print(f"[OK] {len(rows)}행 ({len(grade_tot)}/{len(DTYPE)}등급×24시) → {path}  (헤더 grade/hour/share)")

    # w_vkt = P(road_type): 등급별 관측교통량을 정규화한 구성비 (grade,share) long CSV.
    # ponytail: 상시지점 관측교통량 기준 구성비 = 통계연보 방법론과 동종.
    #           진짜 VKT(연장가중)와는 다를 수 있음 → 상향경로: 15107170 등급별 연장 조인.
    gtot = sum(grade_tot.values()) or 1
    vkt = [dict(grade=g, share=round(t / gtot, 5)) for g, t in grade_tot.items()]
    vpath = os.path.join(OUT, "vkt_sample.csv")
    with open(vpath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["grade", "share"])
        w.writeheader()
        w.writerows(vkt)
    assert abs(sum(r["share"] for r in vkt) - 1) < 0.01, "vkt 구성비 합≠1"
    print(f"[OK] {len(vkt)}등급 구성비 → {vpath}  (헤더 grade/share)")

    missing = [n for n in DTYPE.values() if n not in grade_tot]
    if missing:
        print(f"[한계] itmsh_yearly 미제공 등급(구조적·502): {missing} "
              f"→ vkt/hourly 모두 {len(grade_tot)}/{len(DTYPE)} 등급만. "
              f"방침상 타 소스 보완 안 함 — recon vocab_missing에 명시됨.")


if __name__ == "__main__":
    main()
