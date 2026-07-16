"""KMA ASOS 시간자료(apihub) → raw/kma/asos_sample.csv (recon 입력용).

apihub `kma_sfctm2`는 CSV가 아니라 고정폭 텍스트(주석 #, EUC-KR)라 여기서 파싱해
recon이 읽을 tidy CSV(tm,stn,ta,rn,vs)로 변환한다. 컬럼 인덱스는 help=1 스키마 기준:
TM=0, STN=1, TA=11(기온), RN=15(강수), VS=32(시정).  전 행 46토큰 고정 확인함.

인증키: 환경변수 KMA_API_KEY (프로젝트 .env). 실행 전:  set -a; . ../../../../.env; set +a
실행:  python3 fetch_kma.py
# ponytail: 대표 샘플만 조달(TIMESTAMPS). weather_P1.csv 실구축엔 (월,시)당 다수일
#           집계가 필요 — TIMESTAMPS를 전연도·전시간으로 늘리고 §7에서 집계하면 됨.
"""
import csv
import os
import urllib.request

API = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php"
IDX = dict(tm=0, stn=1, ta=11, rn=15, vs=32)   # help=1 스키마
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw", "kma")

# 대표 샘플: 2022년 각 월 15일, 08시/19시 (월·시 변동 확인용). YYYYMMDDHHMM(12자리).
# 늘리려면 여기만 수정. ⚠️ tm이 malformed/미래면 API가 '현재시각'을 반환하므로 12자리 엄수.
TIMESTAMPS = [f"2022{m:02d}15{h:02d}00" for m in range(1, 13) for h in (8, 19)]


def fetch_one(tm, key):
    url = f"{API}?tm={tm}&stn=0&help=0&authKey={key}"
    with urllib.request.urlopen(url, timeout=30) as r:
        text = r.read().decode("latin1")   # 데이터행은 ASCII, 주석만 EUC-KR
    rows = []
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        f = line.split()
        if len(f) < 33:                    # 방어: 형식 이상행 스킵
            continue
        rows.append({k: f[i] for k, i in IDX.items()})
    # 가드: 반환 tm이 요청과 다르면 API가 현재시각으로 폴백한 것 → 샘플 오염
    if rows and rows[0]["tm"] != tm:
        print(f"  [warn] tm={tm} 요청→반환 {rows[0]['tm']} (폴백). 이 시각 스킵")
        return []
    return rows


def main():
    key = os.environ.get("KMA_API_KEY")
    if not key:
        raise SystemExit("KMA_API_KEY 없음.  set -a; . ../../../../.env; set +a  후 재실행")
    os.makedirs(OUT, exist_ok=True)
    all_rows, ok = [], 0
    for tm in TIMESTAMPS:
        try:
            r = fetch_one(tm, key)
            all_rows += r
            ok += 1
        except Exception as e:
            print(f"  [skip] tm={tm}: {e}")
    if not all_rows:
        raise SystemExit("데이터 0행 — 키/구독 확인")
    path = os.path.join(OUT, "asos_sample.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(IDX))
        w.writeheader()
        w.writerows(all_rows)
    print(f"[OK] {ok}/{len(TIMESTAMPS)} 시각 · {len(all_rows)}행 → {path}")
    print(f"     헤더: {list(IDX)}  (recon roles: tm/rn/ta/vs 매칭)")


if __name__ == "__main__":
    main()
