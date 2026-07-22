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
| LLM fallback (GPT-4o-mini) | — | Gap-3 | EXP-002 |
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
| **Coverage Metrics for Scenario DB (Q1/Q2)** | [evaluation/coverage-metrics-scenario-database.md](evaluation/coverage-metrics-scenario-database.md) | Gap-1, Gap-3 | EXP-003, EXP-004 |
| **Coverage vs Sufficiency (종합 분석: 중요조합 선별+충분성)** | [evaluation/coverage-vs-sufficiency.md](evaluation/coverage-vs-sufficiency.md) | Gap-1, Gap-3, Gap-4 | EXP-003 Phase 0/C, EXP-004 |
| **Exposure 분포 구축 (기관 marginal → VKT-가중 층화 혼합)** | [EXP-003 Phase 1 design](../../experiments/EXP-003/phase1/design.md) | Gap-4 | EXP-003 Phase 1 |
| **Data Scaling Laws for E2E AD (시나리오별 포화곡선)** | [evaluation/data-scaling-laws-e2e-ad.md](evaluation/data-scaling-laws-e2e-ad.md) | Gap-3, Gap-4 | EXP-003 Phase B/C, EXP-004 |
| **Situation Coverage Grid (확률적 안전 검증)** | [evaluation/situation-coverage-grid.md](evaluation/situation-coverage-grid.md) | Gap-1, Gap-3 | EXP-003 Phase 0, EXP-004 |
| **Combinatorial Full-Coverage Testing (t-wise 조합 축소)** | [evaluation/combinatorial-full-coverage-testing.md](evaluation/combinatorial-full-coverage-testing.md) | Gap-1, Gap-3 | EXP-003 Phase 0, EXP-004 |
| **DBCA 의존성 기반 조합 ODD 축소 (t/p-way)** | [evaluation/dbca-combinatorial-odd-reduction.md](evaluation/dbca-combinatorial-odd-reduction.md) | Gap-3, Gap-4 | EXP-003 Phase 1 §2 |
| **Criticality Metrics 리뷰 + 적합성 분석 (~40지표)** | [evaluation/criticality-metrics-suitability.md](evaluation/criticality-metrics-suitability.md) | Gap-4, Gap-1, Gap-3 | EXP-003 Phase 1 §10 |
| **SCOUT 경량 커버리지 레이블 예측** | [evaluation/scout-scenario-coverage.md](evaluation/scout-scenario-coverage.md) | Gap-1, Gap-3 | EXP-005 |
| **Graph-based Coverage Analysis (GINE)** | [evaluation/graph-based-coverage-analysis.md](evaluation/graph-based-coverage-analysis.md) | Gap-1, Gap-3 | EXP-002 Phase B |

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
| **Beyond Neural Scaling Laws (데이터 프루닝)** | [data_distribution/beyond-neural-scaling-laws.md](data_distribution/beyond-neural-scaling-laws.md) | Gap-4 | EXP-003 Phase 0, EXP-004 |
| **Domino: 체계적 오류 슬라이스 발견** | [data_distribution/domino-systematic-error-discovery.md](data_distribution/domino-systematic-error-discovery.md) | Gap-4, Gap-1 | EXP-003 Phase 0, EXP-004 |
| **LESS: 영향력 기반 데이터 선택** | [data_distribution/less-influential-data-selection.md](data_distribution/less-influential-data-selection.md) | Gap-4 | EXP-003 Phase B (대안), EXP-004 |
| **DataComp: 데이터 큐레이션 벤치마크** | [data_distribution/datacomp-dataset-curation-benchmark.md](data_distribution/datacomp-dataset-curation-benchmark.md) | Gap-4 | EXP-003 Phase 0, EXP-004 |
| **합성 데이터 E2E 효과 분석 (Unraveling)** | [data_distribution/unraveling-synthetic-data-e2e.md](data_distribution/unraveling-synthetic-data-e2e.md) | Gap-4, Gap-6 | EXP-003, EXP-004 |
| **ADV-0 Min-Max 적대적 학습** | [data_distribution/adv0-adversarial-training.md](data_distribution/adv0-adversarial-training.md) | Gap-4 | EXP-003, EXP-004 |
| **Counterfactual Safety Learning (Simulating Unseen)** | [data_distribution/simulating-unseen-crash.md](data_distribution/simulating-unseen-crash.md) | Gap-4, Gap-6 | EXP-003, EXP-004 |
| **RoCA: GP 기반 Cross-Domain E2E 적응** | [data_distribution/roca-cross-domain-adaptation.md](data_distribution/roca-cross-domain-adaptation.md) | Gap-4, Gap-1 | EXP-003 |

### Scenario Generation (`scenario_generation/`)

| 기술 | 파일 | 관련 갭 | 적용 실험 |
|------|------|--------|---------|
| **LLM 기반 OOD 시나리오 생성** | [scenario_generation/llm-ood-generation.md](scenario_generation/llm-ood-generation.md) | Gap-3, Gap-4 | EXP-006 (후보) |
| **AIDE 자동 데이터 엔진 (VLM+LLM 루프)** | [scenario_generation/aide-automatic-data-engine.md](scenario_generation/aide-automatic-data-engine.md) | Gap-3, Gap-4, Gap-6 | EXP-002 Phase B |
| **AdvSim 안전 위험 시나리오 생성** | [scenario_generation/advsim-safety-critical-generation.md](scenario_generation/advsim-safety-critical-generation.md) | Gap-4, Gap-6 | EXP-002 Phase D |
| **UniSim 신경망 센서 시뮬레이터** | [scenario_generation/unisim-neural-sensor-simulator.md](scenario_generation/unisim-neural-sensor-simulator.md) | Gap-4, Gap-6 | EXP-002 Phase D |
| **ChatScene LLM → CARLA 자동화** | [scenario_generation/chatscene-llm-carla.md](scenario_generation/chatscene-llm-carla.md) | Gap-4, Gap-6 | EXP-002 Phase D |
| **Scenario Dreamer 벡터 잠재 확산** | [scenario_generation/scenario-dreamer-latent-diffusion.md](scenario_generation/scenario-dreamer-latent-diffusion.md) | Gap-4, Gap-6 | EXP-002 Phase D |
| **Cosmos-Drive-Dreams 월드 파운데이션 생성** | [scenario_generation/cosmos-drive-dreams.md](scenario_generation/cosmos-drive-dreams.md) | Gap-4, Gap-6 | EXP-003, EXP-004 |
| **LTDA-Drive LLM 가이드 롱테일 증강** | [scenario_generation/ltda-drive-longtail-augmentation.md](scenario_generation/ltda-drive-longtail-augmentation.md) | Gap-4, Gap-6 | EXP-003, EXP-004 |

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
| Sorscher et al. (2022) — Beyond Scaling | "Easy" 샘플 기하 프루닝으로 스케일링 법칙 α 급격히 개선, 50% 데이터로 동일 성능 | [data_distribution/beyond-neural-scaling-laws.md](data_distribution/beyond-neural-scaling-laws.md) |
| Eyuboglu et al. (2022) — Domino | Cross-modal embedding으로 모델 실패 슬라이스 자동 발견 (일부 슬라이스 error 5× 높음) | [data_distribution/domino-systematic-error-discovery.md](data_distribution/domino-systematic-error-discovery.md) |
| Xia et al. (2024) — LESS | LoRA gradient similarity로 5% 데이터 선택 → 동일 성능, target-specific 선택 | [data_distribution/less-influential-data-selection.md](data_distribution/less-influential-data-selection.md) |
| Gadre et al. (2024) — DataComp | 38개 태스크 큐레이션 벤치마크: 품질 필터 우선 → 다양성 샘플링 순서가 최선 | [data_distribution/datacomp-dataset-curation-benchmark.md](data_distribution/datacomp-dataset-curation-benchmark.md) |
| de Gelder et al. (2025) — Coverage Metrics | Q1(ODD 커버리지) + Q2(임계 상황 커버리지) 두 가지 정량 메트릭; HighD 200k 검증 | [evaluation/coverage-metrics-scenario-database.md](evaluation/coverage-metrics-scenario-database.md) |
| Ge et al. (2025) — Unraveling Synthetic Data | 희귀 ODD에서 합성 효과적, 일반 ODD에서 도메인 갭 유발; 최적 혼합 비율 존재 | [data_distribution/unraveling-synthetic-data-e2e.md](data_distribution/unraveling-synthetic-data-e2e.md) |
| Mühlenstädt & Bause (2026) — Graph Coverage | 계층적 씬 그래프 + 서브그래프 동형성/GINE 임베딩으로 커버리지 분석 | [evaluation/graph-based-coverage-analysis.md](evaluation/graph-based-coverage-analysis.md) |
| Nie et al. (2026) — ADV-0 | zero-sum Markov game defender-attacker; iterative preference learning으로 Nash Eq. 수렴 | [data_distribution/adv0-adversarial-training.md](data_distribution/adv0-adversarial-training.md) |
| Ren et al. (2025) — Cosmos-Drive-Dreams | Cosmos-1 world FM 특화; 제어 가능 멀티뷰 주행 영상 생성; 3D 검출·E2E 성능 향상 | [scenario_generation/cosmos-drive-dreams.md](scenario_generation/cosmos-drive-dreams.md) |
| Yildiz et al. (2025) — SCOUT | LVLM distillation surrogate로 대규모 커버리지 레이블 저비용 예측 | [evaluation/scout-scenario-coverage.md](evaluation/scout-scenario-coverage.md) |
| Yurt et al. (2025) — LTDA-Drive | LLM 명세 + diffusion으로 롱테일 클래스 다양성 합성; 재샘플링 대비 tail class 다양성 해결 | [scenario_generation/ltda-drive-longtail-augmentation.md](scenario_generation/ltda-drive-longtail-augmentation.md) |
| Li et al. (2025) — Simulating the Unseen | near-miss 기반 counterfactual safety learning; crash-rate prior + 생성 씬 엔진 + 인과 학습 | [data_distribution/simulating-unseen-crash.md](data_distribution/simulating-unseen-crash.md) |
| Yasarla et al. (2025) — RoCA | ego/agent 토큰 GP 모델링 + basis codebook; GP variance로 롱테일 가중·불확실성 기반 active learning (LLM 불필요) | [data_distribution/roca-cross-domain-adaptation.md](data_distribution/roca-cross-domain-adaptation.md) |
| Naumann et al. (2025) — Data Scaling Laws E2E AD | E2E 주행 파워법칙 c≈−0.4; 시나리오별 지수 상이(직진 빠름/차선변경 느림); 5% 개선=+273k시간 | [evaluation/data-scaling-laws-e2e-ad.md](evaluation/data-scaling-laws-e2e-ad.md) |
| Situation Coverage Grid (2025) | "coverage alone is insufficient"; 관측 실패율로 미관측 셀 확률적 상한 → 안전 논증 | [evaluation/situation-coverage-grid.md](evaluation/situation-coverage-grid.md) |
| Full Coverage Testing (Sensors 2025) | t-wise 86.5% vs greedy+GA full-coverage; 482개로 96% 비용 절감 | [evaluation/combinatorial-full-coverage-testing.md](evaluation/combinatorial-full-coverage-testing.md) |

---

## 갭-기술 대응표 (업데이트)

| 갭 ID | 갭 설명 | 검토 중인 기술 | 관련 논문 |
|-------|--------|--------------|---------|
| Gap-1 | 평가셋 편향 (키워드 기반 레이블) | LLM relevance labeling, Subjective Logic CI, μODD 평가셋, 인과 관련성 스코어 | Herd, Schleiss, Chodowiec, Li, Lu |
| Gap-2 | Hybrid = Embedding (ODD 필터 무효) | 소프트 ODD 필터, 확률 가중, state→cost 인과 필터 | Lu |
| Gap-3 | ODD 커버리지 저조 (36~62%) | CatPipe LVLM 태깅, 4-Type 커버리지, LLM 시나리오 생성, NF 커버리지 갭 탐지 | Rivera, Chodowiec, Aasi, Li |
| Gap-4 | 분포 편향 (정상 과다, 희귀 과소) | MOSAIC 데이터 선택, 스케일링 법칙, WOD-E2E 클러스터, TTC 분포, MAF 밀도 추정, TrimFlow IS, **데이터 프루닝(Sorscher)**, **슬라이스 오류 발견(Domino)**, **영향력 기반 선택(LESS)**, **큐레이션 벤치마크(DataComp)** | Dimlioglu, Naumann, Zheng, Xu, Song, Aasi, NF-KDE, TrimFlow, Sorscher, Eyuboglu, Xia, Gadre |
| Gap-5 | 워밍업 미처리 (지연 왜곡) | evaluate.py 워밍업 패치 | — |
| Gap-6 | 쿼리 다양성 부족 | 쿼리 증강, 동의어 확장, WOD-E2E 11개 카테고리, Zheng 23개 유형 | Zheng, Xu, Song |

---

## 실험 아이디어 백로그 (논문에서 추출)

| ID | 아이디어 | 출처 논문 | 관련 갭 | 난이도 |
|----|---------|---------|---------|-------|
| EXP-005 | CatPipe로 83k 클립 재태깅 + ODD 커버리지 재측정 | Rivera 2025 | Gap-3 | 중 |
| EXP-006 | LLM Diverse Tree로 검색 쿼리 자동 생성 | Aasi 2024 | Gap-6 | 중 |
| EXP-003 | MOSAIC + DISC 방식: D_train 분포 프로파일링 → 4차원 갭 체계화 → 타겟 탐색 → 구성 최적화 | Dimlioglu 2026, Sorscher 2022, Eyuboglu 2022, Xia 2024, Gadre 2024 | Gap-4 | 고 |
| EXP-004 | D_train 구성 최적화: 중복/저가치 클립 프루닝 + 갭 오버샘플링 → 도메인별 Recall@5 균등화 | Sorscher 2022, Xia 2024 | Gap-4 | 중 |
| EXP-008 | Subjective Logic으로 Recall@5 95% CI 계산 | Herd 2024 | Gap-1 | 하 |
| EXP-009 | WOD-E2E 11개 카테고리로 현재 데이터 커버리지 측정 | Xu 2025 | Gap-4 | 중 |
| EXP-010 | MAF로 5D ODD 공간 갭 탐지 + KDE 대비 log-likelihood 비교 | NF-KDE 2025, TrimFlow 2024 | Gap-3, Gap-4 | 중 |
| EXP-005 (확장) | PCM 방식 intervention contrastive fine-tuning으로 bge-m3 인과 인코더 구축 | Li 2026 | Gap-1 | 고 |
