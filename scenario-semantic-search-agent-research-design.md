---
title: "시나리오 기반 시맨틱 서치 연구 설계: 다중 에이전트 협업 프레임워크"
category: overviews
sources:
  - multimodal/kim-2025-genius-generative-framework-universal
  - rl-agents/song-2026-paperorchestra-multi-agent-framework
  - autonomous-driving/rivera-2025-scenario-understanding-traffic-scenes
  - autonomous-driving/chodowiec-2026-odd-behaviour-scenario-coverage
  - autonomous-driving/cao-2026-alpamayo-r1-bridging-reasoning
  - autonomous-driving/aasi-2024-generating-out-of-distribution-scenarios
  - autonomous-driving/dimlioglu-2026-scaling-aware-data-selection
  - autonomous-driving/rempe-2022-generating-useful-accident-prone
  - autonomous-driving/russell-2025-gaia-2-controllable-multi-view
tags: [semantic-search, scenario, multi-agent, distribution-analysis, autonomous-driving, research-design]
created: 2026-05-08
---

## 연구 배경 및 목표

**데이터 규모**: 30만 클립 × 20초 = 약 1,667시간 주행 영상

**두 가지 핵심 과제**:
```
과제 A: 시나리오 기반 시맨틱 서치
  → "야간 교차로에서 보행자가 갑자기 나타나는 상황" 같은
     자연어 쿼리로 관련 클립을 빠르고 정확하게 찾아야 함
  → 목표: 30만 클립 전체 검색 < 500ms, Recall@5 > 80%

과제 B: 전체 데이터셋 분포 분석
  → 전체 30만 클립이 어떤 시나리오로 구성되는지
     ODD 커버리지 맵과 임베딩 밀도 맵으로 시각화
```

두 과제는 **같은 인프라(클립 임베딩 + 시나리오 태그)를 공유**하므로 함께 설계해야 한다.

---

## PaperOrchestra 에이전트 구조 → 연구 에이전트로 재매핑

[[rl-agents/song-2026-paperorchestra-multi-agent-framework|PaperOrchestra (Song et al. 2026)]]의 5 에이전트 구조를 이 연구 파이프라인에 직접 대응시킨다.

```
PaperOrchestra            →    이 연구의 에이전트
──────────────────────────────────────────────────────
Outline Agent             →    Research Design Agent
Plotting Agent            →    Data Visualization Agent   (병렬)
Literature Review Agent   →    Experiment Code Agent      (병렬)
Section Writing Agent     →    Evaluation & Analysis Agent
Content Refinement Agent  →    Paper Drafting Agent
```

### Agent 1: Research Design Agent (순차)

**입력**: 연구 목표(시맨틱 서치 + 분포 분석), 데이터 규모, 제약(속도·정확도)

**출력**: JSON 형식의 실험 계획서
```json
{
  "research_axes": [
    "클립 인코더 아키텍처 (CLIP vs 자율주행 특화 vs 비디오 트랜스포머)",
    "시나리오 태깅 방법 (LVLM 자동 태깅 vs ODD 규칙 기반 vs 혼합)",
    "검색 인덱스 방법 (ANN Faiss vs 생성형 Trie vs 하이브리드)",
    "분포 분석 방법 (KDE vs GMM vs 계층 클러스터링)"
  ],
  "evaluation_metrics": {
    "search": ["Recall@5", "MRR@10", "검색 지연시간 ms"],
    "distribution": ["ODD 커버리지율", "롱테일 클립 발굴 수", "클러스터 응집도"]
  }
}
```

### Agent 2: Data Visualization Agent (병렬)

**역할**: 클립 메타데이터(GPS, 속도, 시간대, 날씨 로그)를 분석하여 기준 분포 시각화 생성

[[autonomous-driving/rivera-2025-scenario-understanding-traffic-scenes|Rivera et al.(2025)]] **CatPipe**를 직접 적용해 LVLM으로 각 클립을 16개 시나리오 카테고리로 자동 분류한다. 20초 영상이므로 **키프레임(0, 5, 10, 15, 20초)만 태깅**하여 속도를 높인다.

### Agent 3: Experiment Code Agent (병렬)

**역할**: 검색 시스템의 핵심 실험 코드 자동 생성. 세 가지 접근법을 병렬로 구현한다:

```
접근법 A: 태그 기반 BM25 검색
  └ Rivera CatPipe → 시나리오 태그 → 텍스트 역 인덱스

접근법 B: 임베딩 기반 ANN 검색
  └ CLIP/비디오 인코더 → 클립 임베딩 → Faiss HNSW 인덱스

접근법 C: 생성형 검색 (GENIUS 방식)
  └ 시나리오 → 이산 ID 생성 → Trie 기반 검색
  └ DB 크기와 무관한 O(M) 속도 (GENIUS 핵심 장점)
```

### Agent 4: Evaluation & Analysis Agent

**역할**: 실험 결과를 자동 분석하고 어블레이션 제안

```
실험 결과 로그 입력
    ↓
자동 생성 분석 예시:
- "접근법 C가 검색 속도 3.2× 빠르지만 Recall@5 -8.3%"
- "태그 기반 BM25는 OOD 쿼리에서 급격히 성능 저하"
- "야간 × 비 클립이 전체의 1.2% → 이 구간 Recall 최악"
    ↓
다음 실험 자동 제안:
- "B+C 하이브리드: BM25 pre-filter → GENIUS re-rank"
- "OOD 클립 전용 Recall 지표 추가 필요"
```

### Agent 5: Paper Drafting Agent

**역할**: 실험 로그 → LaTeX 논문 초안 (PaperOrchestra 직접 활용)

실험이 끝날 때마다 결과를 `experiment_log.md`에 누적하고, PaperOrchestra에 넣으면 논문 초안이 자동 업데이트된다.

---

## 핵심 연구 아이디어 3가지

### Idea 1: 계층적 하이브리드 검색 (속도 + 정확도 동시 해결)

[[multimodal/kim-2025-genius-generative-framework-universal|GENIUS (Kim et al. 2025)]]의 핵심 교훈 — *"이산 ID로 후보를 좁히고, 임베딩으로 재순위화하면 속도와 정확도를 모두 잡는다"* — 를 주행 클립 검색에 적용한다.

```
쿼리: "야간 교차로에서 보행자 급등장"
    ↓
Level 1: ODD 태그 필터 (Chodowiec 2026 4차원 커버리지 기반)
  조건: {시간대=야간, 도로유형=교차로, 에이전트=보행자}
  → 30만 → 약 8,000 클립으로 압축 (97% 제거)

Level 2: 시나리오 ID 생성형 검색 (GENIUS 방식)
  쿼리 임베딩 → Trie 빔 서치로 시나리오 ID 생성
  → 8,000 → 상위 50 클립 후보

Level 3: 임베딩 재순위 (GENIUS^R 방식)
  50개 후보 × 클립 임베딩 유사도 계산
  → 최종 Top-K 반환
```

**실험 설계**: Level 별 제거율과 Recall 트레이드오프 측정

### Idea 2: 인과 기반 시나리오 임베딩 (정확도 향상)

[[autonomous-driving/cao-2026-alpamayo-r1-bridging-reasoning|Alpamayo-R1 (Cao et al. 2026)]]의 Chain of Causation을 임베딩 학습 신호로 사용한다.

현재 CLIP 임베딩의 문제:
```
"야간 + 비 + 보행자 출현" 클립
"주간 + 맑음 + 보행자 급등장" 클립
→ 외관이 달라서 임베딩 거리 멀다
→ 하지만 두 클립은 같은 "위험 인과 구조"를 가진다
```

CoC 레이블(인과 요소 + 주행 결정)을 대조 학습 신호로 추가하면:
```
같은 위험 원인 → 가까운 임베딩 (외관 무관)
다른 위험 원인 → 먼 임베딩 (외관 비슷해도)
```

**실험**: CLIP 임베딩 vs CoC 대조 학습 임베딩의 시나리오 검색 Recall@5 비교

### Idea 3: 생성형 쿼리 증강으로 검색 Coverage 확장

GENIUS의 **Query Augmentation**(쿼리-타겟 보간) 개념을 [[autonomous-driving/aasi-2024-generating-out-of-distribution-scenarios|Aasi et al.(2024)]] LLM 분기 트리 방식과 결합해 주행 시나리오 검색에 적용한다.

```
사용자 쿼리: "보행자가 갑자기 나타나는 상황"

쿼리 증강 에이전트:
  LLM이 유사 쿼리 변형 자동 생성:
  - "어린이가 주차된 차 뒤에서 뛰어나오는 상황"
  - "자전거가 골목에서 갑자기 진입하는 상황"
  - "우산 쓴 보행자가 횡단보도 외 구간 횡단"

  → 증강 쿼리 10개로 검색 후 결과 합산 (앙상블)
  → Recall@5 커버리지 확장
```

**핵심 실험 변수**: 증강 쿼리 수(1, 5, 10, 20개) × Recall 변화율

---

## 분포 분석 파이프라인

[[autonomous-driving/chodowiec-2026-odd-behaviour-scenario-coverage|Chodowiec et al.(2026)]] ODD 커버리지 프레임워크 + [[autonomous-driving/rivera-2025-scenario-understanding-traffic-scenes|Rivera et al.(2025)]] CatPipe + 임베딩 밀도 추정을 통합한 4단계 파이프라인이다.

```
Stage 1: ODD 속성 자동 추출 (Rivera CatPipe)
  → 각 클립에 {날씨, 시간대, 도로유형, 교통밀도, 에이전트 유형} 자동 태깅

Stage 2: ODD 커버리지 행렬 생성 (Chodowiec 2026)
  → 행: ODD 조건 조합 / 열: 자아차량 행동 / 값: 클립 수
  → 빈 셀 = 수집 갭

Stage 3: 임베딩 밀도 맵 생성
  → 클립 임베딩 → UMAP 2D 축소 → KDE 밀도 추정
  → 저밀도 영역 = 롱테일 시나리오

Stage 4: 두 분석 교차 검증
  → ODD 갭 셀 ↔ 임베딩 저밀도 영역 일치 여부
  → 불일치 = 새로운 시나리오 유형 자동 제안
```

---

## 에이전트 협업 실행 구조

### 디렉토리 구조

```
research/
├── idea_summary.md       # 연구 아이디어 (PaperOrchestra의 I)
├── experiment_log.md     # 실험 결과 누적 (PaperOrchestra의 E)
├── agents/
│   ├── design_agent.md
│   ├── viz_agent.md
│   ├── code_agent.md
│   └── eval_agent.md
└── outputs/
    ├── distribution_map/
    ├── search_results/
    └── draft_paper/
```

### 반복 실험 사이클

```
매 실험 사이클 (반복):

1. 연구자 → Design Agent
   "다음 실험: 계층적 검색 Level 1 태그 필터 성능 측정"

2. Design Agent → experiment_log.md 업데이트
   실험 계획, 예상 결과, 평가 지표 명시

3. Code Agent (병렬) + Viz Agent (병렬)
   Code: 실험 코드 자동 생성 + 실행
   Viz: 결과 시각화 자동 생성

4. Evaluation Agent
   결과 분석 + 다음 실험 제안 → experiment_log.md 기록

5. Paper Agent (주기적)
   experiment_log.md → PaperOrchestra 입력
   → LaTeX 초안 자동 업데이트

6. 연구자 검토 → 다음 사이클로
```

**핵심**: `experiment_log.md`가 PaperOrchestra의 `E(Experimental Log)` 역할을 하므로, 실험이 쌓일수록 논문 초안 품질이 자동으로 올라간다.

### Research Design Agent 초기 프롬프트 템플릿

```
목표: 30만 주행 클립(클립당 20초)에 대한 시나리오 기반 시맨틱 서치 시스템 설계

연구 방향:
1. 속도: 30만 클립 전체 검색 < 500ms
2. 정확도: Recall@5 > 80% (인간 평가 기준)
3. 분포 분석: ODD 커버리지 맵 + 임베딩 밀도 맵

활용 가능 방법론 (위키 논문 기반):
- Rivera 2025 CatPipe: LVLM 시나리오 자동 태깅
- GENIUS 2025: 생성형 검색 (Trie + 재순위)
- Chodowiec 2026: ODD 4차원 커버리지
- Alpamayo-R1 2026: Chain of Causation 행동 분류

출력 형식: JSON 실험 계획서
  - 3가지 접근법 × 평가 지표 × 어블레이션 계획
```

---

## 연구 로드맵

| 단계 | 기간 | 에이전트 주역할 | 목표 산출물 |
|------|------|--------------|-----------|
| **Phase 0** | 2주 | Design Agent | 실험 계획서, 데이터 샘플 분석 |
| **Phase 1** | 4주 | Code + Viz Agent | 3가지 검색 방법 기준 성능 측정 |
| **Phase 2** | 4주 | Code + Eval Agent | 계층 하이브리드 최적화 + 분포 분석 완성 |
| **Phase 3** | 2주 | Paper Agent | PaperOrchestra로 논문 초안 자동 생성 |

---

## 핵심 인사이트

| 인사이트 | 근거 논문 |
|---------|---------|
| 이산 ID로 후보를 좁히고 임베딩으로 재순위화하면 속도·정확도 동시 확보 | GENIUS 2025 |
| 외관이 아닌 인과 구조로 임베딩하면 동질적 위험 상황을 통합 검색 가능 | Alpamayo-R1 2026 |
| LVLM은 단순 감지보다 추론 카테고리(교차로 복잡도 등)에서 강하다 | Rivera 2025 |
| ODD 태그 필터로 99% 후보를 제거하면 이후 검색 계산 비용 대폭 절감 | Chodowiec 2026 |
| 쿼리 증강(분기 트리)으로 Recall Coverage를 증강 쿼리 수에 비례해 확장 | Aasi 2024 |
| 논문 집필은 실험 로그를 PaperOrchestra에 넣어 자동화할 수 있다 | Song 2026 |

---

## 관련 논문

- [[multimodal/kim-2025-genius-generative-framework-universal]] — 생성형 멀티모달 검색 (계층적 하이브리드 검색 설계 근거)
- [[rl-agents/song-2026-paperorchestra-multi-agent-framework]] — 다중 에이전트 연구 자동화 (에이전트 협업 구조 설계 근거)
- [[autonomous-driving/rivera-2025-scenario-understanding-traffic-scenes]] — CatPipe LVLM 시나리오 태깅
- [[autonomous-driving/chodowiec-2026-odd-behaviour-scenario-coverage]] — ODD 4차원 커버리지 프레임워크
- [[autonomous-driving/cao-2026-alpamayo-r1-bridging-reasoning]] — Chain of Causation 임베딩 학습 신호
- [[autonomous-driving/aasi-2024-generating-out-of-distribution-scenarios]] — LLM 분기 트리 쿼리 증강
- [[autonomous-driving/dimlioglu-2026-scaling-aware-data-selection]] — 스케일링 인식 데이터 혼합 최적화
- [[autonomous-driving/rempe-2022-generating-useful-accident-prone]] — VAE 잠재 공간 기반 희귀 시나리오 발굴
- [[autonomous-driving/russell-2025-gaia-2-controllable-multi-view]] — 세계 모델 잠재 공간 = 분포 분석 공간
