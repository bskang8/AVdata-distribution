# G-Q1 결과 로그

> 설계 `GQ1_design.md`. 코드 `s0_features.py`. 출력 `output/gq1_s0.json`·`output/gq1_s0_perclip.npz`.

## S0 — model-free 부분 완료 (2026-08-11)

**실행**: `python s0_features.py --outdir output` (train infos 28130, 무재학습, R0 venv).

### 결핍 클러스터 (정의 완료)
- candidate = **21.9%**(6149/28130) — tail minority(정제 전 61%였음, 아래 수정).
- 태그(다중 가능): high_interaction 3906(14%)·sharp_turn 2250(8%)·unprotected_left 370(1.3%).
- 서브결핍 **20개**(KMeans over 후보), 크기 118~710 균형. 지배태그 high_interaction 11·sharp_turn 9. 도시: boston 13·singapore 7(밀도 반영).
- 임계(분위 기반): lat_hi=3.18m(횡변위 상위8%)·dist_lo=3.46m(근접 하위12%)·close_hi=11(밀집 상위5%)·agents_hi=31.

### 정제 이력 (첫 컷의 실제 결함 3개 수정)
1. **curvature 저속 폭주**(q98=8705 rad/m) → speed<2m/s는 0, 물리상한 1.0 rad/m clip. (표준화·KMeans 오염 제거)
2. **interaction 임계 과대**(min_dist<6=median) → 분위 tail(dist_lo=q12·close_hi=q95).
3. **occlusion_proxy 제거** — n_agents/밀도로는 42% 오탐, model-free 추론 불가 → M0/perception 필요로 이관.

### 신호
- 계산됨(model-free): `diversity`(kNN 평균거리)·`coverage_redundancy`(SemDeDup식 1/최근접). 상호 ρ=−0.87(역구성, sanity).
- **deferred(M0 필요)**: `recoverability_proxy`(1-step reducible loss)·`uncertainty`(mode엔트로피/stage2 앙상블)·`scaling_gain`(cluster tail-error).

### 판정
- **S0 발산 결론 미완** — G-Q1 핵심(회복가치 vs uncertainty/diversity)은 M0 없이는 불가. 현재 가용 2신호만으론 발산 판정 못 함.
- 준비 완료: 클러스터·서브결핍·model-agnostic 신호·발산 하니스(pluggable). npz에 per-clip token·subdef·신호·feature 저장 → M0 후 주입만.

## 다음
- **M0 학습(보류 중) 후**: `s0_model_signals.py`로 3 deferred 신호 계산 → `divergence()` 하니스에 주입 → S0 발산 행렬 완성 → G-Q1 사전등록 판정(GQ1_design §4).
- occlusion 결핍은 M0 perception 신호로 별도 정의.
