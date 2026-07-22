# RoCA: GP 기반 Cross-Domain E2E 자율주행

## 출처
- **저자**: Rajeev Yasarla, Shizhong Han, Hsin-Pai Cheng, Apratim Bhattacharyya, Shweta Mahajan, Litian Liu, Yunxiao Shi, Risheek Garrepalli, Hong Cai, Fatih Porikli (Qualcomm AI Research)
- **연도**: 2025 (arXiv v1); ICML 2026 채택
- **학술대회/저널**: ICML 2026
- **논문**: arXiv:2506.10145
- **파일**: `literature/papers/yasarla-2025-robust-cross-domain-e2e.pdf`

---

## 핵심 아이디어

E2E 자율주행 모델은 도시·조명·카메라·날씨 등 **도메인이 바뀌면 성능이 급락**한다. 근본 원인은 학습 데이터의 다양성 부족(정상 이벤트 과다, 롱테일 과소)이다. RoCA는 LLM에 의존하지 않고, ego·agent 토큰의 **결합 확률분포를 Gaussian Process(GP)로 모델링**하여 다양한 주행 시나리오를 span하는 basis token codebook을 학습한다. 새로운 씬에 대해 basis와의 유사도로 미래 궤적을 확률적으로 추론하고, GP variance(불확실성)를 이용해 학습 손실 가중과 타겟 도메인 데이터 선택을 수행한다.

### GP 기반 basis token codebook

- Base E2E planner(예: VAD, SparseDrive, SSR, ORION)가 multi-view 이미지에서 ego token `e`, agent token `a`를 추출.
- RoCA 모듈은 소스 도메인에서 **basis token 집합 `b`** 와 각 basis에 1:1 대응하는 **대표 궤적 `w = g(b)`** 를 학습 (ego/agent 토큰 재구성으로 supervise).
- 추론 시: 커널 `κ(e, b)`로 현재 토큰과 basis 간 상관을 계산 → GP posterior로 미래 궤적 `p_w, c_w` 를 확률적으로 예측. 새 씬은 codebook 내 유사 basis로 informed 되므로 일반화가 내재됨.
- Anchor-based 예측: N_ego / N_agent 그룹으로 궤적 분류 후 residual 예측 (SparseDrive 방식 차용).

### 불확실성 활용 — 3가지 적응 모드

GP가 산출하는 **예측 variance = 불확실성**을 세 방향으로 활용:
1. **소스 학습 정규화**: variance로 손실을 동적 가중 → 어렵거나 불확실한(롱테일) 샘플에 더 큰 가중, 학습 불균형 완화. 추론 비용 추가 없음.
2. **Uncertainty-guided active learning**: 타겟 도메인에서 불확실성 높은 샘플 우선 선택 → 적은 라벨로 효율적 적응.
3. **Online / unsupervised adaptation**: pseudo GT를 생성해 base model을 타겟 도메인에 fine-tune (direct finetuning 대비 우수).

---

## 주요 실험 결과

| 실험 | 결과 |
|------|------|
| Bench2Drive closed-loop (220 routes) | RoCA(ORION) mean ability **+11.7%** (54.72→61.11); RoCA(SSR) **+27.8%** (35.38→48.98) |
| Cross-city (Boston→Singapore, zero-shot) | 충돌률이 VAD-Tiny의 **절반 이하** (0.211% vs 0.430%) |
| NAVSIM v1 cross-domain closed-loop | RoCA-SparseDrive L2 0.55→**0.49m**, 충돌률 0.12%→**0.09%** |
| Active learning (5/10/15% 타겟 샘플) | 랜덤 대비 predictive-uncertainty 선택이 우수 |
| 이미지 열화 (저조도/모션블러/악천후) | 열화 조건에서도 planning 성능 견고 |

- 평가: open-loop(L2, collision rate) + closed-loop(Bench2Drive, NAVSIM). Sim→real(Bench2Drive→nuScenes) 포함.

---

## 장단점

**장점**
- LLM 불필요 → 도메인 적응 재학습 비용 회피, 추론 시 추가 연산 없음.
- GP variance가 **원리적 불확실성 측정치**를 제공 → 손실 가중·데이터 선택·online 적응에 재사용.
- Base 모델에 plug-in (VAD/SparseDrive/SSR/ORION 등)으로 붙는 모듈 구조.

**단점**
- GP codebook(basis token) 구축 단계가 별도로 필요 — 소스 도메인 학습 파이프라인에 추가 stage.
- basis 개수·커널 선택 등 하이퍼파라미터 튜닝 의존.
- 궤적/플래닝 태스크에 특화 — 순수 검색·태깅 태스크에 직접 이식은 재해석 필요.

---

## 프로젝트 적용 포인트

### Gap-4 (분포 편향 — 롱테일 과소) 연결

RoCA의 핵심 통찰은 **"불확실성(GP variance)이 롱테일/도메인 갭을 가리키는 신호"** 라는 것이다. 우리 83k 클립 큐레이션에서, 학습된 모델의 예측 불확실성을 데이터 선택 우선순위로 쓰는 active-learning 관점을 차용할 수 있다 — LESS([[less-influential-data-selection]])의 영향력 기반 선택, MOSAIC([[mosaic-data-selection]])의 스케일링 인식 선택과 대비되는 **불확실성 기반 선택** 축.

```python
# GP/앙상블 variance를 클립 선택 점수로 (개념 예시)
# ponytail: 실제 GP 대신 기존 임베딩 앙상블 분산으로 근사 가능
scores = predictive_variance(clip_embeddings)      # 높을수록 불확실 = 롱테일 후보
select = clips[scores.argsort()[::-1][:budget]]    # 예산 내 불확실 클립 우선
```

### Gap-1 (평가셋 불확실성) 연결

GP posterior variance는 Herd & Burton의 Subjective Logic 불확실성과 같은 계열의 "예측 신뢰도" 측정 — 평가셋 relevance 라벨의 불확실성 정량화에 참조 가능.

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-4 | 불확실성(GP variance) 기반 롱테일·도메인 갭 샘플 선택; 분포 불균형을 손실 가중으로 보정 |
| Gap-1 | GP posterior variance = 원리적 예측 불확실성 측정치 |

## 관련 실험
- EXP-003 (분포 진단 기반 데이터 큐레이션 — 불확실성 기반 선택 축 검토)
