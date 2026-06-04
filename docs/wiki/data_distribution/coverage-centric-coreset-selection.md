# Coverage-centric Coreset Selection — 기하학적 커버리지 기반 데이터 선택

## 출처
- **저자**: H. Zheng, R. Liu, F. Lai, A. Prakash
- **연도**: 2023
- **학술대회**: ICLR 2023
- **파일**: `literature/papers/R8_CoverageCoreset_ICLR2023.pdf`

---

## 핵심 아이디어

데이터 커버리지를 **기하학적 set cover 문제**로 정의한다. 각 ODD 조합이 "커버해야 할 셀"이고, 보유 클립이 그 셀을 얼마나 채우는지를 정량화한다. **임의 수치 없이 이산 카테고리 조합만으로** 커버리지를 측정한다.

### Set Cover 프레임워크

```
전체 공간 Ω = {모든 가능한 ODD 조합}
보유 데이터 C ⊆ Ω
커버리지 = |{셀 s ∈ Ω : ∃ x ∈ C, x가 셀 s를 커버}| / |Ω|

→ 커버리지 최대화 = 가장 다양한 조합을 포함하는 서브셋 선택
```

### Coreset 선택 알고리즘

1. 전체 데이터 포인트의 커버리지 기여도 계산
2. Greedy set cover로 커버리지 최대화 서브셋 선택
3. 높은 pruning rate(>80%)에서도 커버리지 유지

### 기존 방법 대비 성능 (ImageNet 90% pruning)

| 방법 | Test Accuracy |
|------|---------------|
| Random Pruning | 74.2% |
| Herding | 75.1% |
| Coverage-centric (본 논문) | **77.3%** |

---

## 장단점

**장점**
- 이산 카테고리 조합 빈도가 직접 검증 가능한 수치 → fog=0.12 방식 대비 신뢰성 높음
- 비용 0, 즉시 실행 가능
- 결과가 완전히 해석 가능 ("fog × night × highway = 3개뿐")

**단점**
- 에이전트 행동, 씬 내 인과 관계를 포착하지 못함
- unknown 클립(traffic_density 63%)은 분석에서 제외
- "실제로 희귀 vs 태깅 누락" 구분 어려움

---

## 프로젝트 적용 포인트

### Gap-3 / Gap-4 → EXP-002 Phase A (ODD 커버리지 매트릭스)

```python
from collections import Counter
import json

d = json.load(open('data/tags/odd_tags.json'))

# 4-way 조합 커버리지 매트릭스
counter = Counter(
    (v['weather'], v['time_of_day'], v['road_type'], v['hazard_level'])
    for v in d.values()
    if 'unknown' not in (v['weather'], v['time_of_day'])
)

total_possible = len(set(v['weather'] for v in d.values()) if ...) * ...  # 전체 셀 수
actual_coverage = len(counter) / total_possible

print(f"현재 ODD 커버리지: {actual_coverage:.1%}")
print("=== 희귀 시나리오 조합 (수집 필요) ===")
for combo, cnt in counter.most_common()[:-21:-1]:
    print(f"{cnt:5d}개 | weather={combo[0]}, time={combo[1]}, "
          f"road={combo[2]}, hazard={combo[3]}")
```

이 방법이 EXP-002 Phase A의 **즉시 실행 가능한 첫 번째 분석**이다.

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-3 | 이산 ODD 조합 커버리지 측정 → 희귀 시나리오 식별 |
| Gap-4 | 수집 우선순위: 커버리지 낮은 조합 = 즉시 수집 대상 |

## 관련 실험
- EXP-002: Phase A [AM] — ODD 커버리지 매트릭스 계산 (비용 0, 즉시 실행)
