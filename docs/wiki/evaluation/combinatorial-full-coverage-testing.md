# Full Coverage Testing for ADS in Logical Scenario Parameter Space (Combinatorial)

## 출처
- **저자**: (ADS 논리 시나리오 파라미터 공간 커버리지 연구진)
- **연도**: 2025
- **학술대회/저널**: Sensors (MDPI), 25(18):5764
- **논문**: doi:10.3390/s25185764
- **링크**: https://pmc.ncbi.nlm.nih.gov/articles/PMC12473291/

---

## 핵심 아이디어

논리 시나리오 파라미터 공간을 **combinatorial(t-wise) testing**으로 커버할 때 얼마나 접히는지 실측하고, heat-guided greedy + 유전 알고리즘(GA)으로 **소수 대표 시나리오만으로 full-coverage**를 달성. 조합 폭발을 실전에서 붕괴시키는 방법의 근거.

### 커버리지 비교 (Cut-in 시나리오, 파라미터 공간 11,776 조합)

| 방법 | 커버리지 | 경계 적합오차(RMSE) |
|------|---------|------|
| Combinatorial t-wise | 86.5% (10,185/11,776) | 0.14 |
| Heat-guided greedy + GA (제안) | 100% | 0.08 |

- **482개 대표 시나리오로 전체 커버 → 96% 비용 절감** (vs 11,776 완전 열거)
- t-wise만으로도 86.5% → 상호작용 차수 제한이 폭발을 붕괴시킴을 실증

### 조합 폭발 대응 원리

```
Full n-way 열거:  모든 파라미터 동시 조합 → 폭발
t-wise:           변수 조합을 체계적으로 선택해 상호작용 포착, 샘플 최소화
                  단, 이산화 스텝에 민감:
                    - 스텝 크면 → 공간 커버 구멍
                    - 스텝 작으면 → 케이스 폭발
제안(heat+GA):    heat-guided greedy로 대표점 선정 + GA 최적화 → full 커버
```

**핵심 시사점**: 이산화 해상도를 균등하게 두지 말고, critical 인자만 조밀하게(위험도 가중) 잡아야 t-wise 구멍과 폭발을 동시에 피한다.

---

## 장단점

**장점**
- t-wise 조합 축소의 실측치 제공 (86.5%, 482개, 96% 절감)
- greedy+GA로 소수 시나리오 full-coverage → 3자 테스트 비용 급감
- 경계 적합오차까지 정량 비교

**단점**
- Cut-in 단일 시나리오 검증 — 다양한 시나리오 타입 일반화는 별도
- 이산화 스텝 의존성 (해상도 설계가 결과 좌우)
- offline 최적화(고정 시나리오 집합) — 동적 상호작용은 미포착

---

## 프로젝트 적용 포인트

### Gap-3: 조합 폭발 축소 (Q1 1단계 근거)

1억+ ODD 조합을 full 열거 대신 t-wise로 접는 것의 실증 근거. coverage-vs-sufficiency 노트 Q1 1단계.

```python
# ODD 조합 축소 전략
# 1. 안전상 상호작용 인자 묶음 식별 (그래프 archetype)
#    → 3-way 승격 (야간 x 우천 x 보행자 등)
# 2. 나머지는 2-way(pairwise) 커버
# 3. critical 인자만 이산화 조밀 (위험도 가중 해상도)
# → 1억 조합 → 수백~수천 셀
```

### EXP-003 Phase 0 연결
- ODD 커버리지 계산 시 full 조합이 아니라 t-wise 타겟 셀 집합으로 정의
- effective_n 낮은 인자(agent_type=1.16 등)는 3-way 승격 후보

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-3 | t-wise로 ODD 조합 폭발 축소 → 수집 대상 셀 집합 정의 |
| Gap-1 | 커버리지 목표를 full 열거 → 차수 제한 커버로 전환 |

## 관련 실험
- EXP-003 Phase 0: ODD 셀 집합을 t-wise로 정의
- EXP-004: 위험도 가중 이산화 해상도 설계

## 관련 문서
- [coverage-vs-sufficiency.md](coverage-vs-sufficiency.md) — Q1 조합 축소 1단계
- [graph-based-coverage-analysis.md](graph-based-coverage-analysis.md) — 상호작용 인자 archetype 식별
- [situation-coverage-grid.md](situation-coverage-grid.md) — 그리드 이산화 + 확률 외삽
