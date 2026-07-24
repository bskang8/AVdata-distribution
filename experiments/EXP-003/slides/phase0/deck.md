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

**100,398 clips**
`experiments/EXP-003/phase0/output/`

---

<!-- _class: section -->
<!-- _paginate: false -->

# 1 · ODD 커버리지 분석
### 이 데이터셋은 운영설계영역(ODD) 조합 공간을 얼마나 커버하는가?
### Step 0-F · 100,398 clips

---

## 1 · ODD 스키마 정의 — 11필드 값 분포

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

## 1 · ODD 커버리지 정량화 — 도출 & 결과

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

## 1 · 결과 ② — 상위 조합 집중 & 최빈 top 20

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

## 1 · 결과 ③ — 필드 편향 · 미관측 값 · 수집 우선순위

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

<!-- _class: section -->
<!-- _paginate: false -->

# 2 · 임베딩 벡터 기반 분포 분석
### 캡션 임베딩 공간에서 데이터가 얼마나 중복되고 몇 방향을 커버하는가?
### Effective N (중복·유효 크기) · Vendi (의미 다양성)

---

## 2 · Effective N — 계산 원리

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

## 2 · Effective N — 목적 & 결과

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

## 2 · Vendi — 계산 원리

<style scoped>
.flow{font-size:10pt;line-height:1.65;margin-top:4px}
.flow b{color:#001F60}.flow .h{color:#00586F;font-weight:700;font-size:11pt}
.scale{font-size:9pt;color:#3a3f47;margin:6px 0 0;line-height:1.55;text-align:center;background:#f6f8fb;border:1px solid #e1e8f0;border-radius:7px;padding:6px 12px}.scale b{color:#001F60}
.bridge{background:#f2f7fb;border:1px solid #cddcee;border-radius:10px;padding:8px 14px;margin:2px 0 6px}
.bridge .bt{text-align:center;font-size:9.5pt;color:#001F60;margin-bottom:7px}
.bridge .bg{display:flex;align-items:stretch;gap:8px;justify-content:center}
.bridge .bs{flex:1;background:#fff;border:1px solid #d5dce6;border-radius:8px;padding:7px 11px;font-size:9pt;color:#333}
.bridge .bs .n{font-family:monospace;font-weight:700;color:#00586F;font-size:9.5pt}
.bridge .bs .d{font-size:8pt;color:#5f6470;margin-top:3px;line-height:1.4}
.bridge .bs .fn{display:block;color:#8a8f98;font-size:7.4pt;margin-top:2px}
.bridge .bs b{color:#001F60}
.bridge .ar{display:flex;align-items:center;color:#00586F;font-weight:700;font-size:15pt}
.bridge .ba{margin-top:8px;font-size:8.7pt;color:#3a3f47;line-height:1.5;background:#fffdf5;border:1px solid #ecdcbf;border-radius:6px;padding:7px 11px}
.bridge .ba b{color:#001F60}
.step{color:#00586F;font-weight:700;font-size:11pt;margin:20px 0 6px;padding-left:9px;border-left:4px solid #00586F}
.step:first-of-type{margin-top:8px}
.step .sub{color:#5f6470;font-weight:600;font-size:9.5pt}
.k ul{margin:2px 0 0;padding-left:18px;font-size:9.5pt;line-height:1.5}.k li{margin:1.5px 0}.k b{color:#001F60}.k code{font-size:.9em}
.k .kd{font-size:8.5pt;color:#5f6470;margin-top:5px}.k .kd b{color:#001F60}
.stab{font-size:9pt;color:#5f6470;margin:2px 0 0;line-height:1.5}.stab b{color:#001F60}
</style>

<div class="step">① 유사도 표(커널 K) 만들기</div>

<div class="k">
<ul>
<li><b>뽑기</b> — 10만 전부는 너무 커(10만² 불가) → <b>임의 2,000개 클립</b> 추출(<b>Nyström</b> 근사)</li>
<li><b>비교</b> — 2,000개 벡터(bge-m3, L2정규화)를 <b>서로서로 코사인 유사도</b> → <b>2000×2000 표 K</b></li>
<li><b>의미</b> — <code>K[i,j]</code> = "클립 i·j가 얼마나 닮았나" (1=똑같음 · 0=무관 · 대각선=자기=1)</li>
</ul>
<div class="kd">🔎 <b>직관</b>: K = "닮음 지도". 닮은 클립 많음 → 행/열 평행 → <b>랭크 낮음</b> → 다음 단계 <b>고유값 λ가 소수 축에 쏠림</b>. <span style="color:#8a8f98">(Effective N과 같은 임베딩, 보는 각도만: 개별 이웃 → 전체 스펙트럼)</span></div>
</div>

<div class="step">② 이 표 K에서 다양성 뽑기 <span class="sub">— 아래 수식으로 계산</span></div>

<div style="text-align:center;margin:2px 0 4px">

$$\text{Vendi}=\exp\!\bigl(H(\mathbf p)\bigr)=\exp\!\Bigl(-\sum_i p_i\log p_i\Bigr),\qquad p_i=\frac{\lambda_i}{\sum_j \lambda_j}\ \ (\lambda=\text{유사도 커널 }K\text{의 고유값})$$

</div>

<div class="bridge">
<div class="bt">K의 고유값 <b>λ</b>를 3토막으로 읽으면 위 수식이 곧 <b>"독립 방향 수"</b></div>
<div class="bg">
<div class="bs"><span class="n">λᵢ</span> : 방향별 <b>크기</b><div class="d">각 독립 축에 데이터가 퍼진 정도(에너지). 큰 λ = 그 방향에 데이터가 몰림.</div></div>
<div class="ar">→</div>
<div class="bs"><span class="n">pᵢ = λᵢ/Σλ</span> : 방향별 <b>비중</b><div class="d">합=1로 정규화 → "전체 다양성 중 이 방향이 차지하는 몫".</div></div>
<div class="ar">→</div>
<div class="bs"><span class="n">exp(H)</span> : <b>"균등 몇 개짜리와 맞먹나"</b>로 환산<div class="d">균등 4방향 → <b>4</b> · 한 방향 97% 쏠림 → <b>≈1</b> ⇒ <b>실제로 일하는 방향 수</b><span class="fn">∵ 지배항 ln0.97≈0 · 1%항은 비중에 눌림 ⇒ H≈0 ⇒ exp(H)≈1</span></div></div>
</div>
<div class="ba">🔑 <b>"균등하게 k개면 정확히 k"</b> → 그래서 exp(H)는 "실질적으로 몇 개 방향인가"를 재는 <b>soft 카운트</b>다. 주사위가 고르면 6, 한 눈에 쏠리면 ≈1로 나오는 <b>'유효 선택지 수'</b>와 같은 원리(= Hill number·유효 종 수).</div>
</div>

<div class="scale">📏 <b>Vendi 눈금</b> — 모든 클립 동일 → <b>1</b> · k개 독립 그룹(균등) → <b>k</b> · 2,000개 전부 독립 → <b>2000</b> &nbsp;|&nbsp; 고유값이 <b>소수에 쏠릴수록 값↓</b>(좁은 공간) · <b>고를수록 값↑</b>(넓은 커버리지)</div>

<div class="step">③ 안정화 <span class="sub">— 재현 가능한 값인가</span></div>

<div class="stab">앵커 2,000개를 다시 뽑아 여러 번 반복, run 간 <b>표준오차/평균 &lt; 2%</b>면 수렴 → 샘플링에 흔들리지 않는 안정값 (이번 3전략 모두 5회 만에 수렴, Sequential Stopping Rule).</div>

---

## 2 · Vendi — 목적 · 결과 · 해석

<style scoped>
.stack{display:flex;flex-direction:column;gap:11px}
.purpose{font-size:10pt;line-height:1.45}.purpose b{color:#001F60}
.h{color:#00586F;font-weight:700;font-size:11pt}
.hero{background:#f2f7fb;border:1.5px solid #bcd6e6;border-radius:12px;padding:13px 18px}
.hero .lbl{display:block;text-align:center;color:#00586F;font-weight:700;font-size:12pt}
.hero .method{text-align:center;font-size:8.7pt;color:#5f6470;margin:5px 0 0}.hero .method b{color:#001F60}
.stats{display:flex;justify-content:center;gap:34px;align-items:flex-end;margin:8px 0 4px}
.stat{text-align:center}
.stat .num{font-size:30pt;font-weight:800;color:#001F60;line-height:.95}
.stat .num.up{color:#1a7f5a}
.stat .cap{font-size:9pt;color:#444;margin-top:2px}.stat .cap b{color:#001F60}
.hero .why{border-top:1px dashed #bcd6e6;margin-top:10px;padding-top:9px;font-size:8.5pt;line-height:1.5;color:#3a3f47}.hero .why b{color:#001F60}.hero .why code{font-size:.92em}
.hero .why ul{margin:4px 0 2px;padding-left:16px}.hero .why li{margin:1.5px 0}.hero .why .src{color:#8a8f98}
.merge{font-size:8.5pt;line-height:1.45;background:#eef4fb;border:1px solid #cddcee;border-radius:8px;padding:9px 13px}
.merge .t{color:#00586F;font-weight:700}.merge b{color:#001F60}
.mtx{border-collapse:collapse;margin:6px 0 0;font-size:8.5pt;width:100%}
.mtx td,.mtx th{border:1px solid #cddcee;padding:4px 9px;text-align:center}
.mtx th{background:#dbe7f5;color:#001F60}
.mtx .bad{background:#fbf3f3;color:#d23b3b;font-weight:700}
.merge .concl{margin-top:6px;padding-top:5px;border-top:1px dashed #cddcee}
</style>

<div class="stack">

<div class="purpose">
<span class="h">목적 — 왜 재나</span>&nbsp; Effective N은 <b>중복 질량</b>(로컬)만 본다 → <b>"몇 개의 독립 의미 방향인가"(글로벌)</b>는 Vendi가 답. <b>같은 공식</b>에 앵커를 <b>3가지 방식</b>으로 뽑아, 다양성 부족의 원인을 <b>중복 vs 커버리지</b>로 분해한다.
</div>

<div class="hero">
<span class="lbl">결과 — Vendi 3전략 (독립 의미 방향 수)</span>
<div class="method">셋 다 <b>같은 Vendi 공식</b>(p11) · 다른 건 <b>앵커 2,000개를 어떻게 뽑나</b>뿐</div>
<div class="stats">
<div class="stat"><div class="num">3.53</div><div class="cap"><b>random</b> — 10만서 <b>균등 무작위</b> 2,000개<br>= 현재 분포(모델이 받는 다양성)</div></div>
<div class="stat"><div class="num">3.64</div><div class="cap"><b>dedup</b> — <b>고유성 가중</b> 뽑기(흔한↓·희귀↑)<br>= Effective N 가중치(w)를 반영한 분포</div></div>
<div class="stat"><div class="num up">4.75</div><div class="cap"><b>topk</b> — 고유성 <b>상위 풀</b>에서 2,000개<br>= <b>Effective N 상위 6,021개</b> (다양성 상한)</div></div>
</div>
<div style="text-align:center;font-size:9pt;color:#5f6470;margin-top:8px;line-height:1.5">억압계수 <b>1.030</b>(<code>dedup÷random</code>) — 중복 다 지워도 <b>+3.0%뿐</b> · 이상적 큐레이션 상한(topk)<b>조차 <span style="color:#1a7f5a">4.75</span></b></div>
<div class="why"><b>어떻게 읽나</b> — <b>진단 2단계 → 처방</b>으로 읽는다:
<ul>
<li><b>① 원인 배분</b> — 억압계수 <b>1.030</b>(<code>dedup÷random</code>) → 중복을 완전히 지워도 다양성은 <b>+3.0%뿐</b> → <b>중복은 범인이 아니다</b>.</li>
<li><b>② 낮은 천장</b> — 중복을 완벽히 지운 상한(topk)<b>조차 4.75</b>(이상적 AV셋은 수십~수백) → 고유 알맹이도 사실상 <b>3~5개 방향</b>('도심 직진' 지배)뿐.</li>
<li><b style="color:#1a7f5a">③ 처방</b> — 부분집합 재조정으론 천장을 못 올림 → <b>없는 시나리오를 새로 수집·합성</b>해야 다양성이 오른다.</li>
</ul>
<span class="src">① 진단(원인 배분) · ② 진단(천장 낮음) 이 함께여야 ③ 처방이 선다 · (Friedman &amp; Dieng, <i>Vendi Score</i>, TMLR 2023)</span></div>
</div>

<div class="merge">
<div><span class="t">🔗 Effective N과 병합 해석 — 로컬 고유성 ≠ 글로벌 다양성</span> &nbsp;개별 클립이 안 겹쳐도(로컬) 전체는 좁은 공간에 몰릴(글로벌) 수 있다. Eff N <b>6,021개조차</b> Vendi로 보면 <b>3~4방향</b>에만 집중.</div>
<table class="mtx">
<tr><th></th><th>Vendi 높음</th><th>Vendi 낮음</th></tr>
<tr><th>Eff N 높음</th><td>✅ 이상적</td><td>⚠ 좁은 공간에 퍼짐</td></tr>
<tr><th>Eff N 낮음</th><td>⚠ 방향만 있고 빈약</td><td class="bad">❌ 이번 데이터셋</td></tr>
</table>
<div class="concl"><b style="color:#001F60">결론</b> — 두 지표가 같은 진단(극히 좁은 공간 집중). <b>로컬(Effective N) ＋ 글로벌(Vendi)을 반드시 함께</b> 봐야 "중복 vs 커버리지"를 갈라 처방할 수 있다.</div>
</div>

</div>

---


<!-- _class: section -->
<!-- _paginate: false -->

# 3 · 두 렌즈의 상호보완
### 조건 커버리지(ODD) × 내용 다양성(임베딩) — 왜 반드시 함께 봐야 하나

---

## 3 · 실증 ① — ODD엔 '같은 조건', 임베딩엔 '다른 장면'

<style scoped>
.lead{font-size:10pt;color:#3a3f47;margin:2px 0 9px}.lead b{color:#001F60}
.hero{background:#f2f7fb;border:1.5px solid #bcd6e6;border-radius:12px;padding:12px 18px;margin-bottom:11px}
.hero .lbl{display:block;text-align:center;color:#00586F;font-weight:700;font-size:11.5pt;margin-bottom:8px}
.row{display:flex;justify-content:center;gap:40px;align-items:center}
.cell{text-align:center}.cell .k{font-size:10pt;color:#444;line-height:1.4}.cell .k b{color:#001F60}
.cell .big{font-size:15pt;font-weight:800;color:#8a8f98;line-height:1.1}
.arrow{font-size:20pt;color:#9cc0d8}
.vend{text-align:center}.vend .num{font-size:34pt;font-weight:800;color:#001F60;line-height:.95}
.vend .cap{font-size:9pt;color:#444;margin-top:3px}.vend .cap b{color:#1a7f5a}
.two{display:flex;flex-direction:column;gap:9px}
.box{border-radius:9px;padding:9px 14px;font-size:8.9pt;line-height:1.5}
.logic{background:#f5f2fb;border:1.5px solid #d8cbe8}.name{background:#fff7f2;border:1.5px solid #eccdbf}
.box .bh{font-weight:700;font-size:10pt;margin-bottom:3px}.logic .bh{color:#6a3fa0}.name .bh{color:#b8562a}
.box b{color:#001F60}.box code{font-size:.9em;background:#eef2f7;padding:0 3px;border-radius:3px}
.q{color:#b8562a;font-weight:700;font-size:11.5pt;text-align:center;margin:2px 0 6px}
.poles{display:flex;gap:9px;margin:5px 0}
.p{flex:1;background:#fff;border:1px solid #eccdbf;border-radius:7px;padding:5px 6px;text-align:center;font-size:8.5pt;color:#3a3f47}
.p b{display:block;color:#001F60;font-size:11pt;margin:1px 0}
.p .t{display:block;color:#8a6a55;font-size:7.7pt}
.note{font-size:7.6pt;color:#a98a76;margin-top:5px;border-top:1px dashed #eccdbf;padding-top:4px}
.callout{background:#ede7f6;border:1.5px solid #c7b3dc;border-radius:7px;padding:4px 10px;text-align:center;margin:5px 0;font-size:9pt;color:#4a2f6a}.callout b{color:#001F60;font-size:13pt}.callout span{font-size:8pt;color:#7a6a8a}
</style>

<div class="lead">개념 주장이 아니라 <b>측정</b>. 가장 흔한 ODD 조합 <b>1개</b>를 떼어, 그 안의 임베딩 다양성을 잰다.</div>

<div class="hero">
<span class="lbl">가장 흔한 ODD 셀 6,578클립 — ODD 튜플이 완전 동일 (urban·clear·cars_only·sparse·post_junction…)</span>
<div class="row">
<div class="cell"><div class="k"><b>6,578</b> 클립<br>ODD 다양성(entropy)<br><span class="big">0.00</span><br>= "한 상황"</div></div>
<div class="arrow">➜</div>
<div class="vend"><div class="num">3.17</div><div class="cap">셀 내부 <b>임베딩 Vendi</b><br>= 무작위 동일크기(3.53)의 <b>89.9%</b></div></div>
</div>
</div>

<div class="two">
<div class="box name"><div class="q">"임베딩 다양성 = 의미없는 노이즈 착각 아니냐?" - 아니다</div>
검증: 6,578개를 임베딩으로 <b>2그룹</b>으로 나눠, 각 그룹 캡션의 <b>대표어(TF-IDF)</b>로 이름 붙임 →
<div class="poles">
<span class="p">정차·노변주차<b>3,163</b><span class="t">parked · street</span></span>
<span class="p">교차로 통과주행<b>3,415</b><span class="t">traffic · intersection</span></span>
</div>
주행 판단이 <b>전혀 다른 상황</b>인데 <b>ODD 11축엔 이 구분이 없다</b> (ODD엔 날씨·조명 같은 '조건'만, 정차/통과 같은 기동·장면 축은 없음) → 노이즈가 아니라 실제 <b>장면 내용(content)</b>.
<div class="note">※ TF-IDF: 각 그룹 캡션에서 <b>그 그룹에만 유독 자주 나오는 단어</b>를 추출(ego·road 등 전체 공통어는 제외) → 그룹의 정체를 한 줄로 요약</div></div>
<div class="box logic"><div class="bh">직교성 — 상관이 아니라 메커니즘</div>임베딩이 ODD를 따른다면 셀 안 Vendi는 <b>1로 붕괴</b>해야 한다 → 관측 <b>3.17</b>(전역의 90%), 안 붕괴 → <b>임베딩 방향 ⊥ ODD 셀</b>. "임베딩=노이즈"설 반박. <span style="color:#8a8f98;font-size:7.6pt">(단, 이건 셀 1개 근거 — 전체 엄밀값은 다음 장 η²)</span></div>
</div>

---

## 3 · 실증 ②(대칭) & 결론 — 양방향 blind spot

<style scoped>
.lead{font-size:9.5pt;color:#3a3f47;margin:2px 0 8px}.lead b{color:#001F60}
.hero{background:#faf7fc;border:1.5px solid #d8cbe8;border-radius:11px;padding:10px 16px;margin-bottom:9px}
.hero .lbl{display:block;text-align:center;color:#6a3fa0;font-weight:700;font-size:11pt;margin-bottom:6px}
.row{display:flex;justify-content:center;gap:34px;align-items:center}
.cell{text-align:center}.cell .k{font-size:9.5pt;color:#444;line-height:1.4}.cell .k b{color:#001F60}
.cell .big{font-size:15pt;font-weight:800;color:#6a3fa0;line-height:1.1}
.arrow{font-size:18pt;color:#c7b3dc}
.flip{margin-top:8px}.flip .ftt{font-size:8pt;color:#6a3fa0;font-weight:700;text-align:center;margin-bottom:4px}
.fr{display:flex;align-items:center;gap:7px;margin:2.5px 0;font-size:8.2pt}
.fr .fn{width:74px;text-align:right;color:#001F60;font-weight:600}
.fr .track{flex:1;background:#efe9f5;border-radius:3px;height:10px}
.fr .fbar{display:block;height:100%;background:#7a3fa0;border-radius:3px}
.fr .fv{width:40px;color:#5f6470}
.fcap{font-size:7.3pt;color:#9a86b0;text-align:center;margin-top:3px}
.cols{display:flex;gap:13px;align-items:stretch}.col{flex:1;display:flex;flex-direction:column}
.bd{border-collapse:collapse;width:100%;font-size:8.5pt}
.bd th,.bd td{border:1px solid #cddcee;padding:5px 8px;text-align:center;line-height:1.3}
.bd th{background:#dbe7f5;color:#001F60}.bd td.l{text-align:left}.bd b{color:#001F60}
.bd .n{font-weight:800;font-size:12pt;color:#001F60}
.mtx2{border-collapse:collapse;width:100%;font-size:8.3pt}
.mtx2 th,.mtx2 td{border:1px solid #cddcee;padding:4px 6px;text-align:center;line-height:1.25}
.mtx2 th{background:#dbe7f5;color:#001F60}
.mtx2 .go{background:#f1f8f3;color:#1a7f5a;font-weight:700}.mtx2 .sy{background:#fbf7f0;color:#b8862a;font-weight:700}.mtx2 .ig{color:#8a8f98}
.pay{font-size:7.9pt;color:#5f6470;margin-top:4px;text-align:center}.pay b{color:#001F60}
.concl{margin-top:9px;background:#eef4fb;border:1px solid #cddcee;border-radius:8px;padding:8px 14px;font-size:8.9pt;line-height:1.5}.concl b{color:#001F60}
</style>

<div class="lead">대칭 검증 — 이번엔 <b>임베딩이 "같다"고 본 이웃</b> 안에서 ODD가 갈리는가.</div>

<div class="hero">
<span class="lbl">임베딩상 가장 닮은 이웃 20개 — 평균 유사도 0.94 ("임베딩상 거의 같음")</span>
<div class="row">
<div class="cell"><div class="k">그 이웃끼리도 ODD 11필드 중<br><span class="big">평균 1.8개</span> 다름<br>(무작위는 3.2개)</div></div>
<div class="arrow">➜</div>
<div class="cell"><div class="k">ODD 다양성 <b>55.3% 보존</b><br>+ 가장 닮은 이웃 20개 묶음에<br><b>다른 ODD 조합 평균 ~11개</b></div></div>
</div>
</div>

<div class="hero">
<span class="lbl">ODD 조합이 같은 클립들 — 전수 분산분석 η² ("조합이 같아도 화면은 딴판")</span>
<div class="row">
<div class="cell"><div class="k">ODD 조합으로 설명되는<br>임베딩 다양성<br><span class="big">21%뿐</span><br>(η² · 순열귀무 2%)</div></div>
<div class="arrow">➜</div>
<div class="cell"><div class="k">임베딩 다양성 <b>80%가 ODD 밖</b><br>실증①의 90%는 top셀 편향<br>→ 엄밀값 <b>80%</b>로 교정</div></div>
</div>
<div class="pay">계산·우연/싱글톤 검증 ▸ 부록 C</div>
</div>

<div class="cols">
<div class="col">
<table class="bd">
<tr><th>고정한 렌즈 / 방법</th><th>남는 상대 다양성</th></tr>
<tr><td class="l">ODD 셀 고정 <span style="color:#8a8f98">(실증①)</span></td><td>임베딩 <span class="n">90%</span></td></tr>
<tr><td class="l">임베딩 이웃 고정 <span style="color:#8a8f98">(실증②)</span></td><td>ODD <span class="n">55%</span></td></tr>
<tr><td class="l">ODD 전체 η² <span style="color:#8a8f98">(실증④)</span></td><td>임베딩 <span class="n">80%</span> 밖</td></tr>
</table>
<div class="pay">양방향·전체 모두 큰 잔차 → <b>진짜 상호보완</b> (세 증거 <b>90 / 55 / 80%</b> 수렴).</div>
</div>
<div class="col">
<table class="mtx2">
<tr><th></th><th>임베딩갭 O</th><th>임베딩갭 X</th></tr>
<tr><th>ODD갭 O</th><td class="go">실수집 최우선<br>S10·S11</td><td class="go">실수집<br>S6·S1</td></tr>
<tr><th>ODD갭 X</th><td class="sy">합성<br>S9·S7</td><td class="ig">무시</td></tr>
</table>
<div class="pay">수집/합성/무시 = 두 플래그 <b>동시</b> 요구</div>
</div>
</div>

<div class="concl"><b>결론 — 직교하는 두 축(ODD=조건 격자 · 임베딩=내용 기하)</b>. 임베딩은 격자를 <b>가로질러</b>(η² 80%가 셀 밖·NN이 ~11조합에 걸침) ODD에 축이 없는 <b>내용 다양성</b>을, ODD는 임베딩이 못 하는 <b>명명·외부앵커·미관측 조건</b>을 잰다. <b>중첩(셀 안/밖)이 아니라 직교</b> — 데이터의 진짜 좌표는 <b>둘의 곱</b>이지 어느 하나가 아니다. <span style="color:#8a8f98">단, 둘 다 캡션 파생 → 완전 독립 검증은 제3 신호(egomotion).</span></div>

---


<!-- _class: section -->
<!-- _paginate: false -->

# 부록
### §3-2 Vendi 수식 유도 · §7 산출물 파일 가이드
### `results_interpretation.md` 참조

---

## 부록 A · Vendi 3전략 — 앵커 2,000개 뽑는 법

<style scoped>
.lead{font-size:10pt;color:#3a3f47;margin:4px 0 8px}.lead b{color:#001F60}
.cmp{border-collapse:collapse;width:100%;font-size:9pt;margin:0 0 10px}
.cmp th,.cmp td{border:1px solid #d5dce6;padding:5px 11px;text-align:left}
.cmp th{background:#f3f6fa;color:#001F60}.cmp .s{font-family:monospace;font-weight:700;color:#00586F}
.mbox{background:#f2f7fb;border:1px solid #cddcee;border-radius:9px;padding:9px 15px;margin:9px 0;font-size:9.5pt;line-height:1.5}
.mbox .mh{color:#00586F;font-weight:700;font-size:10.5pt;margin-bottom:3px}
.mbox b{color:#001F60}.mbox code{font-size:.88em;background:#eef2f7;padding:0 3px;border-radius:3px}
.mbox ul{margin:2px 0 0;padding-left:18px}.mbox li{margin:2px 0}
.mbox .ins{font-size:8.7pt;color:#5f6470;background:#fffdf5;border:1px solid #ecdcbf;border-radius:6px;padding:6px 11px;margin-top:6px}.mbox .ins b{color:#001F60}
.ex{border-collapse:collapse;width:100%;font-size:8.7pt;margin:7px 0 1px}
.ex th,.ex td{border-bottom:1px solid #d5dce6;padding:3px 9px;text-align:center}
.ex th{color:#001F60;border-bottom:1.5px solid #bcd6e6;font-weight:700}
.ex td.l{text-align:left}.ex .bar{font-family:monospace;color:#00586F;font-size:10pt;letter-spacing:-1px;margin-right:5px}
.ex .cap{font-size:8pt;color:#8a8f98;text-align:left;margin:2px 0 0}
</style>

<div class="lead">세 전략은 <b>모두 같은 Vendi 공식</b>(=커널 고유값 엔트로피) · 다른 건 <b>어떤 2,000개를 앵커로 뽑느냐</b>뿐. <code>rng.choice(N, 2000, replace=False, p=?)</code>의 <b>p</b>(뽑힐 확률)만 달라진다.</div>

<table class="cmp">
<tr><th>전략</th><th>앵커 뽑는 법 (<span class="s">p</span>)</th><th>뜻</th></tr>
<tr><td><b>random</b></td><td><span class="s">p=None</span> — 10만 전체서 <b>균등</b> 무작위</td><td>현재 분포 그대로</td></tr>
<tr><td><b>dedup</b></td><td><span class="s">p ∝ 고유성 w</span> — 가중 추출</td><td>Effective N 가중치(w) 반영 분포</td></tr>
<tr><td><b>topk</b></td><td>상위 6,021개 <b>풀</b> → 그 안에서 <span class="s">균등</span></td><td>Effective N 상위 6,021개 (다양성 상한)</td></tr>
</table>

<div class="mbox">
<div class="mh">① dedup — 각 클립에 <span style="color:#001F60">w</span>를 매기고, w에 비례해 뽑는다</div>
<ul>
<li><b>w 계산</b> — 클립마다 <code>w = 1 − (상위 20이웃 평균 유사도)</code> (Effective N 값 재사용). 중복 <code>w≈0</code> · 희귀 <code>w≈1</code>.</li>
<li><b>확률화</b> — <code>p = w / Σw</code> → <b>10만 클립 각자 확률 하나</b> = 길이 10만 벡터 <code>probs</code> (합=1).</li>
<li><b>뽑기</b> — <code>rng.choice(N, 2000, replace=False, p=probs)</code> → w 큰(희귀) 클립이 대부분 뽑힘.</li>
</ul>
<table class="ex">
<tr><th>클립 예</th><th>이웃 평균 유사도</th><th>w = 1−유사도</th><th>뽑힐 확률 (막대 ∝ w)</th></tr>
<tr><td class="l">중복 클립</td><td>0.98</td><td>0.02</td><td class="l"><span class="bar">▏</span>거의 0</td></tr>
<tr><td class="l">보통 클립</td><td>0.60</td><td>0.40</td><td class="l"><span class="bar">████</span>중간</td></tr>
<tr><td class="l">희귀 클립</td><td>0.05</td><td>0.95</td><td class="l"><span class="bar">█████████▌</span>높음</td></tr>
</table>
<div class="ins">🎟 <b>직관</b>: 고유성만큼 <b>제비를 나눠주고</b> 2,000장 뽑는 셈 → 중복은 제비가 거의 없어 안 뽑힘. 삭제가 아니라 <b>확률로 눌러</b> "중복 제거된 셋에서 뽑은 것"과 동등 = <b>SoftDedup</b>.</div>
</div>

<div class="mbox">
<div class="mh">② topk — "고유성 상위 6,021개 풀"은 어떻게?</div>
<ul>
<li><b>1단계 풀 만들기</b> — 고유성 <code>w</code> <b>상위 6,021개</b>(= Effective N 개수) 클립만 골라 <b>고정 풀</b>로 추출 → "실질적으로 독립인 클립"만 모은 집합.</li>
<li><b>2단계 뽑기</b> — 그 풀(6,021) 안에서 <b>균등 무작위 2,000개</b> (<code>p=None</code>).</li>
</ul>
<div class="ins">🏔 <b>직관</b>: 가장 고유한 클립만 남긴 <b>정예 집합</b>에서 잰 다양성 → "이상적으로 중복을 다 걷어냈을 때 도달 가능한 <b>상한</b>". 그래서 topk(4.75) > dedup(3.64) > random(3.53).</div>
</div>

---

## 부록 B · 밀도 & LID — 계산 방법과 타당성

<style scoped>
.lead{font-size:10pt;color:#3a3f47;margin:3px 0 8px}.lead b{color:#001F60}
.mbox{background:#f2f7fb;border:1px solid #cddcee;border-radius:9px;padding:8px 14px;margin:8px 0;font-size:9.3pt;line-height:1.5}
.mbox .mh{color:#00586F;font-weight:700;font-size:10.5pt;margin-bottom:2px}
.mbox b{color:#001F60}.mbox code{font-size:.86em;background:#eef2f7;padding:0 3px;border-radius:3px}
.mbox ul{margin:2px 0 0;padding-left:17px}.mbox li{margin:1.5px 0}
.cols{display:flex;gap:14px}.cols>div{flex:1}
.verdict{border-collapse:collapse;width:100%;font-size:9pt;margin:8px 0 0}
.verdict th,.verdict td{border:1px solid #d5dce6;padding:4px 10px;text-align:left}
.verdict th{background:#f3f6fa;color:#001F60}
.verdict .ok{color:#1a7f5a;font-weight:700}.verdict .warn{color:#c8871a;font-weight:700}
.flag{font-size:8.7pt;color:#7a6420;background:#fbf6ec;border:1px solid #ecdcbf;border-radius:6px;padding:7px 11px;margin-top:8px}.flag b{color:#001F60}
</style>

<div class="lead"><b>밀도·LID는 클립마다 하나씩</b> 계산(각각 <b>길이 10만 벡터</b>, 클립당 값 1개) → 사분면 딱지도 클립별. 두 축 모두 <b>표준·피어리뷰 방법</b> · 임계값도 <b>데이터 주도(GMM+BIC)</b> — 방법은 견고, 단 <b>초고밀도</b>가 LID를 흔든다.</div>

<div class="cols">
<div class="mbox">
<div class="mh">밀도(density) — kNN 커널밀도 프록시</div>
<ul>
<li><code>density = knn_sim[:, :10].mean()</code> = 가장 가까운 <b>10개 이웃과의 평균 코사인 유사도</b>.</li>
<li>높음 = 이웃이 바짝 붙음 = <b>붐빔</b>. "반경 안 밀집도"를 "이웃이 얼마나 가깝나"로 잰 <b>표준 KDE 프록시</b>.</li>
</ul>
</div>
<div class="mbox">
<div class="mh">LID — Ma et al. (ICLR'18) MLE</div>
<ul>
<li><code>LID = −1 / mean(log(r_j / r_max))</code>, 이웃 20개 거리로 추정.</li>
<li>이웃 거리가 <b>고르면 → LID↑</b>(다양·고차원) · <b>퍼지면 → LID↓</b>(단조). 극값이론 기반 정식 추정량.</li>
</ul>
</div>
</div>

<table class="verdict">
<tr><th>축</th><th>방법 타당성</th><th>이 데이터에서 신뢰</th></tr>
<tr><td><b>밀도</b></td><td class="ok">높음 — 표준 KDE 프록시, 단조·견고</td><td class="ok">비교적 신뢰 가능</td></tr>
<tr><td><b>LID</b></td><td class="ok">높음 — 학술 검증된 MLE</td><td class="warn">주의 — 초고밀도로 동적 범위 소실</td></tr>
</table>

<div class="flag">⚠️ <b>핵심 맹점</b> — 이웃 거리가 0.05~0.07로 <b>거의 균일</b> → <code>r_j/r_max ≈ 1</code> → LID 추정량이 <b>수치 발산</b>(→200 클리핑, FLIPD 발산과 동근원). <b><code>lid_reliable=100%</code>는 이걸 못 잡는다</b> — 그 플래그는 "희소·고립"(r_max 큼)만 거를 뿐, "거리 범위가 좁아 불안정"은 통과. &nbsp;+ 모든 축이 <b>캡션 임베딩(bge-m3) 프록시</b>(ODD 정렬 ρ≈0.2, 부분). &nbsp;→ <b>실무: 밀도 축 &gt; LID 축, LID 기반 Q2/Q3·FLIPD 승격은 보수적으로.</b></div>

---

## 부록 C · η²(실증④) — ODD가 같으면 화면도 같을까

<style scoped>
.lead{font-size:10pt;color:#3a3f47;margin:3px 0 8px}.lead b{color:#001F60}
.mbox{background:#f2f7fb;border:1px solid #cddcee;border-radius:9px;padding:8px 14px;margin:8px 0;font-size:9.2pt;line-height:1.5}
.mbox .mh{color:#00586F;font-weight:700;font-size:10.3pt;margin-bottom:2px}
.mbox b{color:#001F60}.mbox code{font-size:.86em;background:#eef2f7;padding:0 3px;border-radius:3px}
.mbox ul{margin:2px 0 0;padding-left:17px}.mbox li{margin:1.5px 0}
.cols{display:flex;gap:14px}.cols>div{flex:1}
.res{border-collapse:collapse;width:100%;font-size:9pt;margin:2px 0 0}
.res th,.res td{border:1px solid #d5dce6;padding:4px 10px;text-align:left}
.res th{background:#f3f6fa;color:#001F60}.res .n{font-family:monospace;font-weight:700;color:#00586F}.res .ok{color:#1a7f5a}
.flag{font-size:8.7pt;color:#7a6420;background:#fbf6ec;border:1px solid #ecdcbf;border-radius:6px;padding:7px 11px;margin-top:8px}.flag b{color:#001F60}
</style>

<div class="lead">질문: <b>ODD 조합(11필드)이 같은 클립들은, 실제로 서로 비슷하게 보일까?</b> &nbsp;답부터: <b style="color:#00586F">거의 아니다</b> — ODD로 설명되는 화면 다양성은 <b>~20%뿐</b>, 나머지 80%는 조합이 같아도 딴판이다. 이 설명력을 통계의 <b>η²(설명된 분산 비율)</b>로 재고, <b>우연히 부풀려진 값이 아님</b>까지 검증했다.</div>

<div class="cols">
<div class="mbox">
<div class="mh">① η²란? — "조합별로 나눠 담고, 조합만으로 얼마나 설명되나"</div>
<ul>
<li>클립마다 <b>ODD 조합</b>이 하나씩(예: 맑음×주간×고속도로) → 10만 클립을 <b>2,070개 조합</b>으로 나눠 담는다.</li>
<li>만약 ODD가 화면을 <b>완전히</b> 결정한다면 → 같은 조합 클립의 임베딩이 한 점에 겹치고(서로 <b>코사인 ≈ 1</b> → 조합 <b>안</b> 분산 = 0), 모든 다양성은 <b>조합끼리</b> 차이에서만 나온다.</li>
<li><b>전체 다양성 ＝ (조합끼리 벌어짐) ＋ (조합 안 흩어짐)</b>으로 놓고, 그중 <b>"조합끼리 벌어짐"의 몫이 전체 다양성을 얼마나 표현하나(η²)</b>를 측정.</li>
<li><b>계산 — 조합끼리 벌어짐</b>: 조합마다 평균점을 구해 <b>(조합 평균 − 전체 평균)²</b>을 조합 크기만큼 가중 합산. <b>조합 안 흩어짐</b>: 각 클립과 <b>제 조합 평균 사이 거리²</b>의 총합. (거리 = 임베딩 코사인)</li>
</ul>
</div>
<div class="mbox">
<div class="mh">② 왜 섞어서 다시 재나 — "작은 조합의 착시" 걷어내기</div>
<ul>
<li>조합 2,070개 중 상당수가 <b>클립 1개짜리</b>. 1개짜리 조합은 "안 차이"가 자동 0 → 잘게 쪼갤수록 <b>의미 없이 η²가 부풀어</b> 오른다.</li>
<li>그래서 ODD 라벨을 <b>무작위로 뒤섞어</b>(조합 크기는 그대로, 의미만 제거) η²를 다시 잰다 = <b>"우연이면 이만큼"인 바닥값(귀무)</b>.</li>
<li>바닥값이 <b>2.1%</b>뿐 → 관측 21%의 <b>거의 전부가 진짜 신호</b>. 보정 η² = (관측−귀무)/(1−귀무).</li>
<li>확인사살: 1개짜리 조합 다 빼고 <b>50개 이상 조합(169개)</b>만으로 재계산 → 값 안 흔들림.</li>
</ul>
</div>
</div>

<div class="cols">
<div style="flex:1.05">
<table class="res">
<tr><th>지표</th><th>값</th><th>의미</th></tr>
<tr><td>η² 관측</td><td class="n">21.3%</td><td>ODD 셀이 설명하는 임베딩 분산</td></tr>
<tr><td>η² 순열귀무</td><td class="n">2.1%</td><td>무의미 그룹의 우연 바닥값 <span class="ok">(인플레 작음 ✓)</span></td></tr>
<tr><td>η² 보정</td><td class="n">19.6%</td><td>우연 제거 후 ODD 순수 기여</td></tr>
<tr><td>η² (≥50클립 169셀)</td><td class="n">18.7%</td><td>싱글톤 빼도 일관 <span class="ok">✓</span></td></tr>
</table>
<div style="font-size:8.8pt;color:#5f6470;margin-top:5px">세 방식(21%·20%·19%)이 <b style="color:#001F60">~20% 근처로 일치</b> → 우연·싱글톤 아티팩트가 아닌 <b style="color:#001F60">견고한 실제 신호</b>. → <b style="color:#001F60">ODD는 임베딩 분산의 ~20%만 설명, ~80%가 ODD 밖.</b></div>
</div>
<div class="mbox" style="flex:0.95">
<div class="mh">해석 — 두 포인트</div>
<ul>
<li><b>(A) 조합 안에 80%가 남는다 = 상호보완의 정량 증거.</b> 날씨·조명·노면이 같아도 화면 다양성의 80%가 흩어짐 → 임베딩은 ODD엔 <b>없는 다른 축</b>(장면 내용·가려짐·모호한 교차로)을 추가로 본다.</li>
<li><b>(B) 앞 장(실증①)을 스스로 교정.</b> 거기서 본 "90% 잔존"은 하필 <b>정상조건 셀 하나</b>만 본 편향치. 전체를 엄밀히 재면 <b>80% 밖(90% 아님)</b>.</li>
</ul>
</div>
</div>

<div class="flag">⚠️ <b>발표 방어선</b> — 결과의 신뢰도는 <b>귀무 2.1%가 낮다</b>는 데 달림. 귀무가 15~20%였다면 "관측 20%"는 싱글톤 아티팩트로 무너짐. 2.1%라 관측 20%의 <b>대부분이 진짜 ODD 신호</b>임이 보장됨. &nbsp;코드: <code>analysis_two_lens.py :: analysis4_eta_squared</code>.</div>
