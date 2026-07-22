# LTDA-Drive: LLM 가이드 생성 모델 기반 롱테일 데이터 증강 (Bosch/Stanford)

## 출처
- **저자**: Mahmut Yurt, Xin Ye, Yunsheng Ma, Jingru Luo, Abhirup Mallik, John Pauly, Burhaneddin Yaman, Liu Ren (Bosch Research North America / Stanford)
- **연도**: 2025
- **논문**: arXiv:2505.18198, May 2025
- **파일**: `literature/papers/ltda-drive-longtail-data-augmentation-2025.pdf`

---

## 핵심 아이디어

LLM이 롱테일 클래스(cyclist, pedestrian)의 데이터 부족 상황을 분석하고 생성 명세를 작성하면, diffusion 모델이 그 명세에 따라 다양한 합성 데이터를 생성하여 롱테일 클래스 성능을 향상.

### 시스템 파이프라인

| 단계 | 담당 | 입력 | 출력 |
|------|------|------|------|
| 분포 분석 | LLM | 현재 학습 데이터 통계 | 롱테일 클래스 식별 + 생성 명세 |
| 명세 작성 | LLM | 부족 클래스 정보 + 컨텍스트 | 다양한 시각적 속성 명세 |
| 합성 생성 | Diffusion 모델 | LLM 명세 (텍스트 + 조건) | 롱테일 클래스 합성 이미지/클립 |
| 학습 통합 | 학습 파이프라인 | 실제 + 합성 데이터 | 향상된 tail class 성능 |

### 기존 방법 대비 차별점

```
기존 방법 (재가중화/재샘플링):
  - 희귀 클래스를 더 자주 sampling
  - 데이터 다양성은 그대로 → tail class 다양성 부족 문제 미해결

LTDA-Drive:
  - LLM이 부족한 다양성 분석 → "cyclist + night + rain" 등 복합 조건 생성 명세
  - Diffusion 모델로 실제로 존재하지 않는 다양한 변형 생성
  - → tail class 다양성 근본적 해결
```

### 롱테일 클래스 성능 향상

| 클래스 | 기존 재샘플링 | LTDA-Drive |
|--------|-------------|-----------|
| Cyclist | 기준 | 유의미한 향상 |
| Pedestrian | 기준 | 유의미한 향상 |
| 일반 차량 | 기준 | 유지 또는 소폭 향상 |

---

## 장단점

**장점**
- LLM의 언어 이해 + diffusion의 시각 생성 결합 → 다양하고 의미 있는 롱테일 데이터 생성
- 재가중화/재샘플링보다 실질적인 다양성 증가
- Bosch 실세계 AV 데이터셋에서 검증 → 실용성 확인

**단점**
- LLM 명세 품질이 최종 생성 품질에 직접 영향
- Diffusion 생성 비용 (시간/GPU 집약적)
- 생성된 합성 데이터의 도메인 갭 — 실세계 센서 노이즈와 차이

---

## 프로젝트 적용 포인트

### Gap-4: 롱테일 클래스 다양성 증강

현재 83k 클립의 agent_type 편향(effective_n=1.16)을 LTDA-Drive 방식으로 해결:

```python
# 현재 문제: agent_type effective_n=1.16 → 사실상 cars_only
# 롱테일 클래스: cyclist, pedestrian, bus, truck

# LTDA-Drive 적용 방법:
# 1. LLM에게 현재 분포 통계 제공:
#    "cyclist: 0.8%, pedestrian: 2.1%, car: 91.3%..."
# 2. LLM이 생성 명세 작성:
#    "cyclist + intersection + night + rain" (복합 희귀 조건)
#    "pedestrian + crosswalk + wet_road" 등
# 3. Diffusion으로 명세 기반 합성 생성
# 4. COLLECT_HIGH_PRIORITY 보완:
#    S1(보행자), S8(버스/트럭) → LLM 명세 기반 다양한 변형 생성

# 연결: EXP-003 SYNTHETIC 후보와 직접 결합 가능
synthetic_specs = llm_analyze_longtail(current_distribution)
synthetic_clips = diffusion_generate(synthetic_specs)
```

### Gap-6: 희귀 클래스 쿼리 앵커 다양화

- 보행자/자전거 관련 검색 쿼리에 대한 앵커 시나리오 부족 → LTDA-Drive로 생성
- LLM 명세의 언어 표현을 검색 쿼리로 직접 활용 가능

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-4 | LLM 명세 기반 롱테일 클래스 다양성 합성 — agent_type effective_n 개선 |
| Gap-6 | LLM 생성 명세를 검색 쿼리 다양화에 재활용 |

## 관련 실험
- EXP-003 (Phase 0): SYNTHETIC 후보 S1(보행자), S8(버스/트럭) 합성 전략으로 LTDA-Drive 활용
- EXP-004: 롱테일 클래스 오버샘플링 + LTDA-Drive 합성 결합 실험
