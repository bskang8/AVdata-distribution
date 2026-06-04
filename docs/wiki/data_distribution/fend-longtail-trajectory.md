# FEND — 롱테일 궤적 예측을 위한 분포 인식 대조 학습

## 출처
- **저자**: Y. Wang, P. Zhang, L. Bai, J. Xue
- **연도**: 2023
- **학술대회**: CVPR 2023
- **파일**: `literature/papers/R16_FEND_CVPR2023.pdf`

---

## 핵심 아이디어

**Future Enhanced Distribution-Aware Contrastive Learning Framework**. 롱테일 분포를 가진 궤적 예측 데이터에서 희귀 시나리오(long-tail)의 예측 성능을 향상시키기 위해 분포 인식 대조 학습을 적용한다.

### 핵심 문제

교통 데이터는 극단적인 롱테일 분포를 가진다:
- **Head**: 직진, 서행 (대다수)
- **Tail**: 급제동, 회피 기동, 비정상 운행 (소수)

표준 학습은 head 분포에 과적합되어 tail 시나리오 예측이 크게 저하된다.

### FEND 메커니즘

1. **Distribution-aware 클러스터링**: 궤적을 분포 특성에 따라 클러스터링
2. **Future-Enhanced 증강**: 미래 궤적 정보를 활용한 현재 임베딩 강화
3. **대조 학습**: 동일 클러스터(positive) vs 다른 클러스터(negative) 페어로 임베딩 분리

```
롱테일 클러스터 식별 → 분포 인식 샘플링 → 대조 학습으로 표현 강화
→ 희귀 시나리오(tail) 예측 성능 향상
```

### 성능 (nuScenes)

| 방법 | ADE (tail) | FDE (tail) |
|------|-----------|-----------|
| Social Force | 1.82 | 3.74 |
| FEND (본 논문) | **1.24** | **2.31** |

---

## 장단점

**장점**
- 추가 레이블 없이 분포 자체에서 tail 클러스터 자동 식별
- 대조 학습으로 tail 클러스터 임베딩 품질 향상
- 임베딩 클러스터링 파이프라인과 자연스럽게 연결

**단점**
- 궤적 데이터(x, y 좌표 시퀀스) 특화 — 캡션 텍스트에 직접 적용 불가
- "Future" 정보(미래 궤적) 필요 → 캡션 기반 데이터에는 미래 컨텍스트 없음
- 대조 학습 학습 비용이 상당함

---

## 프로젝트 적용 포인트

### Gap-4 → EXP-002 Phase C (그래프 기반 씬 커버리지 확장)

FEND의 핵심 아이디어 — **분포 인식 대조 학습으로 롱테일 클러스터 표현 강화** — 를 캡션 임베딩에 적용:

```python
# bge-m3 임베딩에서 롱테일 클러스터 강화
# Phase A 결과: 소규모 클러스터 = tail
tail_clusters = [cid for cid, size in cluster_sizes.items() if size < 500]
head_clusters = [cid for cid, size in cluster_sizes.items() if size >= 500]

# 대조 학습:
# Positive: 같은 tail 클러스터 내 샘플 쌍
# Negative: head 클러스터의 샘플
```

EXP-002 Phase C의 T2SG 그래프 기반 커버리지 분석과 결합하여 롱테일 씬의 표현을 강화한다.

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-4 | 롱테일 시나리오 임베딩 강화 → 분포 편향 탐지 정확도 향상 |

## 관련 실험
- EXP-002: Phase C — 그래프 기반 씬 커버리지 분석 시 FEND 방식 대조 학습 통합
