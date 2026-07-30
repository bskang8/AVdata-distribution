# EXP-003 Phase 1 — 결과: 획득함수 조립 + leave-out 검증 (정직한 마감)

> **한 줄**: 획득함수 `Priority(c)`를 다섯 인자로 end-to-end 조립하는 데는 성공했으나, **egomotion 대리지표는 두-렌즈 G4의 검증에 부적합한 task**임이 leave-out으로 downstream·기계적으로 증명됐다. 획득함수의 실패가 아니라 검증 task의 범위 한계 발견.

## 1. 파이프라인 (전부 완료)

| 산출 | 스크립트 | 결과 |
|---|---|---|
| CV 대리지표 per-clip ADE/FDE | `compute_surrogate.py` | valid 97,820/100,398 · ADE p50 2.16 |
| ODD셀·사분면 집계 → `model_error(c)` | `aggregate_error.py` | 282 ODD셀(94% 커버) · Domino density×error |
| **Priority(c) 5인자 통합 랭킹** | `priority.py` | core(crit×ME×headroom) + full(×exposure×deficit) |
| CV→**학습형 예측기** (model_error 격상) | `learned_surrogate.py` | MLP GroupKFold-OOF · 676,624창 · ADE p50 0.94 |
| exposure **urban/rural 손앵커 확장** | `extend_exposure.py` | 스윕 견고(Spearman +0.97~1.0) · full 6→17셀 |
| **§5 leave-out 재현실험** | `leaveout.py` | 아래 §3 |

### 인자별 신호 (셀=coarse `road_type\|weather\|fog`, exposure 결정공간)
- **criticality**: 축 승수 곱(criticality.json). **exposure**: P_ext(손앵커 확장). **deficit**: log(P_ext/P_self).
  **model_error**: 학습형 per-clip ADE의 셀 가중 CDF. **headroom**: mean uniqueness_weight(비중복 여력).

## 2. 중간 발견 (재확인된 실)

- **학습형 model_error는 분포 의존 신호**: CV와 Spearman 0.885지만 소수 셀(n~25)에서 급등 →
  "기동 절대복잡도"가 아니라 "fleet 기준 비전형성"을 잼(CV는 클립별 자기적합이라 이걸 못 봄).
- **exposure×model_error 충돌**: highway는 과소수집(exposure↑)이나 예측 쉬움(ME↓) — 곱이 상쇄.
  = highway는 더 안 모아도 됨(정답). Priority_full top=`urban\|clear\|present`(fog).
- **exposure 스윕 견고 결론**: **national_road 강건히 과소수집(수집), rural 강건히 과대수집(프루닝 후보)**;
  highway·urban은 near-balanced라 손앵커 민감(결론 보류).

## 3. leave-out 검증 — G4 미성립 (정직한 negative)

**설계**: 테스트베드=학습형 예측기(입력 kinematics 6 + PCA임베딩 16 — 순수 kinematics면 조건축을
학습할 통로가 없어 회복 불가, 초기 smoke가 진단). 5정책 × 예산 × **2 결핍시나리오** × 5 seed,
mixed candidate pool(tail + 잉여 common 3×)로 정책 **변별력** 시험.

| 시나리오 | baseline tail | 정책 순위 (회복 mean±std) | tail_picked |
|---|---|---|---|
| **kinematic** (고yaw) | 0.984 | **diversity +.060±.015** > coverage +.059 > random +.044 > uncertainty +.019 > **guided +.007** | guided **23%** vs coverage 50% |
| **adverse** (snow/fog) | 0.916 | random +.004 > 나머지 ≈0 (결핍 자체 없음) | — |

**핵심 진단 (`tail_picked`)**: kinematic 결핍에서 **guided가 유용 클립을 23%만 집음**(random 25%보다 낮음).
guided = ODD-조건 Priority × per-clip 오차인데, 고yaw 급기동은 **평범한 ODD조건**(urban/highway·clear)에
살아 cell_context가 낮음 → guided가 회피 → 예산 낭비 → 꼴찌. 즉 **guided가 egomotion의 실제 결핍(기동축)
과 구조적으로 어긋난 곳(ODD-조건축)을 겨냥**한다.

**결론**:
1. leave-out 하네스·guided per-clip 재정의·다중seed·mixed pool 전부 구현·작동.
2. **G4(guided > 단일렌즈) 미성립** — egomotion에선 diversity(임베딩)가 이기고 guided가 짐.
   임베딩이 이긴 건 임베딩이 기동공간을 우연히 커버하기 때문.
3. **원인 = task 부적합**: egomotion의 실패는 기동축, Priority는 ODD-조건축 → 구조적 오조준.
   adverse(ODD축)엔 애초 성능결핍이 없음(최고 정책조차 회복 ≈0).

## 3.5 S1 후속 — 축분리 정책으로 ②↔④ 격리 (`guided_sep`·`emb_err_only`)

**동기**: §3의 guided 실패에 대해 §4가 두 설명을 동시에 단다 — **②(성능신호를 틀린 축=ODD셀에서 잼)**
와 **④(가중 타게팅 자체가 나쁨)**. 이 둘은 배타적인데 미격리 상태였다. `leaveout.py`에 정책 2종 추가:
- `emb_err_only`: per-clip ADE를 **임베딩 k-NN(20) 평균**으로 재배치 = 성능신호를 임베딩축에. ODD 무시.
- `guided_sep`: `emb_err × soft ODD context([0.5,1] 넛지, 억제 불가)` = **축분리 결합**(guided 교정형).

**결과** (kinematic, budget 800, 5 seed, 회복 mean±std):

| 정책 | 신호 유형 | 회복 | tail_picked |
|---|---|--:|--:|
| coverage_only | ODD **spread** | **+0.061 ± 0.021** | 50% |
| diversity_only | 임베딩 **spread** | **+0.060 ± 0.015** | 33% |
| random | — | +0.044 ± 0.027 | 25% |
| emb_err_only | 오차 타게팅·**임베딩축** | +0.038 ± 0.016 | 23% |
| guided_sep | emb_err × soft ODD | +0.021 ± 0.009 | 22% |
| uncertainty_only | 오차 타게팅·**원시축** | +0.019 ± 0.019 | 29% |
| guided | 오차 × **ODD-셀 게이트** | +0.007 ± 0.019 | 23% |

**판정 — 이분법이 아니라 중첩(nested)**:
1. **②(축)는 참이나 2차 효과**. `emb_err_only`(+0.038) > `uncertainty_only`(+0.019, ~2×), `guided_sep`(+0.021)
   > `guided`(+0.007, ~2.8×). **두 대조의 부호가 일치** → "ODD-셀은 성능신호를 재기 가장 나쁜 자리, 임베딩축이
   낫다"가 메커니즘 수준에서 확증. *단 각 gap은 1σ 안쪽 → 방향성 근거이지 강한 유의는 아님.*
2. **④(spread)는 1차 효과(지배적)**. spread 2종(~0.060)이 나머지 전부를 여러 σ 차이로 압도(유일하게 견고한 gap).
   **결정적: 오차 타게팅은 어느 축에서 하든 전부 random(+0.044) 이하** — 오직 spread만 random을 넘음.
3. **`guided_sep`(교정형 융합)조차 단일렌즈 spread에 못 미침** → **"두 잣대를 하나의 가중 점수로 융합하지 말라"**가
   축을 고친 뒤에도 살아남음. S1의 가장 강한 결론.

**②↔④ 모순 해소**: *오차 타게팅은 어느 축에서 하든 spread에 진다(④, 1차). 굳이 타게팅한다면 임베딩축이 ODD축보다
2~3배 낫다(②, 2차). 둘은 모순이 아니라 위계* — ②='졌지만 덜 처참하게 지는 법', ④='애초에 타게팅 말고 고루 덮어라'.

**타당성(직교성 활용)에의 함의**:
- 양성: coverage(ODD-spread)≈diversity(임베딩-spread) **공동 1위** → 두 직교축으로 **각자 고루 덮기**가 유효한 활용법.
- 부정 강화: 융합·가중 타게팅(guided·guided_sep)은 **축 교정 후에도 패배** → "직교성을 하나의 획득함수로 결합"은 egomotion에서 반증.
- 미해결: coverage↔diversity 동점이 *다른 클립을 집어 합치면 이득*인지 *같은 클립(중복)*인지는 미측정 → S2(중복도/한계이득) 필요.

*(재현 주: 정책 2종 추가로 rng 스트림이 밀려 coverage_only가 §3 대비 +0.0592→+0.0612로 이동 — 1σ 내. diversity_only는
FPS 결정적이라 +0.0598 불변, 앵커로 확인.)* 산출물: `leaveout_results.json`(`axis_diag` 필드).

## 4. 중간결론 — "ODD·임베딩을 어떻게 써야 하는가" (근거 기반 도출)

> **phase1의 진짜 목적**(methodology_direction_analysis.md 달성): egomotion 성능 자체가 아니라,
> **ODD와 임베딩 두 렌즈를 획득함수에서 어떻게 활용해야 하는지**를 실측으로 규명하는 것.
> 아래 각 결론은 (측정 근거·수치) → (도출 논리) → (제3자 반론 방어) 순으로, 도출의 합리성을 추적 가능하게 적는다.

### 결론 1. 두 렌즈는 **서로 다른 질문에 답한다** — ODD=분포·안전·주소, 임베딩=성능·중복

- **근거**: (a) exposure 스윕 5앵커 전부에서 national_road 과소수집(logr +4.44~+4.89)·rural 과대수집
  (logr −0.47~−1.39) **부호 안정**(§3 표). 이 판정은 외부 앵커(현실 VKT)·명명이 필요해 **임베딩으론 원리적으로 산출 불가**.
  (b) leave-out kinematic에서 임베딩 spread(diversity)가 성능 회복 1위(+0.0598).
- **도출**: ODD만 만들 수 있는 신호(현실 노출·과소수집·이름)와 임베딩만 만드는 신호(모델이 실제 개선되는가)가
  **각각 존재**한다 → 둘은 대체재가 아니라 서로 다른 축의 정보. ODD=*"무엇을 수집해야 하나"*, 임베딩=*"무엇이 실제로 성능을 올리나"*.
- **반론 방어**: "둘 다 그냥 데이터 다양성 아닌가?" → 만약 그렇다면 한 렌즈가 다른 렌즈를 대신할 수 있어야 하는데,
  exposure/deficit는 임베딩에 외부 앵커가 없어 **정의 불가**, 성능회복은 ODD-조건이 예측 실패(결론 3). 상호 대체 불가 = 직교.

### 결론 2. 방법론의 배정 하나가 **틀렸다**: `model_error`는 ODD 셀이 아니라 **임베딩 축**에 산다

- **근거**: guided(=ODD 셀 단위 Priority×오차)는 kinematic 결핍에서 **꼴찌**(+0.0074), 그런데 유용 클립을
  **23%만** 집음 — **random(25%)보다도 낮음**(§3 `tail_picked`). 반면 같은 오차를 임베딩 공간에서 쓴 diversity는 1위.
- **도출**: model_error를 ODD 셀로 집계하면 신호가 사라지는데, 임베딩 공간에서 쓰면 살아난다 →
  성능-실패 신호는 **ODD 조건이 아니라 내용(임베딩) 축에 조직돼 있다**. 방법론 §2가 model_error를 ODD 셀로
  조직하려던 가정은 **역전**돼야 함: **임베딩-first로 실패지점을 찾고 → ODD로 명명(수집발주)** 순서가 맞다.
- **반론 방어**: "guided가 진 건 그냥 운/노이즈 아닌가?" → tail_picked 23%<25%는 **기계적 인과**(guided가 유용
  클립을 *구조적으로 회피*)이지 성능 분산이 아니다. 원인도 명시 가능: 고yaw 급기동은 평범한 ODD조건
  (urban/highway·clear)에 살아 cell_context가 낮음 → guided가 낮게 점수. 재현 가능한 메커니즘.
- **S1 정량 확인(§3.5)**: 성능신호를 임베딩축으로 옮기면 타게팅이 2~3배 회복(emb_err +0.038 > uncertainty +0.019;
  guided_sep +0.021 > guided +0.007). 단 이는 **2차 효과** — 임베딩축 타게팅조차 spread(~0.060)엔 못 미침(결론 4가 1차).

### 결론 3. ODD-조건은 egomotion **성능을 예측하지 못한다** (음성 대조로 격리)

- **근거(대조 설계)**: 두 시나리오를 **대조쌍**으로 돌림. adverse(ODD 조건축, snow/fog)는 baseline tail ADE
  **0.916**(kinematic 0.984보다 낮음)이고 **최고 정책(spread)조차 회복 ≈0(±0.004)** = base가 이미 tail을 잘 예측
  → **결핍 자체가 없음**. kinematic(feature축, 고yaw)만 실재 결핍(baseline 0.984) → 회복 +0.06.
- **도출**: "adverse에 결핍 없음 / kinematic에 결핍 있음"의 대비가 곧 **egomotion의 실패는 기동축, ODD-조건축과 직교**임을
  격리 증명. ODD-조건으로 획득을 유도하면 결핍 없는 곳을 겨냥하게 됨.
- **반론 방어**: "adverse가 회복 안 된 건 데이터가 적어서 아닌가?" → candidate 9,684개로 충분, budget 800.
  회복이 안 된 게 아니라 **회복할 결핍이 없음**(최고 정책조차 ≈0이 직접 근거). 데이터 부족이면 baseline이 높고 spread가 회복시켰어야 함.

### 결론 4. **"커버리지(spread)"로 쓰면 이기고, "가중 타게팅"으로 쓰면 진다** — 두 렌즈의 올바른 사용 모드

- **근거**: leave-out 최종 순위 = coverage(ODD-spread) +0.0592 ≈ diversity(임베딩-spread) +0.0598 > random +0.0437
  > uncertainty +0.0185 > guided +0.0074. 즉 **두 렌즈를 native "고루 덮기"로 쓴 정책이 상위**, 공격적 가중(guided·uncertainty)이 하위.
- **도출**: ODD·임베딩은 각자 **조건공간·내용공간을 폭넓게 덮는 커버리지 도구**로 쓸 때 유효. 심각도/exposure 과가중(guided)은
  실패축과 어긋나 오조준, per-clip 오차 추종(uncertainty)은 **환원불가 노이즈**(못 배우는 hard clip)를 쫓아 실패.
- **반론 방어**: "그럼 획득함수의 가중이 무의미?" → 아니다. 이 결론은 **가중이 실패축과 정렬됐을 때만 유효**임을 뜻함.
  egomotion에선 정렬이 깨져 커버리지가 이겼을 뿐(결론 3). 정렬되는 task에선 가중이 커버리지를 이길 것(결론 5).
- **S1 강화(§3.5)**: 이 "spread>타게팅"은 **1차·지배적 효과** — 오차 타게팅은 임베딩축으로 옮겨도 전부 random 이하,
  오직 spread만 random을 넘는다. 축분리 결합(guided_sep)조차 단일렌즈 spread에 못 미쳐 **"융합 말고 축분리해 각자 덮기"** 확증.

### 결론 5. ODD의 **성능 역할**은 반증된 게 아니라 **미검증**으로 남음 (정직한 경계)

- **근거**: guided 실패의 원인은 egomotion 실패축(기동)과 ODD-조건의 약한 연결(구조적 핸디캡, 결론 2·3).
- **도출**: 그러므로 phase1이 **확증한 것**과 **미검증으로 남긴 것**을 반드시 구분:
  - ✅ 확증: ODD의 분포·안전역할(exposure/deficit 부호안정) · 임베딩의 성능역할(diversity 회복) · 두 축의 직교.
  - ❓ 미검증: **ODD 조건이 성능을 예측한다**는 가정(=두-렌즈 G4). condition-sensitive task(perception: 폐색·야간·악천후가
    실제 성능 저하)에선 ODD 조건이 실패와 정렬 → ODD의 성능역할이 살아날 것으로 예측. egomotion으론 볼 수 없어 이관.

### 왜 이 도출이 합리적인가 — 방법론적 안전장치

| 안전장치 | 무엇을 막았나 |
|---|---|
| **음성/양성 대조쌍**(adverse vs kinematic) | "회복 없음"이 결핍부재 때문인지 데이터부족 때문인지 혼동 방지 → 결론 3 격리 |
| **다중 seed(5) mean±std** | 단일 seed 우연(초기 quick↔full 순위역전 관측됨)을 배제. 순위 주장 전 std 병기 |
| **`tail_picked` 기계적 진단** | guided 실패를 "성능 노이즈"가 아니라 "선택 오조준"으로 **인과 규명**(23%<25%) → 결론 2 |
| **mixed candidate pool**(tail+잉여common) | tail-only면 모든 정책이 유용클립만 집어 변별 불가 → 정책 **변별력**을 실제로 시험 |
| **exposure 손앵커 스윕**(5앵커 부호안정) | urban/rural 앵커가 관측 아닌 손값이라, 결론을 **앵커 불변 항목**(national·rural)에만 국한 |
| **GroupKFold OOF**(same-clip 누수 차단) | model_error가 "모델이 실제 못 본 조건에서 틀린다"를 성립시킴 |

→ 각 결론이 특정 수치와 대조·통제에 묶여 있어, 제3자가 `leaveout_results.json`·`exposure_sweep.json`·
`EXECUTION_LOG.md`로 **추적·재현**할 수 있다.

## 5. 함의 · 다음

- **획득함수 자체는 유효**(조립·인자 전부 성립). 문제는 검증 task와 **model_error의 조직 축**(ODD→임베딩으로 이동 필요).
- **egomotion으로 검증 가능**: 임베딩 성능역할, exposure 과/소수집(national 수집·rural 프루닝).
- **ODD 두-렌즈 G4는 condition-sensitive 다운스트림**(perception/detection)에서 재도전 — 거기선 ODD 조건이 성능과 정렬.

## 6. 후속 de-risking (COMPLEMENTARITY_GAP.md §6·§8 반영) — 실험 A·B

> **동기**: §3~4의 결론은 "고yaw 결핍 한 점"에 걸려 있었고(외적타당성 취약), "융합 금지"의 사정거리도 미확정이었다.
> COMPLEMENTARITY_GAP.md가 이를 감사해 실험 A(외적타당성)·B(결합 스코프)를 설계 → `leaveout.py --expA/--expB`로 실행.

### 실험 A — ablation 배터리 (결핍 21종 → 실재 14종, 5 seed) · `leaveout_battery.json`
- **재현성**: `spread>targeting` **11/14** · `guided_loses(<random)` **11/14** → 순위 결론이 단일 결핍이 아니라 **다수 결핍에서 재현**(외적타당성 확보).
- **경계(반례) 발견**: `speed_p4`에서 **guided 압승(+0.067, spread≈0)** · `a_lat_p2`에서 타게팅 우위 → **"타게팅/융합은 항상 진다"는 거짓**. 결핍이 특정 조건에 정렬되면 타게팅이 이긴다(문서 §6-A 가설 실증).
- **견고성 두 축**:
  - capacity: (32,16)·(128,64) 모두 spread 견고 1위. (16,)는 전정책 회복 ≈0인 **붕괴구간**이라 순위 무의미 → "저용량 아티팩트" 우려 기각.
  - ODD-feature 공정성: ODD one-hot **+36dim** 추가해 모델이 ODD를 직접 봐도 **여전히 coverage 1위** → "성능=임베딩축"이 입력설계 귀결이라는 우려 **해소**(가장 강한 결과).
- null 결핍: `a_long`(전 severity)·`rain`·`snow` → snow/rain null은 결론 3(ODD-조건 ⊥ egomotion) 재확인.

### 실험 B — spread 결합(coverage⊕diversity, 이질 결핍) · `leaveout_spread_combo.json`
- tail = `a_lat@p2`(diversity 선호) + `speed@p8`(coverage 선호), worst-case = min(영역별 회복).
- **판정 = H0**: portfolio·층화가 단일 spread를 **worst-case로 넘지 못함**. 곱셈(mult)은 대조.
- **원인**: 결핍별 cov≈div가 **전역**(유의 분리 0개) → 반대선호 결핍쌍 자체가 없음 = §3 "단일 결핍 충분"의 **이질결핍 확장**.
- **한계(R2)**: baseline 불균형(A 2.76 vs B 1.04)으로 worst-case가 A영역(상대회복 ~1%, near-null)에 지배 → 지표 degeneracy. baseline 정규화 시 point-estimate는 portfolio>single이나 **recA std 이내로 비유의**.
- **곱셈 병리**: quick에선 재현(−0.091)이나 **full에선 비견고**(`mult_fails=False`) → 곱셈 억제 병리도 무대의존.

### 정직한 마감 (스코프 확정)
| 판정 | 주장 |
|---|---|
| ✅ 확증 | 두 렌즈 각각 spread 도구로 유효 · **다수 결핍서 재현**(A) |
| ✅ 확증 | **곱셈-타게팅 융합 실패**(guided·guided_sep) — 단, **결핍이 조건정렬되면 타게팅 승리**하는 반례 존재(A `speed_p4`) |
| ✅ 확증 | egomotion에서 ODD-조건 ⊥ 성능 · surrogate 용량·ODD-feature에 견고(A) |
| ⬜ 시험됨(H0) | **이긴 두 spread의 결합(portfolio/층화)** — 이 무대선 무이득이나 **반증 아님**(반대선호쌍·baseline균형 부재, R2)(B) |
| ❌ 미실증 | **"둘 다 써야 더 낫다"(상호보완·가산성)** — egomotion으로 닫히지 않음 → **실험 C가 유일한 종결** |
| ❓ 미검증 | ODD의 성능예측 역할(condition-sensitive task로 이관) |

> **"융합 금지"는 일반 명제가 아니다** — 지지되는 좁은 주장은 *"오차-타게팅을 곱셈으로 융합하면(이 무대선) 실패한다"*. coverage⊕diversity 결합은 반증되지 않았고(H0), 조건정렬 결핍에선 타게팅도 이긴다.

## 산출물 (output/)
`{,learned_}ade/fde_per_clip.npy` · `{,learned_}model_error_by_odd_cell.json` ·
`learned_ext_priority_ranking.json` · `P_ext_extended.json`(exposure/output) · `exposure_sweep.json` ·
`leaveout_results.json` · `leaveout_battery.json`(expA) · `leaveout_spread_combo.json`(expB)
