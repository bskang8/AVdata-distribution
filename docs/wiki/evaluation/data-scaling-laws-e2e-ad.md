# Data Scaling Laws for End-to-End Autonomous Driving (Naumann et al., NVIDIA)

## 출처
- **저자**: Alexander Naumann, Xunjiang Gu 외 (NVIDIA Autonomous Vehicle Research Group)
- **연도**: 2025
- **학술대회/저널**: CVPR 2025 Workshop on Autonomous Driving (WAD)
- **논문**: arXiv:2504.04338
- **링크**: https://arxiv.org/html/2504.04338v1 · [CVPR PDF](https://openaccess.thecvf.com/content/CVPR2025W/WAD/papers/Naumann_Data_Scaling_Laws_for_End-to-End_Autonomous_Driving_CVPRW_2025_paper.pdf)

---

## 핵심 아이디어

E2E 자율주행 모델의 성능이 학습 데이터 양에 따라 **파워법칙(power law)**으로 개선되며, 결정적으로 **시나리오 타입마다 스케일링 지수가 다르다**는 것을 16~8192시간 데이터로 실증. "타겟 성능 향상에 얼마나 더 데이터가 필요한가"를 외삽으로 답한다.

### 스케일링 관계식

```
L_val − ε∞ = β · x^c      (M2 estimator, 일반 케이스에 가장 적합)

x   = 학습 데이터 크기(시간)
c   ≈ −0.4 (FDE/ADE/MR 전반)
ε∞  = 점근 최소 달성 손실
```

표준 딥러닝 스케일링(`L_val ∝ β x^c`) 프레임을 E2E 주행에 적용. 초기 6개 데이터점(16~512h)으로 estimator를 적합하고 1024~2048h에서 검증한 뒤 관측 범위 밖으로 외삽.

### 시나리오별 스케일링 (핵심 발견)

| 시나리오 | 지수 c | 특성 |
|---------|--------|------|
| Lane keeping | −0.413 | 가장 빨리 개선 → 곧 포화, 추가 데이터 무의미 |
| Turning | — | 8192h까지 개선 후 plateau |
| Lane changing | −0.348 | 가장 느림, 수확체감 (ResNet-50이면 ~78% 적은 데이터로 동등) |

- 액션 분포: **91.8% 직진 / 5.2% 회전 / 3% 차선변경** (전형적 롱테일)
- 모델 용량 효과: ResNet-50이 ResNet-18 대비 ~3,000h(63% 절감)로 동등 성능 → 큰 모델이 대용량 구간에서 전 시나리오 더 빠르게 개선

### 타겟 개선당 필요 데이터 (지수적 폭증)

| 목표 FDE 개선 | 추가 필요 데이터 |
|------|------|
| 1% | +4,000 시간 |
| 3% | +29,000 시간 |
| 5% | +273,000 시간 |

→ 꼬리 성능을 짜낼수록 비용이 지수적으로 폭발. "균등하게 더 수집"이 파산인 정량적 증거.

---

## 장단점

**장점**
- 시나리오별 스케일링 곡선을 실측 → "얼마면 충분한가"의 원리적 정지 기준 제공
- 타겟 성능당 필요 데이터를 외삽으로 정량화 → 데이터 수집 ROI 계산 가능
- open-loop(16~8192h) + closed-loop(DRIVE Sim, ~256h plateau) 이중 검증

**단점**
- 내부 대규모 데이터셋(8,192h) 기반 → 재현에 데이터 접근성 제약
- 파워법칙 외삽이 관측 범위를 크게 벗어나면 신뢰구간 확대
- 시나리오 분류(lane keeping/turning/lane change)가 거친 편 — 세밀한 ODD 셀 단위는 별도 필요

---

## 프로젝트 적용 포인트

### Gap-4: 셀별 포화 곡선으로 충분성 판정

D_train의 71% 직진 편향 = 이 논문의 lane keeping(91.8%, 가장 빨리 포화)과 동형. 이미 포화된 셀은 끊고 가파른 셀에만 예산 투입.

```python
# 셀별 스케일링 적합 → 정지 판정
# 1. 각 ODD 셀에서 데이터 양별 Recall@5 (또는 FDE) 측정
# 2. L - eps = beta * n^c 적합
# 3. |dL/dn| < threshold → 포화 (수집 중단)
#    아직 가파름 → 수집 타겟 등록
# 4. 타겟 개선(예: +3%)에 필요한 n을 외삽 → 수집 예산 산정
```

### EXP-003 Phase C / Phase B 연결
- Phase B 스케일링 파일럿의 이론적 근거 — 시나리오별 지수 상이를 전제로 클러스터별 예산 배분
- MOSAIC의 클러스터별 포화 모델 `Δ̂U=a(1−e^{−n/τ})`과 상보: Naumann=곡선 실증, MOSAIC=곡선 기반 선택 알고리즘

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-4 | 시나리오별 스케일링 지수로 포화 셀 식별 + 수집 예산 산정 |
| Gap-3 | 타겟 개선당 데이터 외삽으로 커버리지 갭의 비용 정량화 |

## 관련 실험
- EXP-003 Phase B/C: 클러스터별 스케일링 파일럿의 이론 근거
- EXP-004: 셀별 포화 곡선 기반 D_train 구성 최적화

## 관련 문서
- [coverage-vs-sufficiency.md](coverage-vs-sufficiency.md) — Q2 충분성 판정의 핵심 근거
- [beyond-neural-scaling-laws.md](../data_distribution/beyond-neural-scaling-laws.md) — 프루닝 관점 스케일링
- [less-influential-data-selection.md](../data_distribution/less-influential-data-selection.md) — 재학습 없는 한계효용 근사
