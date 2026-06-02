# 문헌 & 자료 링크

논문은 `literature/papers/`에 PDF로 저장하고, URL 자료는 여기에 기록한다.  
새 자료 추가 후 위키 파일을 생성하고 `docs/wiki/INDEX.md`에 반영한다.

---

## 형식

```
## [제목]
- **출처**: [저자, 연도, 학술대회]
- **파일**: literature/papers/파일명.pdf
- **관련 갭**: Gap-X
- **핵심 아이디어**: 한 줄 요약
- **위키 파일**: docs/wiki/카테고리/파일명.md
```

---

## 등록된 논문

### (2025) — NF vs KDE: ADS 리스크 정량화 밀도 추정 비교
- **출처**: (SYNERGIES project, Horizon Europe) — IEEE IAVVC 2025
- **파일**: `literature/papers/comparing-2025-normalizing-flows-kde-ads-risk.pdf`
- **관련 갭**: Gap-3, Gap-4
- **핵심 아이디어**: NF가 고차원 ADS 리스크 공간에서 KDE보다 희소 구간 밀도 추정 정밀도 향상; curse of dimensionality에 강건
- **위키 파일**: `docs/wiki/data_distribution/normalizing-flow-kde-ads-risk.md`

---

### Aasi et al. (2024) — LLM 기반 OOD 시나리오 생성
- **출처**: Aasi, Nguyen, Sreeram, Rosman, Karaman, Rus — MIT CSAIL / TRI — arXiv 2024
- **파일**: `literature/papers/aasi-2024-generating-out-of-distribution-scenarios.pdf`
- **관련 갭**: Gap-3, Gap-4
- **핵심 아이디어**: GPT-4o + CoT로 OOD 시나리오 트리를 생성; OOD-ness / Diversity 메트릭 제안
- **위키 파일**: `docs/wiki/scenario_generation/llm-ood-generation.md`

---

### Chodowiec et al. (2026) — ODD & 행동 기반 시나리오 커버리지
- **출처**: Chodowiec, Irvine, Tiele, Takenaka, Zhang, Khastgir, Jennings — Univ. Warwick / DENSO — IEEE Access 2026
- **파일**: `literature/papers/chodowiec-2026-odd-behaviour-scenario-coverage.pdf`
- **관련 갭**: Gap-1, Gap-3
- **핵심 아이디어**: 4가지 커버리지 타입(Attribute Range / ODD&Behaviour / Out-of-ODD / Rules of Road) 프레임워크
- **위키 파일**: `docs/wiki/evaluation/odd-coverage-framework.md`

---

### Dimlioglu et al. (2026) — 스케일링 인식 데이터 선택 (MOSAIC)
- **출처**: Dimlioglu, Chang, Shen, Mahmood, Alvarez — NYU / NVIDIA — arXiv 2026
- **파일**: `literature/papers/dimlioglu-2026-scaling-aware-data-selection.pdf`
- **관련 갭**: Gap-4
- **핵심 아이디어**: 클러스터링 + 스케일링 법칙 추정 + 반복 마이닝으로 80% 효율적 데이터 선택
- **위키 파일**: `docs/wiki/data_distribution/mosaic-data-selection.md`

---

### Herd & Burton (2024) — ML 메트릭 불확실성 (Subjective Logic)
- **출처**: Herd, Burton — Fraunhofer IKS — ACM SAC '24
- **파일**: `literature/papers/herd-2024-can-you-trust-your.pdf`
- **관련 갭**: Gap-1
- **핵심 아이디어**: Subjective Logic으로 Recall 등 ML 메트릭을 Beta 분포로 표현; trust discounting으로 불확실성 전파
- **위키 파일**: `docs/wiki/evaluation/subjective-logic-ml-metrics.md`

---

### Li et al. (2026) — Physics-guided Causal Model (PCM): 인과 장면 인코더
- **출처**: Li et al. — arXiv 2026 (cs.AI)
- **파일**: `literature/papers/li-2026-physics-guided-causal-trajectory.pdf`
- **관련 갭**: Gap-1, Gap-3
- **핵심 아이디어**: Intervention-based disentanglement으로 도메인 불변 인과 피처 추출; CausalODE Decoder로 물리 법칙 통합; zero-shot 일반화
- **위키 파일**: `docs/wiki/embedding/physics-guided-causal-scene-encoder.md`

---

### Lu et al. (2024) — Safety-aware Causal Transformer (CEWM)
- **출처**: Lu et al. — arXiv 2024 (cs.LG / cs.AI)
- **파일**: `literature/papers/lu-2024-safety-aware-causal-representation.pdf`
- **관련 갭**: Gap-1, Gap-2
- **핵심 아이디어**: Causal mask로 state→reward / state→cost 인과 경로 분리; spurious correlation 제거로 안전한 Offline RL 정책 학습
- **위키 파일**: `docs/wiki/embedding/safety-aware-causal-transformer.md`

---

### Naumann et al. (2025) — E2E AV 데이터 스케일링 법칙
- **출처**: Naumann, Gu, Dimlioglu, Bojarski et al. — NVIDIA / Toronto / NYU — CVPR Workshop 2025
- **파일**: `literature/papers/naumann-2025-data-scaling-laws-end-to-end.pdf`
- **관련 갭**: Gap-4
- **핵심 아이디어**: 16h~8192h 규모에서 멱함수 스케일링 확인; open-loop ≠ closed-loop; ResNet-50이 63% 적은 데이터로 동일 성능
- **위키 파일**: `docs/wiki/data_distribution/scaling-laws-e2e-nvidia.md`

---

### Rivera et al. (2025) — LVLM 기반 씬 이해 (CatPipe)
- **출처**: Rivera, Lübberstedt, Uhlemann, Lienkamp — TU Munich — WACV Workshop 2025
- **파일**: `literature/papers/rivera-2025-scenario-understanding-traffic-scenes.pdf`
- **관련 갭**: Gap-3, Gap-6
- **핵심 아이디어**: GPT-4/LLaVA로 16개 카테고리 zero-shot 씬 자동 분류; 3단계 프롬프트 엔지니어링
- **위키 파일**: `docs/wiki/tagging/lvlm-scene-tagging-catpipe.md`

---

### Schleiss et al. (2022) — DL 안전 인식 정량 검증 (μODD)
- **출처**: Schleiss, Hagiwara, Kurzidem, Carella — Fraunhofer IKS — IEEE ISSREW 2022
- **파일**: `literature/papers/schleiss-2022-towards-quantitative-verification-deep.pdf`
- **관련 갭**: Gap-1, Gap-3
- **핵심 아이디어**: μODD로 ODD를 세분화하고 리스크별 테스트 커버리지 목표 설정; SIL 기반 신뢰도 계산
- **위키 파일**: `docs/wiki/evaluation/muodd-quantitative-verification.md`

---

### (2024) — TrimFlow: NF 기반 AV 희귀 사건 중요도 샘플링
- **출처**: arXiv 2024
- **파일**: `literature/papers/trimflow-2024-normalizing-flow-rare-event-av.pdf`
- **관련 갭**: Gap-4, Gap-6
- **핵심 아이디어**: NF + Temporal Importance Sampling으로 위험 희귀 사건 분포 학습; 86.1% 적은 시뮬레이션으로 동일 검증 수준
- **위키 파일**: `docs/wiki/data_distribution/trimflow-rare-event-sampling.md`

---

### Song et al. (2022) — TTC 기반 시나리오 분포 모델
- **출처**: Song, Runeson, Persson — Lund University / Volvo Cars — ASE '22
- **파일**: `literature/papers/song-2022-a-scenario-distribution-model.pdf`
- **관련 갭**: Gap-4, Gap-6
- **핵심 아이디어**: Poisson 분포로 차량-보행자 TTC 분포 예측; worst-case 모델로 critical 시나리오 테스트 할당 최적화
- **위키 파일**: `docs/wiki/data_distribution/ttc-scenario-distribution.md`

---

### Xu et al. (2025) — WOD-E2E: 롱테일 E2E 데이터셋 (Waymo)
- **출처**: Xu, Lin, Jeon, Feng et al. — Waymo LLC — arXiv 2025
- **파일**: `literature/papers/xu-2025-wod-e2e-waymo-open-dataset.pdf`
- **관련 갭**: Gap-4, Gap-1
- **핵심 아이디어**: 4,021개 롱테일 세그먼트(<0.03% 빈도), 11개 클러스터; RFS(Rater Feedback Score) 평가 지표 제안
- **위키 파일**: `docs/wiki/data_distribution/wod-e2e-longtail-dataset.md`

---

### Zheng et al. (2025) — 모방 학습 E2E 스케일링 법칙 (ONE-Drive)
- **출처**: Zheng, Yang, Xia, Zhang et al. — CASIA / Li Auto — arXiv 2025
- **파일**: `literature/papers/zheng-2025-data-scaling-laws-imitation.pdf`
- **관련 갭**: Gap-4, Gap-6
- **핵심 아이디어**: 4M 시연 × 23개 유형 분석; 멱함수 법칙 확인; **분포가 양보다 중요**; 소량 롱테일이 큰 성능 향상
- **위키 파일**: `docs/wiki/data_distribution/imitation-learning-scaling-laws.md`

---

## 참고할 자료 후보

| 주제 | 자료명 | 관련 갭 | 우선순위 |
|------|--------|--------|---------|
| LLM 기반 relevance labeling | "Large Language Models are Zero-Shot Rankers for Recommender Systems" | Gap-1 | 🔴 High |
| Semantic evaluation of retrieval | BEIR Benchmark (Thakur et al., 2021) | Gap-1, Gap-6 | 🔴 High |
| Hybrid search 개선 | "Hybrid Search with BM25 and Dense Retrieval" | Gap-2 | 🟠 High |
| 벡터 DB 스케일 | Milvus GPU_CAGRA | 장기 | 🟡 Medium |
| ODD 온톨로지 표준 | ISO 34503 공식 문서 | Gap-3 | 🔴 High |
