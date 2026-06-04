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

---

### Kim et al. (2023) — TopP&R: 임베딩 공간 Fidelity & Diversity 측정
- **출처**: P. J. Kim, Y. Jang, J. Kim, J. Yoo — NeurIPS 2023
- **URL**: https://proceedings.neurips.cc/paper_files/paper/2023/file/185969291540b3cd86e70c51e8af5d08-Paper-Conference.pdf
- **파일**: `literature/papers/R4_TopPR_NeurIPS2023.pdf`
- **관련 갭**: Gap-3, Gap-4
- **핵심 아이디어**: KDE 기반 지지도 추정으로 데이터셋의 Fidelity(커버리지)와 Diversity(다양성)를 분리 측정
- **위키 파일**: `docs/wiki/evaluation/topp-r-fidelity-diversity-metrics.md`

---

### Limbeck et al. (2024) — Metric Space Magnitude: 잠재 표현 다양성
- **출처**: K. Limbeck, R. Andreeva, R. Sarkar, B. Rieck — NeurIPS 2024
- **URL**: https://proceedings.neurips.cc/paper_files/paper/2024/file/dfc24bd3ec5d74960e104268bbb52849-Paper-Conference.pdf
- **파일**: `literature/papers/R5_MetricSpaceMagnitude_NeurIPS2024.pdf`
- **관련 갭**: Gap-3, Gap-4
- **핵심 아이디어**: 위상수학 Magnitude로 latent representation diversity를 multi-scale, provably stable하게 측정
- **위키 파일**: `docs/wiki/evaluation/metric-space-magnitude-diversity.md`

---

### Kim et al. (2023) — SANFlow: 의미론적 Normalizing Flow 이상 탐지
- **출처**: D. Kim, S. Baik, T. H. Kim — NeurIPS 2023
- **URL**: https://proceedings.neurips.cc/paper_files/paper/2023/file/ee74a6ade401e200985e2421b20bbae4-Paper-Conference.pdf
- **파일**: `literature/papers/R6_SANFlow_NeurIPS2023.pdf`
- **관련 갭**: Gap-3, Gap-4
- **핵심 아이디어**: 위치별 별도 base distribution 부여로 의미론적 NF 실현 — 갭 탐지 결과 시나리오 이름으로 역변환 가능
- **위키 파일**: `docs/wiki/data_distribution/sanflow-semantic-normalizing-flow.md`

---

### Zhao et al. (2024) — Measure Dataset Diversity, Don't Just Claim It
- **출처**: D. Zhao, J. Andrews, O. Papakyriakopoulos, A. Xiang — ICML 2024 (Best Paper Award)
- **URL**: https://raw.githubusercontent.com/mlresearch/v235/main/assets/zhao24a/zhao24a.pdf
- **파일**: `literature/papers/R7_MeasureDatasetDiversity_ICML2024.pdf`
- **관련 갭**: Gap-3, Gap-4
- **핵심 아이디어**: 135개 데이터셋 분석 — "diversity" 선언이 근거 없이 남용됨. 측정 이론 기반 정량화 원칙 제시
- **위키 파일**: `docs/wiki/evaluation/measure-dataset-diversity.md`

---

### Zheng et al. (2023) — Coverage-centric Coreset Selection
- **출처**: H. Zheng, R. Liu, F. Lai, A. Prakash — ICLR 2023
- **URL**: https://openreview.net/pdf?id=QwKvL6wC8Yi
- **파일**: `literature/papers/R8_CoverageCoreset_ICLR2023.pdf`
- **관련 갭**: Gap-3, Gap-4
- **핵심 아이디어**: 데이터 커버리지를 기하학적 set cover 문제로 정의 — 이산 ODD 조합 기반 직접 측정
- **위키 파일**: `docs/wiki/data_distribution/coverage-centric-coreset-selection.md`

---

### Huang et al. (2022) — Density-driven Regularization for OOD Detection
- **출처**: W. Huang, H. Wang, J. Xia, C. Wang, J. Zhang — NeurIPS 2022
- **URL**: https://proceedings.neurips.cc/paper_files/paper/2022/file/05b69cc4c8ff6e24c5de1ecd27223d37-Paper-Conference.pdf
- **파일**: `literature/papers/R9_DensityDrivenReg_NeurIPS2022.pdf`
- **관련 갭**: Gap-3
- **핵심 아이디어**: 임베딩 밀도 구조를 정규화 신호로 활용 — 저밀도 영역 = 희귀 시나리오
- **위키 파일**: `docs/wiki/evaluation/density-driven-ood-detection.md`

---

### Liang et al. (2024) — AIDE: 자율주행 자동 데이터 엔진
- **출처**: M. Liang, J.-C. Su, S. Schulter, S. Garg, S. Zhao, Y. Wu, M. Chandraker — CVPR 2024
- **URL**: https://openaccess.thecvf.com/content/CVPR2024/papers/Liang_AIDE_An_Automatic_Data_Engine_for_Object_Detection_in_Autonomous_CVPR_2024_paper.pdf
- **파일**: `literature/papers/R10_AIDE_CVPR2024.pdf`
- **관련 갭**: Gap-3, Gap-4, Gap-6
- **핵심 아이디어**: VLM+LLM 반복 루프로 long-tail 자동 발견 → 큐레이션 → 레이블링 → 검증
- **위키 파일**: `docs/wiki/scenario_generation/aide-automatic-data-engine.md`

---

### Lv et al. (2025) — T2SG: 교통 위상 씬 그래프
- **출처**: C. Lv, M. Qi, L. Liu, H. Ma — CVPR 2025
- **URL**: https://openaccess.thecvf.com/content/CVPR2025/papers/Lv_T2SG_Traffic_Topology_Scene_Graph_for_Topology_Reasoning_in_Autonomous_CVPR_2025_paper.pdf
- **파일**: `literature/papers/R11_T2SG_CVPR2025.pdf`
- **관련 갭**: Gap-3
- **핵심 아이디어**: 차선 노드 + 연결 엣지 그래프로 에이전트 인과 상호작용 패턴 표현 (7D 벡터 불가 영역)
- **위키 파일**: `docs/wiki/embedding/t2sg-traffic-topology-scene-graph.md`

---

### Wang et al. (2021) — AdvSim: 안전 위험 시나리오 생성
- **출처**: J. Wang, A. Pun, J. Tu, S. Manivasagam, A. Sadat, S. Casas, M. Ren, R. Urtasun — CVPR 2021
- **URL**: https://openaccess.thecvf.com/content/CVPR2021/papers/Wang_AdvSim_Generating_Safety-Critical_Scenarios_for_Self-Driving_Vehicles_CVPR_2021_paper.pdf
- **파일**: `literature/papers/R12_AdvSim_CVPR2021.pdf`
- **관련 갭**: Gap-4, Gap-6
- **핵심 아이디어**: 실제 로그의 에이전트 궤적을 물리 제약 하에 변조하여 안전 위험 시나리오 대규모 생성
- **위키 파일**: `docs/wiki/scenario_generation/advsim-safety-critical-generation.md`

---

### Yang et al. (2023) — UniSim: 신경망 폐루프 센서 시뮬레이터
- **출처**: Z. Yang, Y. Chen, J. Wang, S. Manivasagam, W.-C. Ma, A. J. Yang, R. Urtasun — CVPR 2023
- **URL**: https://openaccess.thecvf.com/content/CVPR2023/papers/Yang_UniSim_A_Neural_Closed-Loop_Sensor_Simulator_CVPR_2023_paper.pdf
- **파일**: `literature/papers/R13_UniSim_CVPR2023.pdf`
- **관련 갭**: Gap-4, Gap-6
- **핵심 아이디어**: 실제 로그 → NeRF 기반 신경 표현 → 행위자 추가/재배치로 반사실적 희귀 시나리오 생성
- **위키 파일**: `docs/wiki/scenario_generation/unisim-neural-sensor-simulator.md`

---

### Zhang et al. (2024) — ChatScene: LLM 기반 안전 시나리오 생성
- **출처**: J. Zhang, C. Xu, B. Li — CVPR 2024
- **URL**: https://openaccess.thecvf.com/content/CVPR2024/papers/Zhang_ChatScene_Knowledge-Enabled_Safety-Critical_Scenario_Generation_for_Autonomous_Vehicles_CVPR_2024_paper.pdf
- **파일**: `literature/papers/R14_ChatScene_CVPR2024.pdf`
- **관련 갭**: Gap-4, Gap-6
- **핵심 아이디어**: 자연어 시나리오 기술 → LLM이 CARLA 시뮬레이션 코드 자동 생성
- **위키 파일**: `docs/wiki/scenario_generation/chatscene-llm-carla.md`

---

### Rowe et al. (2025) — Scenario Dreamer: 벡터화 잠재 확산 모델
- **출처**: L. Rowe, R. Girgis, A. Gosselin, L. Paull, C. Pal, F. Heide — CVPR 2025
- **URL**: https://openaccess.thecvf.com/content/CVPR2025/papers/Rowe_Scenario_Dreamer_Vectorized_Latent_Diffusion_for_Generating_Driving_Simulation_Environments_CVPR_2025_paper.pdf
- **파일**: `literature/papers/R15_ScenarioDreamer_CVPR2025.pdf`
- **관련 갭**: Gap-4, Gap-6
- **핵심 아이디어**: 차선 그래프 + 에이전트를 벡터 잠재 확산으로 생성 — 잠재 공간이 씬 요소와 직접 대응하여 역변환 가능
- **위키 파일**: `docs/wiki/scenario_generation/scenario-dreamer-latent-diffusion.md`

---

### Wang et al. (2023) — FEND: 롱테일 궤적 예측 대조 학습
- **출처**: Y. Wang, P. Zhang, L. Bai, J. Xue — CVPR 2023
- **URL**: https://openaccess.thecvf.com/content/CVPR2023/papers/Wang_FEND_A_Future_Enhanced_Distribution-Aware_Contrastive_Learning_Framework_for_Long-Tail_CVPR_2023_paper.pdf
- **파일**: `literature/papers/R16_FEND_CVPR2023.pdf`
- **관련 갭**: Gap-4
- **핵심 아이디어**: 분포 인식 대조 학습으로 롱테일 궤적 클러스터 표현 강화
- **위키 파일**: `docs/wiki/data_distribution/fend-longtail-trajectory.md`

---

### Li et al. (2023) — ScenarioNet: 대규모 교통 시나리오 플랫폼
- **출처**: Q. Li, Z. Peng, L. Feng, Z. Liu, C. Duan, W. Mo, B. Zhou — NeurIPS 2023 (Datasets & Benchmarks)
- **URL**: https://proceedings.neurips.cc/paper_files/paper/2023/file/0c26a501df8fb919a0350e2df06b5d39-Paper-Datasets_and_Benchmarks.pdf
- **파일**: `literature/papers/R3_ScenarioNet_NeurIPS2023.pdf`
- **관련 갭**: Gap-3, Gap-4
- **핵심 아이디어**: Waymo/nuScenes/Lyft/nuPlan 통합 플랫폼 + 26가지 시나리오 분류 체계로 커버리지 갭 시각화
- **위키 파일**: `docs/wiki/data_distribution/scenarionet-platform.md`

---

### Shirahmad Gale Bagi et al. (2023) — Generative Causal Representation Learning
- **출처**: S. Shirahmad Gale Bagi, Z. Gharaee, O. Schulte, M. Crowley — ICML 2023
- **URL**: https://proceedings.mlr.press/v202/shirahmad-gale-bagi23a/shirahmad-gale-bagi23a.pdf
- **파일**: `literature/papers/R17_GenerativeCausal_ICML2023.pdf`
- **관련 갭**: Gap-1, Gap-3
- **핵심 아이디어**: 생성적 인과 표현 학습으로 OOD 모션 예측 — spurious correlation 제거 + OOD 일반화 27% 향상
- **위키 파일**: `docs/wiki/embedding/generative-causal-ood-forecasting.md`

---

## 참고할 자료 후보

| 주제 | 자료명 | 관련 갭 | 우선순위 |
|------|--------|--------|---------|
| LLM 기반 relevance labeling | "Large Language Models are Zero-Shot Rankers for Recommender Systems" | Gap-1 | 🔴 High |
| Semantic evaluation of retrieval | BEIR Benchmark (Thakur et al., 2021) | Gap-1, Gap-6 | 🔴 High |
| Hybrid search 개선 | "Hybrid Search with BM25 and Dense Retrieval" | Gap-2 | 🟠 High |
| 벡터 DB 스케일 | Milvus GPU_CAGRA | 장기 | 🟡 Medium |
| ODD 온톨로지 표준 | ISO 34503 공식 문서 | Gap-3 | 🔴 High |
