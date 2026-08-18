# S0 model-signals 설계 (`s0_model_signals.py`)

> 목적: G-Q1 S0 발산 스크리닝을 **완성**한다. `s0_features.py`가 만든 model-free 신호(diversity·coverage_redundancy)에
> **모델 유래 신호 3종(recoverability_proxy·uncertainty·scaling_gain)**을 붙여 per-clip rank 상관행렬을 완성 → 조기 컷 판정.
> 제약: **무재학습**(backbone-free), **model-agnostic thesis 보존**(지각 backbone feature 금지), stage1 동결.
> 근거: `GQ1_design.md` §1·§3-S0·§4·§5. 작성 2026-08-11.

---

## 0. 한 줄 요약
released M0(=`sparsedrive_stage1.pth`+`stage2.pth`)의 **이미 저장된 forward 출력 `results.pkl`**에서
uncertainty·scaling_gain을 오프라인 산출, recoverability는 **cluster-level 1-step reducible loss**로 근사 →
`s0_features` 신호와 합쳐 divergence 판정. **GPU 며칠 아님**(오프라인 계산 + 선택적 1-step ×20클러스터).

## 1. 데이터 소스 (전부 이미 존재)
| 소스 | 위치 | 쓰임 |
|---|---|---|
| M0 forward 출력 | `third_party/sparsedrive/work_dirs/sparsedrive_small_stage2/results.pkl` (2.3GB) | 신호 원천 |
| per-clip 정렬·model-free 신호·클러스터 | `r1_gates/output/gq1_s0_perclip.npz` + `gq1_s0.json` | 정렬 키·병합 대상 |
| GT ego 미래궤적·command·fut_boxes | nuScenes infos (`data/infos/nuscenes_infos_val.pkl`) | scaling_gain(오차)·정렬 |

`results.pkl[i]['img_bbox']` 키: **`planning_score`**(=cls.sigmoid, mode 점수) · **`planning`**(전 모드 궤적) · **`final_planning`**(선택 궤적). `ego_fut_mode=3`, `ego_fut_ts=6`, command 3종.

## 2. 신호 조작화 (사전등록 — 결과 보기 전 고정)

### (a) uncertainty  — per-clip, 순수 오프라인
- **1순위(고정)**: `planning_score`의 **주어진 command 행에 대한 mode-엔트로피** `H = -Σ p log p` (softmax normalize).
- 보조(기록만): 전 모드 궤적 `planning`의 **엔드포인트 분산**(top-mode margin). 사전등록은 mode-엔트로피.
- 근거: GQ1 §1 "플래닝 mode-score 엔트로피". stage2-앙상블(§5-3 대안)은 S0에선 불채택(엔트로피가 순수 forward라 더 쌈).

### (b) scaling_gain (MOSAIC 조proxy) — per-clip, 순수 오프라인
- `final_planning` vs GT `gt_ego_fut_trajs`(cumsum) → **per-clip L2 tail-error**(1~3s, planning_eval와 동일 마스킹).
- 정의: 현 tail-error = 포화까지 거리 ∝ 한계이득(MOSAIC 근사). 값 클수록 scaling 여지 큼.
- ⚠️ planning_eval의 `sdc_planning_mask.all()` 불완전 GT 스킵 규칙을 **그대로** 적용(누수·불일치 방지).

### (c) recoverability_proxy — **cluster-level**, 1-step reducible loss
- 순수 forward로는 인과 회복가치 근사 불가 → **1-step**: M0 로드 → 서브결핍 클러스터 c 데이터로 **stage2 헤드에 옵티마이저 1스텝** → c의 planning loss 감소량 `Δloss_c`.
- stage1 동결(§1) → stage2 헤드만 → 20 클러스터 × 1스텝 = 값쌈.
- **대안(구현 단순화 시)**: S0에선 recoverability를 **생략**하고 {uncertainty·scaling_gain·diversity·coverage_redundancy} 4종만 divergence, 인과 회복가치는 **S1 오라클로 위임**(GQ1 §1 "influence 근사는 G2 위임"과 정합). → **결정 필요**(아래 §7).

## 3. 정렬 (핵심 함정)
`results.pkl` 순서 = eval dataloader 순서(val split). `s0_features` 순서 = infos 순서.
→ **sample_token으로 조인**. infos의 `token`과 results 인덱스↔dataloader의 token을 매핑해 per-clip 배열을 동일 순서로 정렬.
불완전 GT 스킵으로 유효 clip 수가 6019보다 작을 수 있음 → **유효 마스크를 공유**해 모든 신호를 같은 부분집합에 정의.

## 4. divergence 계산 (기존 코드 재사용)
- `s0_features.py`의 `spearman`·`topk_jaccard`·`_rank`·`divergence` **그대로 import 재사용**(재구현 금지).
- per-clip 신호행렬 = {recoverability_proxy(있으면), uncertainty, scaling_gain, diversity, coverage_redundancy} → **Spearman ρ 행렬 + top-⌈n/3⌉ Jaccard**.
- recoverability가 cluster-level이면: 나머지 신호도 클러스터 평균으로 집계해 **cluster-level 상관**을 별도 산출(per-clip 상관은 model-free/오프라인 4종끼리).

## 5. 판정 (GQ1 §3-S0 / §4, 결과 전 고정)
- **조기 컷(적색)**: 싼 recoverability 프록시가 uncertainty 또는 diversity와 **|ρ|≥0.7** → S1 확인만(발산 없음 경보).
- **발산(green-ish)**: recoverability가 세 신호와 낮은 ρ → S1(오라클) 진행 정당.
- S0는 **스크리닝**이지 증명 아님(n 큰 per-clip으로 검정력 보완). 최종 PASS/FAIL은 S1+S2.

## 6. 산출물
- `r1_gates/output/gq1_s0.json` **갱신**: `model_signals` 블록(신호 정의·사전등록 선택)·`divergence_full`(5종 ρ/Jaccard 행렬)·`s0_verdict`(early-cut 결과).
- `r1_gates/output/gq1_s0_model_perclip.npz`: `token`, `uncertainty`, `scaling_gain`, (`recov_cluster`), `valid_mask`.
- 기존 `gq1_s0_perclip.npz`(model-free)와 token으로 조인 가능하게.

## 7. 착수 전 사전등록 결정 (2개)
1. **recoverability_proxy 포함 여부**: (A) 1-step reducible loss cluster-level 포함 vs (B) S0는 4종만·회복가치 S1위임. → 권고 **(A)**: 발산의 핵심 축이 recoverability라 S0에서 한 번은 봐야 조기 컷 의미. 단 구현·시간 여유 없으면 (B)로 시작해도 S1이 본증명.
2. **uncertainty 정의**: mode-엔트로피 고정(위 §2a). 변경 시 여기 기록.

## 8. 구현 단계 (다음 작업)
1. `results.pkl` 로더 + token 정렬 유틸(불완전 GT 마스크 공유).
2. uncertainty(엔트로피)·scaling_gain(L2 tail) per-clip 산출 — 순수 numpy/torch, GPU 불필요.
3. (결정 A면) cluster-level 1-step reducible loss 러너 — stage2 헤드 1스텝, GPU1 잠깐.
4. `s0_features.divergence` 재사용해 5종 행렬 → json/npz 기록 + verdict.
5. **self-check(`demo()`/`__main__`)**: 합성 신호로 (i) 완전상관 ρ≈1·독립 ρ≈0, (ii) 정렬 조인 라운드트립, (iii) 엔트로피 경계(균등=최대·단일=0) assert. 프레임워크 없이.

## 9. 통제 (thesis 보호)
- diversity/coverage는 **model-free feature만**(캡션/kinematics/맵) — 지각 backbone feature 금지(§5-4, 쓰면 model-coupled=붕괴). ← `s0_features` 이미 준수.
- scope 명시: **"planning recoverability given fixed perception"**(stage1 동결). 결핍이 perception이면 회복가치 과소평가 → S1에서 full-stage leave-out 1~2개로 캘리브(§5-1).
- eval-슬라이스 누수: recoverability 1-step/오라클 arm은 c의 eval 슬라이스 학습 제외(§5-2).
