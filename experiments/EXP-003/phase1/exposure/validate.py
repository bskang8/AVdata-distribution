"""§11.1 앵커 검증 — 런타임 self-check (design §12 runnable check).

손표·조립이 도메인 상식을 어기면 여기서 assert로 터진다. CI에 붙일 수 있는 관문.
앵커는 신뢰 4축 P_ext(손앵커 marginalize) + 입력표에서 확인 가능한 것으로 한정:
  1. highway 보행자 ≈ 0 (forbidden 하드룰, agent 입력표)
  2. P_ext weather 최빈 = clear (맑음 우세)
  3. P_ext road_surface 최빈 = dry
  4. P_ext snow 비중이 전국 겨울 소수 범위(0.002~0.05)
  5. P_ext 합 = 1 (조립 무결)

실행: python3 validate.py   (터지지 않으면 통과)
"""
import compose
import loader


def _marginal(P, i):
    m = {}
    for c, p in P.items():
        m[c[i]] = m.get(c[i], 0.0) + p
    return m


def main():
    tables = loader.load_all()
    P = compose.compose(tables)

    # 1. highway 보행자 ≈ 0 (구조적 0)
    agent = tables["P3_agent"]
    ped_hw = [dist.get("pedestrians", 0.0) for key, dist in agent.items() if key[0] == "highway"]
    assert all(p < 1e-6 for p in ped_hw), f"highway 보행자≠0: {ped_hw}"

    # 2·3. 최빈 weather=clear, road_surface=dry
    wm = _marginal(P, 1)
    sm = _marginal(P, 3)
    assert max(wm, key=wm.get) == "clear", f"weather 최빈≠clear: {wm}"
    assert max(sm, key=sm.get) == "dry", f"road_surface 최빈≠dry: {sm}"

    # 4. snow 비중 전국 겨울 소수
    snow = wm.get("snow", 0.0)
    assert 0.002 <= snow <= 0.05, f"snow 비중 이상: {snow:.4f} (기대 0.002~0.05)"

    # 5. 조립 무결
    tot = sum(P.values())
    assert abs(tot - 1) < 1e-6, f"P_ext 합≠1: {tot}"

    print("[OK] validate 앵커 통과:")
    print(f"  weather marginal: {{{', '.join(f'{k}:{v:.3f}' for k, v in sorted(wm.items(), key=lambda x:-x[1]))}}}")
    print(f"  surface marginal: {{{', '.join(f'{k}:{v:.3f}' for k, v in sorted(sm.items(), key=lambda x:-x[1]))}}}")
    print(f"  snow={snow:.4f}, highway 보행자={max(ped_hw) if ped_hw else 0}, 합={tot:.6f}")


if __name__ == "__main__":
    main()
