# Situation Coverage Grid — 확률적 안전 검증 (Probabilistic Safety Verification)

## 출처
- **저자**: (autonomous ground vehicle safety verification 연구진)
- **연도**: 2025
- **논문**: arXiv:2507.12158, Jul 2025
- **링크**: https://arxiv.org/pdf/2507.12158

---

## 핵심 아이디어

**"coverage alone is insufficient."** 운영 도메인을 이산 "상황(situation)" 그리드로 나누고, 각 셀에서 관측된 실패율로 **미관측(untested) 셀의 실패율을 확률적으로 상한(bound)** 한다. 커버리지를 단순 카운트가 아니라 정량적 안전 보증의 토대로 전환한다.

### 방법론 3단계

```
① 체계적 열거 (Systematic Enumeration)
   상황 파라미터(날씨·교통밀도·도로기하·센서조건 등) 다차원 그리드 생성
        ↓
② 확률적 외삽 (Probabilistic Extrapolation)
   커버된 셀의 관측 실패율 → 미관측 셀 실패율을 확률적으로 상한
   (미관측 = "실패 0" 가정 금지)
        ↓
③ 통계적 충분성 논증 (Statistical Sufficiency)
   그리드 전체 테스트 결과 분포 → 미관측 영역 안전에 대한 신뢰 정식화
```

### 핵심 차별점

| 기존 커버리지 메트릭 | Situation Coverage Grid |
|---------------------|-------------------------|
| line/branch/시나리오 카운트 | 상황 그리드 + 실패율 |
| 테스트된 것만 서술 | 미관측 영역까지 확률적 논증 |
| "왜 테스트된 게 미관측을 정당화하나" 답 없음 | 실패율 외삽으로 정식 논증 |

미관측 셀을 "실패 0"으로 낙관하지 않고, 이웃 셀 실패율로 상한을 잡는 것이 안전 논증의 핵심.

---

## 장단점

**장점**
- 커버리지를 서술 지표 → 정량적 안전 보증(safety assurance)으로 승격
- 미관측 영역에 대한 형식적 확률 논증 제공 (인증 프로세스 정합)
- 어느 미관측 조합이 통계적으로 위험한지 랭킹 가능

**단점**
- 실패율 외삽이 셀 간 유사성 가정에 의존 (이웃이 실제로 유사해야 유효)
- 그리드 이산화 해상도에 민감 (coverage-vs-sufficiency의 t-wise 이산화 문제와 동일)
- 관측 실패 샘플이 희소하면 상한이 느슨해짐

---

## 프로젝트 적용 포인트

### Gap-3: 미관측 ODD 조합의 위험 랭킹

t-wise로 축소한 셀 랭킹에서, 아직 데이터가 없는 조합을 "0 위험"으로 두지 않고 이웃 셀 성능으로 확률 외삽 → criticality × exposure 축을 안전 논증 수준으로 정식화.

```python
# 미관측 셀 위험 상한
# 1. 커버된 셀별 실패율(1 - Recall@5) 측정
# 2. 임베딩/파라미터 공간에서 미관측 셀의 이웃 식별
# 3. 이웃 실패율 → 미관측 셀 실패율 상한 추정
# 4. 상한 높은 미관측 셀 = 우선 수집 (Q1 랭킹에 반영)
```

### Q1↔Q2 연결
- coverage-vs-sufficiency 노트에서 Q1(중요 조합 선별)과 Q2(충분성)를 잇는 다리 역할
- de Gelder의 Criticality Coverage를 확률적 외삽으로 보강

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-3 | 미관측 ODD 조합 위험 확률 외삽 → 수집 우선순위 정당화 |
| Gap-1 | 커버리지 표를 안전 논증으로 승격 (단순 카운트 탈피) |

## 관련 실험
- EXP-003 Phase 0: ODD 셀 위험 외삽으로 수집 타겟 랭킹
- EXP-004: 미관측 영역 안전 논증으로 D_train 구성 정당화

## 관련 문서
- [coverage-vs-sufficiency.md](coverage-vs-sufficiency.md) — Q1↔Q2 연결 다리
- [coverage-metrics-scenario-database.md](coverage-metrics-scenario-database.md) — de Gelder Criticality Coverage
- [combinatorial-full-coverage-testing.md](combinatorial-full-coverage-testing.md) — 그리드 이산화 조합 축소
