# ODD 기반 시나리오 커버리지 평가 프레임워크 (4-Type)

## 출처
- **저자**: Chodowiec, Irvine, Tiele, Takenaka, Zhang, Khastgir, Jennings (Univ. of Warwick / DENSO)
- **연도**: 2026 (accepted IEEE Access)
- **파일**: `literature/papers/chodowiec-2026-odd-behaviour-scenario-coverage.pdf`

---

## 핵심 아이디어

ADS 테스트에서 시나리오 세트의 **완전성(completeness)**을 4가지 차원으로 정량 평가하는 프레임워크.  
기존 연구가 "시나리오 생성"에 집중했다면, 이 논문은 "생성된 시나리오가 충분한가?"를 측정한다.

### 4가지 커버리지 메트릭

| Type | 이름 | 측정 대상 |
|------|------|-----------|
| Type 1 | Attribute Range | 개별 파라미터 값 범위가 충분히 탐색되었는가 |
| Type 2 | ODD & Behaviour | 시나리오 세트가 ODD와 행동 역량을 충분히 커버하는가 |
| Type 3 | Out-of-ODD | 시스템이 ODD 이탈 시 MRM을 올바르게 수행하는가 |
| Type 4 | Rules of Road | 교통법규 준수 여부 |

### Type 1 (Attribute Range) 핵심
- Bayesian Optimization으로 파라미터 공간 탐색
- Gaussian Process 모델로 failure likelihood 추정
- 단일 최댓값(global max)뿐 아닌 **local minima(숨겨진 위험)**도 식별

### Type 2 (ODD & Behaviour) 핵심
- ISO34503 기반 ODD taxonomy 사용
- OpenLABEL 태그로 시나리오에 ODD 속성 부여
- **태그 비교(tag comparison)**로 커버리지 = 커버된 ODD 태그 / 전체 태그

### Type 3 (Out-of-ODD) 핵심
- Type 3A: 처음부터 ODD 밖에서 시작하는 시나리오
- Type 3B: 운행 중 ODD 이탈 시나리오 (MRM 실행 검증)
- MRM(Minimum Risk Maneuver): 안전 정지, 갓길 정차 등

### ODD 분류 체계 (ISO34503 기반)
```
ODD
├── Scenery elements (Zone, Junctions, Road structures...)
├── Environmental conditions (Weather, Illumination, Particulates...)
└── Dynamic elements (Traffic agents, Subject vehicle...)
```

---

## 장단점

**장점**
- 4가지 독립적 커버리지 지표로 다차원 안전 보증 가능
- ISO 표준(ISO34503, BSI Flex1891) 준수 → 규제 대응 가능
- Bayesian Optimization으로 파라미터 공간 효율적 탐색

**단점**
- Type 2 커버리지는 정확한 ODD 정의가 선행 필요
- 태그 기반 방식이므로 태그 누락 시 커버리지 과대 추정 위험
- 전체 프레임워크 구현 비용이 높음

---

## 프로젝트 적용 포인트

### Gap-3 (ODD 커버리지 36~62%) 직결
현재 프로젝트의 odd_coverage.json이 36~62%인 문제를 이 프레임워크로 진단 가능.

**Type 2 커버리지 적용 방법:**
```python
# 현재 odd_tags.json의 태그 집합 vs ISO34503 전체 태그
covered_tags = set(odd_tags.keys())
total_iso_tags = load_iso34503_taxonomy()
coverage = len(covered_tags & total_iso_tags) / len(total_iso_tags)
```

### Gap-1 (평가셋 편향) 보완
Type 2의 **ODD 태그 밀도 분석**으로 평가셋이 어떤 ODD를 과도하게 커버하는지 시각화 가능.

### 아이디어: Bayesian Optimization으로 희귀 시나리오 탐색
현재 BM25 + Embedding 검색에서 Type 1 커버리지 개념 도입:
- 희귀 ODD 조합(예: 야간+안개+보행자) 파라미터를 BO로 최적 탐색
- 탐색 결과를 longtail_clips.json과 연계

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-1 | Type 2 커버리지 분석으로 평가셋 편향 정량화 |
| Gap-3 | ODD 커버리지 36~62% → Type 2/3 메트릭으로 정확한 측정 |

## 관련 실험
- EXP-002 (ODD Tag Filter Ablation): Type 2 커버리지 보고 지표 추가 검토
