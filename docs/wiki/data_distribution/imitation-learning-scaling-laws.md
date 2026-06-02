# 모방 학습 기반 E2E AV 데이터 스케일링 법칙

## 출처
- **저자**: Zheng, Yang, Xia, Zhang, Zheng, Gu, Jin, Zhang, Lu, Han, Lang, Zhao (CASIA / UCAS / Li Auto)
- **연도**: 2025
- **논문**: arXiv:2412.02689
- **파일**: `literature/papers/zheng-2025-data-scaling-laws-imitation.pdf`

---

## 핵심 아이디어

E2E 자율주행의 데이터 스케일링 법칙을 **4M 시연 × 23개 시나리오 유형**으로 체계 분석.  
핵심 발견: **데이터 양보다 분포(distribution)가 더 중요하다.**

### ONE-Drive 데이터셋

| 항목 | 값 |
|------|-----|
| 총 시연 수 | 4M demonstrations |
| 총 시간 | 30,000+ 시간 |
| 시나리오 유형 | 23개 |
| 도시 다양성 | 여러 중국 도시 |
| 센서 | 7 카메라 360° + 128채널 LiDAR |

### 스케일링 법칙 (멱함수)

```
Y = 0.6833 × X^{-0.188},  r = -0.963
```
- X: 훈련 데이터 수 (demonstrations)
- Y: Normalized ADE
- **강한 멱함수 관계 확인** (r = -0.963)

### 3대 핵심 발견

| 발견 | 의미 |
|------|------|
| ① Open-loop ≠ Closed-loop | Open-loop ADE 개선이 closed-loop 안전으로 이어지지 않음 |
| ② 롱테일 소량 추가 = 큰 효과 | 특정 시나리오 2배 증가 → 성능 9.7~16.9% 향상 |
| ③ 조합 일반화 가능 | 충분한 데이터로 훈련하면 미경험 시나리오에도 일반화 |

### 시나리오별 데이터 효율성

롱테일 시나리오 (DOWN_SUBROAD_LC, SUBROAD_TO_MAINROAD_HIGHWAY):
- 643개 추가 (130% 증가) → ADE 22.8% 개선
- 4972개 추가 (45.1% 증가) → ADE 9.7% 개선

→ **적은 수의 롱테일 데이터가 전체 크기 확대보다 효율적**

### 23개 시나리오 유형 분포

```
NORMAL, NAVIGATION_LCR, EFFICIENCY_LCR, NUDGE_STATIC_OBS,
NUDGE_SLOW_OBS, QUEUE, LEFT_TURN, RIGHT_TURN, UTURN, Y_ROAD,
FOLLOW_CAR_BRAKE, FOLLOW_CAR_STABLE, CITY_SUBROAD_TO_MAIN_ROAD,
DOWN_SUBROAD_LC, SUBROAD_TO_MAINROAD_HIGHWAY, HIGHWAY_NUDGE_OBS,
WAIT_TURN, HIGHWAY_LEFT_CHANGE, HIGHWAY_RIGHT_CHANGE, ...
```

---

## 장단점

**장점**
- 4M 규모 실험 → 가장 대규모 스케일링 분석
- 23개 세밀한 시나리오 유형 → 데이터 수집 우선순위 명확
- 조합 일반화 능력 실험적 검증

**단점**
- 내부 데이터 (Li Auto) → 직접 재현 불가
- 중국 도시 중심 → 환경 편향 가능
- Closed-loop 평가 100개 시연으로 제한

---

## 프로젝트 적용 포인트

### Gap-4 (분포 편향) 핵심 통찰

**"데이터 양 확대보다 분포 개선이 효율적"**은 현재 프로젝트에 직접 적용 가능.

현재 83k 클립 중 롱테일 클립 식별 후 **검색 성능 기여도** 분석:
```python
# 롱테일 클립의 Recall@5 기여도 측정
longtail_clips = json.load(open("data/index/longtail_clips.json"))
normal_clips = [c for c in all_clips if c not in longtail_clips]

recall_all = evaluate_recall(all_clips)
recall_without_longtail = evaluate_recall(normal_clips)

longtail_contribution = recall_all - recall_without_longtail
# 작은 수의 롱테일이 큰 기여 → 수집 우선순위 상승
```

### Gap-4 보완: 시나리오 유형별 데이터 수집 로드맵
Zheng의 23개 유형 → 현재 프로젝트 맥락으로 변환:

| Zheng 유형 | 현재 프로젝트 대응 |
|-----------|--------------|
| QUEUE | 정체 구간 |
| NUDGE_SLOW_OBS | 서행 장애물 회피 |
| HIGHWAY_NUDGE_OBS | 고속도로 장애물 |
| DOWN_SUBROAD_LC | 진입로 차선 변경 |

### 아이디어: 조합 일반화 실험 (EXP-007 후보)
- 특정 ODD 조합(야간+안개)은 학습 데이터 없이도 조합 일반화로 검색 가능한지 테스트
- 현재 Embedding 모델의 조합 일반화 능력 측정

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-4 | "분포 > 양" 원칙으로 데이터 수집 전략 재정립 |
| Gap-6 | 23개 시나리오 유형으로 쿼리 다양성 확보 기준 |

## 관련 실험
- EXP-003 (Distribution Analysis): 롱테일 클립의 검색 성능 기여도 측정
- EXP-004 (Full Scale): 시나리오 유형별 클립 수와 검색 성능 관계 분석
