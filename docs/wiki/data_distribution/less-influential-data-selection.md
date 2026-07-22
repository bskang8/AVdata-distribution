# LESS: LoRA Gradient Similarity 기반 타겟 지향 데이터 선택

## 출처
- **저자**: Mengzhou Xia, Sadhika Malladi, Suchin Gururangan, Sanjeev Arora, Danqi Chen (Princeton University / AI2)
- **연도**: 2024
- **학술대회/저널**: ICML 2024
- **논문**: arXiv:2402.04333
- **파일**: `literature/papers/xia-2024-less-influential-data-selection.pdf`

---

## 핵심 아이디어

훈련 데이터 각각이 특정 평가 목표(eval set)의 성능에 얼마나 기여하는지를 **LoRA gradient similarity로 효율적으로 추정**하는 방법.  
전통적인 influence function은 계산 비용이 금지적(Hessian 역행렬 필요)이었지만, LESS는 LoRA를 활용한 gradient 압축으로 대규모 데이터셋에서도 실용적 계산이 가능하다.  
전체 데이터의 단 5%만 선택해도 동일하거나 더 좋은 성능을 달성하며, 타겟이 달라지면 최적 선택 데이터도 달라지는 **target-specific selection**이 핵심 강점.

### 핵심 수식: Gradient Influence

```
influence(z_i, z_eval) ≈ ∇_θ L(z_eval)^T · ∇_θ L(z_i)
```

- `∇_θ L(z_eval)`: 목표 eval 샘플에 대한 gradient (방향)
- `∇_θ L(z_i)`: 훈련 샘플 z_i에 대한 gradient (방향)
- **내적이 크다** = z_i를 학습하면 eval 목표 성능이 올라감
- **내적이 작거나 음수** = z_i는 해당 타겟에 영향력 낮음 (제거 후보)

### LoRA 기반 Gradient 압축

전체 파라미터 gradient (수십억 차원) → LoRA 공간으로 투영:

```
∇_θ L → ∇_r L   (r << d, 예: r=16)

계산 비용: O(N × d²) → O(N × r × d)   (약 100~1000배 절감)
```

### 성능 비교

| 방법 | 선택 데이터 비율 | 성능 (eval 기준) |
|------|----------------|-----------------|
| 무작위 선택 | 100% | 기준 |
| BM25 기반 선택 | 5% | 기준 -3% |
| **LESS** | **5%** | **기준 동등 또는 +2%** |
| 전체 데이터 파인튜닝 | 100% | 기준 |

### MOSAIC과의 차이점

| 항목 | MOSAIC | LESS |
|------|--------|------|
| 방법 | 파일럿 재학습 (M회 반복) | Gradient 1회 계산 |
| 비용 | 높음 (파일럿 실험 필요) | 낮음 (추론 1패스) |
| 전제 | 스케일링 법칙 추정 필요 | 재학습 불필요 |
| 타겟 적응 | 클러스터 단위 | 샘플 단위 |

---

## 장단점

**장점**
- 재학습(파일럿 실험) 없이 gradient 계산 1회로 데이터 가치 추정
- 타겟별 최적 데이터가 자동으로 달라짐 → 도메인별 맞춤 선택 가능
- 이론적으로 검증된 influence function의 실용적 근사
- LLM 파인튜닝뿐 아니라 임베딩 모델 학습에도 원리 적용 가능

**단점**
- LoRA 학습이 1회 선행 필요 (모델 초기화 단계)
- Gradient 유사도가 실제 학습 기여도를 완전히 반영하지 못할 수 있음 (비선형성 무시)
- 타겟 eval set 품질에 민감: 잘못된 타겟이면 잘못된 데이터를 선택
- 대규모 풀(수백만 클립)에서는 gradient 저장 메모리 비용 발생

---

## 프로젝트 적용 포인트

### Gap-4 연결

도메인별 쿼리셋(야간/우천/교차로 Recall@5)을 **target eval set**으로 설정하면, 각 훈련 클립이 해당 도메인 성능 향상에 기여하는 정도를 gradient influence로 추정할 수 있다.

**도메인별 타겟 예시:**
```python
target_night   = {야간 쿼리 Recall@5 집합}
target_rain    = {우천 쿼리 Recall@5 집합}
target_intersection = {교차로 쿼리 Recall@5 집합}

# 각 클립 z_i의 도메인별 영향력 추정
influence_night_i   = grad(target_night)^T · grad(z_i)
influence_rain_i    = grad(target_rain)^T  · grad(z_i)
influence_inter_i   = grad(target_inter)^T · grad(z_i)
```

**활용**: influence 하위 클립 = 학습에서 제거 → 상위 클립 유지 + 갭 시나리오 보충

### EXP-003 Phase B 대안

현재 EXP-003 Phase B는 스케일링 법칙 파일럿 실험(M×4번 재학습)으로 ROI를 추정.  
LESS 방식은 gradient similarity로 재학습 없이 ROI를 추정 가능 → **파일럿 비용 절감 대안**.

| 비교 항목 | Phase B (MOSAIC 방식) | LESS 방식 |
|---------|----------------------|-----------|
| 재학습 횟수 | M × 4회 | 0회 (gradient만) |
| 정확도 | 높음 | 중간 (근사) |
| 소요 시간 | 수일 | 수시간 |
| 권장 사용 | 최종 의사결정 | 빠른 사전 스크리닝 |

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-4 | 각 클립의 도메인별 gradient influence → 가치 낮은 클립 제거 + 갭 시나리오 우선 확보 |

## 관련 실험
- EXP-003 Phase B: MOSAIC 파일럿 대신 LESS gradient similarity로 클러스터별 ROI 사전 추정
- EXP-004: 데이터 가치 평가 방법으로 gradient influence 지표 도입, MOSAIC 스케일링 추정과 비교
