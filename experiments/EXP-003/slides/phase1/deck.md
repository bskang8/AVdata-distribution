---
marp: true
theme: disc
paginate: true
math: katex
header: 'EXP-003 Phase 1 · 획득함수 조립·검증'
---

<!-- _class: title -->
<!-- _paginate: false -->
<!-- _header: '' -->

# 데이터 획득함수 조립·검증

## Phase 1 결과 요약

**ODD × 임베딩을 어떻게 활용해야 하나**
`experiments/EXP-003/phase1/` · `RESULTS.md`

---

<!-- _class: section -->
<!-- _paginate: false -->

# 0 · Phase 1의 목적

### egomotion 성능 자체가 아니라 —
### **ODD와 임베딩 두 렌즈를 획득함수에서 어떻게 써야 하는지**를 실측으로 규명

---

## 0 · 파이프라인 — 진단(Phase 0) → 처방(획득함수) → 검증(leave-out)

<div class="cols">
<div>

**Phase 0**은 *"두 렌즈는 직교한다"*를 **기술적으로** 보였다(η²=21%, NN이 셀 경계 넘나듦).
**Phase 1**은 그 두 렌즈를 **획득함수로 조립**하고, 실제로 어느 렌즈가 성능을 올리는지 **downstream으로** 시험한다.

```
compute_surrogate ─ CV per-clip ADE/FDE
      │
aggregate_error ─ model_error(c) + Domino
      │
priority ─ Priority(c) 5인자 랭킹
      ├ learned_surrogate ─ CV→학습형(격상)
      ├ extend_exposure ─ urban/rural 손앵커
      └ leaveout ─ §5 정책 5종 회복량 비교
```

</div>
<div>

**성능 대리지표 = egomotion 궤적 예측난이도(ADE/FDE)**
라벨 없이 ego 궤적 자체를 GT로 "과거 2s → 미래 3s" 예측 → 오차 = 그 조건의 예측 어려움.

<div class="kpi-row">
<div class="kpi"><div class="v">97,820</div><div class="l"><b>valid 클립</b><br>커버 97.4% (100,398 중)</div></div>
<div class="kpi"><div class="v">282</div><div class="l"><b>ODD 셀</b><br>valid의 94% 커버</div></div>
</div>

<div class="kpi-row">
<div class="kpi"><div class="v">676,624</div><div class="l"><b>학습 창</b><br>학습형 예측기 학습 표본</div></div>
<div class="kpi"><div class="v">5</div><div class="l"><b>인자</b><br>Priority(c) 구성</div></div>
</div>

</div>
</div>

---

## 0 · 획득함수 `Priority(c)` — 다섯 인자 · 두 렌즈 역할 분담

$$\text{Priority}(c)=\text{criticality}\times\text{exposure}\times\text{deficit}\times\text{model\_error}\times\text{headroom}$$

| 인자 | 의미 | 담당 렌즈 |
|---|---|---|
| **criticality** | 안전 심각도(사고·VRU·악천후) | ODD |
| **exposure** | 현실 노출빈도 $P_{ext}$ | ODD + 기관통계 |
| **deficit** | 과/소수집 $\log(P_{ext}/P_{self})$ | ODD |
| **model_error** | 이 조건에서 모델이 실제 틀리나 | egomotion ADE/FDE |
| **headroom** | 채울 값어치(비중복 여력) | 임베딩 |

> 셀 $c$ = coarse `road_type\|weather\|fog` (exposure 결정공간이자 **이름 있는** 수집발주 단위). 방법론이 배정한 역할 — <span class="danger">ODD가 4인자, 임베딩이 headroom</span> — 을 Phase 1이 실측으로 검증한다.

---

<!-- _class: section -->
<!-- _paginate: false -->

# 1 · 중간 발견 — 신호 격상

### 학습형 model_error · exposure 손앵커 확장

---

## 1 · CV → 학습형 예측기 — model_error를 "분포 의존" 신호로 격상

<div class="cols">
<div>

**왜 교체하나** — CV는 클립별 자기적합이라 오차 = *"기동 절대복잡도"*.
**전역 학습모델**(canonical MLP, GroupKFold OOF)은 fleet 평균 동역학에 맞춰져 오차 = <span class="danger">**"fleet 기준 비전형성"**</span> = 분포 의존 신호. same-clip 누수 차단.

| | CV | 학습형 |
|---|--:|--:|
| ADE p50 | 2.16 | **0.94** |
| ADE p90 | 4.35 | 1.95 |
| 창 수 | — | 676,624 |

</div>
<div>

**검증** — 학습형 vs CV 셀별 model_error **Spearman 0.885**(대체로 일치)이나, **소수 셀**(n≈25)에서 +0.5~0.67 급등:

<div class="kpi-row">
<div class="kpi"><div class="v">0.885</div><div class="l"><b>Spearman</b><br>CV ↔ 학습형 (셀별)</div></div>
<div class="kpi"><div class="v">+0.67</div><div class="l"><b>최대 상승</b><br>희소 셀 (CV 저평가)</div></div>
</div>

> CV는 클립별 적응이라 희소 동역학을 **저평가** → 전역모델은 못 배운 조건에서 실패 → ME↑. "기동 복잡도"가 아니라 **"조건 비전형성"**을 잰다.

</div>
</div>

---

## 1 · exposure를 urban/rural로 확장 — 손앵커 + 민감도 스윕

<div class="cols">
<div>

**문제**: $P_{ext}$(KTDB)가 highway·national_road **2/4등급만**(rural 502·urban 미조사).
**처방**: 관측 hw:nr 비율은 보존, {trunk,urban,rural} 구성만 **손앵커**(통계연보 근사, 관측 아님) → 5앵커 **민감도 스윕**.

**road_type 과/소수집** `deficit logr` (>0 과소=수집 / <0 과대=프루닝):

| anchor | national | rural |
|---|--:|--:|
| central | +4.69 | −0.98 |
| urban_heavy | +4.44 | −0.70 |
| trunk_heavy | +4.89 | −0.98 |
| rural_light | +4.79 | −1.39 |

</div>
<div>

**부호 안정성** — 앵커를 흔들어도 결론이 뒤집히나:

<div class="kpi-row">
<div class="kpi"><div class="v">national</div><div class="l"><b>강건히 과소수집</b><br>→ 수집 (부호 안정 ✓)</div></div>
<div class="kpi danger"><div class="v">rural</div><div class="l"><b>강건히 과대수집</b><br>→ 프루닝 후보 (안정 ✓)</div></div>
</div>

> highway·urban은 near-balanced라 손앵커에 민감 → <span class="warn">결론 보류</span>. 랭킹 견고성: 중심 대비 **Spearman 0.971~1.0**. 결론은 **앵커 불변 항목**(national·rural)에만 국한 — 손앵커 불확실성을 정직하게 격리.

</div>
</div>

---

## 1 · 최종 Priority 랭킹 (학습형 ME × 확장 exposure)

<div class="cols">
<div>

**priority_core** (crit × ME × headroom)

| 셀 | core | crit | ME |
|---|--:|--:|--:|
| rural·snow·present | **0.76** | 6.0 | 1.00 |
| rural·clear·present | 0.11 | 2.4 | 0.64 |
| urban·clear·present | 0.08 | 2.0 | 0.63 |

</div>
<div>

**priority_full** (× exposure × deficit)

| 셀 | full | ME | logr |
|---|--:|--:|--:|
| urban·clear·present | **0.011** | 0.63 | 3.47 |
| rural·clear·present | 0.003 | 0.64 | 0.94 |
| national·clear·none | 0.002 | 0.16 | 4.50 |

</div>
</div>

> **exposure × model_error 충돌**: highway는 과소수집(exposure↑)이나 예측 쉬움(ME↓) → 곱이 상쇄 = *"더 안 모아도 됨"*(정답). 최우선은 <span class="danger">빈발·과소수집·모델실패가 겹친 `urban·clear·present`(안개)</span>. `rural·snow·present`는 core 1위지만 exposure 희소라 full에선 내려감 — ΔRisk=빈도×심각도×오차 가중이 의도대로 작동.

---

<!-- _class: section -->
<!-- _paginate: false -->

# 2 · 검증 — §5 leave-out 재현실험

### 정책별로 다시 "획득"해 성능 회복량 비교 · G4 시험

---

## 2 · 실험 설계 — 결핍 학습셋 → 정책별 되메움 → 회복량

<div class="cols">
<div>

**테스트베드** = 학습형 예측기, 입력 = kinematics(6) + **PCA 임베딩(16)**
*(순수 kinematics면 조건축을 학습할 통로가 없어 초기 smoke가 전 정책 회복 실패 → 장면 feature 필수)*

**5 정책**이 candidate에서 예산만큼 골라 되메움 → 재학습 → test **tail 영역** ADE 회복:
`guided`(Priority) · `random` · `coverage`(ODD 분산) · `uncertainty`(per-clip ADE) · `diversity`(임베딩 FPS)

</div>
<div>

**통제 장치** (도출의 합리성 근거)

| 장치 | 무엇을 막나 |
|---|---|
| 음성/양성 **대조쌍** | 회복부재 vs 데이터부족 혼동 |
| **다중 seed(5)** | 단일 seed 우연 |
| `tail_picked` | 실패를 *선택 오조준*으로 인과규명 |
| **mixed pool** | 정책 변별력 실제 시험 |
| GroupKFold | same-clip 누수 |

> 두 시나리오 = **adverse**(snow/fog, ODD축) vs **kinematic**(고yaw, feature축).

</div>
</div>

---

## 2 · 결과 — G4 미성립, 그리고 `tail_picked`가 밝힌 이유

<style scoped>
table td:nth-child(2){font-weight:700}
</style>

**kinematic** (실재 결핍 · baseline tail ADE 0.984 > overall) — 회복 mean±std:

| 정책 | 회복 | tail 집은 비율 |
|---|--:|--:|
| diversity (임베딩 spread) | **+0.060 ± 0.015** | 33% |
| coverage (ODD spread) | +0.059 ± 0.030 | 50% |
| random | +0.044 ± 0.027 | 25% |
| uncertainty | +0.019 ± 0.019 | 29% |
| **guided (ODD-조건 Priority)** | <span class="danger">**+0.007 ± 0.019**</span> | <span class="danger">**23%**</span> |

> **결정적 진단**: guided가 유용 클립을 **23%만** 집음 — <span class="danger">random(25%)보다도 낮다</span>. 고yaw 급기동은 평범한 ODD조건(urban/highway·clear)에 살아 cell_context가 낮음 → guided가 **회피** → 예산 낭비 → 꼴찌. **adverse**는 baseline(0.916) < overall = 결핍 자체가 없음(전 정책 ≈0).

---

<!-- _class: section -->
<!-- _paginate: false -->

# 3 · 중간결론

### ODD·임베딩을 어떻게 써야 하는가 — 근거 기반 도출

---

## 3 · 결론 ①②③ — 역할 분담 · model_error의 축 · 조건 무관성

<div class="cols">
<div>

**① 두 렌즈는 다른 질문에 답한다**
ODD = *분포·안전·주소*(exposure·deficit·명명) / 임베딩 = *성능·중복*.
근거: exposure 부호안정(임베딩으론 산출 불가) + diversity 회복 1위. → **대체 불가 = 직교**.

**② model_error는 ODD 셀이 아니라 <span class="danger">임베딩 축</span>에 산다**
guided(ODD셀 집계)는 신호 소실, 같은 오차를 임베딩(diversity)으로 쓰면 살아남. → 방법론 §2 배정 **역전**: 임베딩-first로 실패지점 찾고 → ODD로 명명.

</div>
<div>

**③ ODD-조건은 egomotion 성능을 예측하지 못한다**
음성 대조: adverse baseline **0.916 < overall** = 결핍 부재(전 정책 ≈0). kinematic만 실재 결핍(+0.06). → egomotion 실패는 **기동축**, ODD-조건축과 **직교**.

<div class="kpi-row">
<div class="kpi"><div class="v">23%</div><div class="l"><b>guided tail 선택</b><br>random 25%보다 낮음 = 오조준</div></div>
</div>

> ②③이 곧 Phase 0 "직교"의 downstream 확인 + 사용법 처방.

</div>
</div>

---

## 3 · 결론 ④⑤ + 도출의 합리성

<div class="cols">
<div>

**④ spread로 쓰면 이기고, 가중 타게팅은 진다**
순위 = coverage(ODD-spread) ≈ diversity(임베딩-spread) > random > uncertainty > **guided**. 두 렌즈를 native "고루 덮기"로 쓸 때 유효. 심각도/exposure 과가중(guided)은 오조준, per-clip 오차 추종(uncertainty)은 **환원불가 노이즈**를 쫓음.

**⑤ ODD의 성능역할은 반증 아닌 <span class="warn">미검증</span>**
guided 실패 원인 = egomotion 실패축(기동)과 ODD-조건의 약한 연결(구조적 핸디캡). condition-sensitive task에선 정렬될 것.

</div>
<div>

**확증 vs 미검증 — 정직한 경계**

| | 항목 |
|---|---|
| ✅ 확증 | ODD 분포·안전역할(exposure) · 임베딩 성능역할(diversity) · 두 축 직교 |
| ❓ 미검증 | **ODD 조건이 성능 예측**(=두-렌즈 G4) — perception task로 이관 |

> 각 결론이 특정 수치·대조에 묶여 있어 `leaveout_results.json`·`exposure_sweep.json`·`EXECUTION_LOG.md`로 **재현·추적 가능**.

</div>
</div>

---

<!-- _class: statement -->
<!-- _paginate: false -->

> **ODD**는 *무엇을 수집할지*(현실·안전·이름)를, **임베딩**은 *그게 모델을 실제로 개선하는지*(성능·중복)를 담당하며, 둘은 직교해 반드시 함께 써야 한다.
> 단, 성능 신호(**model_error**)는 <strong>ODD 셀이 아니라 임베딩 축</strong>에서 측정해 ODD로 명명해야 한다.

---

<!-- _class: section -->
<!-- _paginate: false -->

# 4 · 다음

### ODD 두-렌즈 G4는 **condition-sensitive 다운스트림**(perception)으로 이관
### egomotion은 임베딩 성능역할 · exposure 과소수집(national 수집·rural 프루닝) 검증에 유효
