# μODD 기반 DL 안전 검증 정량화

## 출처
- **저자**: Schleiss, Hagiwara, Kurzidem, Carella (Fraunhofer IKS, Munich)
- **연도**: 2022
- **학술대회**: IEEE ISSREW 2022
- **파일**: `literature/papers/schleiss-2022-towards-quantitative-verification-deep.pdf`

---

## 핵심 아이디어

DL 인식 컴포넌트의 안전을 **ISO 21448 (SOTIF)** 요건에 맞게 정량적으로 검증하는 전략.  
ODD를 **μODD(Micro-ODD)** 로 세분화하여 각각 통계적으로 측정 가능한 단위로 만든다.

### μODD 개념

전체 ODD를 영향 요인별로 분할:
- **Feature-based**: 환경 요인 (날씨, 조도, 도로 표면)
- **DL Specific**: 모델 파라미터, 아키텍처
- **Risk situation**: 위험 상황의 심각도, 발생 확률

```
ODD
├── μODD_1: 맑은 날씨 + 고속도로 + 고조도
├── μODD_2: 비/눈 + 도시 + 저조도
├── μODD_3: 안개 + 야간 + ...
└── ...
```

### 리스크-성능 매핑

- 각 μODD에 리스크 레벨 할당
- 리스크가 높은 μODD일수록 **더 많은 테스트 커버리지** 요구
- SIL(Safety Integrity Level)로 최소 허용 테스트 신뢰도 결정

### 이분산 테스트 (Binomial Test)

```
500 테스트 + 측정 성능 0.75 → 실제 성능 하한 (신뢰도 1-10^{-9}): 0.67
500 테스트 + 측정 성능 0.90 → 실제 성능 하한 (신뢰도 1-10^{-9}): 0.80
```

### 인식 시스템 정보 흐름 (SUDA 모델)

```
Sense → Understand → Decide → Act

각 단계별 불확실성:
- Sense: 센서 물리 노이즈 (aleatoric)
- Understand: DL 분류 오류 (epistemic + aleatoric)
- Decide: 타 교통참여자 행동 예측 불확실성
```

---

## 장단점

**장점**
- ISO 21448 (SOTIF) 요건을 구체적 수치 목표로 변환
- 리스크 기반 테스트 우선순위 → 고위험 μODD에 집중
- 이분산 테스트로 필요 테스트 케이스 수 사전 계산 가능

**단점**
- μODD 분할이 expert knowledge 의존
- 전체 ODD의 100% 커버리지는 불가능 (무한 입력 공간)
- 카메라 기반에 집중 → 멀티 센서 확장 필요

---

## 프로젝트 적용 포인트

### Gap-1 + Gap-3 통합 적용

**μODD 분할 → 평가셋 설계 개선:**
```
현재 평가셋: 20 queries (keyword_relevance 기반)

개선안: μODD 기반 평가셋 재설계
├── μODD_daytime_clear: 5 queries
├── μODD_nighttime: 5 queries
├── μODD_rainy: 5 queries
├── μODD_intersection: 5 queries
└── ...
```

### 실용적 μODD 정의 (현재 ODD 태그 활용)

```python
muodds = {
    "normal_daytime": lambda tags: tags.get("weather") == "clear" and tags.get("time") == "day",
    "adverse_weather": lambda tags: tags.get("weather") in ["rain", "fog", "snow"],
    "low_visibility": lambda tags: tags.get("time") == "night" or tags.get("weather") == "fog",
}

# 각 μODD별 검색 성능 분리 측정
for muodd_name, condition in muodds.items():
    subset = [clip for clip in clips if condition(clip.tags)]
    recall = evaluate_recall_at_k(subset, k=5)
```

### 이분산 테스트 적용
현재 20 queries로 측정한 Recall@5의 실제 하한 계산:
```python
# TP=14, FN=6, W=2, SIL 목표 신뢰도 1-10^{-4}
# 실제 성능 하한 ≈ 0.62 (측정값 0.70보다 낮음)
```

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-1 | μODD 기반 평가셋 재설계로 편향 제거 |
| Gap-3 | μODD 정의가 ODD 커버리지 측정 기준 제공 |

## 관련 실험
- EXP-002 (ODD Tag Filter): μODD별 Recall@5 분리 측정 추가
