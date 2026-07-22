# Cosmos-Drive-Dreams: 월드 파운데이션 모델 기반 주행 데이터 생성 (NVIDIA)

## 출처
- **저자**: Xuanchi Ren, Yifan Lu, Tianshi Cao, Ruiyuan Gao, Shengyu Huang, Amirmojtaba Sabour, Tianchang Shen, Tobias Pfaff 외 (NVIDIA)
- **연도**: 2025
- **논문**: arXiv:2506.09042, Jun 2025
- **파일**: `literature/papers/cosmos-drive-dreams-2025.pdf`

---

## 핵심 아이디어

NVIDIA Cosmos-1 world foundation model을 자율주행 도메인에 특화하여, 제어 가능한 고품질 멀티뷰·시공간 일관성 있는 주행 영상을 대규모로 생성하고 다운스트림 AV 학습 성능을 향상.

### 시스템 구조

| 컴포넌트 | 역할 |
|---------|------|
| Cosmos-1 World Foundation Model | 대규모 사전학습된 비디오 생성 기반 모델 |
| AV 도메인 특화 파인튜닝 | 주행 데이터 및 제어 신호로 파인튜닝 |
| 멀티뷰 일관성 모듈 | 복수 카메라 뷰 간 시공간 정합 보장 |
| 제어 인터페이스 | HDMap, 날씨, 조명, 에이전트 배치 등 조건부 생성 |

### 생성 데이터 특성

| 특성 | 내용 |
|------|------|
| 뷰 수 | 멀티뷰 (전방/측방/후방 일관성) |
| 시간 일관성 | 시퀀스 전체 물리적 일관성 유지 |
| 제어 가능 요소 | 날씨(야간/비/눈), 장소(교차로/램프), 에이전트(보행자/트럭) |
| 오픈소스 | 파이프라인 툴킷 + 데이터셋 + 모델 가중치 공개 |

### 다운스트림 성능 향상

```
Cosmos-Drive-Dreams 생성 데이터 → 학습 데이터 보강
    ↓
롱테일 분포 문제 완화
    ↓ 성능 향상 확인된 태스크:
    - 3D 차선 검출
    - 객체 검출 (보행자, 자전거, 특수차량)
    - 주행 정책 학습 (E2E AV)
```

---

## 장단점

**장점**
- World Foundation Model 기반 → 물리적으로 그럴듯한 주행 씬 생성
- 멀티뷰·시공간 일관성 → 현실 데이터에 가까운 품질
- 오픈소스 공개 → 즉시 실험 가능
- 롱테일 ODD(야간·악천후·특수 에이전트) 타겟 생성 가능

**단점**
- World Foundation Model 파인튜닝 비용 (GPU 집약적)
- 생성 데이터-실제 데이터 도메인 갭은 여전히 존재
- 제어 가능성의 한계: 극도로 희귀한 시나리오는 생성 품질 저하 가능

---

## 프로젝트 적용 포인트

### Gap-4: SYNTHETIC 후보 시나리오 고품질 생성

EXP-003 phase0 SYNTHETIC 후보에 Cosmos-Drive-Dreams 직접 활용:

```python
# SYNTHETIC 후보 → Cosmos 생성 조건 매핑:
# S3(야간):    조건 → time_of_day=night, lighting=dark
# S9(curve):  조건 → road_type=curve, geometry=sharp_turn
# S0(road):   조건 → road_type=highway, traffic=sparse
# S6(교차로): 조건 → scene=intersection, agent=pedestrian
# S10(주차장): 조건 → scene=parking_lot, agent=mixed

# 멀티뷰 일관성: 기존 단안 카메라 클립 보완
# 현재 83k 클립 중 야간(S3) 비율 낮음 → Cosmos로 보충

# 활용 방법:
# 1. Cosmos 오픈소스 파이프라인으로 타겟 ODD 합성
# 2. 합성 데이터 품질 검증 (FID, LPIPS 등)
# 3. Unraveling 논문의 최적 비율로 혼합
```

### Gap-6: 쿼리 앵커 시나리오 고품질 생성

- 희귀 시나리오(야간 보행자, 안개 교차로 등) 쿼리 앵커를 Cosmos로 생성
- 생성된 씬으로 검색 앵커셋 다양성 확보

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-4 | World Foundation Model로 롱테일 ODD 고품질 합성 데이터 생성 |
| Gap-6 | 희귀 ODD 쿼리 앵커 시나리오 생성으로 검색 다양성 확보 |

## 관련 실험
- EXP-003 (Phase 0): SYNTHETIC 후보 시나리오 생성 도구로 활용
- EXP-004: Cosmos 생성 데이터 + 실제 데이터 최적 혼합 비율 실험
