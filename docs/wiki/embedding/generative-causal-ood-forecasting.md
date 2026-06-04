# Generative Causal Representation Learning — OOD 모션 예측

## 출처
- **저자**: S. Shirahmad Gale Bagi, Z. Gharaee, O. Schulte, M. Crowley
- **연도**: 2023
- **학술대회**: ICML 2023
- **파일**: `literature/papers/R17_GenerativeCausal_ICML2023.pdf`

---

## 핵심 아이디어

**생성적 인과 표현 학습(Generative Causal Representation Learning)**으로 Out-of-Distribution(OOD) 모션 예측 성능을 향상시킨다. 인과 구조를 명시적으로 모델링하여 훈련 분포와 다른 시나리오에서도 일반화 가능한 표현을 학습한다.

### 핵심 메커니즘

```
기존 방식 (Spurious correlation 문제):
  훈련: "비 오는 날 차량 감속" → 상관관계 학습
  테스트: "새로운 도시 구조 + 비" → 분포 이동으로 실패

인과 표현 방식:
  훈련: 개입(Intervention)으로 원인-결과 관계 학습
    "비 → 감속" vs "새 도시 구조 → 감속"
  테스트: 인과 경로 기반 예측 → OOD에서도 안정적
```

### 생성적 프레임워크

1. **인과 변수 분리**: 씬의 causal factors vs non-causal (spurious) factors 분리
2. **생성 모델**: VAE 기반으로 인과 잠재 변수 생성
3. **개입 시뮬레이션**: 특정 변수 개입 시 결과 예측

### 성능 (nuScenes OOD 테스트)

| 방법 | ADE (In-Dist) | ADE (OOD) |
|------|---------------|-----------|
| Social GAN | 0.87 | 1.94 |
| AgentFormer | 0.89 | 1.87 |
| 본 논문 | **0.91** | **1.42** |

OOD 성능에서 27% 향상.

---

## 장단점

**장점**
- OOD 시나리오에서의 일반화 성능이 명확히 향상됨
- 인과 구조 학습으로 spurious correlation 제거
- 개입 가능성 → "만약 날씨가 안개였다면?" 반사실 예측 가능

**단점**
- 인과 그래프 구조를 일부 사전 지식으로 정의해야 함
- 생성 모델 학습 비용이 높음
- 캡션 텍스트보다 궤적 데이터에 최적화

---

## 프로젝트 적용 포인트

### Gap-1 / Gap-3 → EXP-005 (미래 실험)

bge-m3 임베딩에 인과 표현 학습 적용:

```python
# 개입 기반 임베딩 분리
# causal_factors: 씬의 결과(위험도)에 직접 영향을 주는 요소
#   → fog, night, high_density (도메인 불변)
# non_causal: spurious 요소
#   → 카메라 각도, 날씨 배경 텍스처 등

encoder = CausalEncoder(
    causal_dim=64,      # 인과 잠재 변수
    spurious_dim=960,   # 비인과 잠재 변수
    total_dim=1024      # bge-m3 출력 차원
)
```

희귀 시나리오의 **인과 요인**만 추출하면 OOD 데이터에서도 유사한 위험 시나리오를 정확히 검색 가능.

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-1 | 인과 표현 학습으로 평가셋 레이블 편향 감소 |
| Gap-3 | OOD 일반화 → 희귀 시나리오의 인과적 특성 추출 |

## 관련 실험
- EXP-005 (후보): bge-m3에 인과 표현 fine-tuning 적용
