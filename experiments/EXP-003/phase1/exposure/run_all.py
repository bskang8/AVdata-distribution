"""Phase 1 전체 순차 실행 엔트리 (조달→조립→선정).

각 스크립트는 단독 실행형이라 subprocess로 순서대로 돈다. 의존 DAG:
  (fetch_*)→raw → recon → transcribe_* → sources → compose → pself → analyze
                                                  → validate → criticality → sweep

기본 스킵: 외부(raw/클립) 읽는 느린 단계는 산출물 있으면 건너뜀. 조립은 항상 재실행.
사용:
  python3 run_all.py                 # 2부 컴퓨트 체인(캐시 활용)
  python3 run_all.py --force         # 전부 강제 재실행
  python3 run_all.py --force pself    # 특정 단계만 강제
  python3 run_all.py --fetch          # 1부 API 조달부터(키 필요: set -a; . .env; set +a)
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))

# (이름, 스크립트, 산출물 마커, cache=산출물 있으면 스킵, fetch=--fetch일 때만)
STAGES = [
    ("fetch_kma_full", "procure/fetch_kma_full.py", "raw/kma/asos_hourly.csv", True,  True),
    ("fetch_ktdb",     "procure/fetch_ktdb.py",     "raw/ktdb/vkt_sample.csv", True,  True),
    ("recon",          "procure/recon.py",          "recon/availability.json", True,  False),
    ("transcribe_vkt", "procure/transcribe_vkt.py", "sources/vkt_weight.csv",  True,  False),
    ("transcribe_hourly", "procure/transcribe_hourly.py", "sources/hourly_profile.csv", True, False),
    ("transcribe_weather", "procure/transcribe_weather.py", "sources/weather_P1.csv", True, False),
    ("compose",        "compose.py",             "output/P_ext.json",       False, False),
    ("pself",          "select/pself.py",        "output/P_self.json",      True,  False),
    ("analyze",        "select/analyze.py",      "output/analysis.json",    False, False),
    ("validate",       "select/validate.py",     None,                      False, False),  # 게이트
    ("criticality",    "criticality.py",         "output/criticality.json", True,  False),
    ("extrapolate",    "select/extrapolate.py",  "output/extrapolation.json", False, False),
    ("sweep",          "select/sweep.py",        "output/sweep.json",       False, False),
]


def run_stage(name, script, forced):
    t0 = time.time()
    r = subprocess.run([sys.executable, script], cwd=HERE)
    dt = time.time() - t0
    if r.returncode != 0:
        raise SystemExit(f"\n[중단] {name} 실패(exit {r.returncode}). 위 로그 확인.")
    return dt


def summary():
    def load(f):
        p = os.path.join(HERE, "output", f)
        return json.load(open(p)) if os.path.exists(p) else None
    px, an, cr, sw = load("P_ext.json"), load("analysis.json"), load("criticality.json"), load("sweep.json")
    ex = load("extrapolation.json")
    print("\n" + "=" * 60 + "\n[요약]")
    if px:
        print(f"  P_ext: {px['n_cells']}셀(신뢰 4축)")
    if an and an.get("cut"):
        print(f"  §8 핵심영역: 누적95% = 상위 {an['cut'].get('95pct')}조합")
    if cr:
        tgt = cr.get("collection_targets", [])
        if tgt:
            t0 = tgt[0]
            print(f"  §10 수집타겟 {len(tgt)}개, 최상위 crit={t0['crit']} {t0['combo']}")
    if ex:
        print(f"  §10+ 외삽: 수집갭 {ex['n_collection_gap']}(실주행) · 희소 {ex['n_rare_synth']}(합성)")
    if sw:
        print(f"  §11 스윕: exposure 불변={sw['exposure_invariant']}, Fragile={sw['fragile_blocks'] or '없음'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", nargs="*", metavar="STAGE",
                    help="강제 재실행(생략=전체, 예: --force pself criticality)")
    ap.add_argument("--fetch", action="store_true", help="1부 API 조달 단계 포함(키 필요)")
    args = ap.parse_args()

    forced = ({s[0] for s in STAGES} if args.force == [] else set(args.force or []))

    timings = {}
    for name, script, marker, cache, is_fetch in STAGES:
        if is_fetch and not args.fetch:
            continue
        fresh = cache and marker and os.path.exists(os.path.join(HERE, marker)) and name not in forced
        if fresh:
            print(f"── {name}: 스킵(캐시 {marker})")
            continue
        print(f"── {name}: 실행 …")
        timings[name] = round(run_stage(name, script, forced), 1)

    summary()
    if timings:
        print("\n[소요] " + ", ".join(f"{k} {v}s" for k, v in timings.items()))
    print("[OK] Phase 1 파이프라인 완료.")


if __name__ == "__main__":
    main()
