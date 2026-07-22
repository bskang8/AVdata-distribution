# SCOUT: 경량 시나리오 커버리지 평가 프레임워크 (Stanford)

## 출처
- **저자**: Anil Yildiz, Sarah M. Thornton, Carl Hildebrandt, Sreeja Roy-Singh, Mykel J. Kochenderfer (Stanford)
- **연도**: 2025
- **논문**: arXiv:2510.24949, Oct 2025
- **파일**: `literature/papers/scout-scenario-coverage-2025.pdf`

---

## 핵심 아이디어

LVLM(Large Vision-Language Model)을 매번 추론하지 않고, LVLM distillation으로 학습된 경량 surrogate 모델로 대규모 자율주행 데이터셋의 시나리오 커버리지 레이블을 저비용으로 예측.

### SCOUT 시스템 구조

| 단계 | 방법 | 비용 |
|------|------|------|
| 오프라인 LVLM 라벨링 | 소규모 대표 샘플에만 LVLM 적용 | 일회성 고비용 |
| Surrogate 학습 | LVLM 레이블로 경량 분류기 distillation | 낮음 |
| 온라인 추론 | 사전 계산 perception feature + surrogate | 매우 낮음 |
| 커버리지 집계 | 예측 레이블 → 커버리지 메트릭 계산 | O(N) |

### 핵심 설계 원칙

```
기존 방법: LVLM → 모든 클립에 매번 추론 → 비용 O(N × LVLM 비용)
SCOUT:    LVLM → 소규모 대표 샘플 → Surrogate 학습 → 사전 피처로 전체 추론
                                                      비용 O(N × surrogate 비용)
```

- **사전 계산 perception feature 활용**: 이미 계산된 탐지/분류 피처 재활용 → 중복 계산 제거
- **지속적 LVLM 추론 불필요**: 초기 distillation 이후 LVLM 비용 발생 안 함
- **높은 정확도 유지**: 대규모 실제 자율주행 데이터셋에서 LVLM 대비 정확도 거의 동일

### 성능 특성

| 지표 | LVLM 직접 | SCOUT |
|------|-----------|-------|
| 추론 비용 | O(N) × 고비용 | O(N) × 저비용 |
| 커버리지 정확도 | 기준 | ≈ 동일 |
| 확장성 | 제한적 | 대규모 적용 가능 |

---

## 장단점

**장점**
- LVLM 없이 실시간 수준의 커버리지 레이블 예측 → 대규모 데이터셋 적용 가능
- 사전 계산 피처 재활용으로 중복 계산 제거 (파이프라인 효율화)
- distillation 기반이라 도메인별 커스터마이징 가능

**단점**
- distillation 품질이 초기 LVLM 레이블 품질에 의존
- 커버리지 레이블 정의가 LVLM의 주관적 판단에 기반
- surrogate 모델 재학습 주기 관리 필요 (데이터 분포 변화 시)

---

## 프로젝트 적용 포인트

### Gap-1: 커버리지 레이블 자동화

현재 83k 클립에 수동/규칙 기반 태깅을 SCOUT 방식으로 대체:

```python
# 현재: regex 패턴 기반 ODD 태깅 → 커버리지 추정
# SCOUT 방식:
# 1. 83k 중 대표 샘플 ~1k에 LVLM(GPT-4V) 커버리지 레이블
# 2. 기존 caption embedding(bge-m3)을 perception feature로 활용
# 3. 경량 classifier(SVM 또는 MLP) distillation 학습
# 4. 전체 83k 커버리지 레이블 예측 → ODD Coverage 계산

# 현재 캡션 임베딩이 이미 계산되어 있으므로 추가 비용 최소
```

### Gap-3: 시나리오 커버리지 갭 대규모 측정

COLLECT_HIGH_PRIORITY 시나리오 커버리지 비율을 저비용으로 지속 모니터링:
- S4(회전/교차로), S1(보행자), S8(버스/트럭) 비율 추적
- 신규 클립 수집 후 커버리지 변화 자동 감지

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-1 | LVLM distillation surrogate로 평가셋 커버리지 레이블 자동화 |
| Gap-3 | 경량 모델로 대규모 ODD 커버리지 지속 모니터링 가능 |

## 관련 실험
- EXP-003 (Phase 0): 커버리지 레이블 예측에 surrogate 방식 도입 검토
- EXP-005: CatPipe + SCOUT 결합 — LVLM 태깅 비용 절감
