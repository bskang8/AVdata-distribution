# WOD-E2E: 롱테일 시나리오 특화 데이터셋 (Waymo)

## 출처
- **저자**: Xu, Lin, Jeon, Feng, Zou, Sun, Gorman 외 (Waymo LLC)
- **연도**: 2025
- **논문**: arXiv:2510.26125
- **파일**: `literature/papers/xu-2025-wod-e2e-waymo-open-dataset.pdf`

---

## 핵심 아이디어

E2E 자율주행 벤치마크가 일반적인 nominal 시나리오에 편향된 문제를 해결하기 위해  
**롱테일(발생 빈도 <0.03%) 시나리오만** 큐레이션한 4,021개 세그먼트 데이터셋.

### 데이터셋 규모

| 항목 | 값 |
|------|-----|
| 총 세그먼트 수 | 4,021 |
| 총 시간 | ~12시간 |
| 세그먼트 길이 | 20초 |
| 카메라 수 | 8 (360° 커버리지) |
| 롱테일 빈도 | <0.03% in 6.4M 마일 |
| Train/Val/Test | 2037/479/1505 |

### 11개 시나리오 클러스터

| 클러스터 | 특징 |
|---------|------|
| Construction | 공사구역 경로 변경, 비정상 노면 |
| Intersection | 비보호 회전, 복잡 교차로 상호작용 |
| Pedestrians | 오클루전, 예측 불가 보행자 행동 |
| Cyclists | 자전거 그룹, 제어력 상실 |
| Multi-Lane Maneuvers | 고속도로 차선 변경 |
| Single-Lane Maneuvers | 좁은 도로 추월 |
| Cut-ins | 공격적 끼어들기 |
| Foreign Object Debris (FOD) | 동물, 낙하물, 침수 도로 |
| Special Vehicles | 긴급차량, 갓길 정차 |
| Spotlight | Gemini로 탐색한 챌린지 시나리오 |
| Others | 위 분류 외 |

### 새로운 평가 지표: RFS (Rater Feedback Score)

기존 ADE/FDE의 한계 극복:
- 전문가 레이터가 3개 후보 궤적을 0~10점 채점
- 최소 1개가 6점 이상이어야 유효 레이블
- 롱테일에서 복수의 합리적 경로 존재 → ADE 단일값 부적합

### 롱테일 마이닝 전략

```
6.4M 마일 주행 로그
    ↓ Rule-based heuristics + MLL 필터링
6,888 마일 (0.108%, mined long-tail)
    ↓ Human review (conversion rate 30%)
2,150 마일 (0.034%, human-verified)
```

---

## 장단점

**장점**
- 실제 롱테일 시나리오의 최대 규모 공개 데이터셋
- RFS: 복수 합리 경로를 반영한 더 현실적인 평가
- 11개 세밀한 카테고리로 분석 가능

**단점**
- 공개 데이터이지만 Waymo 시스템 의존 (3D 검출, 매핑 등)
- 롱테일 특화라 일반 성능 벤치마킹 부적합
- 미국 도시 중심 (한국 도로 환경과 차이 가능)

---

## 프로젝트 적용 포인트

### Gap-4 (분포 편향) 직결

WOD-E2E의 11개 클러스터를 현재 83k 클립 분류 기준으로 활용:

```python
# 현재 캡션에서 WOD-E2E 카테고리 키워드 매칭
wod_categories = {
    "Construction": ["construction", "roadwork", "barrier", "cone"],
    "FOD": ["animal", "debris", "fallen", "flood"],
    "Cut-ins": ["cut in", "sudden lane", "merge aggressive"],
    ...
}

for clip in clips:
    for cat, keywords in wod_categories.items():
        if any(kw in clip.caption for kw in keywords):
            clip.longtail_category = cat
```

### Gap-4 보완: 수집 가이드 작성 기준
WOD-E2E 11개 클러스터 = **현재 데이터에서 부족한 시나리오 유형 체크리스트**

현재 83k에서 각 클러스터 비율 측정 → 목표 분포 (nuScenes 또는 WOD-E2E) 대비 부족 클러스터 식별

### RFS 아이디어
현재 LLM relevance labeling (EXP-002)에 RFS 방식 도입:
- 단일 yes/no 레이블 → 여러 검색 결과에 대한 선호도 점수 (0~10)
- 복수의 합리적 결과를 허용하는 relevance 측정

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-4 | 11개 롱테일 클러스터로 분포 편향 측정 기준 제공 |
| Gap-1 | RFS 방식으로 평가셋 레이블 개선 |

## 관련 실험
- EXP-003 (Distribution Analysis): WOD-E2E 카테고리 분포를 현재 데이터와 비교
- EXP-004 (Full Scale): 전체 83k에서 롱테일 비율 측정
