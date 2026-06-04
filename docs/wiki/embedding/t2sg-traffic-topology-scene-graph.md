# T2SG — 자율주행 위상 추론을 위한 교통 토폴로지 씬 그래프

## 출처
- **저자**: C. Lv, M. Qi, L. Liu, H. Ma
- **연도**: 2025
- **학술대회**: CVPR 2025
- **파일**: `literature/papers/R11_T2SG_CVPR2025.pdf`

---

## 핵심 아이디어

교통 시나리오를 **차선 노드 + 연결 관계 엣지의 위상 그래프**로 표현한다. 7D 스칼라 ODD 벡터로는 표현 불가능한 **에이전트-도로 위상 구조**를 인간이 해석 가능한 형태로 제공한다.

### 그래프 구조

```
노드 (Node):
  - 차선 세그먼트 (시작점, 끝점, 방향, 속도 제한)
  - 에이전트 (위치, 속도, 가속도, 유형)
  - 도로 인프라 (신호등, 정지선, 횡단보도)

엣지 (Edge):
  - 차선 연결 (predecessor, successor, left, right)
  - 에이전트-차선 점유 관계
  - 에이전트 간 상호작용 (following, yielding, overtaking)
```

### 7D ODD 스칼라로 불가능한 표현

```
7D 스칼라 벡터 방식의 한계:
  {"visibility": 0.12, "traffic_density": 0.85, ...}
  → 에이전트 간 인과적 상호작용 표현 불가

T2SG 방식:
  ego → (거리 15m, 속도 90) → leading_car
  leading_car → (emergency_brake) → ego → (avoid_collision) → ...
  → "앞차 급제동 → 1번째 차량 인지 → 회피 기동" 인과 체인 표현 가능
```

### 위상 추론 응용

- 차선 변경 가능성 예측
- 에이전트 의도 추론 (교차로 진입 방향)
- 교통 규칙 준수 여부 판단

---

## 장단점

**장점**
- 에이전트 간 인과적 상호작용 패턴 포착 (7D 벡터 불가 영역)
- 그래프 클러스터링으로 씬 토폴로지 패턴 분류 가능
- 인간이 해석 가능한 구조적 표현

**단점**
- HD Map 데이터 필요
- 캡션 텍스트 → 씬 그래프 변환에 LLM 추론 필요 (추가 비용)
- 그래프 학습/클러스터링 파이프라인 구축 필요

---

## 프로젝트 적용 포인트

### Gap-3 → EXP-002 Phase C

캡션 텍스트에서 LLM으로 씬 그래프를 추출하여 위상 커버리지 분석:

```python
# 캡션 → LLM → 씬 그래프 추출
scene_graph_prompt = """
다음 주행 캡션에서 씬 그래프를 JSON으로 추출하라:
{
  "ego": {"action": str, "speed": str},
  "agents": [{"type": str, "relation": str, "behavior": str}],
  "road": {"type": str, "lanes": int},
  "condition": {"weather": str, "time": str}
}
"""

# 10,000개 파일럿 (EXP-002 Phase C)
scene_graphs = [extract_graph(caption) for caption in sample_captions]

# T2SG 방식 위상 그래프 클러스터링
graph_embeddings = encode_graphs(scene_graphs)  # GNN 또는 LLM 임베딩
topology_clusters = hdbscan.fit(graph_embeddings)
```

비용 추정: GPT-4o-mini 10,000개 → ~$1

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-3 | 에이전트 상호작용 패턴 포착 → ODD 커버리지 분석 확장 |

## 관련 실험
- EXP-002: Phase C [Week 1] — 씬 그래프 추출 파일럿 (10,000개 캡션)
