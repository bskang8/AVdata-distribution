# LLM 기반 OOD 시나리오 생성 (Diverse Tree)

## 출처
- **저자**: Aasi, Nguyen, Sreeram, Rosman, Karaman, Rus (MIT CSAIL / TRI)
- **연도**: 2024
- **학술대회**: arXiv:2411.16554 (ICRA급)
- **파일**: `literature/papers/aasi-2024-generating-out-of-distribution-scenarios.pdf`

---

## 핵심 아이디어

GPT-4o + Few-shot Chain-of-Thought로 OOD 시나리오를 **트리 구조**로 생성한다.  
각 트리 경로(root → leaf)가 하나의 유일한 OOD 시나리오를 정의한다.

### 3단계 파이프라인

1. **Tree-LLM**: Initial tree 생성 (40 nodes, CoT prompting)
2. **Red-LLM**: 100회 반복 red-teaming으로 Diverse tree로 확장 (77 nodes)
3. **Augmenter-LLM**: CARLA 시뮬레이터 자동화 (시뮬레이터 제약 → Simulatable tree, 22 nodes)

### OOD 분류 체계

| 대분류 | 예시 |
|--------|------|
| Environmental | 짙은 안개, 폭우, 노면 장애물, 공사 구역 |
| Interactional | 갑작스러운 보행자 횡단, 역주행 차량, 돌발 경찰 검문 |

### 평가 메트릭

- **OOD-ness**: 생성 시나리오 임베딩과 nuScenes baseline 임베딩 간 최소 코사인 유사도 (낮을수록 OOD)
- **Diversity**: self-similarity score의 음수값 (높을수록 다양)

| Dataset | OOD-ness | Diversity |
|---------|----------|-----------|
| nuScenes baseline | -0.953 | -0.781 |
| Ours-100 | -0.691 | -0.638 |
| Ours-simulatable | -0.765 | -0.762 |

---

## 장단점

**장점**
- 기존 데이터에 없는 희귀 시나리오를 체계적으로 생성
- 텍스트 기반이라 시뮬레이터 없이도 시나리오 카탈로그 구축 가능
- OOD-ness threshold로 현실성 조절 가능

**단점**
- CARLA 시뮬레이터 자산 제약으로 77 → 22 nodes로 축소
- VLM들의 safe control action 성공률이 낮음 (GPT-4o: 66%, Claude: 50%)
- 텍스트-시뮬레이션 매핑이 LLM 오류에 취약

---

## 프로젝트 적용 포인트

### Gap-4 (분포 편향) 직결
현재 83k 캡션의 OOD-ness를 측정하는 데 **aasi et al.의 코사인 임베딩 메트릭**을 그대로 차용 가능.

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')

# nuScenes baseline 임베딩 구축 후
# 각 clip caption의 OOD-ness 계산
ood_score = min(cosine_similarity(clip_emb, baseline_embs))
```

### Gap-3 (ODD 커버리지) 보완
- Aasi의 **Environmental/Interactional 분류 체계**를 현재 ODD taxonomy에 추가
- LLM tree 기반 쿼리 생성으로 현재 캡션 검색 시스템 테스트 가능

### 아이디어: LLM 쿼리 자동 생성
Aasi의 diverse tree를 참조하여 검색 쿼리를 자동 생성 → EXP-006 후보

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-3 | ODD taxonomy 확장 참조 |
| Gap-4 | OOD-ness 메트릭으로 데이터 분포 편향 측정 |

## 관련 실험
- EXP-003 (분포 분석): OOD-ness 스코어를 UMAP KDE와 함께 활용 검토
