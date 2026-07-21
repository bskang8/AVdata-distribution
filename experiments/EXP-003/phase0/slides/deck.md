---
marp: true
theme: disc
paginate: true
math: katex
header: 'EXP-003 Phase 0 · 데이터 분포 진단'
---

<!-- _class: title -->
<!-- _paginate: false -->
<!-- _header: '' -->

# AV 데이터 분포 진단
## Phase 0 결과 요약

**100,398 clips** · 실행일 2026-07-08
`experiments/EXP-003/phase0/output/`

---

<!-- _class: section -->
<!-- _paginate: false -->

# 2 · ODD 커버리지 분석
### 이 데이터셋은 운영설계영역(ODD) 조합 공간을 얼마나 커버하는가?
### Step 0-F · 100,398 clips

---

## 2 · ODD 스키마 정의 — 11필드 값 분포

<style scoped>
.dist{display:flex;flex-direction:column;gap:5px;margin:12px 0 6px}
.dhead{display:flex;gap:12px;font-size:8pt;color:#5f6470;font-weight:700}
.dhead .ax{width:70px;text-align:center}.dhead .fname{width:150px}
.frow{display:flex;align-items:center;gap:12px}
.frow .ax{width:70px;flex:none;font-size:9pt;font-weight:700;color:#00586F;text-align:center}
.frow .fname{width:150px;flex:none;font-size:9pt;font-family:monospace;color:#001F60}
.frow .fname.n{font-weight:700}
.bar{flex:1;display:flex;height:26px;border-radius:4px;overflow:hidden;border:1px solid #d5dce6}
.bar span{display:flex;align-items:center;padding:0 7px;font-size:8pt;color:#fff;white-space:nowrap;overflow:hidden;flex:none;print-color-adjust:exact;-webkit-print-color-adjust:exact}
.bar span.g{flex:1}.bar span.d{color:#1a1a1a}
.bar span.k1{background:#001F60}.bar span.k2{background:#00586F}.bar span.k3{background:#00C1DE}.bar span.k4{background:#c8871a}.bar span.k5{background:#d23b3b}
.note{font-size:7.5pt;color:#5f6470;margin-left:6px;flex:none}
</style>

AV 지각·예측·계획 난이도로 정의한 **11개 ODD 필드**. 각 막대 = 값의 **클립 비율**(좌→우 빈도순, 100% 누적) · 지배값이 막대를 꽉 채울수록 편중이 심함.

<div class="dist">
<div class="dhead"><div class="ax">AV 축</div><div class="fname">필드</div><div>현재 분포 (비율)</div></div>

<div class="frow"><div class="ax">지각</div><div class="fname">weather</div><div class="bar"><span class="g k1" title="clear 92,314">clear 92%</span><span class="k2" style="width:5.2%">rain</span><span class="k3" style="width:1.6%"></span><span class="k4" style="width:1.3%"></span></div><div class="note">rain 5.2% · snow 1.6% · fog 1.3%</div></div>

<div class="frow"><div class="ax">지각</div><div class="fname">lighting</div><div class="bar"><span class="g k1">moderate 44%</span><span class="k2" style="width:42.2%">well_lit 42%</span><span class="k3 d" style="width:13.8%">poorly_lit 14%</span></div></div>

<div class="frow"><div class="ax">지각</div><div class="fname">occlusion_level</div><div class="bar"><span class="g k1" title="low 99,467">low 99.1%</span><span class="k2" style="width:0.8%"></span><span class="k3" style="width:0.5%"></span></div><div class="note">medium 0.8% · high 0.1%</div></div>

<div class="frow"><div class="ax">지각</div><div class="fname">lane_marking</div><div class="bar"><span class="g k1" title="clear 95,109">clear 95.8%</span><span class="k2" style="width:4.0%">faint</span><span class="k3" style="width:0.6%"></span></div><div class="note">faint 4.0% · absent 0.3%</div></div>

<div class="frow"><div class="ax">예측</div><div class="fname">agent_type</div><div class="bar"><span class="g k1" title="cars_only 97,402">cars_only 97%</span><span class="k2" style="width:2.6%"></span><span class="k3" style="width:0.4%"></span></div><div class="note">mixed 2.6% · VRU 0.4%</div></div>

<div class="frow"><div class="ax">예측</div><div class="fname">traffic_density</div><div class="bar"><span class="g k1">sparse 71%</span><span class="k2" style="width:26.4%">moderate 26%</span><span class="k4" style="width:2.2%"></span></div><div class="note">dense 2.2%</div></div>

<div class="frow"><div class="ax">예측·계획</div><div class="fname">junction_proximity</div><div class="bar"><span class="g k1">none 40%</span><span class="k2" style="width:38.9%">post_junction 39%</span><span class="k3 d" style="width:11.5%">approaching 12%</span><span class="k4" style="width:9.2%">in_junction 9%</span></div></div>

<div class="frow"><div class="ax">계획</div><div class="fname">road_type</div><div class="bar"><span class="g k1">urban 44%</span><span class="k2" style="width:40.1%">rural 40%</span><span class="k3 d" style="width:15.6%">highway 16%</span><span class="k4" style="width:0.3%"></span></div><div class="note">national_road 0.2%</div></div>

<div class="frow"><div class="ax">계획</div><div class="fname">road_surface</div><div class="bar"><span class="g k1">dry 80%</span><span class="k2" style="width:19.0%">wet 19%</span><span class="k3" style="width:1.4%"></span></div><div class="note">snow 1.4%</div></div>

<div class="frow"><div class="ax">계획</div><div class="fname">visibility_range</div><div class="bar"><span class="g k1">good 86%</span><span class="k2" style="width:9.3%">moderate</span><span class="k3" style="width:4.7%"></span></div><div class="note">moderate 9.3% · poor 4.7%</div></div>

<div class="frow"><div class="ax">계획</div><div class="fname">special_event</div><div class="bar"><span class="g k1" title="none 100,361">none 99.97%</span><span class="k4" style="width:0.5%"></span></div><div class="note">obstacle 0.03% · accident·emergency 0%</div></div>
</div>

> **표 분석** — 11개 필드 **모두 값이 등장**하고 `lighting`·`junction_proximity`·`road_type`·`traffic_density`는 2~4개 값이 비교적 고르게 분포(채워짐). 반면 나머지 7개 필드는 <span class="danger">단일 지배값에 80~99.97% 쏠림</span>(clear 92% · low 99% · cars_only 97% · none 99.97% 등) — **값은 있으나 다양성은 없는** 구조. 특히 안전 크리티컬 값(high·absent·poor·VRU)은 막대에서 실선 수준으로만 존재 → 커버리지 저조의 직접 원인.

---

## 2 · ODD 커버리지 정량화 — 도출 & 결과

**질문**: AV 안전성은 *"마주칠 조건 조합을 얼마나 학습했나"*에 좌우 → ODD를 이산 필드로 정의하고 **관측 / 이론** 조합 비율(커버율)을 측정.

<div class="cols">
<div>

**도출 4단계**

**①** 클립 → 11-튜플 (각 클립 = 11필드 값 1튜플)

```
(urban, clear, well_lit, cars_only, sparse,
 post_junction, dry, low, good, none, clear)
```
↑ <span class="danger">**최빈 조합**</span> · 6,578클립(6.55%)이 이 하나에 몰림

**②** 중복 제거 → **2,070 고유 조합** *(싱글톤 897 / 반복 1,173)*

**③** 이론 = 값 수의 곱 `5×5×4×6×4×5×4×4×4×5×4` = **15,360,000**

**④** 커버율 = 2,070 / 15.36M = <span class="danger">**0.013%**</span> (클린 0.167%)

</div>
<div>

**필드 정의를 바꿔도 결론 동일** — 비교군 대비

| 필드 정의 | 필드 | 관측 | 이론 | 클린 커버율 |
|--------|:--:|--:|--:|--:|
| 비교군 ① | 19 | 7,240 | 2.4×10¹¹ | 0.0008% |
| 비교군 ② | 9 | 1,384 | 614,400 | 2.26% |
| **본 분석 스키마** | **11** | **2,070** | **15.36M** | <span class="danger">**0.167%**</span> |

<div style="font-size:8.5pt;color:#5f6470;line-height:1.5;margin-top:12px;border-left:3px solid #00C1DE;padding:2px 0 2px 11px">
<b style="color:#001F60">결론은 스키마와 무관.</b> 필드 9·11·19개 어느 정의든 커버율 극저(최대 2.26%). 필드를 늘릴수록 <b>이론 조합만 폭증하고 관측은 정체</b> → 커버율은 오히려 하락. 즉 저커버리지는 <b style="color:#001F60">데이터의 구조적 결함</b>.
</div>

</div>
</div>

<div class="kpi-row">
<div class="kpi"><div class="v">15.36M</div><div class="l"><b>이론 조합</b><br>가능한 전체 조합 (값 수의 곱)</div></div>
<div class="kpi"><div class="v">2,070</div><div class="l"><b>관측 조합</b><br>실제 등장 · 커버율 0.013%</div></div>
<div class="kpi danger"><div class="v">99.987%</div><div class="l"><b>미관측 조합</b><br>이론 중 한 건도 없음</div></div>
</div>

> 2,070개 중 **897개(43.3%)는 싱글톤**, 최빈 조합 하나(`urban·clear·well_lit·cars_only·sparse·…`)에만 <span class="danger">**6,578클립(6.55%)**</span> 집중 = Gap-3(ODD 커버리지 저조)의 정량적 근거.

---

## 2 · 결과 ② — 상위 조합 집중 & 최빈 top 20

<style scoped>
.cols{gap:22px}
table{font-size:9.5pt;border-collapse:collapse;width:100%}
th,td{padding:4px 8px}
th{font-size:8.5pt}
.fnote{font-size:8.5pt;line-height:1.45;color:#1a1a1a;margin-top:12px}
.fnote .ttl{font-weight:800;color:#001F60;font-size:9.5pt;margin-bottom:8px}
.fnote .blk{margin-bottom:9px;border-left:3px solid #00C1DE;padding-left:9px}
.fnote .h{color:#00586F;font-weight:700}
.fnote .v{color:#5f6470;font-size:7.5pt}
</style>

<div class="cols">
<div>

**중복 집중도**

| 구분 | 조합 수 | 클립 수 | 평균 클립/조합 | 비고 |
|------|--:|--:|--:|--|
| 싱글톤(1회) | 897 | 897 | 1.0 | 조합 43.3%·클립 0.9% |
| 반복(2회+) | 1,173 | 99,501 | 84.8 | 클립 99.1% |
| **상위 100** | 100 | **86,372** | **863.7** | **전체 86.0%** |

**최빈 top 1–10** (클립 · %)

| # | 클립 | % | road_type·lighting·traffic_density·junction_proximity |
|--|--:|--:|--|
| 1 | 6,578 | 6.55 | urban·well_lit·sparse·post_junction |
| 2 | 5,935 | 5.91 | rural·well_lit·sparse·none |
| 3 | 5,217 | 5.20 | rural·moderate·sparse·none |
| 4 | 4,878 | 4.86 | rural·well_lit·sparse·post_junction |
| 5 | 4,185 | 4.17 | rural·moderate·sparse·post_junction |
| 6 | 3,955 | 3.94 | urban·moderate·sparse·post_junction |
| 7 | 3,914 | 3.90 | urban·well_lit·moderate·post_junction |
| 8 | 2,489 | 2.48 | highway·well_lit·sparse·none |
| 9 | 2,436 | 2.43 | urban·well_lit·moderate·in_junction |
| 10 | 2,306 | 2.30 | urban·moderate·moderate·post_junction |

</div>
<div>

**top 11–20** (클립 · %)

| # | 클립 | % | road_type·lighting·traffic_density·junction_proximity |
|--|--:|--:|--|
| 11 | 2,288 | 2.28 | highway·well_lit·moderate·none |
| 12 | 2,245 | 2.24 | urban·well_lit·moderate·approaching |
| 13 | 2,165 | 2.16 | highway·moderate·sparse·none |
| 14 | 1,970 | 1.96 | rural·moderate·sparse·none·**wet** |
| 15 | 1,769 | 1.76 | rural·poorly·sparse·none·**poor** |
| 16 | 1,675 | 1.67 | rural·poorly·sparse·none |
| 17 | 1,551 | 1.54 | urban·moderate·moderate·approaching |
| 18 | 1,530 | 1.52 | urban·well_lit·sparse·in_junction |
| 19 | 1,503 | 1.50 | highway·moderate·moderate·none |
| 20 | 1,401 | 1.40 | urban·well_lit·sparse·approaching |

<div style="font-size:8pt;color:#5f6470;margin-top:5px">* 14·15위만 <b style="color:#001F60">5개 항목</b> — 평소 고정되던 필드가 뒤집혀 5번째 값 추가(14위 road_surface=<b style="color:#001F60">wet</b> · 15위 visibility=<b style="color:#001F60">poor</b>).</div>

<div class="fnote">
<div class="ttl">11필드 = 고정 7 + 변동 4</div>
<div class="blk"><span class="h">완전 고정 4</span> <span class="v">(데이터 전체)</span><br>weather=clear · agent_type=cars_only · occlusion=low · special_event=none</div>
<div class="blk"><span class="h">top 20 내 사실상 고정 3</span><br>road_surface=dry · visibility=good · lane_marking=clear <span class="v">(14위 wet·15위 poor만 예외)</span></div>
<div class="blk"><span class="h">변동 4 → 순위 결정</span><br>road_type · lighting · traffic_density · junction_proximity</div>
</div>

</div>
</div>

> 상위 20 조합조차 전부 **정상 상황의 변주** — 첫 비정상은 14·15위(wet·poor). top 100에서도 완전 고정 필드는 **2개뿐**(occlusion=low·event=none), 나머지 9개는 값이 갈리나 정상 조건 내에 국한.

---

## 2 · 결과 ③ — 필드 편향 · 미관측 값 · 수집 우선순위

<style scoped>
.cols{gap:22px;margin-bottom:34px}
table{font-size:9pt;border-collapse:collapse;width:100%}
th,td{padding:3px 8px}
.basis{margin-top:16px;font-size:8pt;line-height:1.5;color:#1a1a1a;border-left:3px solid #00C1DE;padding-left:11px}
.basis b{color:#001F60}
.basis .h{color:#00586F;font-weight:700}
</style>

<div class="cols">
<div>

**필드별 편향**

| 필드 | 지배 값 | 비중 | 진단 |
|------|--------|-----:|------|
| `weather` | clear=92,314 | **91.9%** | 비·눈·안개 거의 없음 |
| `agent_type` | cars_only=97,402 | **97.0%** | <span class="warn">VRU 극소</span> (보행 268·자전거 97) |
| `occlusion_level` | low=99,467 | **99.1%** | 고폐색 전무 |
| `special_event` | none=100,361 | **99.96%** | <span class="danger">accident·emergency 0건</span> |
| `lane_marking` | clear=95,109 | 94.7% | 차선 불량 극소 (absent 252) |

</div>
<div>

**미관측 스키마 값** — 전혀 등장하지 않는 값

| 필드 | 미관측 값 | 의미 |
|------|----------|------|
| `special_event` | accident · emergency | 사고·긴급 상황 클립이 데이터에 **전무** |

> `special_event`의 `obstacle`은 관측됨. `accident`·`emergency`는 100,398클립 전체에서 <span class="danger">**단 한 건도 없음**</span>.

</div>
</div>

**수집 우선순위** (ODD 커버리지 관점) — 관측 비율이 극히 낮거나 전무한 조합 = 데이터 수집 우선 타깃

| 우선 | 타깃 조건 | 현재 클립 수 | 비고 |
|:--:|----------|--:|------|
| <span class="danger">🔴 최우선</span> | `special_event=accident / emergency` | **0** | 안전 크리티컬 — 전체 데이터에 단 1건도 없음 |
| <span class="danger">🔴 최우선</span> | `occlusion_level=high` | 123 | 고폐색 = 지각 모델 직접 실패 · 상위 100 조합 전체 부재 |
| <span class="danger">🔴 최우선</span> | `traffic_density=dense` + `weather=rain/snow` | ~148 | 혼잡+악천후 복합 (독립 분포 기반 추정) |
| <span class="warn">🟠 높음</span> | `agent_type=cyclists / pedestrians` (VRU) | 97 / 268 | 취약 도로 이용자 — VRU 예측 학습 데이터 극소 |
| <span class="warn">🟠 높음</span> | `lane_marking=absent` | 252 | 차선 탐지 모델 완전 실패 구간 |
| <span class="warn">🟠 높음</span> | `weather=snow / fog` | 1,600 / 1,263 | 동절기·안개 시나리오 극소 |
| <span class="warn">🟠 높음</span> | `road_type=national_road` | 242 | 거의 미수집 |

<div class="basis">
<b>표 작성 근거</b> — 각 등급은 <b>정량 + 정성의 결합</b>이다. &nbsp;<span class="h">정량 (코드로 검증)</span> = 관측 클립 수(step_a 실측) · 상위 100 조합 부재(analyze_top100). &nbsp;<span class="h">정성 (도메인 판단 · 코드 metric 없음)</span> = 안전 크리티컬 · 모델 실패 유발 · 취약 · 성능 저하 등 <b>심각도 서술 전부</b>.<br>
<span class="h">등급 부여</span>: 🔴 <b>최우선</b> = <b>[정성]</b> 안전 크리티컬 <b>+ [정량]</b> 상위 100(86%)에서조차 전무(고정 = occlusion=low·special_event=none뿐) · 🟠 <b>높음</b> = <b>[정성]</b> 모델 실패 취약 <b>+ [정량]</b> 관측 극소 · 🟡 <b>중간</b> = <b>[정성]</b> 성능 저하 <b>+ [정량]</b> 관측 존재(본 표 제외).<br>
<span class="v">※ 등급은 관측 수로 정하지 않음 — 🟠 snow(1,600)·fog(1,263)가 🟡 medium(807)·wet(414)보다 <b>데이터가 더 많은데도 더 높은 등급</b>. 즉 등급을 가르는 건 관측 수(정량)가 아니라 심각도(정성).</span> &nbsp; <span class="h">비고 열</span> = AV 성능 영향(정성) + 관측 상태(step_a 실측·정량, ~는 추정).
</div>

---

<!-- _class: statement -->

> 10만 클립이지만, 실질적으로는
> **6,021개 분량**의 정보만 담긴
> 극도로 중복적인 데이터셋

---

## 1 · 핵심 진단 대시보드

<div class="kpi-row">
<div class="kpi"><div class="v">6.0%</div><div class="l">Effective N (soft)<br>6,021 / 100,398</div></div>
<div class="kpi"><div class="v">3.53</div><div class="l">Vendi (random)<br>실질 3~4개 의미 방향</div></div>
<div class="kpi warn"><div class="v">0.944</div><div class="l">상위 10이웃 유사도<br>모든 클립 94% 유사</div></div>
</div>

<div class="kpi-row">
<div class="kpi danger"><div class="v">60.5%</div><div class="l">Q1 PRUNE<br>과반이 밀집+단조</div></div>
<div class="kpi danger"><div class="v">0개</div><div class="l">healthy scenarios<br>12개 중 건강 시나리오 전무</div></div>
<div class="kpi"><div class="v">1.030</div><div class="l">억압 계수 (dedup/random)<br>중복 제거해도 +3.0%뿐</div></div>
</div>

> **진단**: 다양성 부족의 원인은 "중복"이 아니라 **"수집하지 못한 시나리오"**

---

## 3 · Effective N — 계산 원리

<style scoped>
.flow{font-size:10pt;line-height:1.7;margin-top:8px}
.flow b{color:#001F60}.flow .h{color:#00586F;font-weight:700;font-size:11pt}
</style>

<div style="text-align:center;margin:6px 0 2px">

$$\text{Effective N}=\sum_{i=1}^{N} w_i\quad(0\le\text{Effective N}\le N),\qquad \bar s_i=\frac{1}{K}\sum_{j=1}^{K}\text{sim}(x_i,\ \text{NN}_j)$$

$$\underbrace{w_i = 1-\bar s_i}_{\textbf{soft}}\qquad\qquad \underbrace{w_i = \tfrac{1}{\,1+\#\{\text{sim}>0.95\}\,}}_{\textbf{hard}}$$

</div>

<div style="text-align:center;font-size:10pt;color:#001F60;margin:0 0 6px"><b>직관</b>: 각 클립을 <b>독립 클립 몇 개 분량</b>(0~1)으로 세어 더한 값.</div>

<div style="text-align:center;font-size:9.5pt;color:#5f6470;margin:0 0 14px">공통 뼈대는 <b>Σ wᵢ</b>, <b style="color:#001F60">차이는 wᵢ 계산법뿐</b> — soft = 평균 유사도 감점, hard = 근접복제(sim&gt;0.95) 개수 감점. count는 상위 K=20 중(자기 제외), 범위 <b>0~K</b> → hard wᵢ ∈ [1/21, 1].</div>

<div class="flow">

<span class="h">입력 & 계산</span> — 임베딩 **유사도만** 사용 (ODD·캡션 텍스트 직접 안 씀)

**재료**: `embeddings.npy` (N×1024, bge-m3 캡션 임베딩, L2 정규화)
&nbsp;&nbsp;→ **① k-NN** (FAISS): 각 클립의 **상위 20이웃 유사도** 반환 (*평균 아직 X*) → `knn_sim` (N×K)
&nbsp;&nbsp;→ **② 집계** (`knn_sim`만 입력): soft = 20이웃 유사도 **평균**, hard = `sim>0.95` **개수**

**예시** (클립 #5, `knn_sim[5]=[0.98, 0.97, …, 0.91]`) — 같은 이웃, 두 방식:
&nbsp;&nbsp;**soft**: 20이웃 평균 0.945 → `w=1−0.945=`**`0.055`** &nbsp;·&nbsp; **hard**: `sim>0.95` 이웃 3개 → `w=1/(1+3)=`**`0.25`**

</div>

> **요약**: ① k-NN이 각 클립의 *가장 가까운 20개 이웃 + 유사도*를 찾음 → ② 그 20개로 wᵢ 계산 — **soft** = 유사도 *평균*으로 감점(연속), **hard** = 그 중 `sim>0.95` *개수*로 감점(이진).

<div style="font-size:9pt;line-height:1.5;background:#f3f6fa;border:1px solid #d5dce6;border-radius:8px;padding:10px 13px;margin-top:14px">
<b style="color:#001F60">soft·hard는 같은 스케일</b> — 둘 다 <code>Σwᵢ</code>이고 wᵢ = "이 클립을 독립 클립 <b>몇 개</b>로 칠까"(0~1)로 의미가 같다. 완전 고유→wᵢ=1, 완전 중복→wᵢ≈0 으로 <b>끝점(눈금)이 동일</b> → 결과 단위가 같은 "독립 클립 수 ∈ [0,N]". 그래서 <b>6,021 vs 55,766 = 같은 분모의 6% vs 56%</b>, 직접 비교가 정당하다(차이는 오직 애매한 중간=회색지대 판정).
</div>

---

## 3 · Effective N — 목적 & 결과

<style scoped>
.stack{display:flex;flex-direction:column;gap:11px}
.purpose{font-size:10pt;line-height:1.45}.purpose b{color:#001F60}
.h{color:#00586F;font-weight:700;font-size:11pt}
/* 결과 = 히어로 */
.hero{background:#f2f7fb;border:1.5px solid #bcd6e6;border-radius:12px;padding:13px 18px}
.hero .lbl{display:block;text-align:center;color:#00586F;font-weight:700;font-size:12pt}
.stats{display:flex;justify-content:center;gap:44px;align-items:flex-end;margin:8px 0 4px}
.stat{text-align:center}
.stat .num{font-size:32pt;font-weight:800;color:#001F60;line-height:.95}
.stat .num.soft{color:#c8871a}
.stat .cap{font-size:9pt;color:#444;margin-top:2px}.stat .cap b{color:#001F60}
.hero .why{border-top:1px dashed #bcd6e6;margin-top:10px;padding-top:9px;font-size:8.5pt;line-height:1.5;color:#3a3f47}.hero .why b{color:#001F60}.hero .why code{font-size:.92em}
.hero .why ul{margin:4px 0 2px;padding-left:16px}.hero .why li{margin:1.5px 0}.hero .why .src{color:#8a8f98}
.lim{font-size:8.5pt;line-height:1.45;background:#fbf6ec;border:1px solid #ecdcbf;border-radius:8px;padding:9px 13px}
.lim .t{color:#c8871a;font-weight:700}.lim b{color:#001F60}
.lim .sub{color:#00586F;font-weight:700}.lim .ex{color:#7a6420;font-size:8pt;margin-top:3px}
.lim ol,.lim ul{margin:3px 0 0;padding-left:17px}.lim li{margin:2px 0}.lim li b{color:#001F60}
.lim .hint{color:#8a7a55;font-size:7.6pt}
.lim .concl{margin-top:6px;padding-top:5px;border-top:1px dashed #e3cf9e}
</style>

<div class="stack">

<div class="purpose">
<span class="h">목적 — 왜 재나</span>&nbsp; <b>"10만 클립 = 실질 정보 몇 개 분량인가"</b> 정량화. 중복 많으면 클립 수↑라도 실질 정보량↓ → ① <b>유효 크기</b> 추정 ② <b>pruning 여지</b> 판단. 중복 기준 엄격도만 달리한 두 버전을 <b>범위</b>로 봄 — <b>Hard</b>=관대(상한, <code>sim&gt;0.95</code> 복제만) · <b>Soft</b>=엄격(하한, 평균 유사도 연속 감점). 격차 = 부드러운 중복량 진단.
</div>

<div class="hero">
<span class="lbl">결과 — 전체 100,398 클립의 실질 정보량</span>
<div class="stats">
<div class="stat"><div class="num soft">6.0%</div><div class="cap">Soft (엄격·하한)<br>Effective N = <b>6,021</b></div></div>
<div class="stat"><div class="num">56%</div><div class="cap">Hard (관대·상한)<br>Effective N = 55,766</div></div>
</div>
<div style="text-align:center;font-size:9pt;color:#5f6470;margin-top:8px;line-height:1.5"><b style="color:#c8871a">Soft</b> 기준 나머지 <b>94%</b>는 반복 정보 · <b style="color:#001F60">Hard</b> 기준 나머지 <b>44%</b>는 반복 정보</div>
<div class="why"><b>왜 6% ↔ 56%로 벌어지나</b> — 격차 <b>≈5만 클립</b> = '애매하게 닮은(near-중복)' 장면의 양. <b>차이는 판정 엄격도뿐</b>:
<ul>
<li><b style="color:#001F60">Hard</b>(관대) — 거의 똑같은 복사본(<code>sim&gt;0.95</code>)<b>만</b> 중복 처리 → <b>55,766</b> 남김</li>
<li><b style="color:#c8871a">Soft</b>(엄격) — <code>0.90~0.95</code> 미묘하게 닮은 장면까지 깎음 → <b>6,021</b> 남김</li>
<li>📷 <b>비유</b> — 연사(burst) 10장: Hard는 <b>10장</b> · Soft는 사실상 <b>1장</b>으로 셈</li>
<li><b>이 데이터셋</b> — '도심 직진'류 연사형 장면 수만 장 → Soft에서만 대량 필터 → 격차 발생</li>
</ul>
<span class="src">(Yao et al., <i>SoftDedup</i>, ACL 2024)</span></div>
</div>

<div class="lim">
<div><span class="t">⚠ 한계 — 단독으로 믿으면 안 되는 이유</span></div>
<ul>
<li><b>정체</b> — 각 클립이 <b>K=20 이웃만</b> 보는 <b>로컬</b> 통계</li>
<li><b>가능</b> "중복이 얼마나 많나(질량)" · <b>불가</b> "독립 덩어리가 몇 개인가(글로벌)"</li>
<li><b>약점</b> — K·유사도에 민감 → <b>클러스터 크기 ≈ K면 값 왜곡</b></li>
</ul>
<div class="ex"><b>예)</b> 거의 같은 클립 <b>21장</b> 그룹이 <b>4,762개</b>(총 10만) → 직관 답 "독립 ≈ 4,762". 그러나 K=20이면 각 클립이 <b>1−0.98=0.02장</b>으로만 세어져 합계 <b>≈2,000</b> = 참값(4,762)도 총수(10만)도 아닌 <b>K에 휘둘린 값</b>.</div>
<div style="margin-top:5px"><span class="sub">✔ 보완</span></div>
<ol>
<li><b>Vendi 병행(주)</b> — 글로벌 스펙트럼으로 "덩어리 몇 개"를 직접 포착. <i>Effective N을 단독으로 안 쓰는 이유.</i></li>
<li><b>K-민감도</b> — K=10/20/40으로 다시 세어 값이 크게 흔들리면 "클러스터 크기 ≈ K" 경고. <span class="hint">쉽게: 자(K)를 바꿨더니 잰 값이 달라지면 그 값은 못 믿는다.</span></li>
<li><b>그룹 수가 필요하면</b> — 유사도 τ 이상 닮은 클립끼리 사슬처럼 이어붙여 <b>덩어리 개수를 직접</b> 셈(연결요소). <span class="hint">쉽게: A~B, B~C면 A·C도 한 무리 — 친구의 친구까지 사슬로 이어 붙이면 연사 500장도 통째로 1덩어리.</span></li>
</ol>
<div class="concl"><b style="color:#001F60">결론</b> — 로컬(Effective N) <b>＋</b> 글로벌(Vendi)을 <b>반드시 함께</b>.</div>
</div>

</div>

---

## 3 · Vendi 3전략 — 중복 vs 커버리지

| 전략 | Vendi | 의미 |
|------|------:|------|
| random (현재 분포) | 3.530 | 모델이 실제로 받는 다양성 |
| dedup (중복 완전 제거) | 3.636 | +0.106 (**+3.0%**) |
| topk (커버리지 확장 상한) | 4.745 | +1.215 (**+34.4%**) |

<div class="kpi-row">
<div class="kpi"><div class="v">11.5×</div><div class="l">커버리지 문제가 중복 문제보다<br>11.5배 더 큰 원인</div></div>
<div class="kpi"><div class="v">1.030</div><div class="l">억압 계수 — 중복 완전 제거해도<br>3.0% 향상에 그침</div></div>
</div>

> **중복 제거보다 새 시나리오 수집·합성이 ~10배 효과적.**

---

## 3 · 두 지표는 상보적

| 지표 | 질문 | 관점 |
|------|------|------|
| **Effective N** | 중복 안 된 샘플이 몇 개? | 로컬 (개별 밀도) |
| **Vendi** | 독립 의미 방향이 몇 개? | 글로벌 (스펙트럼) |

> 로컬 고유성 ≠ 글로벌 다양성. Effective N=6,021개**조차** Vendi로 보면 3~4개 방향에만 집중.

|  | Vendi 높음 | Vendi 낮음 |
|--|--|--|
| **Eff N 높음** | ✅ 이상적 | ⚠️ 좁은 공간에 퍼짐 |
| **Eff N 낮음** | ⚠️ 방향만 있고 빈약 | <span class="danger">❌ 이번 데이터셋</span> |

---

## 3 · 6-분류 Action Map (FLIPD 후)

밀도(density)와 LID 2축을 GMM 임계값으로 사분면화 → 6개 액션 레이블

| 분류 | 레이블 | FLIPD 전 | FLIPD 후 |
|:--:|--------|--------:|--------:|
| Q0 | KEEP (잘 수집된 다양) | 11,710 (11.7%) | 변동 없음 |
| Q1 | <span class="danger">PRUNE</span> (밀집+단조) | 60,731 (**60.5%**) | 변동 없음 |
| Q2 | COLLECT (수집 대상) | 11,426 (11.4%) | **17,694 (17.6%)** ↑ |
| Q3 | EVALUATE (경계) | 16,531 (16.5%) | **10,263 (10.2%)** ↓ |

> GMM 임계값(BIC K=3): `density=0.9363` · `lid=16.855` — 두 분포 모두 3성분으로 분리(단봉 아님). Q4/Q5(불신뢰)=0 → 초고밀도라 LID 추정 전부 신뢰 가능.
> ⚠️ Q3→Q2 업그레이드 **6,268개**는 초고밀도에서 FLIPD 공식 발산(upgrade_rate=1.0)한 결과 — 신뢰도 낮음, Q3 수동 샘플링 확인 권장.

---

## 4 · 시나리오 12개 (TF-IDF K-Means, K=12)

<style scoped>table{font-size:8.5pt}th,td{padding:3px 9px}</style>

| S | 크기 | Q1% | Q2% | Vendi | 주요 키워드 · 성격 |
|---|-----:|----:|----:|:--:|------|
| **S0** | 5,648 | <span class="danger">83.2</span> | 4.2 | 2.3 | headlights — 야간 단조 (첫 pruning 대상) |
| S1 | 5,307 | 62.9 | 14.2 | 2.6 | travels, ego — COLLECT 후보 |
| S2 | 3,131 | 46.1 | 26.1 | 2.6 | parking lot, low speed — Q2 많음 |
| S3 | 2,220 | 65.4 | 16.5 | 2.5 | snow covered — 설면 |
| S4 | 10,188 | 72.5 | 9.9 | 2.5 | highway, lane — Q1 과다 |
| S5 | 9,182 | 69.5 | 10.5 | 2.6 | sedan, suv — Q1 과다 |
| S6 | 10,115 | 62.3 | 15.3 | 2.6 | intersection — COLLECT 후보 |
| S7 | 10,639 | 69.7 | 13.0 | 2.8 | vehicle, lane, ego |
| S8 | 11,798 | 60.4 | 17.0 | 2.6 | parked vehicles — COLLECT 후보 |
| S9 | 8,912 | 43.3 | 29.9 | 2.9 | sharp curve — Q2 많음 |
| S10 | 11,310 | 35.1 | <span class="warn">37.4</span> | 3.0 | turn/교차로 — Q2 최다 |
| S11 | 11,948 | 61.7 | 14.3 | 2.6 | vehicle, lane — COLLECT 후보 |

> 전 시나리오 Vendi **2.3~3.0** — 내부도 다양성 낮음. 억압 계수 1.02~1.05 → 구조적 갭(중복 아님). 두 공간 독립성 NMI=0.034·ARI=0.011 → 시나리오↔사분면 교차표 유효.

---

## 5 · 수집 · 합성 우선순위

<div class="cols">
<div>

**COLLECT — 즉시 수집 (7개)**

| S | 갭 수 | 부족 유형 |
|---|----:|------|
| S10 | 6,284 | roundabout·cyclist |
| S8 | 2,741 | 주차 bus·truck |
| S6 | 2,651 | 교차로·wet |
| S11 | 2,448 | 공사·습노면 |

</div>
<div>

**SYNTHETIC — 합성 (5개)**

| S | 갭 수 | 키워드 |
|---|----:|------|
| S9 | 4,261 | sharp curve |
| S7 | 2,283 | rural·보행자 |
| S2 | 1,537 | parking lot |
| S3 | 672 | snow |

</div>
</div>

> HIGH: LID(≥16.86) 또는 ODD eff_n(≥22) 충족. SYNTHETIC은 합성 전 Q2 클립 선수집 권장.

---

## 6 · 다음 액션

**즉시 검토**
- FLIPD 이슈: Q3 클립(10,263개) 수동 샘플링 검증
- `lid_threshold` 16.86 → 13~15 하향 재실행 검토

**EXP-004 데이터 수집**
- HIGH: S10·S11·S8·S6·S5·S1 갭
- 합성: S9·S7·S2·S3·S0

**Pruning**
- S0 (야간 직진, Q1=83%) 1순위 → Q1 전체 60,731개 제거 전략

---

<!-- _class: section -->
<!-- _paginate: false -->

# 부록
### §3-2 Vendi 수식 유도 · §7 산출물 파일 가이드
### `results_interpretation.md` 참조
