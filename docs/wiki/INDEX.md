# 기술 위키 — Index

이 디렉토리는 논문·자료에서 추출된 기술을 정리한다.  
각 기술 문서에는 **설명 / 출처 / 장단점 / 구현 참고 / 적용된 실험** 이 포함된다.

---

## 카테고리별 기술 목록

### Embedding & Retrieval (`embedding/`)

| 기술 | 파일 | 관련 갭 | 적용 실험 |
|------|------|--------|---------|
| BAAI/bge-m3 (현재 사용) | — | — | EXP-001 |
| **PCM Disentangled Scene Encoder (인과 피처 분리)** | [embedding/physics-guided-causal-scene-encoder.md](embedding/physics-guided-causal-scene-encoder.md) | Gap-1, Gap-3 | EXP-005 |
| **Safety-aware Causal Transformer (CEWM)** | [embedding/safety-aware-causal-transformer.md](embedding/safety-aware-causal-transformer.md) | Gap-1, Gap-2 | EXP-002, EXP-004 |
| **T2SG 교통 위상 씬 그래프** | [embedding/t2sg-traffic-topology-scene-graph.md](embedding/t2sg-traffic-topology-scene-graph.md) | Gap-3 | EXP-002 Phase C |
| **Generative Causal OOD 모션 예측** | [embedding/generative-causal-ood-forecasting.md](embedding/generative-causal-ood-forecasting.md) | Gap-1, Gap-3 | EXP-005 |

### Search Methods (`search/`)

| 기술 | 파일 | 관련 갭 | 적용 실험 |
|------|------|--------|---------|
| BM25s (현재 사용) | — | — | EXP-001 |
| Hybrid soft filter | — | Gap-2 | EXP-004 |

### ODD Tagging (`tagging/`)

| 기술 | 파일 | 관련 갭 | 적용 실험 |
|------|------|--------|---------|
| Regex 패턴 (현재 사용) | — | Gap-3 | EXP-001 |
| LLM fallback (GPT-4o-mini) | — | Gap-3 | EXP-003 |
| **LVLM 씬 자동 태깅 (CatPipe)** | [tagging/lvlm-scene-tagging-catpipe.md](tagging/lvlm-scene-tagging-catpipe.md) | Gap-3, Gap-6 | EXP-005 |

### Evaluation (`evaluation/`)

| 기술 | 파일 | 관련 갭 | 적용 실험 |
|------|------|--------|---------|
| keyword_relevance (현재 사용) | — | Gap-1 | EXP-001 |
| LLM-based relevance labeling | — | Gap-1 | EXP-002 |
| **4-Type ODD 커버리지 프레임워크** | [evaluation/odd-coverage-framework.md](evaluation/odd-coverage-framework.md) | Gap-1, Gap-3 | EXP-002 |
| **Subjective Logic 메트릭 불확실성** | [evaluation/subjective-logic-ml-metrics.md](evaluation/subjective-logic-ml-metrics.md) | Gap-1 | EXP-002 |
| **μODD 정량적 안전 검증** | [evaluation/muodd-quantitative-verification.md](evaluation/muodd-quantitative-verification.md) | Gap-1, Gap-3 | EXP-002 |
| **TopP&R Fidelity & Diversity 측정** | [evaluation/topp-r-fidelity-diversity-metrics.md](evaluation/topp-r-fidelity-diversity-metrics.md) | Gap-3, Gap-4 | EXP-002 Phase A |
| **Metric Space Magnitude 다양성** | [evaluation/metric-space-magnitude-diversity.md](evaluation/metric-space-magnitude-diversity.md) | Gap-3, Gap-4 | EXP-002 Phase A |
| **Measure Dataset Diversity (ICML Best Paper)** | [evaluation/measure-dataset-diversity.md](evaluation/measure-dataset-diversity.md) | Gap-3, Gap-4 | EXP-002 방법론 근거 |
| **Density-driven OOD 탐지** | [evaluation/density-driven-ood-detection.md](evaluation/density-driven-ood-detection.md) | Gap-3 | EXP-002 Phase A |

### Data Distribution (`data_distribution/`)

| 기술 | 파일 | 관련 갭 | 적용 실험 |
|------|------|--------|---------|
| **NF vs KDE: ADS 밀도 추정 (MAF)** | [data_distribution/normalizing-flow-kde-ads-risk.md](data_distribution/normalizing-flow-kde-ads-risk.md) | Gap-3, Gap-4 | EXP-002 |
| **TrimFlow: NF 기반 희귀 사건 샘플링** | [data_distribution/trimflow-rare-event-sampling.md](data_distribution/trimflow-rare-event-sampling.md) | Gap-4, Gap-6 | EXP-002 |
| **MOSAIC 데이터 선택 최적화** | [data_distribution/mosaic-data-selection.md](data_distribution/mosaic-data-selection.md) | Gap-4 | EXP-003, EXP-004 |
| **E2E AV 스케일링 법칙 (NVIDIA)** | [data_distribution/scaling-laws-e2e-nvidia.md](data_distribution/scaling-laws-e2e-nvidia.md) | Gap-4 | EXP-003 |
| **모방학습 스케일링 법칙 (ONE-Drive)** | [data_distribution/imitation-learning-scaling-laws.md](data_distribution/imitation-learning-scaling-laws.md) | Gap-4, Gap-6 | EXP-003 |
| **WOD-E2E 롱테일 데이터셋** | [data_distribution/wod-e2e-longtail-dataset.md](data_distribution/wod-e2e-longtail-dataset.md) | Gap-4, Gap-1 | EXP-003, EXP-004 |
| **TTC 시나리오 분포 모델** | [data_distribution/ttc-scenario-distribution.md](data_distribution/ttc-scenario-distribution.md) | Gap-4, Gap-6 | EXP-003 |
| **ScenarioNet 시나리오 플랫폼 (26-카테고리)** | [data_distribution/scenarionet-platform.md](data_distribution/scenarionet-platform.md) | Gap-3, Gap-4 | EXP-002 Phase B |
| **SANFlow 의미론적 Normalizing Flow** | [data_distribution/sanflow-semantic-normalizing-flow.md](data_distribution/sanflow-semantic-normalizing-flow.md) | Gap-3, Gap-4 | EXP-002 Phase B |
| **Coverage-centric Coreset Selection** | [data_distribution/coverage-centric-coreset-selection.md](data_distribution/coverage-centric-coreset-selection.md) | Gap-3, Gap-4 | EXP-002 Phase A |
| **FEND 롱테일 궤적 대조 학습** | [data_distribution/fend-longtail-trajectory.md](data_distribution/fend-longtail-trajectory.md) | Gap-4 | EXP-002 Phase C |

### Scenario Generation (`scenario_generation/`)

| 기술 | 파일 | 관련 갭 | 적용 실험 |
|------|------|--------|---------|
| **LLM 기반 OOD 시나리오 생성** | [scenario_generation/llm-ood-generation.md](scenario_generation/llm-ood-generation.md) | Gap-3, Gap-4 | EXP-006 (후보) |
| **AIDE 자동 데이터 엔진 (VLM+LLM 루프)** | [scenario_generation/aide-automatic-data-engine.md](scenario_generation/aide-automatic-data-engine.md) | Gap-3, Gap-4, Gap-6 | EXP-002 Phase B |
| **AdvSim 안전 위험 시나리오 생성** | [scenario_generation/advsim-safety-critical-generation.md](scenario_generation/advsim-safety-critical-generation.md) | Gap-4, Gap-6 | EXP-002 Phase D |
| **UniSim 신경망 센서 시뮬레이터** | [scenario_generation/unisim-neural-sensor-simulator.md](scenario_generation/unisim-neural-sensor-simulator.md) | Gap-4, Gap-6 | EXP-002 Phase D |
| **ChatScene LLM → CARLA 자동화** | [scenario_generation/chatscene-llm-carla.md](scenario_generation/chatscene-llm-carla.md) | Gap-4, Gap-6 | EXP-002 Phase D |
| **Scenario Dreamer 벡터 잠재 확산** | [scenario_generation/scenario-dreamer-latent-diffusion.md](scenario_generation/scenario-dreamer-latent-diffusion.md) | Gap-4, Gap-6 | EXP-002 Phase D |

---

## 문헌 → 기술 매핑

| 문헌 | 핵심 기여 | 위키 파일 |
|------|---------|---------|
| (2025) — NF vs KDE (SYNERGIES) | NF가 고차원 ADS 리스크 공간에서 KDE보다 밀도 추정 정밀도 향상 | [data_distribution/normalizing-flow-kde-ads-risk.md](data_distribution/normalizing-flow-kde-ads-risk.md) |
| Aasi et al. (2024) | LLM+CoT로 OOD 시나리오 트리 생성, OOD-ness/Diversity 메트릭 | [scenario_generation/llm-ood-generation.md](scenario_generation/llm-ood-generation.md) |
| Chodowiec et al. (2026) | 4-Type 시나리오 커버리지 프레임워크 (Attr/ODD/OutODD/RoR) | [evaluation/odd-coverage-framework.md](evaluation/odd-coverage-framework.md) |
| Dimlioglu et al. (2026) | MOSAIC: 클러스터링+스케일링 인식 데이터 선택 (80% 효율) | [data_distribution/mosaic-data-selection.md](data_distribution/mosaic-data-selection.md) |
| Herd & Burton (2024) | Subjective Logic으로 ML 메트릭 불확실성 정량화 | [evaluation/subjective-logic-ml-metrics.md](evaluation/subjective-logic-ml-metrics.md) |
| Li et al. (2026) | PCM: Intervention-based disentanglement으로 도메인 불변 인과 피처 + CausalODE | [embedding/physics-guided-causal-scene-encoder.md](embedding/physics-guided-causal-scene-encoder.md) |
| Lu et al. (2024) | CEWM: state→reward/cost 인과 경로 분리, spurious correlation 제거 | [embedding/safety-aware-causal-transformer.md](embedding/safety-aware-causal-transformer.md) |
| Naumann et al. (2025) | E2E AV 데이터 스케일링 법칙 (16h~8192h, NVIDIA) | [data_distribution/scaling-laws-e2e-nvidia.md](data_distribution/scaling-laws-e2e-nvidia.md) |
| Rivera et al. (2025) | CatPipe: LVLM 기반 16개 카테고리 자동 씬 태깅 | [tagging/lvlm-scene-tagging-catpipe.md](tagging/lvlm-scene-tagging-catpipe.md) |
| Schleiss et al. (2022) | μODD 분할 + 리스크 기반 테스트 전략 (ISO 21448) | [evaluation/muodd-quantitative-verification.md](evaluation/muodd-quantitative-verification.md) |
| Song et al. (2022) | TTC 기반 차량-보행자 시나리오 분포 모델 (Poisson) | [data_distribution/ttc-scenario-distribution.md](data_distribution/ttc-scenario-distribution.md) |
| (2024) — TrimFlow | NF + Temporal IS: 86.1% 적은 시뮬레이션으로 희귀 위험 사건 커버 | [data_distribution/trimflow-rare-event-sampling.md](data_distribution/trimflow-rare-event-sampling.md) |
| Xu et al. (2025) | WOD-E2E: 롱테일 특화 4,021 세그먼트 + RFS 평가 | [data_distribution/wod-e2e-longtail-dataset.md](data_distribution/wod-e2e-longtail-dataset.md) |
| Zheng et al. (2025) | ONE-Drive 4M 시연 스케일링 분석: 분포 > 양 | [data_distribution/imitation-learning-scaling-laws.md](data_distribution/imitation-learning-scaling-laws.md) |
| Kim et al. (2023) — TopP&R | KDE 지지도 추정으로 Fidelity/Diversity 분리 측정 | [evaluation/topp-r-fidelity-diversity-metrics.md](evaluation/topp-r-fidelity-diversity-metrics.md) |
| Limbeck et al. (2024) — Metric Space Magnitude | 위상수학 기반 latent diversity 측정 (provably stable) | [evaluation/metric-space-magnitude-diversity.md](evaluation/metric-space-magnitude-diversity.md) |
| Kim et al. (2023) — SANFlow | 의미론적 NF — 클러스터별 base distribution으로 역변환 가능 | [data_distribution/sanflow-semantic-normalizing-flow.md](data_distribution/sanflow-semantic-normalizing-flow.md) |
| Zhao et al. (2024) — ICML Best Paper | 135개 데이터셋 분석: diversity 선언은 측정 이론 기반이어야 함 | [evaluation/measure-dataset-diversity.md](evaluation/measure-dataset-diversity.md) |
| Zheng et al. (2023) — Coverage Coreset | 기하학적 set cover로 ODD 커버리지 정량화 | [data_distribution/coverage-centric-coreset-selection.md](data_distribution/coverage-centric-coreset-selection.md) |
| Huang et al. (2022) — Density-driven | 임베딩 밀도 기반 OOD 탐지 정규화 | [evaluation/density-driven-ood-detection.md](evaluation/density-driven-ood-detection.md) |
| Liang et al. (2024) — AIDE | VLM+LLM 반복 루프로 long-tail 자동 발견·큐레이션 | [scenario_generation/aide-automatic-data-engine.md](scenario_generation/aide-automatic-data-engine.md) |
| Lv et al. (2025) — T2SG | 차선 노드+엣지 그래프로 에이전트 인과 상호작용 표현 | [embedding/t2sg-traffic-topology-scene-graph.md](embedding/t2sg-traffic-topology-scene-graph.md) |
| Wang et al. (2021) — AdvSim | 실제 로그 궤적 변조로 safety-critical 시나리오 3.8× 생성 | [scenario_generation/advsim-safety-critical-generation.md](scenario_generation/advsim-safety-critical-generation.md) |
| Yang et al. (2023) — UniSim | NeRF 기반 폐루프 센서 시뮬레이터: 반사실적 희귀 씬 생성 | [scenario_generation/unisim-neural-sensor-simulator.md](scenario_generation/unisim-neural-sensor-simulator.md) |
| Zhang et al. (2024) — ChatScene | 자연어 → LLM → CARLA 코드 자동 변환 | [scenario_generation/chatscene-llm-carla.md](scenario_generation/chatscene-llm-carla.md) |
| Rowe et al. (2025) — Scenario Dreamer | 벡터 잠재 확산으로 씬 생성 — 잠재 차원=씬 요소 역변환 가능 | [scenario_generation/scenario-dreamer-latent-diffusion.md](scenario_generation/scenario-dreamer-latent-diffusion.md) |
| Wang et al. (2023) — FEND | 분포 인식 대조 학습으로 롱테일 궤적 표현 강화 | [data_distribution/fend-longtail-trajectory.md](data_distribution/fend-longtail-trajectory.md) |
| Li et al. (2023) — ScenarioNet | Waymo/nuScenes 통합 + 26-카테고리 시나리오 분류 체계 | [data_distribution/scenarionet-platform.md](data_distribution/scenarionet-platform.md) |
| Shirahmad Gale Bagi et al. (2023) | 생성적 인과 표현 학습으로 OOD 모션 예측 27% 향상 | [embedding/generative-causal-ood-forecasting.md](embedding/generative-causal-ood-forecasting.md) |

---

## 갭-기술 대응표 (업데이트)

| 갭 ID | 갭 설명 | 검토 중인 기술 | 관련 논문 |
|-------|--------|--------------|---------|
| Gap-1 | 평가셋 편향 (키워드 기반 레이블) | LLM relevance labeling, Subjective Logic CI, μODD 평가셋, 인과 관련성 스코어 | Herd, Schleiss, Chodowiec, Li, Lu |
| Gap-2 | Hybrid = Embedding (ODD 필터 무효) | 소프트 ODD 필터, 확률 가중, state→cost 인과 필터 | Lu |
| Gap-3 | ODD 커버리지 저조 (36~62%) | CatPipe LVLM 태깅, 4-Type 커버리지, LLM 시나리오 생성, NF 커버리지 갭 탐지 | Rivera, Chodowiec, Aasi, Li |
| Gap-4 | 분포 편향 (정상 과다, 희귀 과소) | MOSAIC 데이터 선택, 스케일링 법칙, WOD-E2E 클러스터, TTC 분포, MAF 밀도 추정, TrimFlow IS | Dimlioglu, Naumann, Zheng, Xu, Song, Aasi, NF-KDE, TrimFlow |
| Gap-5 | 워밍업 미처리 (지연 왜곡) | evaluate.py 워밍업 패치 | — |
| Gap-6 | 쿼리 다양성 부족 | 쿼리 증강, 동의어 확장, WOD-E2E 11개 카테고리, Zheng 23개 유형 | Zheng, Xu, Song |

---

## 실험 아이디어 백로그 (논문에서 추출)

| ID | 아이디어 | 출처 논문 | 관련 갭 | 난이도 |
|----|---------|---------|---------|-------|
| EXP-005 | CatPipe로 83k 클립 재태깅 + ODD 커버리지 재측정 | Rivera 2025 | Gap-3 | 중 |
| EXP-006 | LLM Diverse Tree로 검색 쿼리 자동 생성 | Aasi 2024 | Gap-6 | 중 |
| EXP-007 | MOSAIC 방식 클러스터별 검색 성능 스케일링 분석 | Dimlioglu 2026 | Gap-4 | 고 |
| EXP-008 | Subjective Logic으로 Recall@5 95% CI 계산 | Herd 2024 | Gap-1 | 하 |
| EXP-009 | WOD-E2E 11개 카테고리로 현재 데이터 커버리지 측정 | Xu 2025 | Gap-4 | 중 |
| EXP-010 | MAF로 5D ODD 공간 갭 탐지 + KDE 대비 log-likelihood 비교 | NF-KDE 2025, TrimFlow 2024 | Gap-3, Gap-4 | 중 |
| EXP-005 (확장) | PCM 방식 intervention contrastive fine-tuning으로 bge-m3 인과 인코더 구축 | Li 2026 | Gap-1 | 고 |
