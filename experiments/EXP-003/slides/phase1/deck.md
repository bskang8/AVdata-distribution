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

### egomotion **점수**가 목적이 아니라 — 그 예측오차를 **자로 삼아**:
### ① **수집 가이드를 어떻게 설계할지** 원리를 도출하고 ② 그 설계에 **ODD·임베딩을 쓰는 게 타당한지** 실측한다

---

## 0 · 한눈에 — 목적 · 실험 계획 · 다음 수행

<style scoped>
.ov{display:flex;flex-direction:column;gap:9px;font-size:9.2pt;line-height:1.5;margin-top:4px}
.sec{border-radius:10px;padding:9px 14px}
.sec .lbl{font-weight:800;color:#001F60;font-size:10pt;margin-bottom:5px}
.sec .lbl .tag{background:#001F60;color:#fff;border-radius:5px;padding:1px 9px;font-size:9pt;margin-right:8px;letter-spacing:.5px}
.goal{background:#f2f7fb;border:1.5px solid #bcd6e6}
.plan{background:#f6f8fb;border:1px solid #dbe3ec}
.res{background:#eef7f0;border:1.5px solid #b9dcc1}
.next{background:#fbf6ec;border:1px solid #ecdcbf}
.q{color:#00586F;font-weight:800}
.steps{display:flex;gap:8px;margin:7px 0 6px}
.step{flex:1;background:#fff;border:1px solid #cddcee;border-radius:7px;padding:6px 10px;font-size:8.5pt;line-height:1.45}
.step b{color:#001F60}
.pol code{font-size:.9em;background:#eef2f7;padding:0 3px;border-radius:3px}
.bot{display:flex;gap:9px}
.bot .sec{flex:1;margin:0}
.res .lbl .tag{background:#1f7a43}.next .lbl .tag{background:#b5701a}
.res div,.next div{margin:2px 0}
.flow{margin:6px 0 5px}
.fl1{display:flex;align-items:center;justify-content:center;gap:10px}
.node{background:#fff;border:1.5px solid #bcd6e6;border-radius:7px;padding:5px 12px;color:#001F60;font-weight:700;text-align:center;line-height:1.25;font-size:8.6pt}
.node.base{border-color:#e0b877;background:#fbf6ec}
.arr{color:#00586F;font-weight:700;text-align:center;font-size:8.2pt;line-height:1.25}
.fan{text-align:center;color:#5f6470;font-size:8.5pt;margin:5px 0 4px}.fan b{color:#001F60}
.pols{display:flex;gap:6px;justify-content:center;margin-bottom:5px}
.chip{background:#eef2f7;border:1px solid #cddcee;border-radius:6px;padding:3px 9px;font-size:8.3pt;color:#333}
.chip.g{background:#fbecec;border-color:#e6b3b3;color:#a33;font-weight:700}
.conv{text-align:center;background:#f2f7fb;border:1px solid #cddcee;border-radius:7px;padding:5px 10px;font-size:8.5pt}.conv b{color:#001F60}
.note2{font-size:8pt;color:#5f6470;margin-top:6px;line-height:1.5}.note2 code{font-size:.92em;background:#eef2f7;padding:0 3px;border-radius:3px}.note2 b{color:#001F60}
.split2{display:flex;gap:9px;margin:5px 0}
.bx{flex:1;border-radius:8px;padding:7px 11px;font-size:8.4pt;line-height:1.35;text-align:center}
.bx.base{background:#fbf6ec;border:1.5px solid #e0b877}
.bx.cand{background:#eef4fb;border:1.5px solid #bcd6e6}
.bx b{color:#001F60}
.hl{color:#c0392b;font-weight:800}
.note2.two{display:flex;gap:14px}.note2.two>div{flex:1}.note2.two>div+div{border-left:1px solid #d5dce6;padding-left:12px}
.note2 .h{color:#001F60;font-weight:800;display:block;margin-bottom:2px}
</style>

<div class="ov">

<div class="sec goal">
<div class="lbl"><span class="tag">목적</span>정해진 예산(<b>≈5천 클립</b>)에서 성능이 가장 오르는 <b>데이터 수집 가이드</b>를 제시</div>
<span class="q">Q1</span> ODD·임베딩을 쓰는 게 <b>타당한가</b>(두 잣대 검증) &nbsp;→&nbsp; <span class="q">Q2</span> 타당하면 이 둘로 <b>어떻게 가이드를 짜나</b>(설계 원리)
</div>

<div class="sec plan">
<div class="lbl"><span class="tag">계획</span><b>target 조건</b>을 <b>ablation</b>해 결핍을 유도하고, <b>acquisition 정책</b>별로 보충·재학습하여 회복량을 분석하는 leave-out 벤치마크 · surrogate 소형 MLP</div>

<div class="flow">
<div class="fl1">
<span class="node">train pool<br>(전체의 75%)</span>
<span class="arr">➊ target 조건 클립<br><b>ablation (leave-out)</b> ▶</span>
</div>
<div class="split2">
<div class="bx base"><b>base 학습셋</b><br>non-target 클립만 (<span class="hl">target 0개</span>)<br>→ <b>결핍 base 모델</b> (획득 전 baseline)</div>
<div class="bx cand"><b>candidate pool</b><br>ablation된 target 전부 <b>+ distractor 3×</b><br>(정책이 여기서 <b>800클립 획득</b>)</div>
</div>
<div class="fan">➋ 각 acquisition 정책이 candidate pool에서 <b>서로 다른 기준으로</b> <b>800클립 획득</b>(base에 add) + <b>개별 재학습</b> ↓</div>
<div class="pols">
<span class="chip">random</span><span class="chip">coverage</span><span class="chip">diversity</span><span class="chip">uncertainty</span><span class="chip g">Priority</span>
</div>
<div class="conv">➌ held-out test(<b>target 조건 포함</b>)에서 <b>ΔADE = 회복량(recovery)</b>으로 정책 랭킹</div>
</div>

<div class="note2 two">
<div>
<span class="h">ablation 대상 (2 시나리오)</span>
· <b>kinematic</b> = 고yaw 급기동 상위4%(<b>3,913</b>클립) → <b>실재 결핍 O(양성)</b> → 회복 측정 가능, Priority 최하위<br>
· <b>adverse</b> = snow∨fog(<b>3,228</b>클립) → <b>결핍 X(이미 잘 예측, 음성 대조)</b> → 회복 불가 = 실험 검증
</div>
<div>
<span class="h">선택 기준 (각 정책이 무엇으로 클립을 뽑나)</span>
coverage = ODD 조건 골고루(spread) · diversity = 기존 선택과 유사도 최저인 것 반복 선택(임베딩) · uncertainty = 오차 큰 클립 우선(per-clip ADE) · <span class="danger">Priority = 두 축 종합점수 높은 것(fusion) — 후보로 평가</span>
</div>
</div>
</div>

<div class="sec res">
<div class="lbl"><span class="tag">결과</span>이번 실험 근거강도별</div>
<div><span class="danger">✅ <b>coverage·diversity(공간 고루 덮기)가 회복 최상위</b></span> — <b>통계적으로 견고</b>(회복이 편차의 ~3배↑) · 오차 큰 클립만 고르거나(uncertainty) 두 축을 곱한 Priority는 그보다 낮음 · <b>Priority 꼴찌 = 곱셈-타게팅 융합 실패</b>(<span class="warn">일반 "융합 금지" 아님 — 스코프는 §2</span>)</div>
<div>✅ <b>시험한 ODD-조건(악천후)은 egomotion 결핍과 무관</b> — 악천후 클립을 빼도 성능 그대로지만, 급기동 클립을 빼면 성능 저하. 난이도는 <b>날씨가 아니라 기동축</b>에 있음 · <span class="warn">ODD 전체 일반화는 미검증(→perception)</span></div>
<div><span class="warn">▲ (가설) <b>오차 큰 클립 노리는 정책들</b>의 오차(ADE) 매기는 방식(그 클립 자신 / ODD-카테고리 / 닮은 장면) 중 <b>'닮은 장면(임베딩 이웃) 평균'</b>으로 매긴 쪽이 회복 조금 큼</span> — §2 참조. <b>※ 전체 1위는 ODD 기반 coverage — '임베딩&gt;ODD'라는 뜻 아님</b></div>
<div><span class="warn">📎 <b>두 축 "상호보완 → 함께 써야"는 미실증 가설</b></span> (ODD=수집·현실빈도, 임베딩=성능) — 직교는 확증이나 <b>가산성·비대체성은 미측정</b> → 실험 C로 검증(§4)</div>
<div><span class="warn">❓ ODD의 성능예측 역할 미검증</span> — condition-sensitive task(perception)으로 이관해 완성</div>
</div>

</div>

> 이 덱의 축은 **"Priority가 좋은가"가 아니라 "ODD·임베딩을 어떻게 써야 하는가"**. Priority(융합)는 그 답을 찾기 위해 **시험대에 올린 귀무가설**이며, 실제로 진다.

---

## 0 · 파이프라인 — 진단(Phase 0) → 두 잣대 타당성 질문 → 전략 경쟁 검증

<div class="cols">
<div>

**Phase 0**: "두 잣대(ODD·임베딩)는 직교"를 기술적으로 확인(η²=21%, NN이 셀 경계 넘나듦).
**Phase 1**: 그 둘을 **어떻게 써야 하는지**를, 여러 수집 전략을 경쟁시켜 실측한다.

**가설 → 검증 흐름** (상세는 화살표 슬라이드)

| 단계 | 무엇을 · 어떻게 | 상세 |
|---|---|:--:|
| **[가설] ① 융합안** | 5인자 곱 = 클립별 `Priority` = 두 축을 한 점수로 **곱한 순진한 가설** | →4·8 |
| **[검증] ② 빼기** | 특정 조건(예: 고yaw) 클립을 학습셋서 **통째 제거** → 결핍 유발 | →10 |
| **[검증] ③ 규칙** | 각 잣대를 **정책**으로 — Priority 순 등으로 후보 선택(+대조 2종) | →10 |
| **[검증] ④ 성능** | 학습형 MLP 재학습 → "과거2초→미래3초" 오차=ADE **회복량** 비교 | →6·11 |

> **핵심 구분**: Priority **값끼리 비교가 아니라**, Priority로 고른 데이터가 재학습 후 **ADE를 더 줄였는지**(성능)로 판정 → 그래서 Priority(`guided`)가 **최선이 아니어도, 그 한계의 원인이 수집 가이드 설계 원리를 준다.**

**"그 한계의 원인 → 설계 원리"가 성립하는 근거** (진단 장치가 "졌다"를 원리로 승격)

- **기계적 진단**(`tail_picked`, →11): guided가 유용 클립을 23%만 집음(random 25% 이하) — 고yaw 급기동이 평범한 ODD조건에 살아 **구조적으로 회피**. 성능 노이즈가 아니라 *오조준의 원인*이 드러남 → 원리: **성능신호를 ODD 셀에서 재지 말 것 · 두 축을 하나로 곱하지 말 것(융합 금지)**.
- **우연 배제**: 음/양성 대조쌍 · 다중 seed(5)±std · S1 격리실험(→12)이 "우연히 졌다"를 걷어내 승패를 원리로 쓸 자격 부여.

</div>
<div>

**성능 대리지표 = 예측오차(ADE) — 예측이 실제 경로에서 평균 몇 m 빗나갔나**
라벨 없이 ego 궤적 자체를 GT로 삼아 "과거 2초 → 미래 3초" 궤적을 예측하고 실제 주행경로와 비교. 많이 빗나갈수록(ADE↑) 그 조건이 예측하기 어렵다는 뜻.

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

## 0 · 시험대에 올릴 융합 가설 `Priority(c)` — 두 축을 한 점수로 곱하면?

$$\text{Priority}(c)=\text{criticality}\times\text{exposure}\times\text{deficit}\times\text{model\_error}\times\text{headroom}$$

<div class="cols">
<div>

| 인자 | 의미 | 담당 잣대 |
|---|---|---|
| **criticality** | 안전 심각도(사고·VRU·악천후) | ODD |
| **exposure** | 현실 노출빈도 $P_{ext}$ | ODD + 기관통계 |
| **deficit** | 과/소수집 $\log(P_{ext}/P_{self})$ | ODD |
| **model_error** | 이 조건에서 모델이 실제 틀리나 | egomotion ADE/FDE |
| **headroom** | 채울 값어치(비중복 여력) | 임베딩 |

</div>
<div>

**조립 = 정규화 → 곱 → 셀→클립**
1. **정규화 [0,1]** — criticality·exposure·deficit·headroom은 **min-max**, model_error는 **가중 CDF** → 스케일·부호 통일(deficit 음수도 흡수).
2. **곱(conjunctive)** — 모든 인자가 높아야 우선(하나라도 낮으면 하향) = 위험·빈발·과소·모델실패·비중복이 **겹치는** 셀.
3. **셀→클립** — 셀 점수(cell_context)를 클립 per-clip model_error에 곱해 **클립 랭킹**(leave-out `guided`).

</div>
</div>

> 셀 $c$ = coarse `road_type\|weather\|fog` (exposure 결정공간이자 **이름 있는** 수집발주 단위). **core**=crit×ME×headroom(전 셀) · **full**=×exposure×deficit(P_ext 정의 셀만, →8). 방법론 배정 — <span class="danger">ODD 4인자·임베딩 headroom</span> — 을 Phase 1이 실측 검증.

---

<!-- _class: section -->
<!-- _paginate: false -->

# 1 · 개별 잣대가 의미있는 신호인지 정당화

### 성능신호(model_error) 학습형 격상 · 분포신호(exposure) 손앵커 확장

---

## 1 · CV → 학습형 예측기 — model_error를 "분포 의존" 신호로 격상

<div class="cols">
<div>

**무엇** — ego 궤적 "과거 2초 → 미래 3초" 예측(라벨 없이 **궤적 자체가 GT**). 오차(ADE)가 곧 그 조건의 예측 난이도.

**왜 CV→학습형 교체** — CV는 클립별 자기적합 → 오차 = *"기동 절대복잡도"*. **전역 MLP**(fleet 평균 동역학)로 바꾸면 오차 = <span class="danger">**"fleet 기준 비전형성"**</span> = 분포 의존 신호.

**누수 차단** — GroupKFold **OOF**(클립 단위 분리, out-of-fold 예측만) → "모델이 **못 본** 조건에서 틀린다"가 성립(same-clip 창 누수 제거). 이게 model_error를 정당화.

| | CV | 학습형 |
|---|--:|--:|
| ADE p50 | 2.16 | **0.94** |
| ADE p90 | 4.35 | 1.95 |
| 학습 창 | — | 676,624 |

</div>
<div>

**`model_error(c)`** = 학습형 per-clip ADE를 ODD 셀별 **가중 CDF**로 집계 = "이 조건에서 모델이 실제 틀리나".

**검증** — 학습형 vs CV 셀별 model_error **Spearman 0.885**(대체로 일치)이나, **희소 셀**(n≈25)에서 +0.5~0.67 급등:

<div class="kpi-row">
<div class="kpi"><div class="v">0.885</div><div class="l"><b>Spearman</b><br>CV ↔ 학습형 (셀별)</div></div>
<div class="kpi"><div class="v">+0.67</div><div class="l"><b>최대 상승</b><br>희소 셀 (CV 저평가)</div></div>
</div>

> CV는 클립별 적응이라 희소 동역학을 **저평가** → 전역모델은 못 배운 조건에서 실패 → ME↑. "기동 복잡도"가 아니라 "**조건 비전형성**"을 잰다.

</div>
</div>

---

## 1 · exposure를 urban/rural로 확장 — 손앵커 + 민감도 스윕

<div class="cols">
<div>

**지표** — `deficit = log(P_ext / P_self)`. $P_{ext}$=**현실 노출빈도**(기관통계), $P_{self}$=우리 데이터 자기분포. **>0 과소수집(→수집) / <0 과대수집(→프루닝)**.

**문제** — $P_{ext}$ 출처 KTDB(교통량 통계)가 highway·national_road **2/4등급만** 조사(rural·urban 미조사).
**처방** — 관측 hw:nr 비율 보존, 미조사 {trunk,urban,rural} 구성만 **손앵커**(통계연보 근사, 관측 아님) → 가정 바꾼 **5앵커 민감도 스윕**.

**road_type별 `deficit`** (앵커별):

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

## 1 · 융합 가설의 출력 — Priority 랭킹 (학습형 ME × 확장 exposure) → §2에서 반증

<div class="cols">
<div>

**priority_core** — 안전·성능만 (exposure 제외, **진단용**)

| 셀 | core | crit | ME | head |
|---|--:|--:|--:|--:|
| rural·snow·present | **0.76** | 6.0 | 1.00 | 0.76 |
| rural·clear·present | 0.11 | 2.4 | 0.64 | 0.60 |
| urban·clear·present | 0.08 | 2.0 | 0.63 | 0.65 |

</div>
<div>

**priority_full** — ×exposure×deficit = **최종 수집 우선순위**

| 셀 | full | ME | logr |
|---|--:|--:|--:|
| urban·clear·present | **0.011** | 0.63 | 3.47 |
| rural·clear·present | 0.003 | 0.64 | 0.94 |
| national·clear·none | 0.002 | 0.16 | 4.50 |

</div>
</div>

> **읽는 법** (17 coarse 셀 중 top-3): 표는 해석용 값 — **crit·logr=원시값, ME·head=정규화[0,1]**. 점수(core/full)는 **정규화값의 곱**이라 원시 crit(6.0)로는 검산 안 됨(실제 crit_n≤1).

> **exposure × model_error 충돌**: highway는 과소수집(exposure↑)이나 예측 쉬움(ME↓) → 곱이 상쇄 = *"더 안 모아도 됨"*(정답). 최우선은 <span class="danger">빈발·과소수집·모델실패가 겹친 `urban·clear·present`(안개)</span>. `rural·snow·present`는 core 1위지만 exposure 희소라 full에선 내려감 — ΔRisk=빈도×심각도×오차 가중이 의도대로 작동.

---

<!-- _class: section -->
<!-- _paginate: false -->

# 2 · 구축 전략 경쟁 — 어느 설계가 이기나

### 5가지 수집 전략을 leave-out으로 겨뤄 **설계 원리**를 도출 (Priority는 그중 한 후보 = 순진한 융합안)

---

## 2 · 실험 설계 — 클립을 4분할해 "결핍 → 되메움 → 회복" 측정

<div class="cols">
<div>

**아이디어**: 특정 조건을 학습셋에서 **일부러 빼고**(결핍), 정책이 후보에서 **되메워**(획득), 그 조건의 예측오차가 **얼마나 회복되나**로 정책을 채점. 테스트베드 = 학습형 예측기(**surrogate = 소형 MLP**(22→32→16→12, scikit-learn) — **model_error 생성기(슬라이드 6)와 별개 · 정책마다 재학습**, 입력 kinematics 6 + **임베딩 PCA 16** — 순수 kinematics면 조건축 학습 통로가 없어 전 정책 회복 실패, 임베딩이 장면조건 통로).

```
clips-with-windows
├ test (25%, seed고정)  ── 전 정책 공통 평가셋
│                         회복은 test의 "tail 영역"에서만 측정
└ pool (75%)
   ├ tail = 결핍조건 클립 ─────────┐ 학습셋서 제거
   └ common                        ├→ candidate (정책이 픽)
      ├ 잉여(tail×3)=무용 미끼 ────┘
      └ 나머지 = base (tail 결핍 학습셋)
```

**회복 = ADE_base − ADE_add** — 예산 B∈{0,400,800} 픽을 base에 add·재학습. baseline(B=0)=결핍 상태, 회복↑ = 그 정책이 결핍을 잘 채움.
**5 정책** — 공통: 같은 pool·budget에서 **정렬 상위 B개 add**. *선택 기준만 다름*:

| 정책 | 선택 기준 (selection criterion) | 계열 |
|---|---|---|
| `random` | **무작위로 뽑음** | 대조 |
| `coverage` | **ODD 조건 골고루**(셀 교대로 하나씩, round-robin) | spread |
| `diversity` | **기존 선택과 유사도 최저인 것 반복**(임베딩 FPS) | spread |
| `uncertainty` | **오차 큰 클립 우선**(per-clip ADE 내림차순) | 오차 우선 |
| `guided`=Priority | **두 축 종합점수 높은 것**(ODD맥락 × 오차) | 오차 우선·<span class="danger">융합</span> |

</div>
<div>

**통제 장치** (도출의 합리성 근거)

| 장치 | 무엇을 막나 |
|---|---|
| 음성/양성 **대조쌍** | 회복부재 vs 데이터부족 혼동 |
| **다중 seed(5)** ±std | 단일 seed 우연 |
| `tail_picked` | 실패를 *선택 오조준*으로 인과규명 |
| **mixed pool**(tail+미끼) | 정책 변별력 실제 시험 |
| GroupKFold | same-clip 누수 |

**두 시나리오 = 대조쌍**
<div class="kpi-row">
<div class="kpi"><div class="v">adverse</div><div class="l">snow/fog · ODD축<br>baseline <b>0.916</b></div></div>
<div class="kpi"><div class="v">kinematic</div><div class="l">고yaw · feature축<br>baseline <b>0.984</b></div></div>
</div>

> adverse는 baseline이 더 낮음(0.916<0.984) = base가 tail을 이미 잘 예측 → **결핍 부재**. 되메워도 최고 정책조차 ≈0(결과 페이지) = 채울 게 없음의 직접 증거. 이 대비가 결론 ③.

</div>
</div>

---

## 2 · 결과 — spread 전략 승, 융합(guided) 패 · `tail_picked`가 밝힌 이유

<style scoped>
table td:nth-child(2){font-weight:700}
</style>

<div class="cols">
<div>

**kinematic — 급기동을 빼니 성능 저하 = 실재 결핍** (baseline 0.984 · 후보 11,740 · budget 800) · 회복(=오차 감소량) 평균±편차:

| 정책 | 회복 | tail 집음 |
|---|--:|--:|
| coverage (ODD spread) | **+0.061 ± 0.021** | 50% |
| diversity (임베딩 spread) | **+0.060 ± 0.015** | 33% |
| random | +0.044 ± 0.027 | 25% |
| uncertainty (per-clip 오차) | +0.019 ± 0.019 | 29% |
| **guided**(=Priority, ODD-조건) | <span class="danger">**+0.007 ± 0.019**</span> | <span class="danger">**23%**</span> |

**읽기**: 공간 고루 덮기(coverage·diversity)가 공동 1위, 오차 큰 클립만 고른 정책(uncertainty·guided)은 <span class="danger">무작위(random)보다도 못함</span>. → 두 잣대는 "고루 덮기"로 쓸 때만 효과(결론 ④).

</div>
<div>

**왜 guided가 졌나 — `tail_picked`(유용 클립을 얼마나 골랐나)**
guided가 정작 필요한 급기동 클립을 <span class="danger">**23%만**</span> 집음 = 무작위(25%)보다도 낮음. 급기동은 평범한 ODD조건(맑은 도심·고속도로)에 섞여 있어 → guided의 ODD 점수가 낮아짐 → **그 유용한 클립을 구조적으로 회피** → 예산 낭비 → 꼴찌. *우연이 아니라 기계적 오조준*(결론 ②).

**adverse — 악천후를 빼도 성능 그대로 = 대조군** (baseline 0.916 · 후보 9,684)
<div class="kpi-row">
<div class="kpi danger"><div class="v">≈0</div><div class="l">전 정책 회복<br>(±0.004, 최고 정책도)</div></div>
</div>

악천후를 빼도 성능이 안 나빠짐(baseline 낮음) → **채울 결핍이 없어** 어떤 정책도 회복 0. 진짜 데이터 부족이면 성능이 나빠졌어야 함. 즉 egomotion 난이도는 **기동축에 있고 날씨(ODD-조건)와 무관**(결론 ③).

</div>
</div>

---

## 2 · S1 후속 — guided 실패는 "틀린 축"인가 "오차 우선 고르기 자체"인가

<div class="cols">
<div>

**동기**: 결과의 guided 실패에 **서로 배타적인 두 설명**이 붙어 있다 — 미격리 상태.
- **② (축)**: 성능신호를 *ODD 셀*에서 재서 죽음 → 임베딩축에서 재면 산다
- **④ (오차 우선)**: 오차 큰 것만 고르기 *자체*가 나쁨 → 고루 덮기가 답

**격리 실험**: `leaveout.py`에 정책 2종 추가(같은 파이프라인·데이터, **정책만 교체**)
- `emb_err_only`: per-clip ADE를 **임베딩 k-NN(20) 평균**으로 재배치 = 성능신호를 임베딩축에. ODD 무시.
- `guided_sep`: `emb_err × soft ODD([0.5,1] 넛지, 억제 불가)` = **축분리 결합**(guided 교정형)

</div>
<div>

**무엇을 보면 무엇이 참인가**

| 관측 | 판정 |
|---|---|
| emb_err > uncertainty | 성능신호는 **임베딩축**(②) |
| guided_sep > guided | ODD-셀 게이트가 범인, 축분리가 교정 |
| guided_sep ≈ spread | 결합이 승자 도달 = **H2**(축만 문제) |
| guided_sep ≪ spread | 축 고쳐도 오차 우선 고르기 패배 = **H1**(고루 덮기만 유효) |

> guided = per-clip 오차 × **ODD-셀 context**. 범인 후보 (a)context 게이트가 좋은 클립을 억제 (b)오차 축이 틀림 (c)오차 우선 고르기 자체 — 두 정책이 (a)(b)를 분리한다.

</div>
</div>

---

## 2 · S1 결과 — 고루 덮기가 1차 승부 · 임베딩축 우세는 2차 · 곱셈 융합 패

<div class="cols">
<div>

**kinematic 7정책 회복** (budget 800 · 5 seed):

| 정책 | 신호 | 회복 |
|---|---|--:|
| coverage | ODD spread | **+0.061** |
| diversity | 임베딩 spread | **+0.060** |
| random | — | +0.044 |
| emb_err_only | 오차·**임베딩축** | +0.038 |
| guided_sep | emb_err×soft ODD | +0.021 |
| uncertainty | 오차·원시축 | +0.019 |
| guided(=Priority) | 오차×**ODD-셀** | <span class="danger">+0.007</span> |

</div>
<div>

**두 결과는 모순이 아니라 위계(1차 > 2차)**
- **1차(지배적): 고루 덮기가 압승**. coverage·diversity가 나머지 전부를 **편차의 여러 배로** 앞섬(견고). <span class="danger">오차 큰 클립만 고른 정책은 어느 축이든 무작위보다도 못하고</span>, 오직 고루 덮기만 무작위를 넘음.
- **2차(부차적): 굳이 오차 큰 클립을 우선 고른다면 임베딩축이 나음**. 오차 재는 **축만 바꾼 두 쌍**에서 임베딩 쪽이 회복 2~3배·방향 일치(아래 표). *단 차이가 **편차 이내**라 통계 미확정 = 방향성뿐.*
- **융합 금지**: <span class="danger">두 축을 결합한 guided_sep(+.021)조차 단일 고루 덮기 diversity(+.060)에 못 미침</span> → 하나로 합치지 말고 **각자 커버리지 도구로**.

**②의 근거 — 오차 재는 "축"만 바꾼 두 쌍** (나머지 조건 동일 · 임베딩 쪽이 앞섬):

| 비교 | 임베딩으로 잰 오차 | ODD·원시로 잰 오차 |
|---|--:|--:|
| 오차만 | emb_err **+0.038** | uncertainty +0.019 |
| 오차 × ODD | guided_sep **+0.021** | guided +0.007 |

> 정리: 오차 큰 클립 우선 고르기는 어느 축이든 고루 덮기에 진다(1차). 굳이 그렇게 한다면 임베딩축이 2~3배 낫다(2차).

</div>
</div>

---

<!-- _class: section -->
<!-- _paginate: false -->

# 3 · 중간결론

### ODD·임베딩을 어떻게 써야 하는가 — 근거 기반 도출

---

## 3 · 결론 ① 역할분담 · ② model_error의 축 — 근거→도출→반론방어

<div class="cols">
<div>

**① 두 잣대는 다른 질문에 답한다** — ODD=분포·안전·주소 / 임베딩=성능·중복
**근거** exposure 5앵커 부호안정(national 과소·rural 과대) — 외부앵커·명명 필요 → **임베딩으론 원리적 산출 불가**. + diversity 회복 1위(+0.060).
**도출** ODD만 만드는 신호(노출·과소수집·이름)와 임베딩만 만드는 신호(실제 개선)가 **각각 존재** → 대체재 아닌 직교 축.
**방어** *"둘 다 그냥 다양성?"* → 그렇다면 상호 대체돼야 하나 exposure는 임베딩에 앵커 없어 정의 불가, 성능회복은 ODD가 예측 실패(③). **대체 불가 = 직교**.

</div>
<div>

**② 성능신호는 ODD 셀 아닌 <span class="danger">임베딩 축</span>에 산다** (2차 효과)
**근거** guided(ODD셀×오차) 꼴찌 +0.007·tail 23%<random 25%. S1: emb_err(+.038)>uncertainty(+.019) ~2×, guided_sep(+.021)>guided(+.007) ~2.8×.
**도출** ODD셀로 집계하면 신호 소실, 임베딩서 쓰면 살아남 → 실패신호는 **내용(임베딩)축에 조직**. §2 배정 역전: **임베딩-first로 찾고 ODD로 명명**.
**방어** *"guided 패배는 운?"* → tail 23%<25%는 기계적 인과 — 고yaw가 평범한 ODD셀에 살아 cell_context↓ → **구조적 회피**. 재현가능.

</div>
</div>

---

## 3 · 결론 ③ 조건무관성 · ④ spread 사용모드 — 근거→도출→반론방어

<div class="cols">
<div>

**③ ODD-조건은 egomotion 성능을 예측 못 한다**
**근거(대조)** adverse(snow/fog): **최고 정책조차 회복 ≈0**(±0.004)=결핍 부재 / kinematic(고yaw): 실재 결핍 +0.06.
**도출** "adverse 결핍없음 / kinematic 결핍있음" 대비 = egomotion 실패는 **기동축**, ODD-조건축과 직교.
**방어** *"adverse는 데이터 부족?"* → cand 9,684·budget 800 충분. baseline 낮음(0.916) = 회복할 결핍이 없는 것. 부족이면 baseline↑이어야.

</div>
<div>

**④ spread로 이기고 오차 우선 고르기는 진다** (<span class="danger">1차·지배</span>)
**근거** 순위 coverage·diversity(~0.060) > random > 오차 우선 고르기(uncertainty·guided). S1: 오차 우선 고르기는 축 불문 **random 이하**, spread만 초과.
**도출** 두 잣대는 공간을 **폭넓게 덮는 커버리지 도구**로 쓸 때 유효. 과가중(guided)=오조준, 오차추종(uncertainty)=환원불가 노이즈. guided_sep조차 spread 못미침 → **융합 금지**.
**방어** *"가중이 무의미?"* → 아님. 가중은 실패축과 **정렬됐을 때만** 유효. egomotion선 정렬 깨져 커버리지 승 — 정렬 task선 가중이 이길 것(⑤).

</div>
</div>

---

## 3 · 결론 ⑤ 미검증 경계 + 확증/미검증 · 재현성

<div class="cols">
<div>

**⑤ ODD의 성능역할은 반증 아닌 <span class="warn">미검증</span>**
**근거** guided 실패 원인 = egomotion 실패축(기동)과 ODD-조건의 약한 연결 = **구조적 핸디캡**(②③).
**도출** 확증한 것과 미검증을 반드시 구분(→표). condition-sensitive task(perception: 폐색·야간·악천후가 실제 성능저하)선 ODD 조건이 실패와 **정렬** → 성능역할 살아날 것으로 예측.
**방어** **반증이 아님** — 실패 원인이 task 부적합(구조적 핸디캡)으로 규명됨. egomotion으론 볼 수 없어 이관.

</div>
<div>

**확증 vs 미검증 — 정직한 경계**

| | 항목 |
|---|---|
| ✅ 확증 | ODD 분포·안전역할(exposure) · 임베딩 성능역할(diversity) · 두 축 직교 |
| ❓ 미검증 | **ODD 조건이 성능 예측**(=두-잣대 G4) — perception으로 이관 |

> 각 결론이 특정 수치·대조에 묶여 `leaveout_results.json`·`exposure_sweep.json`으로 **재현·추적 가능**.

</div>
</div>

---

## 3 · 권장 설계 — 원리를 "수집 가이드 레시피"로

<div class="cols">
<div>

**핵심: 두 축을 분리 운용 (하나의 점수로 융합 금지)**

1. **성능 커버 [임베딩축]** — `diversity`(임베딩 spread)로 실패지점을 폭넓게 덮는다. 성능 신호(model_error)는 **임베딩 이웃**에서 측정.
2. **명명·발주 [ODD축]** — `exposure`·`deficit`로 "무엇을·왜"(현실 노출·과소수집·안전)를 **이름 붙여** 수집 발주.
3. **spread > 오차 우선 고르기** — 고루 덮기가 이긴다. 심각도·오차로 **과가중 금지**.
4. **곱셈 융합 금지** — 두 축을 **한 점수로 곱하지** 말 것(`guided`·`guided_sep` 패, S1). <span class="warn">단 일반 "융합 금지" 아님</span>: coverage⊕diversity **결합(portfolio/층화)은 expB서 시험 → 이 무대선 무이득(H0)이나 반증도 아님**. 결핍이 특정 조건에 정렬되면 타게팅이 이기는 반례도 존재(expA `speed_p4`).

</div>
<div>

**각 항목의 근거**

| 레시피 | 근거 |
|---|---|
| 성능 = 임베딩축 | 결론 ② · S1(emb_err↑) |
| 명명 = ODD | 결론 ①(exposure 부호안정) |
| spread > 오차 우선 고르기 | 결론 ④ · S1(오차 우선 고르기 전부 random 이하) |
| 곱셈 융합 금지 | S1(guided_sep 패) · expB(결합도 H0·반증 아님) |

> **경계**: ODD의 **성능 역할**은 아직 미검증 — condition-sensitive(perception)에서 정렬 기대. 여기 레시피는 **egomotion으로 확증된 부분**만.

</div>
</div>

---

<!-- _class: statement -->
<!-- _paginate: false -->

> **ODD**는 *무엇을 수집할지*(현실·안전·이름)를, **임베딩**은 *그게 모델을 실제로 개선하는지*(성능·중복)를 담당한다 — 두 축의 **직교성**(η²·downstream)은 확증됐다.
> 단, 성능 신호(**model_error**)는 <strong>ODD 셀이 아니라 임베딩 축</strong>에서 측정해 ODD로 명명해야 한다.
>
> **"함께 써야"는 아직 결론이 아니라 <span class="warn">미실증 가설</span>** — 직교(≠)는 확증됐으나 **상호 대체불가(non-substitutability)는 미측정**, **가산성(둘 다 > 단일)은 egomotion에서 실증 못함**(spread엔 한 렌즈로 충분·near-ceiling). 종결은 **조건민감 task 가산성 실험(C)**. 

---

<!-- _class: section -->
<!-- _paginate: false -->

# 4 · 상호보완은 열린 가설 — 실험 로드맵

### "함께 써야"는 egomotion으로 닫히지 않는다 · de-risking(A·B) 완료 → 종결은 실험 C

---

## 4 · de-risking 결과 — expA(외적타당성) · expB(결합 스코프)

<div class="cols">
<div>

**실험 A — ablation 배터리** (결핍 21종 → 실재 14종, 5 seed)
- **재현성**: `spread>targeting` **11/14** · `guided_loses` **11/14** → 기존 결론이 "고yaw 한 점"이 아님(외적타당성 확보).
- **경계(반례)**: <span class="danger">`speed_p4`에서 guided 압승(+0.067)</span> → **"타게팅 항상 패"는 거짓** · 결핍이 조건에 정렬되면 타게팅 유효.
- **견고성**: capacity (32,16)·(128,64) 모두 spread 견고((16,)는 전정책 ≈0 붕괴구간) · **ODD one-hot +36dim 넣어도 coverage 1위** → "성능=임베딩축"이 입력설계 귀결이라는 우려 기각.

</div>
<div>

**실험 B — spread 결합**(coverage⊕diversity, 이질 결핍)
- tail = `a_lat@p2`(div선호) + `speed@p8`(cov선호), worst-case 판정.
- **결과 = H0**: portfolio/층화가 단일 spread를 **worst-case로 못 넘음** · 곱셈(mult)만 대조.
- **원인**: 결핍별 cov≈div가 **전역**(유의 분리 0) → 반대선호쌍 자체가 없음.
- **한계**: baseline 불균형(2.76 vs 1.04)으로 worst-case가 A영역 지배(R2) → 정규화해도 비유의.

> **함의**: 성능(spread) 논거로는 "함께 써야"가 닫히지 않음 → **exposure/명명 논거 + 실험 C**에 의존.

</div>
</div>

---

## 4 · 실험 로드맵 A~F — 상호보완을 닫으려면

<style scoped>
table{font-size:8.6pt}
</style>

| 순서 | 실험 | 무엇을 닫나 | 중요도 | 상태 |
|:--:|---|---|:--:|:--:|
| **A** | ablation 배터리(결핍 다양화) | 순위결론 외적타당성 | ★★★ | ✅ 완료 |
| **B** | spread 결합(portfolio·층화 vs 곱셈) | "융합 금지" 사정거리 | ★★☆ | ✅ 완료(H0) |
| **C** | 조건민감 task(perception) **가산성** | **(d) 상호보완 · ODD 성능역할** | ★★★ | ⬜ 핵심·미착수 |
| **D** | 다목적 평가(exposure 고유 outcome) | ODD 고유가치·(I) 발주 | ★★☆ | ⬜ |
| **E** | 비대체성 정량화(교차 누락) | (c) non-substitutability | ★★☆ | ⬜ |
| **F** | 실규모(≈5천)·실모델 재현 | 규모·모델 외적타당성 | ★★☆ | ⬜ |

> **Wave 1(A·B) 완료**: 현행 결론의 기반 점검 + "융합 금지" 스코프 확정 — 단 **상호보완을 증명하진 못함**(청소·de-risking). **Wave 2 = C**가 상호보완을 닫는 유일한 실험(ODD가 성능을 인과적으로 좌우하는 task 필요). egomotion은 임베딩 성능역할·exposure 과소수집(national 수집·rural 프루닝) 검증엔 유효.

---

<!-- _paginate: false -->

## 부록 · 용어 미니사전

<div class="cols">
<div>

| 용어 | 정의 |
|---|---|
| **ADE / FDE** | 예측 궤적이 실제 경로서 벗어난 평균/최종 거리(m) |
| **η² (에타²)** | Phase0 효과크기 — ODD가 임베딩 분산 설명 비율(21%) |
| **model_error(ME)** | 이 조건서 모델이 실제 틀리는 정도(학습형 per-clip ADE의 셀 CDF) |
| **exposure $P_{ext}$** | 현실 노출빈도(기관통계). $P_{self}$=데이터 자기분포 |
| **deficit** | `log(P_ext/P_self)` — 과(>0)/소(<0)수집 |
| **criticality** | 안전 심각도 승수(사고·VRU·악천후) |
| **headroom** | 비중복 여력(mean uniqueness_weight) |

</div>
<div>

| 용어 | 정의 |
|---|---|
| **coarse 셀** | `road_type\|weather\|fog` — 수집발주 단위 |
| **cell_context** | Priority에서 ME 뺀 나머지(expo×crit×deficit×headroom) |
| **GroupKFold OOF** | 클립 단위 분리·out-of-fold 예측 = 누수 차단 |
| **FPS** | farthest-point sampling — 임베딩 최대거리 순 = diversity |
| **Domino** | density×error 집계(aggregate_error) |
| **손앵커** | 미조사 구성을 통계연보로 손 근사(관측 아님) |
| **tail** | 결핍 조건 영역(회복 측정 대상) |
| **G4** | "ODD 조건이 성능을 예측"(두-잣대 가설) |

</div>
</div>
