# G-Q1 / S1 — 클러스터 오라클 인과 회복가치(leave-out) 설계·하네스

> 상위: `GQ1_design.md §3-S1`, `S0_MODEL_SIGNALS_DESIGN.md`. 기질 R0(`../r0_repro`, SparseDrive-S).
> 목적: S0(무재학습 발산 스크리닝)를 **오라클 인과 회복가치**로 확증한다. 작성 2026-08-12.
> 생사: recov(오라클) vs {uncertainty, diversity, scaling_gain} 발산 = Plan C-temporal 정당; 수렴 = scoop.

---

## 0. 증명 대상 (S1 = 발산 확증)
오라클 회복가치가 싼 신호(uncertainty·diversity·scaling_gain)와 **순위가 다르다**(중복 아님).
- 지표: **Spearman ρ + top-⌈n/3⌉ Jaccard** (recov vs 각 싼신호).
- 판정(사전등록, §5): max|ρ|≤0.5 & max Jaccard≤0.5 → **DIVERGE 확증**(S2 진입). |ρ|≥0.7 → **FAIL(scoop)**.

## 1. 오라클 회복가치 정의
**ΔTail_c = Tail_c(train-minus-c 재학습) − Tail_c(full 재학습)**
- 두 arm 모두 **stage2-only 재학습, stage1(perception) 동결**. 동일 recipe, ann_file만 차이.
- `Tail_c` = 클러스터 c의 **val eval 슬라이스** 평균 planning L2 (per-clip 순간 L2 6-step 평균).
- ΔTail_c > 0 = c를 빼면 c-슬라이스 tail이 악화 = c의 회복가치(인과 기여) 큼.
- **scope**: "planning recoverability **given fixed perception**"(stage1 동결). 결핍이 perception이면 과소평가 →
  §6 full-stage leave-out 1~2개로 근사오차 캘리브.

## 2. 하네스 (3 파일)
| 파일 | 역할 | GPU |
|---|---|---|
| `s1_leaveout.py` | **offline**: `prep`(centroid 재현+val→train 투영+leave-out pkl) · `tail`(results.pkl→per-cluster tail) · `oracle`(ΔTail→발산·판정) | 불필요 |
| `projects/configs/s1_leaveout_stage2.py` | stage2 base 상속 + **FreezeStage1Hook**(stage1.pth param 동결) + leave-out ann_file(env `S1_LEAVEOUT`) + 1-GPU/epochs(env) | — |
| `r0_repro/s1_run.sh` | 한 arm 학습→eval(`--out results.pkl`)→tail. `--launcher none`, `CUDA_VISIBLE_DEVICES` | 1 |

### 실행 흐름
```
# 0) 준비(1회): centroid 재현 + val 투영 + leave-out pkl 20개
python s1_leaveout.py prep            # → output_val/val_subdef_trainaligned.npz, data/infos/leaveout/*.pkl
# 1) baseline arm(full) 학습+tail
setsid bash r0_repro/s1_run.sh baseline 1
# 2) 각 leave-out arm (병렬 2 GPU 가능)
setsid bash r0_repro/s1_run.sh c5 1
setsid bash r0_repro/s1_run.sh c8 0   # GPU0은 Carla 상주 확인 후
# 3) 발산·판정
python s1_leaveout.py oracle --baseline output_val/tail_baseline.json \
   --leaveout_tails output_val/tail_c*.json   # → output_val/gq1_s1.json
```

## 3. ⚠️ 정렬 함정 2건 (둘 다 하네스가 처리)
1. **results ↔ infos 순서**: `results.pkl` 순서 = eval dataloader 순서 = **timestamp 정렬**
   (`nuscenes_3d_dataset.py:282`, load_interval=1). raw infos로 짝지으면 L2가 5~6m로 폭주(스크램블).
   → `offline_signals`가 timestamp 정렬 후 짝지음. **(이 버그가 기존 S0 model-signal을 오염 — §7)**
2. **train c번 ≠ val c번**: `s0_features.run()`은 train/val을 독립 KMeans(데이터셋별 표준화·재적합).
   → val eval 슬라이스는 **train centroid에 투영**해 정의(`project_val`). centroid 재현 일치율=**1.0000** 검증.

## 4. 결핍 단위·검정력
- train 서브결핍 20개(`output/gq1_s0_perclip.npz` subdef, 크기 118~710).
- **val 투영 슬라이스 크기**(prep 산출): 대부분 26~176, 단 **c4=2·c5=13은 과소** → tail 불안정.
- 사용 클러스터 = **val 슬라이스 ≥30**(≈16개: c0,1,2,7,8,9,10,11,12,13,14,15,16,17,18,19). n=16 = §5 검정력 하한.
- ρ≈0.5+만 검출 → S0 per-clip(大 n)로 발산 검정력 보완. **S1은 인과 확증이지 고정밀 순위 아님.**

## 5. 사전등록 판정 (결과 전 고정)
| 결과 | 조건 | 처분 |
|---|---|---|
| **DIVERGE 확증** | recov vs {unc,div} max\|ρ\|≤0.5 & max Jaccard≤0.5 | S2 우위 획득 라운드 진입 |
| **FAIL(scoop)** | \|ρ\|≥0.7 (unc/div와) | Plan C-temporal 기각 → ActiveAD 흡수 |
| **AMBIGUOUS** | 그 사이 | G0 고여지 층화 재검 |

## 6. 교란·통제
1. **stage2-only 타당성**: full-stage leave-out 1~2개(예 c17·c9)로 ΔTail 근사오차 캘리브(R0 §4). scope 명시.
2. **eval-슬라이스 누수**: leave-out은 **train에서만** c 제거(val 슬라이스는 평가용, 학습 제외 자동).
3. **BN running-stat**: frozen perception BN이 train모드로 갱신 → 두 arm 공통 recipe라 ΔTail에서 common-mode 상쇄
   (config 주석). 정밀 필요시 frozen 모듈 `.eval()` 훅 추가.
4. **diversity model-free**: 캡션/kinematics/맵만(§S0). 지각 backbone feature 금지.

## 7. ⚠️ 기존 S0 결과 무효 (이번 세션 발견)
- 기존 `output_val/gq1_s0_model.json`의 **DIVERGE(ρ_recov≈0.02)**는 §3-1 정렬버그로 **스크램블된 값** — 신뢰 불가.
- 교정 후 싼신호 상호상관 상승: `unc|div` 0.30→**0.47**, `unc|scg` −0.02→**0.33** (교정 npz 재생성 완료).
- recoverability(1-step proxy)도 같은 버그 + `recoverability_1step`이 sorted dataset을 raw subdef로 인덱싱 → **이중 오정렬**.
- **처분**: S0 verdict는 폐기. 발산 증명은 **S1 오라클**이 담당(설계상 "S0=스크리닝, S1+S2=증명"과 정합).
  S0 싼신호 상관은 교정본 사용. S0 1-step recov는 재실행 불요(오라클로 대체).

## 8. 비용 (실측 기반, §아래 업데이트)
- arm당 stage2-only 재학습: bs4·1GPU·`S1_EPOCHS` epochs, `num_iters/epoch=7032`.
- 실측 iter-time → 아래 RESULTS에 기록. epochs·클러스터 수는 **비용/수렴 트레이드오프(사용자 결정)**.
- baseline 1 + leave-out ~16 = **17 arm**. 2 GPU 병렬 시 벽시계 ≈ (17/2)×(arm시간).

## 9. 산출물
- `output_val/val_subdef_trainaligned.npz`(투영), `data/infos/leaveout/train_minus_c*.pkl`.
- `output_val/tail_<arm>.json`(arm별 per-cluster tail), `output_val/gq1_s1.json`(발산·판정).
- `GQ1_S1_RESULTS.md`(실측 비용·판정 로그).

## 10. 스킵(의도적, ponytail)
- collision-rate per-slice tail → 후속(현 tail=mean L2). per-clip collision 미계산.
- BN eval-mode 정밀 동결 → common-mode 상쇄로 defer.
- 20개 전수 대신 val 슬라이스 ≥30인 ~16개만.
