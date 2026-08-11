# G-Q1 실사 실험 설계 — 인과 회복가치 발산·우위 (생사 게이트)

> 맥락: `../../PAPER_DIRECTION.md §10-3`(G-Q1=축 판별보다 절대 선행), `../../CONCEPT_ALIGNMENT.md §9`(문헌실사: ActiveAD가 이미 다라운드 → novelty는 인과 신호+Q2에만). 기질=R0(`../r0_repro/`, SparseDrive + stage2-only leave-out). 작성 2026-08-11.
> **왜 생사인가**: G-Q1 실패 시 회복가치 신호가 ActiveAD식 diversity/uncertainty로 수렴 = **scoop**. 이 게이트 통과 전 축(arch/rounds) 논쟁·전면 투자 금지.

---

## 0. 증명 대상 (둘 다 필요)
1. **발산(divergence)**: 인과 회복가치가 uncertainty·diversity·scaling-gain과 **순위가 다르다**(중복 아님). 필요조건·값쌈.
2. **우위(dominance)**: 회복가치로 고르면 tail 회복이 예산 대비 **더 크다**(계산 값어치). 보상·비쌈.
→ 싼 발산부터, 조기 사살.

## 1. 신호 정의 (backbone-free/무재학습 준수)
| 신호 | nuScenes/SparseDrive 조작화 | 비용 |
|---|---|---|
| **회복가치(오라클)** = 인과 GT | 결핍 c: `ΔTail = Tail(c 제거 학습) − Tail(c 포함 학습)`, **stage2-only 재학습(stage1 동결)**, c의 eval 슬라이스 collision/L2 tail | 재학습 n회 |
| **회복가치(싼 프록시)** = 무재학습 근사 | 1-step reducible loss(첫 fine-tune 스텝 손실감소) 또는 influence 근사(PD §6 G2 위임) | forward |
| **uncertainty** | 플래닝 mode-score 엔트로피/top-mode margin, 또는 **stage2 헤드 K개 앙상블**(stage1 동결이라 값쌈) 궤적 분산 | forward/소재학습 |
| **diversity/coverage** | 모델무관 feature(씬캡션 emb·ego kinematics·맵위상) kNN 밀도/SemDeDup 중복도 | 임베딩 |
| **scaling-gain(MOSAIC 근사)** | c의 현 tail-error(포화 거리 ∝ 한계이득) — *조proxy, 정식 MOSAIC은 후속 baseline* | forward |

⚠️ uncertainty·diversity·scaling-gain은 **무재학습**으로 계산돼야 "싼 gate". 오라클만 재학습.

## 2. 결핍 단위 (통계력)
- planning-relevant 실패 클러스터(PD §5-1/§8): 급코너(|yaw|/곡률)·비보호좌회전·고인터랙션(에이전트 수/低TTC)·occlusion + M0 collision/high-L2 슬라이스.
- **n≥15 서브결핍**으로 세분(5 대분류로는 상관 검정력 0). 각 서브결핍 = leave-out 1단위.

## 3. 3단 프로토콜 (조기 사살)
### S0 — 무재학습 발산 스크리닝 (거의 공짜, 大 n)
- 전 clip: {싼 회복가치 프록시, uncertainty, diversity, scaling-gain} → **per-clip rank 상관 행렬**.
- 조기 컷: 싼 프록시가 uncertainty/diversity와 **ρ≥0.7** → 적색경보 → S1 확인만.
- 발산이면 S1. *비용: forward 수 시간.*

### S1 — 클러스터 오라클 인과 발산 (핵심, 중간)
- n≥15 서브결핍 stage2-only leave-out → **오라클 회복가치**.
- 오라클 vs {uncertainty, diversity, scaling-gain} **Spearman ρ + top-⌈n/3⌉ Jaccard**.
- *비용: ~2h × n, 2GPU 병렬 2개씩 → 벽시계 ~15h/15단위.*

### S2 — 우위 미니 획득 라운드 (보상, 최대)
- 동일 예산 B를 {회복가치, uncertainty, diversity}로 선택 → stage2 fine-tune → **tail 회복량 비교**.
- G0 연계: 고여지/저여지 층화(파일럿: speed 통과·yaw 실패) — 우위가 고여지에서만인지.
- *비용: stage2 재학습 3~4회.*

## 4. 사전등록 판정 규칙 (결과 전 고정)
| 결과 | 조건 | 처분 |
|---|---|---|
| **PASS** | 오라클이 세 신호 모두와 max\|ρ\|≤0.5 & top-k Jaccard≤0.5 **AND** S2 회복가치-선택 tail회복 > 최선 싼신호, paired p<.05 | 축 판별(§10-3 G2-arch vs G-Drift) 진입 |
| **FAIL(scoop)** | \|ρ\|≥0.7 (uncertainty/diversity와) | Plan C-temporal 기각 → ActiveAD 흡수/재프레이밍 |
| **AMBIGUOUS** | 발산은 하나 S2 우위 무 | "다르나 낫지 않음" → G0 고여지 층화서 우위 재검(고여지 한정 논문) |

**검정력**: n=15 상관은 ρ≈0.5+만 검출 → S0 per-clip 프록시(大 n)로 발산 검정력 보완. **스크리닝이지 증명 아님.**

## 5. 교란·통제
1. **stage2-only 타당성**: 결핍이 perception(stage1)에 있으면 회복가치 과소평가 → **full-stage leave-out 1~2개로 근사오차 캘리브**(R0 §4). scope="planning recoverability given fixed perception" 명시.
2. **eval-슬라이스 누수**: c의 eval 슬라이스 전 arm 학습 제외.
3. **uncertainty 사전고정**: mode-엔트로피 vs stage2-앙상블 중 예약(앙상블이 stage1 동결로 값쌈).
4. **diversity feature 무관성**: 모델무관 소스만(캡션/kinematics/맵), 지각 backbone feature 금지(쓰면 model-coupled=thesis 붕괴).
5. **scaling-gain 조proxy** — 정식 MOSAIC은 후속 baseline 분리.

## 6. 산출물
- `output/gq1_divergence.json`(S0/S1 상관·Jaccard), `output/gq1_dominance.json`(S2 tail회복), `GQ1_RESULTS.md`(판정).

## 7. 스킵한 것 (의도적)
- per-clip 오라클(너무 비쌈) → 클러스터 오라클로 대체.
- 정식 MOSAIC/RoCA 비교 → G1 위생검사·후속 baseline으로 분리.
- S0 죽으면 S1·S2 미진행.
