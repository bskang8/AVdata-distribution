# EXP-002 실험 방법론 수정 방향 (개정판)

**최초 작성일**: 2026-06-04
**개정일**: 2026-06-04
**배경**: EXP-002 Phase 2 (Axis B) 파이프라인의 근본 한계 분석 및 대안 기술 검토.
CVPR / NeurIPS / ICML / ICLR 최신 연구를 기반으로 우선순위 및 방법론 전면 재검토.
**목적**: 데이터셋 커버리지 분석과 수집 처방의 효율성을 높이기 위한 방법론 개선 방향 제시

---

## 목차

1. [현재 방법론의 한계 진단](#1-현재-방법론의-한계-진단)
2. [핵심 문제 재정의](#2-핵심-문제-재정의)
3. [대안 기술 분석](#3-대안-기술-분석)
   - [3-1. 의미 임베딩 클러스터링 + LLM 레이블링](#3-1-의미-임베딩-클러스터링--llm-레이블링)
   - [3-2. ODD 커버리지 매트릭스](#3-2-odd-커버리지-매트릭스)
   - [3-3. LLM 직접 시나리오 분류체계 (AIDE 방식)](#3-3-llm-직접-시나리오-분류체계-aide-방식)
   - [3-4. 의미론적 Normalizing Flow (SANFlow 방식)](#3-4-의미론적-normalizing-flow-sanflow-방식)
   - [3-5. 그래프 기반 씬 커버리지 분석](#3-5-그래프-기반-씬-커버리지-분석)
   - [3-6. 갭 시나리오 생성으로 커버리지 보완](#3-6-갭-시나리오-생성으로-커버리지-보완)
4. [방법별 종합 비교](#4-방법별-종합-비교)
5. [수정된 실험 우선순위 로드맵](#5-수정된-실험-우선순위-로드맵)
6. [EXP-002 기존 파이프라인 계속 여부 판단 (개정)](#6-exp-002-기존-파이프라인-계속-여부-판단-개정)
7. [참고 문헌](#7-참고-문헌)

---

## 1. 현재 방법론의 한계 진단

### 1-1. EXP-002 Phase 2 (Axis B) 파이프라인 구조

현재 파이프라인은 캡션 텍스트에서 7D 연속 ODD 벡터를 추출하는 두 단계로 구성된다.

```
[캡션 텍스트]
    │
    ▼  Step 2-1 (EXP-001 산출물 재사용)
[Regex 매칭] ────── _HEURISTICS 딕셔너리, "first match wins"
    │
    ▼
[이산 태그] ─── {"weather": "fog", "road_type": "highway", ...}
    │
    ▼  Step 2-1 변환
[룩업 테이블] ── fog → 0.12, clear → 0.98, ...
    │
    ▼
[7D 연속 벡터] ─ {"visibility_level": 0.12, "traffic_density_cont": 0.85, ...}
    │
    ▼  Phase 3 (Axis C)
[Normalizing Flow] ──→ 밀도 추정 → 갭 탐지
```

### 1-2. 정보 손실 연쇄 (Information Loss Chain)

각 변환 단계에서 정보가 손실되거나 왜곡된다.

| 단계 | 손실 유형 | 구체적 예시 |
|------|---------|-----------|
| 캡션 → Regex | 공출현 조건 누락 | "foggy and rainy" → rain만 태그됨 (first match wins) |
| Regex → 이산 태그 | unknown 과다 | traffic_density: 63%(187,356개) unknown |
| 이산 태그 → 연속 수치 | 검증 불가 수치 할당 | fog→0.12는 직관 기반, 근거 없음 |
| 연속 벡터 → NF 공간 | 의미 단절 | 갭 좌표 → 시나리오 설명 역변환 불가 |

### 1-3. Unknown 전파 규모

`data/tags/odd_tags.json` (299,180개 클립) 기준 실제 분포:

| 필드 | unknown 비율 | unknown 클립 수 |
|------|-----------|--------------|
| `traffic_density` | **62.6%** | 187,356개 |
| `time_of_day` | **37.3%** | 111,554개 |
| `weather` | **47.1%** | 140,937개 |
| `road_type` | 3.3% | 9,929개 |
| `hazard_level` | 15.3% | 45,712개 |

---

## 2. 핵심 문제 재정의

### 2-1. 문제의 학술적 위상 확인

ICML 2024 Best Paper (Oral) ["Measure Dataset Diversity, Don't Just Claim It"][R7]은 135개 공개 데이터셋을 분석한 결과, **"diversity"라는 단어가 실증적 근거 없이 선언적으로 사용되고 있음**을 폭로하고 사회과학의 측정 이론(measurement theory)에 기반한 다양성 정량화 원칙을 제시했다.

이 프로젝트의 fog=0.12 방식은 해당 논문이 비판하는 행태의 전형이다. 즉, 현재 파이프라인의 문제는 구현 오류가 아니라 **방법론적 설계 오류**다.

### 2-2. 두 가지 독립적 실패

**문제 A: 신뢰성 (Trustworthiness)**

```
fog → 0.12
clear → 0.98
```

이 수치는 **도메인 직관으로 수동 할당한 값**이다. 실증적 근거가 없다.

- "fog의 시인성은 0.12이다"를 어떻게 검증하는가?
- rain(0.65) vs snow(0.72)의 차이 0.07은 무엇을 근거로 하는가?
- Normalizing Flow가 "visibility_level < 0.15 영역이 희박하다"고 탐지해도, 그 영역이 실제로 희박한 것인지 **수치 할당 방식의 아티팩트**인지 구분할 수 없다.

**문제 B: 해석성 및 처방 가능성 (Actionability)**

NF가 갭을 발견해도 출력은 7D 좌표 범위다:

```json
{
  "visibility_level": [0.08, 0.18],
  "traffic_density_cont": [0.72, 0.90],
  "lighting_level": [0.05, 0.20],
  ...
}
```

이 좌표에서 "**어떤 시나리오를 수집해야 하는가?**"로 번역하는 역변환이 없다. 표준 NF는 임베딩 공간의 모든 위치에 동일한 표준정규분포를 가정하여 의미론적 구분이 불가능하다 [R6].

---

## 3. 대안 기술 분석

### 3-1. 의미 임베딩 클러스터링 + LLM 레이블링

**이 프로젝트에 가장 즉시 적용 가능한 방법이다.** bge-m3 임베딩(1024-dim)이 299k 클립에 대해 이미 `data/active/hnsw.index`에 존재하기 때문이다.

#### 학술적 근거

NeurIPS 2023 "Topological Precision & Recall (TopP&R)"[R4]은 임베딩 공간에서 지지도(support)를 KDE로 추정하여 데이터셋의 **fidelity**(실제 분포를 얼마나 커버하는가)와 **diversity**(내부 다양성)를 분리 측정한다. 이 프레임워크를 클러스터 크기 분포에 직접 적용할 수 있다.

NeurIPS 2024 "Metric Space Magnitude"[R5]는 위상수학 이론에 기반해 latent representation의 diversity를 multi-scale로 측정하며, perturbation에 대해 수학적으로 안정적(provably stable)임을 증명했다. Vendi Score 대비 이론적 보장이 강하다.

#### 작동 원리

```
[bge-m3 임베딩 벡터] (299k × 1024-dim, 이미 존재)
    │
    ▼  PCA(50차원) → UMAP(10차원) 축소
    ▼  HDBSCAN 클러스터링
[자동 발견된 k개 클러스터 + noise points]
    │
    ├─ Metric Space Magnitude 계산 (클러스터별 diversity 수치)
    │
    ▼  각 클러스터의 centroid 근접 캡션 5~10개를 GPT-4o-mini에 전달
["이 클러스터는 어떤 시나리오인가?" 프롬프트]
    │
    ▼
[자연어 시나리오 레이블 + 클러스터 크기 + diversity 점수]
    │
    ▼
[커버리지 보고서: 클러스터명 × 클립 수 × 다양성 지표]
```

#### 출력 예시 (예상)

| 클러스터 크기 | LLM 자동 생성 시나리오 레이블 | Magnitude 점수 | 상태 |
|------------|--------------------------|--------------|------|
| 42,180개 | "교차로 보행자 횡단 — 맑은 낮" | 341.8 | 포화 |
| 28,450개 | "고속도로 순항 — 트럭 혼재" | 278.4 | 충분 |
| 1,240개 | "교량 위 빗길 — 급제동 상황" | 23.1 | 부족 |
| **89개** | **"안개 + 야간 + 고속도로 후방 추돌 회피"** | **8.2** | **수집 필요** |
| **34개** | **"적설 노면 + 보행자 횡단 + 교차로"** | **3.7** | **수집 필요** |
| 12개 (noise) | — | — | 희귀 이상 씬 |

#### 비용 및 시간 추정

| 단계 | 비용 | 시간 |
|------|------|------|
| HDBSCAN (CPU) | 무료 | ~10분 |
| Metric Space Magnitude 계산 | 무료 | ~5분 |
| GPT-4o-mini 레이블링 (100개 클러스터 기준) | ~$0.50 | ~5분 |
| **합계** | **~$0.50** | **~20분** |

---

### 3-2. ODD 커버리지 매트릭스

**가장 즉시 실행 가능하고 비용이 0인 방법이다.** 이미 존재하는 `data/tags/odd_tags.json`을 직접 활용한다.

#### 학술적 근거

ICLR 2023 "Coverage-centric Coreset Selection"[R8]은 데이터 커버리지를 **기하학적 set cover 문제**로 정의한다. 각 ODD 조합이 하나의 "커버해야 할 셀"이고, 보유 클립이 그 셀을 얼마나 채우는지 측정한다. 임의 수치 없이 이산 카테고리 조합만으로 커버리지를 정량화하므로 측정 신뢰성이 높다.

ICML 2024 Best Paper[R7]의 권고에 따라 "다양성을 선언하지 말고 측정하라" — 이산 조합 빈도는 직접 검증 가능한 수치이므로 fog=0.12보다 신뢰할 수 있다.

#### 작동 원리

연속 수치 변환 없이 **이산 카테고리 조합의 클립 수**를 직접 센다.

```python
from collections import Counter
import json

d = json.load(open('data/tags/odd_tags.json'))

# 4-way 조합 커버리지 매트릭스
counter = Counter(
    (v['weather'], v['time_of_day'], v['road_type'], v['hazard_level'])
    for v in d.values()
    if 'unknown' not in (v['weather'], v['time_of_day'])  # known만
)

# 하위 20개 = 가장 희귀한 조합
print("=== 희귀 시나리오 조합 (수집 필요) ===")
for combo, cnt in counter.most_common()[:-21:-1]:
    print(f"{cnt:5d}개 | weather={combo[0]}, time={combo[1]}, "
          f"road={combo[2]}, hazard={combo[3]}")
```

#### 방법의 특성

**장점**:
- 결과가 완전히 해석 가능하다 ("fog × night × highway × high-hazard가 3개뿐")
- 비용 0, 실행 즉시 결과
- 수집 우선순위를 직접 도출할 수 있다

**단점**:
- 에이전트 행동, 씬 내 인과 관계를 포착하지 못한다
- unknown 클립(traffic_density 63%)은 분석에서 제외된다
- "실제로 희귀한가 vs 태깅이 안 된 것인가" 구분이 어렵다

---

### 3-3. LLM 직접 시나리오 분류체계 (AIDE 방식)

**신뢰성과 해석성이 가장 높은 방법이다.** 수치 변환 없이 LLM이 직접 시나리오 분류를 수행한다.

#### 학술적 근거

CVPR 2024 "AIDE: An Automatic Data Engine for Object Detection in Autonomous Driving"[R10]은 VLM + LLM을 활용해 **문제 식별 → 데이터 큐레이션 → 자동 레이블링 → 시나리오 생성 검증**의 반복 루프를 구성한다. 희귀 카테고리(long-tail)를 자동 발견하고 처방하는 엔드-투-엔드 파이프라인이다.

NeurIPS 2023 "ScenarioNet"[R3]은 Waymo / nuScenes / Lyft / nuPlan을 통합한 시나리오 플랫폼으로, 실세계 데이터와 합성 데이터 간의 커버리지 갭을 시나리오 클러스터링으로 시각화한다. 이 프로젝트의 LLM 분류체계 설계에 참고 가능한 26가지 시나리오 분류체계를 포함한다.

#### 작동 원리

```
1단계: 분류체계 생성
  캡션 1,000개 샘플 → GPT-4o → 시나리오 분류체계 (20~50 카테고리)

2단계: 전체 분류
  299k 클립 캡션 → GPT-4o-mini → 카테고리 할당

3단계: AIDE 방식 반복 루프
  희귀 카테고리 식별 → 수집 처방 → 신규 데이터 추가 → 재분류
```

#### 결과 형태

| 카테고리 ID | 시나리오 이름 | 클립 수 | 비율 | 상태 |
|-----------|------------|--------|------|------|
| M01 | "교차로 직진 보행자 횡단 — 맑은 낮" | 42,180 | 14.1% | 포화 |
| R01 | "안개 야간 고속도로" | 890 | 0.3% | **부족** |
| R02 | "적설 결빙 노면" | 340 | 0.1% | **매우 부족** |
| V03 | "어린이/노인 보행자" | 120 | 0.04% | **심각하게 부족** |

**비용 추정**: ~$5~10

---

### 3-4. 의미론적 Normalizing Flow (SANFlow 방식)

**현재 NF 방식을 폐기하지 않고 문제 B(역변환 불가)를 구조적으로 해결하는 방법이다.**

#### 학술적 근거

NeurIPS 2023 "SANFlow: Semantic-Aware Normalizing Flow for Anomaly Detection"[R6]은 표준 NF가 모든 임베딩 위치에 동일한 단위 정규분포를 강제 적용하여 **의미론적 정보가 소실**됨을 지적한다. SANFlow는 이미지의 위치별(여기서는 시나리오 속성별)로 **다른 base distribution을 부여**하여 semantic-aware density estimation을 실현한다.

표준 NF:
```
모든 ODD 속성 → 단위 정규분포 N(0, I)
→ 갭 위치가 어떤 속성과 연결되는지 추적 불가
```

SANFlow 방식:
```
fog 클러스터 → N(μ_fog, Σ_fog)
rain 클러스터 → N(μ_rain, Σ_rain)
night 클러스터 → N(μ_night, Σ_night)
→ 갭 위치 → 가장 가까운 속성 분포 → 시나리오 설명 역추적 가능
```

#### 이 프로젝트 적용 방식

1. 3-1의 HDBSCAN 클러스터 결과를 base distribution의 사전으로 사용
2. 각 클러스터(시나리오 레이블)마다 별도의 Gaussian을 할당
3. NF가 탐지한 갭 좌표 → 가장 가까운 클러스터 분포 → 시나리오 이름으로 역변환

```
NF 갭 탐지 결과:
  [0.08, 0.18] × [0.72, 0.90] × [0.05, 0.20] ...
      │
      ▼  SANFlow base distribution 역추적
  가장 가까운 클러스터: "안개 + 야간 + 고속도로" (클러스터 #47)
      │
      ▼
  "클러스터 #47의 커버리지가 낮음 → 수집 필요"
```

**이 방법은 현재 EXP-002 Phase 3 (Axis C)를 폐기하지 않고 역변환 가능성을 추가한다.**

---

### 3-5. 그래프 기반 씬 커버리지 분석

**에이전트 간 인과적 상호작용 패턴을 포착하는 유일한 방법이다.**

#### 학술적 근거

CVPR 2025 "T2SG: Traffic Topology Scene Graph for Topology Reasoning"[R11]은 교통 시나리오를 차선 노드 + 연결 관계 엣지의 위상 그래프로 표현한다. 7D 스칼라 ODD 벡터로는 표현 불가능한 에이전트-도로 위상 구조를 인간이 해석 가능한 형태로 제공한다.

**현재 접근이 포착하지 못하는 것**:
- "ego 차량 앞 2번째 차량이 급제동하고, 1번째 차량이 이에 반응하는 상황"
- "보행자가 신호 없이 횡단하고 ego가 인지 후 회피하는 인과 체인"

이런 **에이전트 간 인과적 상호작용 패턴**은 7D 스칼라 ODD 벡터로 표현할 수 없다.

#### 이 프로젝트 적용 시 필요한 추가 작업

```
캡션 텍스트
    │
    ▼  LLM 씬 그래프 추출 (GPT-4o-mini)
{
  "ego": {"action": "braking", "speed": "medium"},
  "agent_1": {"type": "truck", "relation": "leading", "behavior": "cutting_in"},
  "agent_2": {"type": "pedestrian", "relation": "crossing_right"},
  "condition": {"weather": "fog", "road": "highway", "time": "night"}
}
    │
    ▼  그래프 구성 + 클러스터링
[씬 토폴로지 커버리지 보고서]
```

**비용 추정**: LLM 그래프 추출 10만 개 ~ $10~20, 클러스터링 ~ 수십 분

---

### 3-6. 갭 시나리오 생성으로 커버리지 보완

**커버리지 분석 이후 단계 — 갭을 실제 수집이 아닌 합성 데이터로 보완하는 방법이다.**

#### 학술적 근거 (검증된 CVPR 논문)

- **CVPR 2021 "AdvSim"**[R12]: 기존 실제 로그의 에이전트 궤적을 물리적으로 타당하게 변조해 안전 위험 시나리오를 대규모 자동 생성한다.
- **CVPR 2023 "UniSim"**[R13]: 단일 실제 주행 로그를 신경망 기반 센서 시뮬레이터로 변환하여 행위자 추가/재배치, 반사실적 희귀 시나리오를 리얼리스틱 데이터로 생성한다.
- **CVPR 2024 "ChatScene"**[R14]: LLM이 자연어 시나리오 기술 → CARLA 시뮬레이션 코드로 자동 변환한다.
- **CVPR 2025 "Scenario Dreamer"**[R15]: 벡터화된 씬 요소(차선 그래프 + 에이전트 바운딩 박스)를 잠재 확산 모델로 생성한다. 잠재 공간의 각 차원이 씬 구성 요소에 대응하므로 역변환이 가능하다.

#### 활용 방식 (이 프로젝트 적용)

1. 3-1(임베딩 클러스터링) 또는 3-2(ODD 매트릭스)로 **갭 시나리오 식별**
2. 갭 시나리오를 자연어로 기술 → **ChatScene**으로 CARLA 시뮬레이션 생성
3. **UniSim**으로 기존 클립 로그를 반사실적으로 변조하여 희귀 씬 추가

| 시나리오 | 실제 수집 난이도 | 합성 대체 방법 |
|---------|--------------|------------|
| "안개 야간 고속도로 역주행 차량" | 매우 높음 | UniSim 반사실 변조 |
| "폭설 중 어린이 돌발 횡단" | 높음 | ChatScene → CARLA |
| "교량 위 결빙 노면 다중 충돌" | 매우 높음 | Scenario Dreamer 생성 |

---

## 4. 방법별 종합 비교

| 방법 | 갭 해석성 | 수집 처방 | 에이전트 상호작용 | 즉시 적용 | 비용 | 신뢰성 | 학술 근거 |
|------|---------|---------|----------------|---------|------|--------|---------|
| **현재: NF 7D 수치 ODD** | 낮음 | 어려움 | ✗ | ✅ | ~$6 | 낮음 | 없음 |
| **3-2. ODD 커버리지 매트릭스** | 높음 | 쉬움 | ✗ | ✅ 즉시 | 무료 | 중간 | ICLR 2023 [R8] |
| **3-1. 임베딩 클러스터링 + LLM** | 매우 높음 | 매우 쉬움 | 부분적 | ✅ ~20분 | ~$0.50 | 높음 | NeurIPS 2023/2024 [R4][R5] |
| **3-3. LLM 직접 시나리오 분류** | 최고 | 최고 | ✗ | 부분적 | ~$10 | 높음 | CVPR 2024 [R10], NeurIPS 2023 [R3] |
| **3-4. SANFlow 의미론적 NF** | 높음 | 높음 | ✗ | 구현 필요 | 무료 | 매우 높음 | NeurIPS 2023 [R6] |
| **3-5. 그래프 기반 씬 커버리지** | 매우 높음 | 높음 | ✅ | 구현 필요 | 중간 | 매우 높음 | CVPR 2025 [R11] |
| **3-6. 갭 시나리오 생성** | — | 완전 자동 | ✅ | 구현 필요 | 높음 | 높음 | CVPR 2021/2023/2024/2025 [R12~R15] |

### 핵심 결론

> **NF 방식의 근본 한계는 정확도 문제가 아니라 설계 문제다 [R6].**
> 표준 NF는 모든 임베딩 위치에 동일한 단위 정규분포를 강제하여 의미론적 구조를 소실한다.
> SANFlow 방식으로 클러스터별 base distribution을 주입하면 갭-시나리오 역변환이 가능해진다.
> 임베딩 클러스터링은 클러스터 자체가 시나리오 레이블이므로 역변환 단계가 불필요하다.

---

## 5. 수정된 실험 우선순위 로드맵

> **기존 로드맵 대비 핵심 변경 사항**
> - Phase A에 Metric Space Magnitude 기반 다양성 측정을 추가 (NeurIPS 2024 [R5])
> - Phase B에서 SANFlow 방식 NF로 교체하여 역변환 가능성 확보 (NeurIPS 2023 [R6])
> - Phase C에 ChatScene / UniSim 기반 갭 시나리오 생성 추가 (CVPR 2024/2023 [R14][R13])
> - LLM refinement ($5) 보류 결정 유지 — 대신 임베딩 클러스터링으로 대체

### Phase A: 즉시 실행 (비용 최소, 1일 이내) ← 최우선

```
[AM] ODD 커버리지 매트릭스 계산 (3-2)
  - 입력: data/tags/odd_tags.json (이미 존재)
  - 코드: 약 20줄 Python
  - 출력: 희귀 (weather × time × road × hazard) 조합 목록
  - 근거: ICLR 2023 distribution cover 개념 [R8]

[PM-1] HDBSCAN 클러스터링 (3-1)
  - 입력: data/active/hnsw.index (이미 존재)
  - 코드: ~50줄 (faiss → numpy → PCA → UMAP → HDBSCAN)
  - 출력: 클러스터 크기 분포 + noise point 목록

[PM-2] Metric Space Magnitude 계산 (3-1 확장)
  - 입력: HDBSCAN 클러스터별 임베딩 부분집합
  - 출력: 클러스터별 diversity 점수 → 수집 우선순위 근거
  - 근거: NeurIPS 2024 [R5]

[PM-3] LLM 레이블링 (하위 50개 클러스터 캡션 → GPT-4o-mini)
  - 비용: ~$0.50
  - 출력: 클러스터별 자연어 시나리오 이름
```

### Phase B: 단기 (3~5일) ← 기존 Phase 2/3 대체

```
[Day 2-3] SANFlow 방식 NF 재설계 (3-4)
  목표: 표준 NF → 의미론적 NF로 교체
  방법:
    1. Phase A 클러스터 결과를 base distribution 사전으로 로드
    2. 각 클러스터에 Gaussian(μ_k, Σ_k) 할당
    3. NF 학습 (기존 fit_normalizing_flow.py 수정)
    4. 갭 탐지 후 → 클러스터 역추적 → 시나리오 이름 출력
  근거: NeurIPS 2023 SANFlow [R6]

[Day 4-5] LLM 직접 시나리오 분류체계 구축 (3-3)
  - 캡션 1,000개 샘플 → GPT-4o → 분류체계 설계
  - ScenarioNet의 26가지 분류 참고 [R3]
  - 전체 299k 분류 → 카테고리별 클립 수
  - AIDE 반복 루프 적용 [R10]
```

### Phase C: 중기 (1~2주) ← 기존 Phase C 확장

```
[Week 1] 그래프 기반 씬 구조 추출 파일럿 (3-5)
  - 10,000개 캡션 → LLM 씬 그래프 추출
  - T2SG 방식 위상 그래프 클러스터링 [R11]
  - FEND 방식 대조 학습으로 롱테일 클러스터 강화 [R16]

[Week 2] 전체 평가 보고서
  - Phase A: ODD 매트릭스 + 임베딩 다양성
  - Phase B: SANFlow NF 갭 탐지 결과 (시나리오 이름 포함)
  - Phase B: LLM 분류체계 커버리지 보고서
  비교: 기존 7D 좌표 갭 vs. 시나리오 이름 갭 표현 비교
```

### Phase D: 장기 (1~3개월) ← 신규 추가

```
[Month 1] 갭 시나리오 합성 데이터 생성 파이프라인 (3-6)
  - ChatScene: LLM → CARLA 시뮬레이션 자동화 [R14]
  - UniSim: 기존 로그 반사실적 변조 [R13]

[Month 2-3] 전체 그래프 기반 커버리지 분석
  - Scenario Dreamer 방식 벡터 잠재 확산 모델 [R15]
  - 합성 데이터로 희귀 씬 커버리지 보완 검증
```

---

## 6. EXP-002 기존 파이프라인 계속 여부 판단 (개정)

| 단계 | 판단 | 근거 |
|------|------|------|
| Phase 1 (Axis A) | **계속 진행** | 검색 품질 평가는 여전히 유효 |
| Phase 2 Step 2-1 (Regex → 7D) | **계속 진행 (참고용)** | 무료이며 ODD 매트릭스 입력으로 재활용 가능 |
| Phase 2 Step 2-2 (LLM $5) | **보류** | 임베딩 클러스터링이 더 저렴($0.50)하고 신뢰성 높음 |
| Phase 3 (표준 NF 학습) | **SANFlow 방식으로 교체** | 표준 NF는 역변환 불가 — 의미론적 base distribution 주입 필요 [R6] |
| 갭 탐지 후 역변환 | **Phase B SANFlow로 해결** | 7D 좌표 → 클러스터 역추적 → 시나리오 이름 |

---

## 7. 참고 문헌

### CVPR (CVF Open Access 확인)

[R12] J. Wang, A. Pun, J. Tu, S. Manivasagam, A. Sadat, S. Casas, M. Ren, R. Urtasun,
"AdvSim: Generating Safety-Critical Scenarios for Self-Driving Vehicles,"
*CVPR 2021.* https://openaccess.thecvf.com/content/CVPR2021/papers/Wang_AdvSim_Generating_Safety-Critical_Scenarios_for_Self-Driving_Vehicles_CVPR_2021_paper.pdf

[R16] Y. Wang, P. Zhang, L. Bai, J. Xue,
"FEND: A Future Enhanced Distribution-Aware Contrastive Learning Framework for Long-Tail Trajectory Prediction,"
*CVPR 2023.* https://openaccess.thecvf.com/content/CVPR2023/html/Wang_FEND_A_Future_Enhanced_Distribution-Aware_Contrastive_Learning_Framework_for_Long-Tail_CVPR_2023_paper.html

[R13] Z. Yang, Y. Chen, J. Wang, S. Manivasagam, W.-C. Ma, A. J. Yang, R. Urtasun,
"UniSim: A Neural Closed-Loop Sensor Simulator,"
*CVPR 2023.* https://openaccess.thecvf.com/content/CVPR2023/html/Yang_UniSim_A_Neural_Closed-Loop_Sensor_Simulator_CVPR_2023_paper.html

[R10] M. Liang, J.-C. Su, S. Schulter, S. Garg, S. Zhao, Y. Wu, M. Chandraker,
"AIDE: An Automatic Data Engine for Object Detection in Autonomous Driving,"
*CVPR 2024.* https://openaccess.thecvf.com/content/CVPR2024/html/Liang_AIDE_An_Automatic_Data_Engine_for_Object_Detection_in_Autonomous_CVPR_2024_paper.html

[R14] J. Zhang, C. Xu, B. Li,
"ChatScene: Knowledge-Enabled Safety-Critical Scenario Generation for Autonomous Vehicles,"
*CVPR 2024.* https://cvpr.thecvf.com/virtual/2024/poster/29457

[R11] C. Lv, M. Qi, L. Liu, H. Ma,
"T2SG: Traffic Topology Scene Graph for Topology Reasoning in Autonomous Driving,"
*CVPR 2025.* https://openaccess.thecvf.com/content/CVPR2025/papers/Lv_T2SG_Traffic_Topology_Scene_Graph_for_Topology_Reasoning_in_Autonomous_CVPR_2025_paper.pdf

[R15] L. Rowe, R. Girgis, A. Gosselin, L. Paull, C. Pal, F. Heide,
"Scenario Dreamer: Vectorized Latent Diffusion for Generating Driving Simulation Environments,"
*CVPR 2025.* https://openaccess.thecvf.com/content/CVPR2025/papers/Rowe_Scenario_Dreamer_Vectorized_Latent_Diffusion_for_Generating_Driving_Simulation_Environments_CVPR_2025_paper.pdf

### NeurIPS (proceedings.neurips.cc 확인)

[R3] Q. Li, Z. Peng, L. Feng, Z. Liu, C. Duan, W. Mo, B. Zhou,
"ScenarioNet: Open-Source Platform for Large-Scale Traffic Scenario Simulation and Modeling,"
*NeurIPS 2023 (Datasets & Benchmarks Track).* https://proceedings.neurips.cc/paper_files/paper/2023/hash/0c26a501df8fb919a0350e2df06b5d39-Abstract-Datasets_and_Benchmarks.html

[R4] P. J. Kim, Y. Jang, J. Kim, J. Yoo,
"TopP&R: Robust Support Estimation Approach for Evaluating Fidelity and Diversity in Generative Models,"
*NeurIPS 2023.* https://proceedings.neurips.cc/paper_files/paper/2023/hash/185969291540b3cd86e70c51e8af5d08-Abstract-Conference.html

[R6] D. Kim, S. Baik, T. H. Kim,
"SANFlow: Semantic-Aware Normalizing Flow for Anomaly Detection and Localization,"
*NeurIPS 2023.* https://proceedings.neurips.cc/paper_files/paper/2023/hash/ee74a6ade401e200985e2421b20bbae4-Abstract-Conference.html

[R5] K. Limbeck, R. Andreeva, R. Sarkar, B. Rieck,
"Metric Space Magnitude for Evaluating the Diversity of Latent Representations,"
*NeurIPS 2024.* https://proceedings.neurips.cc/paper_files/paper/2024/file/dfc24bd3ec5d74960e104268bbb52849-Paper-Conference.pdf

[R9] W. Huang, H. Wang, J. Xia, C. Wang, J. Zhang,
"Density-driven Regularization for Out-of-distribution Detection,"
*NeurIPS 2022.* https://proceedings.neurips.cc/paper_files/paper/2022/hash/05b69cc4c8ff6e24c5de1ecd27223d37-Abstract-Conference.html

### ICML (proceedings.mlr.press 확인)

[R7] D. Zhao, J. Andrews, O. Papakyriakopoulos, A. Xiang,
"Measure Dataset Diversity, Don't Just Claim It,"
*ICML 2024 (Best Paper Award, Oral).* https://proceedings.mlr.press/v235/zhao24a.html

[R17] S. Shirahmad Gale Bagi, Z. Gharaee, O. Schulte, M. Crowley,
"Generative Causal Representation Learning for Out-of-Distribution Motion Forecasting,"
*ICML 2023.* https://proceedings.mlr.press/v202/shirahmad-gale-bagi23a.html

### ICLR (openreview.net 확인)

[R8] H. Zheng, R. Liu, F. Lai, A. Prakash,
"Coverage-centric Coreset Selection for High Pruning Rates,"
*ICLR 2023.* https://openreview.net/forum?id=QwKvL6wC8Yi

---

*이 문서는 2026-06-04 CVPR / NeurIPS / ICML / ICLR 논문 검증 결과를 반영하여 개정되었다.*
*각 대안 기술은 현재 인프라(bge-m3 임베딩, odd_tags.json)를 최대한 재사용하는 방향으로 설계되었다.*
