"""KMA ASOS 시간자료(apihub) 다년·전시간 대량 조달 → raw/kma/asos_hourly.csv.

weather_P1/fog_P1 전사(집계)용 실데이터. (월,시)당 다수일이 필요해 전 시간(0~23)·전일·
다년을 훑는다. sfctm2는 시각당 1콜이라 콜 수가 많음(≈26k) → 재시도·재개·스트리밍 필수.

- 재개(resumable): asos_hourly.csv 이미 있으면 그 안의 tm을 스킵하고 이어감(쿼터·중단 대비).
- 스트리밍: 타임스탬프마다 append+flush → 중단돼도 받은 만큼 보존.
- 가드: 반환 tm≠요청 tm(현재시각 폴백)이면 스킵.

인증키: 환경변수 KMA_API_KEY.  실행 전:  set -a; . <project>/.env; set +a
실행(백그라운드):  python3 fetch_kma_full.py
"""
import calendar
import csv
import os
import time
import urllib.request

API = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php"
IDX = dict(tm=0, stn=1, ta=11, rn=15, vs=32)   # help=1 스키마 (전 행 46토큰 고정)
YEARS = [2022, 2023, 2024]                      # 완결 3개년 (오늘 2026-07 기준 과거)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw", "kma")
PATH = os.path.join(OUT, "asos_hourly.csv")


def all_timestamps():
    for y in YEARS:
        for m in range(1, 13):
            for d in range(1, calendar.monthrange(y, m)[1] + 1):
                for h in range(24):
                    yield f"{y}{m:02d}{d:02d}{h:02d}00"


def fetch_one(tm, key, tries=4):
    url = f"{API}?tm={tm}&stn=0&help=0&authKey={key}"
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                text = r.read().decode("latin1")
            break
        except Exception:
            if i == tries - 1:
                return None                      # 이 tm 포기(다음 실행 때 재개)
            time.sleep(1.5 * (i + 1))
    rows = []
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        f = line.split()
        if len(f) < 33:
            continue
        rows.append([f[i] for i in IDX.values()])
    if rows and rows[0][0] != tm:                # 현재시각 폴백 → 오염, 스킵
        return None
    return rows


def main():
    key = os.environ.get("KMA_API_KEY")
    if not key:
        raise SystemExit("KMA_API_KEY 없음.  set -a; . <project>/.env; set +a 후 재실행")
    os.makedirs(OUT, exist_ok=True)

    done = set()
    if os.path.exists(PATH):
        with open(PATH) as f:
            next(f, None)
            for line in f:
                done.add(line.split(",", 1)[0])
        print(f"[resume] 기존 {len(done)}개 tm 스킵")

    todo = [tm for tm in all_timestamps() if tm not in done]
    print(f"[start] 전체 {len(todo)}개 tm 조달 시작 (years={YEARS})")

    f = open(PATH, "a", newline="")
    w = csv.writer(f)
    if not done:
        w.writerow(list(IDX))
    ok = skip = 0
    for n, tm in enumerate(todo, 1):
        rows = fetch_one(tm, key)
        if rows:
            w.writerows(rows)
            ok += 1
        else:
            skip += 1
        if n % 200 == 0:
            f.flush()
            print(f"  {n}/{len(todo)}  ok={ok} skip={skip}  (최근 tm={tm})", flush=True)
    f.flush(); f.close()
    print(f"[done] ok={ok} skip={skip} → {PATH}")


if __name__ == "__main__":
    main()
