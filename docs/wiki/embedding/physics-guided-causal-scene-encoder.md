# Physics-guided Causal Model (PCM) — 인과 장면 인코더

## 출처
- **저자**: Li et al.
- **연도**: 2026
- **학술대회/저널**: arXiv preprint (cs.AI)
- **논문**: arXiv:2602.13936
- **파일**: `literature/papers/li-2026-physics-guided-causal-trajectory.pdf`

---

## 핵심 아이디어

자율주행 궤적 예측에서 도메인 간 zero-shot 일반화를 위해 **Disentangled Scene Encoder** + **CausalODE Decoder** 구조를 제안한다. 핵심은 intervention-based disentanglement로 장면에서 도메인 불변 인과 피처를 분리 추출하는 것이다.

### 두 핵심 구성 요소

#### 1. Disentangled Scene Encoder

Intervention-based disentanglement로 장면 표현을 두 부분으로 분리:

```
Scene → Encoder → [causal_features | spurious_features]
                        ↓                    ↓
              도메인 불변 (인과)      도메인 의존 (상관)
              이 부분만 디코더로 전달
```

- **Intervention**: 장면의 도메인 특성(날씨, 조명 등)을 인위적으로 변경해도 유지되는 피처 = 인과 피처
- **Contrastive learning**: 동일 물리 상황 다른 도메인 쌍으로 학습

#### 2. CausalODE Decoder

두 바퀴 운동학 모델(two-wheel kinematic model)을 Neural ODE에 통합:

```
causal_features + trajectory_query → CausalODE → predicted_trajectory
                                         ↑
                              물리 법칙(가속도, 조향각)을 prior로 내장
```

Causal attention mechanism으로 문맥 정보와 물리 제약 통합.

### 학습 신호

- 궤적 예측 손실 (L2 regression)
- Intervention 일관성 손실 (도메인 변경 후 인과 피처 불변 강제)
- Contrastive 손실 (같은 물리 상황 → 같은 인과 피처 임베딩)

---

## 장단점

**장점**
- Zero-shot 일반화: 새로운 도메인(날씨, 지역 등)에 fine-tuning 없이 적용
- 인과 피처와 상관 피처 명시적 분리 → 해석 가능성 향상
- 물리 법칙 내장으로 물리적으로 타당한 궤적 예측

**단점**
- Intervention 설계가 수동 정의 필요 (어떤 변수를 개입할지)
- 학습 데이터에 도메인 다양성이 충분해야 disentanglement 효과적
- 현재 bge-m3 텍스트 임베딩과 직접 결합 어려움 (멀티모달 확장 필요)

---

## 프로젝트 적용 포인트

### Gap-1 (평가셋 편향) + Gap-3 (ODD 커버리지) → EXP-002 Axis A / EXP-005

**단기 적용 (EXP-002)**: 인과 체인 쿼리 설계 원칙으로 활용

PCM의 인과 피처 분리 개념 → L2 인과 체인 쿼리의 3단계 구조:
```
원인 (환경 조건) → 매개 (ego 반응) → 결과 (위험 상황)
"wet road"      → "sudden braking" → "near-collision"
```

**장기 적용 (EXP-005)**: bge-m3 fine-tuning 설계 참조

```python
# EXP-005 설계안 (intervention-based contrastive fine-tuning)
# 인과 쌍: (원인 캡션, 결과 캡션) → 가까운 임베딩 거리 강제
# 비인과 쌍: (무관 캡션, 결과 캡션) → 먼 임베딩 거리 강제

loss = contrastive_loss(
    anchor=embed("wet road emergency braking"),
    positive=embed("slippery surface sudden stop near pedestrian"),
    negative=embed("clear highway cruise control")
)
```

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-1 | 인과 피처 기반 임베딩으로 키워드 의존성 탈피 |
| Gap-3 | 도메인 불변 인코더로 새로운 ODD 조건 일반화 |

## 관련 실험
- EXP-002: Axis A — 인과 체인 쿼리 설계 원칙 참조
- EXP-005: 인과 인코더 fine-tuning (백로그)
