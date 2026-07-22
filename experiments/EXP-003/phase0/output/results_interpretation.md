# Phase 0 Results Interpretation
**실행일**: 2026-07-08 | **데이터**: 100,398 clips | **출력 경로**: `experiments/EXP-003/phase0/output/`

---

## 1. 핵심 진단 — 데이터셋 성격

> **결론: 100,398개 클립이지만 실질적으로는 6,021개 분량의 정보만 담긴 극도로 중복적인 데이터셋**

| 지표 | 값 | 의미 |
|------|-----|------|
| Effective N (soft) | **6,021** (6.0%) | 실질 독립 클립 수 — 나머지 94.0%는 이미 있는 정보의 반복 |
| Vendi random | **3.530** ± 0.017 | 현재 분포 그대로 — 3~4개 의미 차원만 커버 |
| Vendi dedup | **3.636** ± 0.020 | 중복 제거 후 분포 — 억압 계수 1.030 (3.0% 향상에 그침) |
| Vendi topk | **4.745** ± 0.022 | 상위 Effective N 풀(6,022개) 상한 — 이상적 dedup 후 최대 기대치 |
| 상위 10이웃 유사도 중앙값 | **0.9446** | 모든 클립이 서로 94% 수준으로 유사 |
| Q1 PRUNE | **60.5%** | 과반이 "밀집+단조" — 중복 제거 대상 |
| healthy_scenarios | **0개** | 12개 시나리오 중 Q0 지배 시나리오 없음 |
| ODD 고유 조합 (전체) | **507 / 7,560 (6.7%)** | 7개 ODD 차원 조합 커버리지 — 17k 추가에도 조합 패턴 변화 미미 |
| ODD effective N (전체) | **37.5** | 507개 조합 중 실질 37개 수준만 고르게 분포 |
| ODD effective N (topk) | **40.8** | 고유성 상위 6,022개 기준 실질 ODD 조합 수 |
| ODD mean_norm_entropy (전체) | **0.412** | 전체 클립 기준 ODD 다양성 |
| ODD mean_norm_entropy (topk) | **0.430** | 고유성 상위 클립이 ODD 관점에서도 더 다양 |
| ODD 임베딩 정렬 (쌍별 Spearman) | **ρ=0.221 (partial)** | 임베딩 거리 ↔ ODD 거리 약한 정렬 |
| Vendi-ODD run 정렬 (n=30) | **ρ≈0.22 / 0.20 / 0.00** | random/dedup: 약한 양의 정렬 (통계적 미유의) — topk: 무상관 |

---

## 2. ODD 커버리지 분석 (Step 0-F)

**실행 기준**: 100,398 clips (caption_v3/odd 전체) | 분석 필드: odd_final 19개 + odd_compat 9개 + **odd_compat_v2 11개 (AV 성능 기준)**

---

### 2-1. 커버리지 요약

| 분석 단위 | 관측 조합 | 이론 조합 | 커버율 | 클린 커버율 (unknown 제외) |
|----------|---------|---------|------|--------------------------|
| odd_final (19 필드) | **7,240** | 238,878,720,000 | 0.0000% | 6,460 / 806,215,680 (0.0008%) |
| odd_compat (9 필드) | **1,384** | 614,400 | **0.23%** | 1,317 / 58,320 (**2.26%**) |
| **odd_compat_v2 (11 필드, AV 성능 기준)** | **2,070** | 15,360,000 | **0.013%** | 1,562 / 933,120 (**0.167%**) |

#### odd_compat_v2 관측 조합 2,070 도출 방법

**① 클립 → 11개 값의 튜플 변환**

100,398개 클립 각각을 `_to_compat_v2()`로 11개 필드 값의 튜플 1개로 변환.

```
클립 #1 → (urban, clear, well_lit, cars_only, sparse, post_junction, dry, low, good, none, clear)
클립 #2 → (urban, clear, well_lit, cars_only, sparse, post_junction, dry, low, good, none, clear)  ← 동일
클립 #3 → (rural, rain,  moderate, cars_only, moderate, none,         wet, low, good, none, clear)
...  (100,398개)
```

**② 중복 제거 → 고유 조합 수**

100,398개 튜플에서 완전히 동일한 것끼리 묶으면 **2,070개 고유 조합**.

| 구분 | 수 |
|------|--:|
| 입력 튜플 (클립 수) | 100,398 |
| 고유 튜플 = **관측 조합** | **2,070** |
| — 싱글톤 (1번만 등장) | 897 |
| — 반복 (2번 이상 등장) | 1,173 |

최빈 조합(urban + clear + well_lit + cars_only + sparse + post_junction + dry + low + good + none + clear)은 **6,578개** 클립이 동일 튜플.

**③ 이론 조합 수 = 각 필드 허용 값 수의 곱**

| 필드 | 허용 값 수 |
|------|:--------:|
| `road_type` | 5 |
| `weather` | 5 |
| `lighting` | 4 |
| `agent_type` | 6 |
| `traffic_density` | 4 |
| `junction_proximity` | 5 |
| `road_surface` | 4 |
| `occlusion_level` | 4 |
| `visibility_range` | 4 |
| `special_event` | 5 |
| `lane_marking_quality` | 4 |
| **곱** | **5×5×4×6×4×5×4×4×4×5×4 = 15,360,000** |

**④ 커버율**

```
관측 2,070 / 이론 15,360,000 = 0.013%
클린 커버율 (unknown 포함 조합 제외): 1,562 / 933,120 = 0.167%
```

> 15,360,000가지 조합이 이론상 존재하는데, 실제 데이터에서는 **2,070가지 패턴만 등장** — 나머지 99.987%의 조합은 한 건도 없음. 이것이 Gap-3(ODD 커버리지 저조)의 정량적 근거.

---

### 2-2. 중복 집중도 (odd_compat_v2 기준)

- **상위 100개 조합이 전체 86,372클립(86.0%) 차지**
- 싱글톤 조합(1회만 등장): 897개 — 전체 2,070개 조합의 43.3%
- 반복 조합(2회 이상): 1,173개가 나머지 99,501클립(99.1%)을 독점

| 구분 | 조합 수 | 클립 수 | 평균 클립/조합 |
|------|---------|---------|--------------|
| 싱글톤 (1회) | 897 | 897 | 1.0 |
| 반복 (2회+) | 1,173 | 99,501 | **84.8** |
| 상위 100 | 100 | 86,372 | **863.7** |

> odd_final 기준 참고: 싱글톤 3,741개 / 반복 3,499개(96,657클립) / 상위 100 → 51,727클립(51.5%)

#### 중복 상위 20개 튜플 구성

상위 20개 튜플 전체에서 4개 필드가 단일 값으로 고정:
`weather=clear` / `agent_type=cars_only` / `occlusion_level=low` / `special_event=none`

아래 표는 변동 7개 필드만 표기.

| 순위 | 클립 수 | 비율 | `road_type` | `lighting` | `traffic_density` | `junction_proximity` | `road_surface` | `visibility_range` | `lane_marking_quality` |
|:---:|-------:|:---:|------------|-----------|:----------------:|---------------------|:-------------:|:-----------------:|:--------------------:|
| 1 | **6,578** | 6.55% | urban | well_lit | sparse | post_junction | dry | good | clear |
| 2 | **5,935** | 5.91% | rural | well_lit | sparse | none | dry | good | clear |
| 3 | **5,217** | 5.20% | rural | moderate | sparse | none | dry | good | clear |
| 4 | **4,878** | 4.86% | rural | well_lit | sparse | post_junction | dry | good | clear |
| 5 | **4,185** | 4.17% | rural | moderate | sparse | post_junction | dry | good | clear |
| 6 | **3,955** | 3.94% | urban | moderate | sparse | post_junction | dry | good | clear |
| 7 | **3,914** | 3.90% | urban | well_lit | moderate | post_junction | dry | good | clear |
| 8 | **2,489** | 2.48% | highway | well_lit | sparse | none | dry | good | clear |
| 9 | **2,436** | 2.43% | urban | well_lit | moderate | in_junction | dry | good | clear |
| 10 | **2,306** | 2.30% | urban | moderate | moderate | post_junction | dry | good | clear |
| 11 | **2,288** | 2.28% | highway | well_lit | moderate | none | dry | good | clear |
| 12 | **2,245** | 2.24% | urban | well_lit | moderate | approaching | dry | good | clear |
| 13 | **2,165** | 2.16% | highway | moderate | sparse | none | dry | good | clear |
| 14 | **1,970** | 1.96% | rural | moderate | sparse | none | **wet** | good | clear |
| 15 | **1,769** | 1.76% | rural | poorly_lit | sparse | none | dry | **poor** | clear |
| 16 | **1,675** | 1.67% | rural | poorly_lit | sparse | none | dry | good | clear |
| 17 | **1,551** | 1.54% | urban | moderate | moderate | approaching | dry | good | clear |
| 18 | **1,530** | 1.52% | urban | well_lit | sparse | in_junction | dry | good | clear |
| 19 | **1,503** | 1.50% | highway | moderate | moderate | none | dry | good | clear |
| 20 | **1,401** | 1.40% | urban | well_lit | sparse | approaching | dry | good | clear |

> **고정 값**: `weather=clear` · `agent_type=cars_only` · `occlusion_level=low` · `special_event=none` — 상위 20개 전체 공통
>
> **패턴 요약**: 상위 20개 튜플은 모두 맑은 날씨·차량만·저폐색·이벤트 없음의 "정상 조건" 고정. 도로 유형(urban/rural/highway)·조명(well_lit/moderate)·교통 밀도(sparse/moderate)·교차로 근접(none/post_junction/in_junction/approaching)의 4개 차원만 조합되어 순위가 결정됨. 14위(wet)와 15위(poor visibility)가 처음으로 비정상 조건을 포함.

---

### 2-3. 필드별 값 분포 및 편향 (odd_compat_v2 기준)

| 필드 | 분포 요약 | 편향 진단 |
|------|----------|----------|
| `road_type` | urban=44,042 / rural=40,039 / highway=15,581 / national_road=242 | national_road 극소 (0.2%) |
| `weather` | clear=**92,314** / rain=5,215 / snow=1,600 / **fog=1,263** | 맑음 91.9% 독점. fog가 독립 값으로 분리되어 이전 compat의 1,263건 누락 해소 |
| `lighting` | moderate=44,177 / well_lit=42,404 / poorly_lit=13,817 | 야간(poorly_lit) 13.8% |
| `agent_type` | cars_only=97,402 / mixed=2,612 / pedestrians=268 / cyclists=97 | 차량만 97.0%, VRU 극소 |
| `traffic_density` | sparse=71,665 / moderate=26,546 / dense=2,183 | dense 2.2% |
| `junction_proximity` | none=40,066 / post_junction=38,504 / approaching=11,344 / in_junction=9,122 | post_junction+in_junction 합산 47.6% — 교차로 관련 클립 절반에 육박 |
| `road_surface` | dry=79,849 / wet=19,051 / **snow=1,360** | 습윤·설면 합산 20.4%. snow가 별도 값으로 정규화 |
| `occlusion_level` | low=99,467 / medium=807 / high=123 | **99.1%가 low** — 고폐색 시나리오 거의 전무 |
| `visibility_range` | good=86,269 / moderate=9,362 / poor=4,767 | poor 4.7% — 수집은 되었으나 극소 |
| `special_event` | none=100,361 / obstacle=34 | **accident·emergency 0건** — 안전 크리티컬 시나리오 전무 |
| `lane_marking_quality` | clear=95,109 / faint=3,965 / absent=252 | 94.7%가 clear — 차선 불량 시나리오 극소 |

---

### 2-4. 미관측 스키마 값 (전혀 등장하지 않는 값)

| 필드 | 미관측 값 | 의미 |
|------|----------|------|
| `special_event` | `accident`, `emergency` | 사고·긴급 상황 클립이 데이터에 **전무** |

> `special_event`의 `obstacle`은 관측됨. `accident`와 `emergency`는 100,398클립 전체에서 단 한 건도 없음.

---

### 2-5. 수집 우선순위 (ODD 커버리지 관점)

아래는 현재 데이터에서 **관측 비율이 극히 낮거나 전무한 ODD 조합**으로, 데이터 수집 시 우선 타깃.
필드 출처: odd_compat_v2 기준 (★표 항목은 odd_final 전용 필드)

| 우선순위 | 타깃 조건 | 현재 클립 수 | 비고 |
|---------|----------|----------:|------|
| 🔴 최우선 | `special_event=accident` or `emergency` | **0** | 안전 크리티컬 — 전체 데이터에 단 1건도 없음 |
| 🔴 최우선 | `occlusion_level=high` | **123** | 고폐색 = 지각 모델 직접 실패 구간. 상위 100 조합 전체에서 부재 |
| 🔴 최우선 | `traffic_density=dense` + `weather=rain/snow` | **~148** | 혼잡+악천후 복합 (독립 분포 기반 추정) |
| 🔴 최우선 | `scene_ambiguity=high` ★ | **120** | 판단 난이도 최고 케이스 (odd_final 기준) |
| 🟠 높음 | `agent_type=cyclists` or `pedestrians` | **97 / 268** | 취약 도로 이용자 — VRU 예측 학습 데이터 극소 |
| 🟠 높음 | `lane_marking_quality=absent` | **252** | 차선 탐지 모델 완전 실패 구간 |
| 🟠 높음 | `weather=snow` | **1,600** | 동절기 시나리오 극소 |
| 🟠 높음 | `weather=fog` | **1,263** | 안개 시나리오 — 이전 compat에서 누락, v2에서 독립 추적 |
| 🟠 높음 | `road_type=national_road` | **242** | 거의 미수집 |
| 🟡 중간 | `road_surface=wet` + `traffic_density=dense` | **~414** | 습노면 고밀도 (독립 분포 기반 추정) |
| 🟡 중간 | `lane_marking_quality=faint` | **3,965** | 차선 탐지 저하 구간 — 수는 있으나 clear 대비 4.2% |
| 🟡 중간 | `visibility_range=poor` | **4,767** | 유효 센서 범위 축소 — 계획 수평선 단축 |
| 🟡 중간 | `occlusion_level=medium` | **807** | 부분 폐색 — 객체 탐지 오류율 증가 구간 |
| 🟡 중간 | `scene_ambiguity=medium` ★ | **468** | 경계 케이스 (odd_final 기준) |

> ★ `scene_ambiguity`는 odd_compat_v2에서 제거된 필드(다른 필드들의 파생 지표로 판단). 수집 우선순위 판단 시에는 여전히 odd_final 기준으로 참고 가능.

> #### 표 작성 근거
>
> **① 현재 클립 수 열 — 실측치 기반**
>
> `step_a_odd_coverage.py`로 100,398 클립 전체를 odd_compat_v2 기준 집계한 **실측치**. 단, `~` 표기 항목은 각 필드의 독립 분포를 가정한 **추정치**:
> - `dense+rain/snow ~148`: `traffic_density=dense`(2,183) × `weather=rain/snow` 비율(6.8%)
> - `wet+dense ~414`: `road_surface=wet`(19,051) × `traffic_density=dense` 비율(2.2%)
>
> **② 🔴/🟠/🟡 우선순위 등급 — 정량 + 정성의 결합 (코드 자동판정 아님)**
>
> 각 등급은 두 축을 결합해 연구자가 부여한다:
> - **[정량] 코드로 검증 가능**: ① 관측 클립 수(`step_a_odd_coverage.py` 실측) · ② 상위 100 조합 부재(`analyze_top100_combos.py` — top 100 완전 고정 필드가 `occlusion_level=low`·`special_event=none`뿐 → `high`·`accident`·`emergency`는 top 100 전무가 직접 확인됨).
> - **[정성] 도메인 판단 (코드 metric 없음)**: 안전 크리티컬 · 지각·예측 모델 실패 유발 · 취약 케이스 · 성능 저하 등 **심각도 서술 전부**. 데이터에 safety-critical 플래그가 없으며, "무엇이 지각·예측·계획 실패를 거쳐 사고로 이어지는가"에 대한 AV 도메인 해석에 기반(자동 판정 아님).
>
> **등급 부여**:
> - 🔴 **최우선** = **[정성]** 안전 크리티컬(사고·고폐색·복합 악조건) **+ [정량]** 상위 100(86%)에서조차 전무.
> - 🟠 **높음** = **[정성]** 지각·예측 모델 실패 취약 **+ [정량]** 관측 극소(수백~수천).
> - 🟡 **중간** = **[정성]** 성능 저하 **+ [정량]** 관측 상대적 존재.
>
> ※ **등급은 관측 수로 정하지 않는다** — 관측 수로 정한다면 🟠(높음)이 항상 🟡(중간)보다 적어야 하지만, 실제로는 **🟠 `snow`(1,600) · `fog`(1,263)가 🟡 `occlusion=medium`(807) · `wet+dense`(414)보다 데이터가 더 많은데도 더 높은 등급**을 받는다. 즉 관측 수(정량)만으로는 두 등급을 가를 수 없고, 실제로 등급을 결정하는 것은 **심각도(정성 판단)** ("완전 실패 vs 저하", "안전 등급 급변 vs 오류율 증가")이다. 재현성이 필요하면 심각도 규칙(안전 크리티컬·모델 실패 유발 값 집합 등)을 `config.py`에 명시 정의해 규칙화할 수 있다.
>
> ⚠️ **주의 — 다른 분석과 혼동 금지**: `config.py`의 `GAP_RATIO_HIGH_PRIORITY=0.4` · `ODD_HIGH_PRIORITY_THRESHOLD=22.0` · `VENDI_SUPPRESSION_HIGH=2.0`은 **이 표(ODD 값 단위 우선순위)의 기준이 아니다.** 이들은 `step_f2_gap.py`가 **시나리오 단위** 갭 분석에서 `COLLECT_HIGH_PRIORITY`로 자동 승격할지 판정하는 임계값(입력: `gap_in_scenario_ratio`·`odd_effective_n`·`vendi_suppression_ratio`)으로, **§5(갭 슬라이스 — 수집/합성 우선순위)** 에 해당한다.
>
> **③ 비고 열 설명 — AV 도메인 지식 기반 해석 (자동 판단 아님)**
>
> 각 조건이 AV 시스템에 미치는 영향을 연구자가 해석하여 기술. 근거가 되는 업계 통용 사실:
> - `occlusion_level=high` → 객체 탐지 모델 직접 실패 구간 (LiDAR·카메라 입력 품질 저하)
> - `agent_type=cyclists/pedestrians` → 예측 모델의 안전 등급 급변 (VRU = Vulnerable Road User)
> - `special_event=accident/emergency` → 전체 학습 데이터에 0건 = 해당 상황 대응 모델 학습 불가
> - `lane_marking_quality=absent` → 차선 탐지 모델 완전 실패로 계획 모듈 입력 붕괴

---

### 2-6. odd_compat_v2 (AV 성능 11개 필드) — 스키마 정의 및 top 100 분석

> **분석 스크립트**: `experiments/EXP-003/phase0/analyze_top100_combos.py odd_compat_v2`

odd_compat(9개)의 도로 구조 중심 필드를 AV 지각·예측·계획 난이도 기준으로 재설계한 스키마.

#### 2-6-0. 스키마 정의 (필드 구성 및 선택 근거)

| AV 축 | 필드 | 허용 값 | odd_final 원천 | 현재 분포 (클립 수) | 선택/변경 이유 |
|:-----:|------|---------|--------------|-------------------|--------------|
| 지각 | `weather` | `clear` / `rain` / `snow` / `fog` / `unknown` | `precipitation` + `fog` 병합 | clear=92,314 / rain=5,215 / snow=1,600 / fog=1,263 | 비·눈·안개를 단일 센서저하 지표로 통합. **fog를 별도 값으로 분리** |
| 지각 | `lighting` | `well_lit` / `moderate` / `poorly_lit` / `unknown` | `lighting_condition` | well_lit=42,404 / moderate=44,177 / poorly_lit=13,817 | 카메라 성능 직결. 유지 |
| 지각 | `occlusion_level` | `low` / `medium` / `high` / `unknown` | `occlusion_level` | low=99,467 / medium=807 / high=123 | **신규 추가** — 객체 탐지 품질 직접 지표 |
| 지각 | `lane_marking_quality` | `clear` / `faint` / `absent` / `unknown` | `lane_marking_quality` | clear=95,109 / faint=3,965 / absent=252 | **신규 추가** — 차선 탐지 모델 실패 원인 직결 |
| 예측 | `agent_type` | `cars_only` / `mixed` / `pedestrians` / `cyclists` / `emergency` / `unknown` | `road_user_types` | cars_only=97,402 / mixed=2,612 / pedestrians=268 / cyclists=97 | VRU 존재 = 안전 등급 급변. 유지 |
| 예측 | `traffic_density` | `sparse` / `moderate` / `dense` / `unknown` | `traffic_density` | sparse=71,665 / moderate=26,546 / dense=2,183 | 다중 에이전트 복잡도. 유지 |
| 예측·계획 | `junction_proximity` | `none` / `approaching` / `in_junction` / `post_junction` / `unknown` | `junction_proximity` | none=40,066 / approaching=11,344 / in_junction=9,122 / post_junction=38,504 | **신규 추가** — 교차로 근접은 행동 전략 분기 지점, AV 사고 다발 구간 |
| 계획 | `road_type` | `highway` / `national_road` / `urban` / `rural` / `unknown` | `road_type` | highway=15,581 / national_road=242 / urban=44,042 / rural=40,039 | 시나리오 맥락 정의. 유지 |
| 계획 | `road_surface` | `dry` / `wet` / `snow` / `unknown` | `road_surface` (정규화) | dry=79,849 / wet=19,051 / snow=1,360 | **신규 추가** — 제동·조향 동역학 핵심. snow/snow-dusted → snow 정규화 |
| 계획 | `visibility_range` | `good` / `moderate` / `poor` / `unknown` | `visibility_range` | good=86,269 / moderate=9,362 / poor=4,767 | **신규 추가** — 유효 센서 범위 = 안전 정지 거리 확보 가능 여부 |
| 계획 | `special_event` | `none` / `accident` / `obstacle` / `emergency` / `unknown` | `special_event` | none=100,361 / obstacle=34 / **accident·emergency=0** | **신규 추가** — 사고·장애물 = 안전 크리티컬 롱테일 (현재 0건) |
| — | ~~`lanes_ego_direction`~~ | — | — | — | **제거** — road_type과 높은 상관, AV 행동 분기 기여 낮음 |
| — | ~~`lanes_opposite`~~ | — | — | — | **제거** — road_type/divider로 대부분 추론 가능 |
| — | ~~`road_divider`~~ | — | — | — | **제거** — AV 성능 분기 영향 낮음 |
| — | ~~`scene_ambiguity`~~ | — | — | — | **제거** — 나머지 필드들의 결과물에 가까운 파생 지표 |

> **이론 조합 수**: 5×5×4×6×4×5×4×4×4×5×4 = **15,360,000**

#### 2-6-1. weather 필드 병합 규칙

```
precipitation=rain  → weather=rain
precipitation=snow  → weather=snow
fog=present         → weather=fog   (precipitation과 독립)
precipitation=none AND fog=none → weather=clear
그 외              → weather=unknown
```

#### 2-6-2. road_surface 정규화 규칙

```
dry              → dry
wet              → wet
snow, snow-dusted → snow
uneven, dirt, unpaved, gravel, dusty, sandy (76건) → unknown
```

#### 2-6-3. 이론 조합 수 비교

| 스키마 | 필드 수 | 이론 조합 | 관측 조합 | 클린 커버율 |
|--------|:------:|--------:|--------:|----------:|
| odd_compat | 9 | 614,400 | 1,384 | 2.26% |
| **odd_compat_v2** | **11** | **15,360,000** | **2,070** | **0.167%** |

#### 2-6-4. top 100 조합 필드별 구성 (odd_compat_v2 기준)

top 100 조합이 86,372클립(86.0%) 차지.

**완전 고정 필드**: odd_compat에서 9개 → v2에서 **2개**로 감소 — 스키마 교체 효과

| 고정 필드 | 값 | 의미 |
|----------|---|------|
| `occlusion_level` | `low` | 고폐색 시나리오 상위 100 부재 |
| `special_event` | `none` | 사고·장애물 시나리오 상위 100 부재 (전체 데이터도 0건) |

**변동 필드 9개 세부 분포**:

| 필드 | 값 | 조합 수 | 조합 비율 | 클립 수 | 클립 비율 |
|------|---|------:|--------:|-------:|--------:|
| `road_type` | `urban` | 46 | 46% | 38,686 | 44.8% |
| `road_type` | `rural` | 38 | 38% | 34,596 | 40.1% |
| `road_type` | `highway` | 16 | 16% | 13,090 | 15.2% |
| `weather` | `clear` | 87 | 87% | 83,984 | 97.2% |
| `weather` | `rain` | 10 | 10% | 1,954 | 2.3% |
| `weather` | `fog` | 2 | 2% | 321 | 0.4% |
| `weather` | `snow` | 1 | 1% | 113 | 0.1% |
| `lighting` | `moderate` | 52 | 52% | 37,165 | 43.0% |
| `lighting` | `well_lit` | 30 | 30% | 39,483 | 45.7% |
| `lighting` | `poorly_lit` | 18 | 18% | 9,724 | 11.3% |
| `agent_type` | `cars_only` | 92 | 92% | 84,718 | 98.1% |
| `agent_type` | `mixed` | 8 | 8% | 1,654 | 1.9% |
| `traffic_density` | `sparse` | 60 | 60% | 61,818 | 71.6% |
| `traffic_density` | `moderate` | 32 | 32% | 23,212 | 26.9% |
| `traffic_density` | `dense` | 8 | 8% | 1,342 | 1.6% |
| `junction_proximity` | `none` | 38 | 38% | 34,368 | 39.8% |
| `junction_proximity` | `post_junction` | 33 | 33% | 35,059 | 40.6% |
| `junction_proximity` | `approaching` | 16 | 16% | 9,087 | 10.5% |
| `junction_proximity` | `in_junction` | 11 | 11% | 7,614 | 8.8% |
| `junction_proximity` | `unknown` | 2 | 2% | 244 | 0.3% |
| `road_surface` | `dry` | 63 | 63% | 74,714 | 86.5% |
| `road_surface` | `wet` | 35 | 35% | 11,276 | 13.1% |
| `road_surface` | `snow` | 2 | 2% | 382 | 0.4% |
| `visibility_range` | `good` | 80 | 80% | 79,581 | 92.1% |
| `visibility_range` | `moderate` | 13 | 13% | 3,513 | 4.1% |
| `visibility_range` | `poor` | 7 | 7% | 3,278 | 3.8% |
| `lane_marking_quality` | `clear` | 96 | 96% | 85,847 | 99.4% |
| `lane_marking_quality` | `faint` | 4 | 4% | 525 | 0.6% |

> **핵심 해석**: odd_compat v2로 전환 시 고정 필드가 9개 → 2개로 감소. 기존 compat에서 고착되어 있던 날씨·에이전트·교차로·노면 정보가 실제로 조합을 분기시키는 유효 차원으로 작동함을 확인. `special_event`와 `occlusion_level`이 여전히 고정(`none`/`low`)인 것은 데이터 수집 우선순위 1순위를 재확인.

---

## 3. 데이터 품질 분석

> Effective N · Vendi Score · LID · Action Map 기반 임베딩/밀도 관점 분석.

---

### 3-1. Effective N (Soft) 계산 방법

**목적 — 무엇을 알아내려는가**
"10만 클립이 실질적으로 서로 다른 정보 **몇 개 분량**인가"를 정량화한다. 클립 수가 많아도 중복이 많으면 실질 정보량은 적으므로, 이 값으로 ① 데이터셋의 **유효 크기**(중복 제거 후 독립 표본 수)를 추정하고 ② **pruning 여지**(얼마나 버려도 정보 손실이 없는가)를 가늠한다.

- **Soft의 목적**: 유사도를 *연속값*으로 감점 — 유사도 0.94인 이웃도 "부분 중복"으로 취급(정보 6%만 인정). **부드러운 중복까지** 잡아 실질 정보량을 보수적으로 추정.
- **Hard의 목적**: `sim > 0.95`인 이웃만 *이진*으로 "중복" 카운트 — **명백한 근접복제**만 잡음. 관대한 추정.
- **둘을 함께 보는 이유**: 두 값의 격차(6,021 vs 55,766)가 곧 **"유사도 0.93~0.95의 부드러운 중복이 얼마나 많은가"** 를 진단한다.

**입력(재료) — 무엇을 먹여서 계산하나**
임베딩 간 **유사도 하나만** 사용한다(ODD 필드·캡션 텍스트를 직접 쓰지 않음). 계산은 **두 단계**로 나뉜다:

**0. 재료 준비** — `embeddings.npy` (N×1024): bge-m3가 각 클립 캡션을 인코딩한 L2 정규화 벡터.

**① k-NN 단계 = "이웃 찾기"** (`step_b_knn`, FAISS)
각 클립 벡터에 대해 나머지 전체 클립과 코사인 유사도를 비교해, **가장 비슷한 상위 K개 클립("이웃")을 찾고 그 K개와의 유사도 값을 반환**한다. *여기서 평균은 아직 내지 않는다 — 유사도 K개를 나열만 함.*
- "이웃"은 위치가 아니라 **임베딩이 가장 비슷한(코사인 유사도가 가장 높은) 다른 클립**을 뜻한다.
- 결과 = `knn_foundation.npz`의 `knn_sim` (N×K 행렬). 예) `knn_sim[5] = [0.98, 0.97, …, 0.91]` — 클립 #5의 상위 20이웃 유사도 20개.

**② 집계 단계 = Effective N** (`step_b_diversity`)
위 `knn_sim` **행렬만** 입력으로 받아 클립별로 집계한다.
- **soft**: 상위 K=20 이웃 유사도의 **평균** → `soft_commonness` (예: `mean(0.98…0.91)=0.945`) → 고유성 `uniqueness_weight = 1 − 0.945 = 0.055` → 전 클립 합산 = Effective N.
- **hard**: `sim > 0.95`인 **이웃 개수**로 중복을 이진 카운트.

> 요약: ① k-NN은 *가장 가까운 20개 이웃과 그 유사도 20개*를 찾아주고, ② soft는 *그 20개를 평균*내 "이 클립이 얼마나 흔한가(중복인가)"를 구한다. "각 클립 벡터와 **가장 가까운 20개**와의 평균 유사도"인 셈.

### 수식

$$\text{Effective N} = \sum_{i=1}^{N} w_i, \quad w_i = 1 - \bar{s}_i, \quad \bar{s}_i = \frac{1}{K} \sum_{j=1}^{K} \text{sim}(x_i,\ \text{NN}_j(x_i))$$

- $\bar{s}_i$: 클립 $i$의 상위 $K=20$개 이웃과의 **평균 코사인 유사도** (`soft_commonness`)
- $w_i = 1 - \bar{s}_i$: 클립 $i$의 **고유성 가중치** (`uniqueness_weight`)

> **공통 뼈대는 $\sum_i w_i$이고, soft·hard의 차이는 $w_i$ 정의뿐이다.** 위 $w_i = 1-\bar s_i$는 **soft**(평균 유사도로 연속 감점). **hard**는 $w_i = \dfrac{1}{1+\#\{\text{sim}>0.95\}}$ (근접복제 개수로 감점) — 상세 비교는 아래 「Hard 방식과 비교」 참조.
> 여기서 $\#\{\text{sim}>0.95\}$는 **상위 $K=20$ 이웃 중** 센 값(FAISS 결과에서 자기 자신 제외, `knn_sim[:, 1:]`)이라 범위가 **$0 \sim K$** — 따라서 hard $w_i \in [1/21,\ 1]$, 완전 고유 클립은 $\#=0 \Rightarrow w_i=1$로 온전히 1개로 계수된다.

### 코드 (step_b_diversity.py)

```python
soft_commonness   = knn_sim[:, :K_UNIQUENESS].mean(axis=1)  # 상위 20이웃 평균 유사도
uniqueness_weight = np.clip(1.0 - soft_commonness, 0, 1)    # 고유성 가중치
effective_N       = float(uniqueness_weight.sum())           # 가중치 합산
```

### 이번 실행 수치로 역추적

| 단계 | 값 |
|------|-----|
| N 전체 클립 수 | 100,398 |
| 상위 20이웃 평균 유사도 (전체 평균) | ≈ 0.9400 |
| 클립당 평균 고유성 가중치 | `1 - 0.9400` ≈ **0.060** |
| Effective N | `100,398 × 0.060` ≈ **6,021** ✓ |

### 직관

각 클립을 "1개"로 세지 않고, **얼마나 새로운 정보인가**에 비례한 분수로 셉니다.

| 이웃과의 유사도 | 고유성 가중치 | 의미 |
|---------------|-------------|------|
| 0.99 | 0.01 | 거의 중복 — 0.01개로 취급 |
| 0.94 | 0.06 | 이번 데이터셋 평균 수준 |
| 0.50 | 0.50 | 절반 정도 새로운 정보 |
| ~0.00 | ~1.00 | 완전히 독립적인 정보 |

### Hard 방식과 비교

| 방식 | 공식 | 기준 | Effective N |
|------|------|------|------------|
| **Soft** | $w_i = 1 - \bar{s}_i$ | 연속적 유사도 평균 | **6,021** |
| **Hard** | $w_i = \frac{1}{1 + \text{count}_{>0.95}}$ | sim > 0.95인 이웃 개수 | 55,766 |

이 데이터셋은 유사도 0.93~0.95 구간의 **"부드러운 중복"** 이 대량 존재합니다.
Hard 방식은 0.95 미만을 중복으로 보지 않아 관대하게 추정하고,
Soft 방식은 해당 구간도 중복으로 반영하므로 훨씬 낮게 나옵니다.

> 출처: Yao et al., *"SoftDedup: Soft Deduplication for Natural Language Texts"*, ACL 2024.

### soft vs hard — 직관적 차이와 "같은 스케일" 여부

**① 핵심 차이 = "중복"을 정의하는 방식**
유사도는 연속값(0~1)이라, "중복이냐 아니냐"를 세려면 어딘가 **선을 그어야** 한다. 그 선을 긋는 방식이 두 방법을 가른다.

- **Hard = 이진(threshold)**: `sim>0.95`면 중복, 아니면 아님. "**명백한 복사본만** 중복." — dedup의 **표준 baseline**(원래 "중복 제거" = 똑같은/거의 똑같은 파일 지우기).
- **Soft = 연속(감점)**: 선을 긋지 않고, 이웃과 비슷한 **정도에 비례해 감점**. "중복은 예/아니오가 아니라 **정도의 문제**."

**② hard의 맹점 → soft가 필요한 이유**
Hard는 이웃이 전부 0.94로 비슷한 클립도 `sim>0.95`가 하나도 없으면 "완전 고유(w=1)"로 센다 — 실제론 거의 똑같은데도. 즉 **0.90~0.95 "회색지대" 중복을 통째로 놓쳐 다양성을 과대평가**한다. Soft는 이 구간을 정직하게 반영한다.

**③ 두 값의 "격차"가 진단이다**
- soft ≈ hard → 중복이 전부 명백한 복사본(>0.95). 데이터가 "깔끔"(복사본이거나 완전 다르거나).
- **soft ≪ hard** (이번: **6,021 vs 55,766**) → **0.90~0.95 near-중복이 대량**. hard는 "다 다르다(56%)", soft는 "대부분 변주다(6%)". **격차 자체가 회색지대(부드러운) 중복의 양.**
- *비유*: 10만 장 사진에서 "서로 다른 순간이 몇 개?" — Hard는 **연사(burst) 10장을 10개**로, Soft는 **≈1개**로 센다. 이 데이터셋은 "같은 도심 직진 장면의 연사" 같은 클립이 수만 장이라, soft만 이를 잡아낸다.

**④ 두 결과는 같은 스케일인가? → 그렇다**
계산법이 달라 스케일이 다를까 헷갈리기 쉬우나 **동일 스케일**이다:

- 둘 다 형태가 `Effective N = Σ wᵢ`이고, **wᵢ = "이 클립을 독립 클립 몇 개로 칠까"(0~1의 분수)** 로 의미가 같다 → 결과 단위는 둘 다 **"실질 독립 클립 수 ∈ [0, N]"**.
- **끝점(anchor)이 일치**: 완전 고유 클립 → soft·hard 모두 $w_i=1$, 완전 중복 → 모두 $w_i\approx 0$. **같은 눈금**.
- 차이는 **애매한 중간만** 다르게 매기는 것 — 이웃 0.94인 클립을 soft는 0.06개, hard는 1개로 세지만 **둘 다 "몇 개"라는 같은 단위**로 답한다.
- 따라서 6,021 vs 55,766 = **같은 분모 N에 대한 6% vs 56%**, 직접 비교가 정당하다. 격차는 스케일 불일치가 아니라 **회색지대 판정의 실제 의견차**다.

> 단서: hard의 $w_i$ 하한은 0이 아닌 $1/21$이라 대형 클러스터($>K$)에서는 hard가 미세하게 과대계상된다(아래 「한계와 보완」의 K-의존 이슈와 같은 뿌리). 단 "고유=1" 기준점이 동일하므로 "% 독립"으로 해석·비교하는 데는 문제없다.

### 한계와 보완

**한계 — 로컬·K 의존 추정**
Effective N은 각 클립이 **자기 이웃 K개만** 보는 1차·로컬 통계다. 데이터가 몇 개의 독립 덩어리(클러스터)로 나뉘는지(**글로벌 구조**)는 보지 못하며, 그 결과 **K 선택과 유사도 절대값에 민감**하다. 특히 **클러스터 크기가 K와 비슷하거나 K보다 클 때** 추정이 왜곡된다.

- 예) 10만 클립이 크기 ~21 클러스터(내부 유사도 0.98)로 이뤄지고 K=20이면: 각 클립 `w = 1−0.98 = 0.02` → 클러스터당 `21×0.02 ≈ 0.42` → Effective N ≈ 클러스터 수(4,762) × 0.42 ≈ **2,000**. "구별 그룹 수 4,762"도 "총 10만"도 아닌, **K·유사도에 휘둘리는 값**이 나온다(내부 유사도가 0.95였다면 ≈4,762로 정답에 근접).
- 즉 Effective N은 **"중복 질량이 얼마나 되나"(로컬)** 를 답할 뿐, **"몇 개의 독립 덩어리인가"(글로벌)** 를 직접 세지 않는다.

**보완 — 세 가지**
1. **Vendi Score 병행 (주 보완)**: 전체 유사도 행렬의 고유값 스펙트럼을 보는 글로벌 지표로, "몇 개의 독립 방향/덩어리"를 잡아 로컬이 놓치는 구조를 포착한다(§3-2·§3-3). → 이 프로젝트가 Effective N을 **단독으로 쓰지 않고 Vendi와 함께 쓰는 이유**.
2. **K-민감도 점검**: `K=10/20/40`으로 바꿔 값이 흔들리면 "클러스터 크기 ≈ K" 신호(§3-4의 LID k-민감도와 동일 발상).
3. **"구별 그룹 수"가 필요하면 클러스터링으로 직접 카운트**: 임베딩을 유사도 임계값 τ에서 **연결요소(connected components)** 로 묶어 그룹 수를 세는 편이, 고정 K 로컬 추정보다 robust하다.

> **결론**: Effective N은 로컬 중복 진단에는 유효하나, 단독으로 "다양성/그룹 수"를 결론짓지 말 것. **Effective N(로컬) + Vendi(글로벌)** 를 반드시 함께 볼 것.

---

### 3-2. Vendi Score 계산 원리와 의미

### 핵심 아이디어

Vendi Score = **고유값 스펙트럼의 엔트로피를 지수화한 값** = "데이터가 실질적으로 몇 개의 독립적인 방향을 커버하는가"

$$\text{Vendi} = \exp\!\Bigl(-\sum_i p_i \log p_i\Bigr) = \exp\!\bigl(H(\mathbf{p})\bigr)$$

$p_i = \lambda_i / \sum_j \lambda_j$ — 커널 행렬 고유값을 확률 분포로 정규화한 것.

### 계산 절차 (step_b_diversity.py)

```python
# 단일 앵커 세트에서 Vendi 계산
def _vendi_once(anchors):
    K  = anchors.astype(np.float64) @ anchors.astype(np.float64).T  # (2000×2000)
    ev = np.maximum(np.linalg.eigvalsh(K), 0)
    p  = ev / (ev.sum() + 1e-12)
    return float(np.exp(-np.sum(p * np.log(p + 1e-12))))

# Sequential Stopping Rule — 평균의 상대 표준오차 < 2%이면 중단
def _vendi_until_stable(embeddings, n_anchor, rng, p=None):
    scores = []
    for _ in range(VENDI_MAX_RUNS):      # 상한 30회
        idx = rng.choice(len(embeddings), n_anchor, replace=False, p=p)
        scores.append(_vendi_once(embeddings[idx]))
        if len(scores) >= VENDI_MIN_RUNS:  # 최소 5회 후
            se = np.std(scores, ddof=1) / np.sqrt(len(scores))
            if se / (np.mean(scores) + 1e-10) < VENDI_TARGET_CV:  # SE/mean < 2%
                break
    ...

# 세 가지 앵커 전략
v_random = _vendi_until_stable(embeddings, 2000, rng, p=None)          # 균등 샘플링
v_dedup  = _vendi_until_stable(embeddings, 2000, rng, p=uniqueness_w)  # 고유성 비례 샘플링
# topk: 상위 Effective_N개(=3,458개) 풀에서 2,000개 샘플링
v_topk   = _vendi_until_stable(pool_emb, 2000, rng, p=None)
```

> 전체 54,912×54,912 행렬 계산은 불가능하므로 2,000개 앵커로 전체 스펙트럼을 근사하는 **Nyström 근사** 사용.
> 샘플링 분산을 제어하기 위해 **Sequential Stopping Rule** (Law & Kelton 2000) 적용 — 이번 실행에서 3전략 모두 5회 만에 수렴(n=5, converged=True).

### anchors → K_mm 변환 상세

`K_mm = anchors @ anchors.T` 한 줄이 하는 일을 풀어서 설명합니다.

**행렬 크기 변화**

```
anchors     : (2000, 1024)   ← 2000개 클립, 각각 1024차원 벡터
anchors.T   : (1024, 2000)   ← 전치
K_mm        : (2000, 2000)   ← (2000×1024) @ (1024×2000)
```

**각 원소의 의미**

$$K_{ij} = \text{anchors}[i] \cdot \text{anchors}[j] = \sum_{k=1}^{1024} a_{ik} \cdot a_{jk}$$

임베딩이 L2 정규화되어 있으므로(`normalize_embeddings=True`) 이 내적은 곧 코사인 유사도입니다.

$$K_{ij} = \cos(\text{clip}_i,\ \text{clip}_j)$$

**→ K_mm은 2000×2000 코사인 유사도 행렬.**

```
          clip0  clip1  clip2  ...  clip1999
clip0   [ 1.00   0.95   0.93  ...   0.94  ]
clip1   [ 0.95   1.00   0.94  ...   0.93  ]
clip2   [ 0.93   0.94   1.00  ...   0.95  ]
...
clip1999[ 0.94   0.93   0.95  ...   1.00  ]
```

- 대각선 = 자기 자신과의 유사도 (≈1.0)
- 나머지 = 클립 쌍 간 코사인 유사도

**왜 유사도 행렬의 고유값이 "다양성"을 나타내는가**

```
모든 클립이 동일할 때:
  K_mm = [[1,1,1,...],    → 랭크 1 행렬 → 고유값 하나만 ≠ 0
           [1,1,1,...],   → Vendi = 1
           ...]

모든 클립이 완전히 다를 때:
  K_mm = [[1,0,0,...],    → 단위 행렬 → 고유값 모두 동일
           [0,1,0,...],   → Vendi = 2000
           ...]

이번 데이터셋:
  K_mm ≈ [[1.00, 0.94, 0.93,...],   → 대부분 비슷 → 열벡터가 거의 평행
           [0.94, 1.00, 0.95,...],   → 행렬 랭크 낮음 → 고유값 소수 지배
           ...]                       → Vendi = 3.513 (random)
```

유사도가 높은 클립이 많다는 것은 행렬의 열벡터들이 거의 평행하다는 뜻이고, 평행한 벡터들로 이루어진 행렬은 랭크가 낮아 고유값이 소수에 집중됩니다.

### 고유값이 의미하는 것

커널 행렬의 고유값은 **데이터가 차지하는 독립적인 "축"의 크기**입니다.

```
λ₁ ████████████████████  (1번 축 — 가장 지배적인 패턴)
λ₂ ██████████
λ₃ █████
λ₄ ██
...
λ₂₀₀₀ ░  (이후 거의 0)
```

- 고유값이 한두 개에 집중 → 데이터가 좁은 공간에 몰림 → **Vendi 낮음**
- 고유값이 균등 분포 → 데이터가 넓은 공간을 커버 → **Vendi 높음**

### 극단 사례로 이해

| 상황 | 고유값 분포 | Vendi |
|------|-----------|-------|
| 모든 클립이 동일 | λ₁=1, 나머지=0 | **1.0** |
| 2개의 완전히 다른 그룹 | λ₁=λ₂=0.5, 나머지=0 | **2.0** |
| k개의 완전히 독립 그룹 | 균등 분포 | **k** |
| 2000개가 전부 독립 | 모두 동일 | **2000** |
| **이번 데이터셋** | **소수 고유값 지배** | **3.513** |

### Vendi 세 전략 — 샘플링 방식과 ± 값의 의미

세 전략 모두 **동일한 Vendi 공식**(커널 행렬 고유값 엔트로피)을 사용합니다. 차이는 단 하나 — **어떤 2,000개 클립을 앵커로 뽑는가**입니다.

#### vendi_random = 3.530 ± 0.017

```
전체 100,398개에서 균등 무작위 2,000개 선택
모든 클립 선택 확률 동일 = 1/100,398
```

중복 클립이 100,398개 중 대다수이므로, 무작위 2,000개 안에도 중복 클립이 비례적으로 포함됩니다. 유사한 벡터가 반복될수록 커널 행렬 랭크가 낮아지고 Vendi가 낮아집니다. **현재 분포 그대로, 모델이 실제 학습 시 받는 다양성 신호를 측정**합니다.

#### vendi_dedup = 3.636 ± 0.020

```
전체 100,398개에서 uniqueness_weight(= 1 - soft_commonness) 비례 샘플링
흔한 클립(이웃과 유사도 높음) → 선택 확률 낮음
희귀 클립(이웃과 유사도 낮음) → 선택 확률 높음
```

중복이 많은 클립일수록 가중치가 낮아져 앵커에 덜 포함됩니다. **SoftDedup을 완전히 적용한 이상적 데이터셋의 다양성을 시뮬레이션**합니다. std(0.020)가 random보다 약간 높은 이유: 희귀 클립은 수가 적으므로 선택 여부에 따라 Vendi가 random보다 조금 더 흔들립니다.

#### vendi_topk = 4.745 ± 0.022

```
1단계: uniqueness_weight 상위 6,022개(= Effective N) 클립을 고정 풀로 추출
2단계: 그 풀 안에서 균등 무작위 2,000개 선택
```

Effective N = 6,021은 "이 데이터셋에서 실질적으로 독립적인 클립 수 추정치"이므로, 상위 6,022개는 데이터셋의 모든 다양성이 응축된 집합입니다. 이 풀만으로 학습할 때의 **다양성 상한**을 측정합니다. 풀(6,022) > 앵커(2,000)이므로 여전히 무작위성이 있지만 풀 자체가 이미 고유 클립으로 구성되어 std(0.022)가 세 전략 중 가장 낮은 수준입니다.

---

#### ± 값이 생기는 구조 — Sequential Stopping Rule

세 전략 모두 **2,000개 앵커를 여러 번 다시 뽑고** 평균을 냅니다. 매 회 다른 2,000개가 선택되므로 Vendi가 조금씩 달라지고, 이 run 간 표준편차가 ± 값입니다.

```
[vendi_random 실제 실행 흐름]
run 1: 무작위 2,000개 → Vendi = 3.513
run 2: 다른 2,000개   → Vendi = 3.548
run 3:                → Vendi = 3.513
run 4:                → Vendi = 3.545
run 5:                → Vendi = 3.532
              ↓
SE/mean = std/√5 / mean = 0.017 / 3.530 = 0.48% < 2% 수렴 기준 충족 → 중단
              ↓
결과: mean=3.530, std=0.017  ← 이것이 3.530 ± 0.017
```

반복 횟수는 `SE/mean < 2%`가 될 때까지 자동 결정(최소 5회, 최대 30회). 이번 실행에서 세 전략 모두 5회(최소값)에서 수렴했습니다.

| 전략 | mean | ± std | std가 상대적으로 다른 이유 |
|------|------|-------|--------------------------|
| vendi_random | 3.530 | ± 0.017 | 100,398 균등 샘플 → 안정적 |
| vendi_dedup  | 3.636 | ± 0.020 | 희귀 클립 과대 표집 → run마다 편차 조금 큼 |
| vendi_topk   | 4.745 | ± 0.022 | 풀(6,022개) 안에서 2,000개 샘플링 |

---

#### 세 전략이 말하는 것

| 비교 | 격차 | 의미 |
|------|------|------|
| dedup − random | **+0.106 (3.0%)** | 중복 제거로 얻을 수 있는 다양성 이득 |
| topk − random | **+1.215 (34.4%)** | 커버리지 확장으로 얻을 수 있는 다양성 이득 |
| topk − random / dedup − random | **11.5배** | 커버리지 문제가 중복 문제보다 11.5배 더 큰 원인 |

**억압 계수(dedup/random) = 1.030**: 중복을 완벽히 제거해도 다양성은 3.0% 향상에 그칩니다.

> **진단**: 다양성 부족의 원인은 "중복"이 아닌 **"수집하지 못한 시나리오"** — 중복 제거보다 새 시나리오 수집·합성이 10배 더 효과적입니다.

### Vendi = 3.530의 의미

100,398개 클립이 있지만, 임베딩 공간에서 이 데이터는 사실상 **3~4개의 독립적인 의미 방향**만 커버합니다.

```
이상적인 다양한 AV 데이터셋:
  고속도로 직진, 도심 교차로, 야간, 악천후, 공사구간,
  보행자 밀집, 주차장, 터널, 합류로, 급커브 ...
  → Vendi 수십~수백

이번 데이터셋 (Vendi=3.530):
  대부분이 [일반 도심 직진] 변주 ───────────────── λ₁ (지배)
  조금의 [주차 주변]         ────── λ₂
  조금의 [교차로/신호등]     ─── λ₃
  나머지는 앞의 변주 반복    ░░░░  (새 정보 없음)
```

시나리오별 Vendi 평균 2.6 (CV=0.068)도 같은 맥락 — **각 시나리오 내부에서도 2~3개 방향만 존재하며, 시나리오 간 편차도 거의 없음**.

### Effective N과의 관계

두 지표는 서로 다른 각도에서 같은 현상을 측정합니다.

| 지표 | 무엇을 측정 | 이번 값 |
|------|-----------|---------|
| **Effective N** | 개별 클립의 고유성 가중치 합 — *얼마나 많은 독립 클립이 있나* | 6,021 (6.0%) |
| **Vendi Score** | 고유값 스펙트럼 엔트로피 — *몇 개의 독립 방향을 커버하나* | 3.530 (random) |

둘 다 같은 진단: **이 데이터셋은 극히 좁은 공간에 집중 수집됨**.

> 출처: Friedman & Dieng, *"The Vendi Score: A Diversity Evaluation Metric for Machine Learning"*, TMLR 2023.
> Shannon 엔트로피의 지수화(`exp(H)`)는 생태학의 **Hill number** (유효 종 수)와 동일한 수학 구조.

### ODD 정렬 검증 — Vendi 타당성 평가

#### 왜 이 검증이 필요한가

Vendi Score는 **임베딩 공간의 다양성**을 측정합니다. 그런데 이 데이터셋의 임베딩은 bge-m3가 캡션 텍스트를 인코딩한 결과입니다. 캡션이 weather, lighting 같은 ODD 조건 변화를 얼마나 잘 묘사하느냐에 따라 임베딩이 ODD 변화를 포착할 수도, 못할 수도 있습니다.

만약 임베딩이 ODD 변화를 전혀 반영하지 못한다면:
- Vendi=3.5는 "캡션 문체의 다양성"만 측정하는 것
- "Vendi가 낮다 = ODD 커버리지가 좁다"는 해석이 근거 없음

반대로 임베딩이 ODD 변화를 잘 반영한다면:
- Vendi=3.5는 실제 주행 환경 다양성을 간접 측정하는 것
- Vendi 기반 분석 결과를 ODD 진단에 신뢰하고 사용 가능

이 검증은 **"Vendi 숫자를 ODD 다양성 진단에 사용해도 되는가"** 를 확인하기 위한 것입니다.

#### 데이터 추출 방법

```
1. 전체 54,912개 클립에서 무작위로 두 인덱스 배열 추출 (replace=True, 독립 샘플링)

   pi_a = [3, 7, 12, 201, ...]   ← 10,000개 클립 인덱스
   pi_b = [9, 2,  88,  45, ...]   ← 10,000개 클립 인덱스

   → pi_a[i]와 pi_b[i]가 하나의 쌍을 이룸 (총 10,000쌍)
   → 자기 자신과의 쌍(pi_a[i] == pi_b[i])은 제거

2. 각 쌍에 대해 두 가지 거리를 계산

   [ODD Hamming 거리]
   odd_mat: 54,912 × 7 행렬 (클립별 7개 ODD 차원 값)

   예시:
   clip_3:  [urban, clear,    day,   cars_only, low,  none,  solid]
   clip_9:  [highway, rain,   day,   cars_only, low,  none,  solid]
   → 7개 중 2개 다름 → ham_dist = 2/7 = 0.286

   [임베딩 코사인 거리]
   cos_dist = 1 - (emb[pi_a[i]] · emb[pi_b[i]])
   → 임베딩 벡터가 비슷할수록 0에 가깝고, 다를수록 1에 가까움
```

#### Spearman ρ 계산

10,000쌍 각각에서 `(ham_dist, cos_dist)` 쌍을 얻은 뒤 **순위 상관계수**를 계산합니다.

Spearman ρ는 "두 값이 같은 방향으로 움직이는가"를 측정합니다. Pearson과 달리 절댓값이 아닌 **순위**를 기준으로 하므로, 임베딩 거리와 ODD 거리의 스케일이 달라도 비교가 가능합니다.

```
쌍 번호  ham_dist  cos_dist
쌍 1     0.286     0.08
쌍 2     0.000     0.02    ← ODD 동일한데 임베딩도 가까움
쌍 3     0.571     0.15
쌍 4     0.143     0.05
...      (10,000개)

→ "ham_dist 순위"와 "cos_dist 순위"가 얼마나 일치하는가 = Spearman ρ
```

#### 결과

| 항목 | 값 | 해석 |
|------|-----|------|
| Spearman ρ | **0.221** | partial — 임베딩이 ODD 변화를 부분적으로 포착 |
| p-value | 0.0 | 통계적으로 유의미 (우연이 아님) |
| n_pairs | 10,000 | |
| 해석 기준 | ρ>0.3=aligned, 0.1~0.3=partial, <0.1=misaligned | |

ρ=0.221의 실질적 의미:

```
ODD가 다른 두 클립 → 임베딩도 멀 가능성이 약간 높음 (완전하진 않음)
ODD가 같은 두 클립 → 임베딩도 가까울 가능성이 약간 높음 (완전하진 않음)
```

**결론**: ρ=0.221는 임베딩이 ODD 조건 차이를 **약하게만** 포착함을 의미합니다. 따라서 Vendi=3.5는 ODD 다양성과 캡션 의미 다양성의 혼합 신호이며, "ODD가 3~4개 방향만 커버된다"는 결론의 **완전한 근거로 사용하기에는 유보가 필요**합니다.

**ODD 자체 다양성 분석 (0-B, found_ratio=100%):**

#### 컬럼 정의 및 계산 방법

**`n_unique`** — 해당 차원에서 데이터셋에 실제로 등장한 카테고리 수 (단순 카운트).
분포와 무관하게, 한 클립이라도 있으면 1개로 셉니다.

```
agent_type: cars_only, car_truck, car_bus, car_cyclist, mixed, pedestrian → n_unique = 6
```

**`norm_entropy (전체)`** — 전체 54,912개 클립 기준, 카테고리 분포가 얼마나 균등한가 (0~1).

```
H      = -Σ p_i × log(p_i)          # Shannon entropy
norm_H = H / log(n_unique)           # 최대 가능 entropy로 나눠 0~1로 정규화

= 1.0 : 모든 카테고리에 완벽히 균등 분포 (이상적)
= 0.0 : 클립 전부가 하나의 카테고리에 집중
```

**`effective_n (전체)`** — 전체 클립 기준, 실질적으로 고르게 쓰이는 카테고리 수.

```
effective_n = exp(H)                 # Shannon entropy를 지수화

n_unique개 카테고리가 완벽히 균등 → effective_n = n_unique
n_unique개가 있지만 1개에 집중    → effective_n ≈ 1
```

> `n_unique`는 "카탈로그에 몇 종이 있나", `effective_n`은 "실제로 몇 종처럼 동작하나".
> `agent_type`의 경우 n_unique=6이지만 effective_n=1.16 — 있기는 하지만 cars_only 한 종이나 마찬가지.

**`norm_entropy (topk)`** — uniqueness_weight 상위 3,458개(topk) 클립만 놓고 계산한 norm_entropy.
전체값과 비교해 ↑면 임베딩 고유성이 높은 클립들이 해당 ODD 차원에서도 더 다양하게 분포, ↓면 그렇지 않음.

---

| ODD 차원 | n_unique | norm_entropy (전체) | effective_n (전체) | norm_entropy (topk) | 변화 |
|---------|---------|-------------------|--------------------|-------------------|------|
| lighting | 3 | **0.909** | 2.71 | 0.819 | ↓ |
| road_type | 6 | 0.590 | 2.88 | 0.657 | ↑ |
| road_divider | 5 | 0.580 | 2.54 | 0.548 | ↓ |
| traffic_density | 4 | 0.488 | 1.97 | 0.496 | ↑ |
| weather | 4 | 0.206 | 1.33 | 0.280 | ↑ |
| agent_type | **7** | **0.076** | 1.16 | 0.149 | ↑ |
| scene_ambiguity | 3 | **0.035** | 1.04 | 0.062 | ↑ |
| **평균** | | **0.412** | | **0.430** | ↑ |

#### 행별 해석

| 차원 | 해석 |
|------|------|
| **lighting 0.909 / eff=2.71** | 주간·야간·황혼 3종이 고르게 분포. 이 데이터셋에서 가장 다양한 차원. topk에서 ↓ — 임베딩 고유성은 주간 집중 클립이 높아 topk에 야간·황혼이 오히려 덜 포함됨 |
| **road_type 0.591 / eff=2.88** | 6종 중 3종 수준만 실질 커버. topk에서 ↑ — 고유 클립일수록 도로 유형도 다양 |
| **road_divider 0.581 / eff=2.55** | 중간 수준. topk에서 ↓ — 임베딩이 road_divider 차이를 거의 반영 못함 |
| **traffic_density 0.487 / eff=1.97** | 4단계 중 2단계 수준. 혼잡·원활만 주로 수집됨 |
| **weather 0.206 / eff=1.33** | ⚠️ 4종 중 맑음(clear)에 80% 이상 집중. 비·눈·안개 거의 없음 |
| **agent_type 0.076 / eff=1.16** | ⚠️⚠️ 7종 있지만 사실상 cars_only 단일 카테고리. 버스·트럭·자전거·보행자 극소수 |
| **scene_ambiguity 0.035 / eff=1.04** | ⚠️⚠️ 3등급 있지만 전부 low(모호성 없음)에 몰림. 사실상 단일값 |

- **전체 100,398개**: 고유 ODD 조합 507개 (7,560 가능 조합의 6.7%), **odd_effective_n = 37.5**
- **고유성 상위 6,022개 (topk)**: 고유 ODD 조합 267개, **odd_effective_n = 40.8**

#### odd_effective_n 해석

전체에 422개 조합이 존재하지만, 특정 조합(맑음+도심+cars_only+주간+…)에 클립이 수만 개 집중되고 나머지 조합은 수십~수백 개 수준입니다. 이처럼 분포가 편중되면 Shannon entropy가 낮아지고, `exp(H)` 로 계산한 effective_n도 낮게 나옵니다. 결과적으로 422개 조합이 있어도 **실질적으로 고르게 커버되는 조합은 37개 수준**입니다.

```
조합1 (맑음+도심+cars_only+주간…) ████████████████████████ 수만 개
조합2                             ████
조합3                             ███
...
조합422                           ░ 몇 개
→ effective_n = exp(H) = 37.4
```

topk 267개의 effective_n=40.8이 전체보다 높은 이유: 조합 수는 줄었지만 남은 267개 조합의 **분포가 더 균등**하기 때문입니다 (많이 쏠린 조합들이 topk에서 걸러짐).

#### topk ↑↓ 변화가 ρ=0.24와 연결되는 이유

임베딩이 ODD와 완전히 무관하면 topk에서도 ODD 분포가 전체와 같아야 합니다 (↑↓ 없음).
임베딩이 ODD를 완벽히 반영하면 topk는 ODD도 훨씬 다양해야 합니다 (전부 ↑, 큰 폭).

실제: 7차원 중 **5개 ↑, 2개 ↓** — 부분적으로만 반영. 이것이 ρ=0.24 (partial)와 일관됩니다.
↓인 lighting·road_divider는 임베딩이 해당 조건 차이를 포착하지 못하는 차원입니다.

**결론**: ①ODD 커버리지 자체가 좁고 (agent_type·scene_ambiguity 사실상 단일값), ②임베딩이 ODD를 부분 반영(ρ=0.24)하므로 Vendi도 낮습니다. **"Vendi=3.5가 낮은 이유"는 ODD 커버리지 자체가 좁기 때문이 주요인이고, 임베딩의 ODD 민감도 부족은 부차 요인**입니다.

#### Per-run Vendi-ODD 동시 비교 (n=30)

쌍별 Spearman(ρ=0.24)이 "임베딩 벡터가 ODD 조건 차이를 인코딩하는가"를 답한다면, 이 분석은 **"Vendi score 수치가 ODD 다양성 수치와 함께 움직이는가"** 를 직접 답합니다.

**방법**: Vendi 계산의 각 run에서 사용한 동일한 2,000개 앵커로 ODD entropy를 함께 계산 → 30회 (Vendi, ODD entropy) 쌍으로 Spearman ρ 계산

| 전략 | 앵커 모집단 | Vendi 범위 | ODD H 범위 | Spearman ρ | p값 (추정) |
|------|-----------|-----------|-----------|-----------|-----|
| random | 전체 100,398개 | 3.487~3.548 | 0.427~0.491 | **0.221** | ~0.24 |
| dedup | 전체 100,398개 (고유성 비례) | 3.610~3.671 | 0.437~0.469 | **0.198** | ~0.29 |
| topk | 고유성 상위 6,022개 | 4.712~4.782 | 0.426~0.466 | **0.001** | ~0.99 |

random/dedup ρ≈0.2 — 약한 양의 상관이지만 **n=30 기준 통계적 유의 미달 (p>0.2)**.

**해석**: 100k 클립에서는 random/dedup 전략에서 "Vendi가 높은 run은 ODD entropy도 높다"는 경향이 약하게 나타납니다(ρ≈0.2). 그러나 n=30에서 유의 임계값 ρ>0.36(p<0.05)에 미치지 못해 우연 수준과 구별하기 어렵습니다. topk(ρ≈0)는 6,022개 고유 풀 안에서의 2,000개 샘플링이므로 풀 자체의 균질성으로 인해 run 간 ODD 편차가 작아 상관이 사라집니다.

**두 검증의 종합 해석**:

```
쌍별 Spearman ρ=0.221 (partial)
  → 임베딩 벡터가 ODD 조건 차이를 약하게 인코딩함 (벡터 특성)
  → Vendi는 ODD 다양성의 부분적 대리 지표로만 사용 가능

Per-run Spearman ρ≈0.2 (random/dedup), ρ≈0 (topk) — 통계적 미유의
  → 약한 양의 경향 존재하나 n=30에서 확증 불가
  → Vendi와 ODD diversity는 반드시 함께 봐야 하는 상호 보완 지표
```

---

### 3-3. Effective N vs Vendi Score — 근본적 차이

### 한 줄 요약

| 지표 | 질문 | 관점 |
|------|------|------|
| **Effective N** | "중복되지 않은 샘플이 몇 개인가?" | 개별 샘플 수준, **로컬** |
| **Vendi Score** | "몇 개의 독립적인 의미 방향을 커버하는가?" | 데이터셋 전체 수준, **글로벌** |

### 수학적 구조의 차이

**Effective N — 1차 통계 (로컬 밀도 추정)**

각 클립이 **자기 이웃 k개만** 봅니다. 반경 $r$ 안에 얼마나 많이 몰렸는지를 측정하는 커널 밀도 추정(KDE)과 수학적으로 동치입니다.
Yao et al. (ACL 2024)은 이를 명시적으로 "local density reweighting"으로 정의합니다.

**Vendi Score — 2차 통계 (공분산 스펙트럼)**

**모든 쌍(pairwise)**의 유사도를 행렬로 구성하고 그 스펙트럼을 봅니다.
이는 커널 PCA의 설명분산 엔트로피와 동치입니다.
Friedman & Dieng (TMLR 2023)은 이를 생태학의 **Hill number**(유효 종 수)의 머신러닝 확장으로 정의합니다.

### 서로 보지 못하는 것

**Effective N이 놓치는 것 — "로컬하게는 독특하지만 글로벌하게는 같은 방향"**

```
예: 10개의 서로 다른 도심 교차로 클립
  clip A (교차로 동쪽)
  clip B (교차로 서쪽)  → A,B 유사도 0.85 → 이웃이 아님 → w_A, w_B 높음
  clip C (교차로 북쪽)  → Effective N에서 셋 다 "독립 샘플"로 카운트

  Vendi 관점: 셋 모두 "교차로" 방향 λ₁에 기여
  → 교차로 방향 하나를 세 번 커버한 것 — 새 방향이 아님
```

Effective N은 "이미 있는 방향 내에서 얼마나 퍼져 있나"는 측정하지만,
**"그 방향 자체가 몇 개인가"는 보지 못합니다.**

Marion et al. (2023, *When Less is More*)은 LLM 사전학습 실험에서 이를 직접 확인했습니다.
중복 제거(Effective N 향상)만으로는 다운스트림 성능이 개선되지 않고,
**다양성(Vendi 향상)이 함께 이루어져야** 효과가 있음을 실증했습니다.

**Vendi가 놓치는 것 — "방향은 있지만 얼마나 충분히 샘플링됐는가"**

```
D₁: 5개 방향, 각 방향에 10,000개 클립  (잘 샘플링된 데이터셋)
D₂: 5개 방향, 각 방향에 1개 클립       (방향만 있고 빈 데이터셋)

→ Vendi(D₁) = Vendi(D₂) = 5  (구분 불가)
```

Vendi는 각 방향이 얼마나 충분히 커버됐는지(coverage density)를 보지 못합니다.
또한 전혀 다른 클립 1개가 추가되면 새로운 고유값이 생겨 Vendi가 과도하게 올라가는
**이상치 과민** 문제가 있습니다.
Tirumala et al. (2023, *D4*)은 이 때문에 Vendi 단독 사용 시 노이즈 데이터에 취약하다고 지적합니다.

### 이번 데이터셋에서 두 지표가 함께 말하는 것

```
Effective N = 6,021  (6.0%)   — 로컬하게 독특한 샘플
      ↓ 그 6,021개를 다시 Vendi로 보면
Vendi       = 3.5             — 그 6,021개조차 3~4개 방향에만 집중
```

**로컬 고유성 ≠ 글로벌 다양성**

| | Effective N 높음 | Effective N 낮음 |
|---|---|---|
| **Vendi 높음** | ✅ 이상적: 많은 독립 샘플 × 넓은 방향 커버 | ⚠️ 방향은 다양하지만 각 방향에 샘플 부족 |
| **Vendi 낮음** | ⚠️ 샘플은 퍼져 있지만 좁은 공간 안에서만 | ❌ **이번 데이터셋**: 중복 많고 방향도 좁음 |

### 어떤 상황에서 어느 지표를 우선 보는가

| 목적 | 우선 지표 | 이유 |
|------|----------|------|
| Pruning 대상 선정 | **Effective N** | 개별 클립 수준의 중복 탐지 가능 |
| 수집 전략 수립 | **Vendi** | 어떤 방향이 부족한지 진단 |
| 합성 데이터 품질 평가 | **Vendi** | 생성 모델이 새 방향을 커버하는지 확인 |
| 두 데이터셋 비교 | **둘 다** | 중복률(Effective N)과 커버리지(Vendi) 모두 필요 |

### 참고 문헌

- Yao et al., *SoftDedup*, ACL 2024 — Effective N의 이론적 기반 (local density reweighting)
- Friedman & Dieng, *The Vendi Score*, TMLR 2023 — Vendi의 Hill number 연결
- Marion et al., *When Less is More*, 2023 — 중복 제거 단독으로는 부족함을 실증
- Tirumala et al., *D4: Deduplication and Diversification*, 2023 — 두 지표의 상보적 사용
- Hill, *Diversity and Evenness*, Ecology 1973 — Vendi의 생태학적 뿌리

---

### 3-4. LID 분포 및 k-민감도 분석 (0-D)

### LID 분포

LID(Local Intrinsic Dimensionality)는 각 클립 주변에 **실질적인 변동 축이 몇 개 존재하는지**를 측정합니다. 희소 영역이 "다양한 시나리오가 아직 수집 안 됐는가"(LID 높음)인지 "본질적으로 단조로운 공간인가"(LID 낮음)인지 구분하는 핵심 지표입니다.

| 지표 | 값 | 의미 |
|------|-----|------|
| median LID | **13.41** | 클립 주변 평균 변동 축 수 — GMM 임계값(16.86)보다 낮음 |
| mean LID | 14.09 | 중앙값보다 높음 → 고LID 클립이 평균을 끌어올림 |
| P10 | 8.99 | 하위 10% — 매우 단조로운 클립 |
| P90 | 19.98 | 상위 10% — 다양한 변주 공간 존재 |
| lid_reliable_ratio | **100.0%** | k=20 이웃 거리 r_max < 0.6 → 전 클립 LID 신뢰 가능 |

**분포 해석**: 중앙값(13.41)이 GMM 임계값(16.86)보다 낮으므로 **과반수 클립이 저LID(Q1/Q3 후보)**입니다. P10=8.99는 일부 클립이 사실상 1~2차원 구조(직선 반복)임을 시사합니다. lid_reliable_ratio=100%는 이번 데이터셋이 초고밀도(이웃이 항상 가까움)이기 때문에 r_max가 작아 LID 추정 자체는 안정적입니다.

### k-민감도 분석

k=15/20/25 세 가지로 LID를 계산하여 **"k=20 MLE 추정이 k 선택에 얼마나 민감한가"**를 검증합니다. 민감하다는 것은 경계 클립의 LID 판정이 불안정함을 의미합니다.

| 단계 | k_sensitive_rate | 임계값 기준 | 비고 |
|------|-----------------|-----------|------|
| 0-D (중앙값 13.41 기준) | **0.053** | > 0.05 → flipd_recommended=True | 원본 추정 |
| 0-E (GMM 임계값 16.86 재계산) | **0.035** | < 0.05 → flipd_recommended=False | 확정값 |

```
k_sensitive_rate = (k=20 저LID 판정이지만 k=15 또는 k=25에서 고LID) / 전체 저밀도 신뢰 클립
```

- **0-D 단계**: 임시 임계값(중앙값 13.41)으로 계산 시 0.053 > 0.05 → FLIPD 실행 권고
- **0-E 단계**: GMM 확정 임계값(16.86)으로 재계산 시 0.035 < 0.05 → FLIPD 불필요 판정
- **결론**: GMM 임계값 16.86이 클립 분포의 자연 경계이므로 경계 클립 수가 줄어들어 k-민감도가 낮아진 것. 실제 FLIPD는 `q3_boundary_rate=37.9% > 0.3` 조건으로 트리거됨

### Q4 부재 이유

`Q4 LID_UNCERTAIN = 0` — 저밀도 클립 중 LID 불신뢰(r_max ≥ 0.6) 클립이 한 개도 없습니다. 데이터가 초고밀도이므로 어느 클립도 k=20 이웃이 0.6 이상 거리에 있지 않고, 따라서 LID 추정이 전부 신뢰 가능합니다. **LID 불신뢰로 인한 불확실성은 이 데이터셋에서 문제가 되지 않습니다.**

---

### 3-5. 6-분류 Action Map 결과 (0-E / 0-E-val)

### FLIPD 전/후 비교

| 분류 | 레이블 | FLIPD 전 | FLIPD 후 | 비고 |
|------|--------|-----------|----------|------|
| Q0 | KEEP | 11,710 (11.7%) | 변동 없음 | 잘 수집된 다양한 클립 |
| Q1 | PRUNE | 60,731 (60.5%) | 변동 없음 | 밀집+저차원 = 중복 제거 대상 |
| Q2 | COLLECT | 11,426 (11.4%) | **17,694 (17.6%)** | +6,268 (FLIPD 업그레이드) |
| Q3 | EVALUATE | 16,531 (16.5%) | **10,263 (10.2%)** | -6,268 → Q2로 이동 |
| Q4 | LID_UNCERTAIN | 0 (0.0%) | 변동 없음 | 고립 클립 없음 |
| Q5 | PRUNE_UNCERTAIN | 0 (0.0%) | 변동 없음 | |

- GMM 임계값: `density=0.9363 (K=3)`, `lid=16.8550 (K=3)`
- 두 분포 모두 3성분 혼합으로 분리됨 (단봉 없음)

### ⚠️ FLIPD 결과 해석 주의

```
upgrade_rate       = 1.000   (6,268/6,268 전원 Q3→Q2)
median_correction  = 184.39  (정상 범위 초과)
```

**원인**: 데이터가 초고밀도(kNN 거리 0.05~0.07로 균일)하여 `r_j/r_k ≈ 1.0` →
FLIPD 경계 보정항 `j*(r_j/r_k)^mle`이 수치 발산 → 200으로 클리핑 → 전원 임계값 초과.

**의미**: 이 6,268개 Q3→Q2 업그레이드는 FLIPD 공식이 초고밀도 데이터에서 발산한 결과이므로
신뢰도가 낮음. Q3 클립 샘플링으로 직접 확인 권장.

---

## 4. 시나리오별 분석 (0-F-1)

**K=12 선택** (실루엣 flat_fallback=True — TF-IDF 공간 클러스터 구조 약함)

| S | 크기 | Q0% | Q1% | Q2% | Q3% | Vendi | 주요 키워드 | 비고 |
|---|------|-----|-----|-----|-----|-------|------------|------|
| **S0** | 5,648 | 10.4 | **83.2** | 4.2 | 2.2 | 2.3 | vehicle, lane, road, headlights | **Q1 극단 (야간 단조)** |
| S1 | 5,307 | 6.0 | 62.9 | 14.2 | 17.0 | 2.6 | vehicle, travels, ego, lane | COLLECT 후보 |
| S2 | 3,131 | 4.9 | 46.1 | 26.1 | 23.0 | 2.6 | parking lot, low speed | Q2 많음 |
| S3 | 2,220 | 4.4 | 65.4 | 16.5 | 13.7 | 2.5 | snow covered, vehicle, road | 설면 시나리오 |
| S4 | 10,188 | 12.5 | 72.5 | 9.9 | 5.1 | 2.5 | lane, vehicle, highway | Q1 과다 |
| S5 | 9,182 | 13.8 | 69.5 | 10.5 | 6.2 | 2.6 | lane, sedan, suv | Q1 과다 |
| S6 | 10,115 | 11.5 | 62.3 | 15.3 | 10.9 | 2.6 | light, intersection, ego | COLLECT 후보 |
| S7 | 10,639 | 8.9 | 69.7 | 13.0 | 8.4 | 2.8 | vehicle, lane, road, ego | |
| S8 | 11,798 | 16.4 | 60.4 | 17.0 | 6.2 | 2.6 | parked vehicles, ego | COLLECT 후보 |
| S9 | 8,912 | 8.9 | 43.3 | 29.9 | 17.9 | 2.9 | vehicle, curve, sharp | Q2 많음 |
| S10 | 11,310 | 9.4 | 35.1 | 37.4 | 18.2 | 3.0 | vehicle, turn, ego, road | Q2 많음 |
| S11 | 11,948 | 17.8 | 61.7 | 14.3 | 6.2 | 2.6 | vehicle, lane, ego, road | COLLECT 후보 |

**두 공간 독립성**: NMI=0.0336, ARI=0.0105 → `two_space_independence_ok=True` ✓
(TF-IDF 시나리오 분류 ↔ 임베딩 사분면 분류가 독립적 — 교차표 유효)

**주목 포인트**:
- **S0 (야간/헤드라이트)**: Q1=83.2% — 밤 직진 주행만 과도 수집된 가장 단조로운 시나리오
- **S9, S10, S2**: Q2 비율 26~37% — 수집되지 않은 다양한 케이스 상대적으로 많음
- 모든 시나리오 Vendi 2.3~3.0: **시나리오 내부도 다양성 낮음**
- **억압 계수(vendi_dedup/vendi_random)**: 전 시나리오 1.018~1.050 (평균 1.035) — VENDI_SUPPRESSION_HIGH=2.0 미달 → 중복 제거만으로는 다양성 개선 기대 어려움. **S0(야간)=1.050** 이 가장 높아 중복 제거 효과가 다소 큼
- `caution_scenarios=[]`: PRUNE_THRESH=90.75% (1.5 × 60.5%)로 설정 → 어떤 시나리오도 위험 판정 미달
- `healthy_scenarios=[]`: 어떤 시나리오도 Q0 ≥ 40% + size ≥ 500 기준 미달

---

## 5. 갭 슬라이스 분석 — 수집/합성 우선순위 (0-F-2)

### COLLECT 후보 (7개)

수집 우선순위 결정 기준: ① LID 기반 (mean_lid ≥ 16.855 또는 gap_in_scenario_ratio ≥ 0.4), ② ODD 기반 (odd_effective_n ≥ 22.0). 두 기준 중 하나라도 충족 시 COLLECT_HIGH_PRIORITY.

#### HIGH PRIORITY (5개) — LID 또는 ODD 기준 충족

| 시나리오 | 갭 수 | Q2 유효 N | mean LID | ODD eff_n | 승격 근거 | 부족한 유형 |
|---------|-------|----------|----------|----------|----------|------------|
| **S10** (회전/교차로) | 6,284 | 335.6 | 16.96 | 24.18 | LID+ODD | roundabout, crossing, cyclist, yield |
| **S6** (교차로) | 2,651 | 120.7 | 15.88 | 22.11 | **ODD** | cyclist, wet, bus, tram, hatchback |
| **S11** (일반 주행) | 2,448 | 131.0 | 17.24 | 28.49 | LID+ODD | construction zone, roundabout, 습노면, bus |
| **S5** (일반/감속) | 1,531 | 74.9 | 16.79 | 23.48 | LID+ODD | ramp, 감속, urban stop |
| **S1** (단선 주행) | 1,654 | 59.9 | 14.55 | 22.90 | **ODD** | bus, ramp, wet, truck, hatchback |

- S10·S5·S11: LID(≥16.86) + ODD(≥22) 둘 다 충족. `lid_context_caution=True` — 시나리오 내 희귀 케이스.
- S6·S1: mean_lid < 16.86 — 임베딩 공간 기준으로는 단조하지만 **ODD 다양성(≥22)으로 승격**. 임베딩(ρ=0.221 partial)이 ODD 조건 변화를 완전히 포착하지 못해 LID만으로 판단하면 놓치는 케이스.

#### NORMAL (2개) — LID 기반

| 시나리오 | 갭 수 | Q2 유효 N | mean LID | ODD eff_n | 부족한 유형 |
|---------|-------|----------|----------|----------|------------|
| **S8** (주차 주변) | 2,741 | 153.0 | 17.69 | 16.37 | cyclist, bus, truck, 교차로 회전 |
| **S4** (고속도로) | 1,531 | 77.4 | 16.92 | 21.74 | ramp, 진입로, 감속 |

> 억압 계수 전 후보 1.03~1.05 — VENDI_SUPPRESSION_HIGH=2.0 미달. 모든 후보가 중복 때문이 아닌 **해당 유형 클립 자체가 수집되지 않은** 구조적 갭임.

### SYNTHETIC 후보 (5개)

> 모두 odd_effective_n ≤ 22.0 + mean_lid < 16.86 → 임베딩·ODD 두 기준 모두 미달

> 모두 `partial_collect_flag=True` → 합성 전 기존 Q2 클립 별도 수집 먼저 권장

| 시나리오 | 갭 클립 수 | mean LID | ODD eff_n | 주요 키워드 |
|---------|-----------|----------|----------|------------|
| S9 (커브) | 4,261 | 16.28 | 15.27 | curve, sharp, road |
| S7 (주행) | 2,283 | 16.12 | 16.98 | rural, pedestrians, straight |
| S2 (주차장) | 1,537 | 15.35 | 15.56 | parking lot, low speed |
| S3 (설면) | 672 | 15.27 | 15.67 | snow covered, traction |
| S0 (야간) | 364 | 16.67 | 8.30 | headlights, poorly lit, highway |

---

## 6. 다음 단계 권장 액션

### 즉시 검토
- [ ] **FLIPD 이슈 확인**: Q3 클립(10,263개) 수동 샘플링 → 실제로 Q2(다양)인지 Q3(단조)인지 육안 확인
- [ ] **lid_threshold 재검토**: 현재 16.86 → 13~15 범위 하향 조정 후 재실행 고려

### EXP-004 데이터 수집

**HIGH PRIORITY (LID+ODD 기준 충족)**
- [ ] **S10 갭** (roundabout/crossing/cyclist): 6,284클립, Q2 유효 N=336 — 가장 큰 갭
- [ ] **S11 갭** (construction zone/roundabout/습노면): 2,448클립, Q2 유효 N=131
- [ ] **S8 갭** (주차 주변 cyclist/bus/truck): 2,741클립, Q2 유효 N=153
- [ ] **S6 갭** (교차로/cyclist/wet): 2,651클립, Q2 유효 N=121
- [ ] **S5 갭** (ramp/감속/urban stop): 1,531클립, Q2 유효 N=75
- [ ] **S1 갭** (단선/bus/wet/ramp): 1,654클립, Q2 유효 N=60

**NORMAL (LID 기반)**
- [ ] **S4 갭** (고속도로 ramp/진입/감속): 1,531클립, Q2 유효 N=77

### 데이터 합성
- [ ] 5개 SYNTHETIC 후보 (S9/S7/S2/S3/S0) — 시나리오별 Q2 클립 먼저 분리 수집 후 합성 생성

### Pruning (EXP-004)
- [ ] **S0 (야간 직진)**: Q1=83.2% — 첫 번째 pruning 대상
- [ ] **Q1 전체 60,731개** 중 유효 다양성 보존하면서 제거 전략 수립

---

## 7. 산출물 파일 가이드

### 7.1 스텝별 산출물 전체 목록

#### [0-B] FAISS k-NN 기반 구조 구축

| 파일 | 형식 | 내용 | 우선순위 |
|------|------|------|---------|
| `embeddings.npy` | npy (N×1024) | 클립별 임베딩 벡터. 0-B Vendi·0-E-1 per-scenario Vendi 계산에 직접 사용 | ★★ |
| `knn_foundation.npz` | npz | k=50 이웃 코사인 유사도 행렬 (N×50). **모든 후속 단계의 공통 기반** — 이 파일 하나에서 밀도·LID·Effective N이 전부 파생됨 | ★★★ |
| `clip_ids.npy` | npy (N,) | 클립 인덱스 ↔ 실제 파일명 매핑. 특정 클립 인덱스를 실제 데이터와 연결할 때 사용 | ★★ |

#### [0-C] Effective N + Vendi Score + 연속 밀도장

| 파일 | 형식 | 내용 | 우선순위 |
|------|------|------|---------|
| `diversity_profile.json` | JSON | **전체 다양성 진단 요약.** Effective N(soft/hard), Vendi 3전략(random/dedup/topk), 억압 계수(suppression_ratio), 중복률, 밀도 분위수(p10/median/p75), ODD 다양성 분석(odd_diversity — per-dim 엔트로피·고유 조합 수·임베딩 정렬 Spearman ρ) | ★★★ |
| `density_per_clip.npy` | npy (N,) | 클립별 연속 밀도값 (k=10 이웃 평균 코사인 유사도). 값이 높을수록 주변이 조밀한 클립 | ★★ |
| `density_quartile.npy` | npy (N,) | 클립별 밀도 4분위 등급 (0=하위25% 희소, 3=상위25% 조밀). 0-E-1에서 시나리오별 밀도 분포 집계에 사용 | ★ |
| `uniqueness_weight.npy` | npy (N,) | 클립별 고유성 가중치 = `1 - soft_commonness`. Effective N 합산의 원천. 0-E-1에서 시나리오별 dedup Vendi 계산에 재사용 | ★★ |

#### [0-D] LID + 신뢰도 + k-민감도

| 파일 | 형식 | 내용 | 우선순위 |
|------|------|------|---------|
| `lid_per_clip.npy` | npy (N,) | 클립별 LID 추정값 (k=20 MLE). 높을수록 주변에 다양한 변동 축 존재 → COLLECT 후보. 낮을수록 본질적 단조 → PRUNE 후보 | ★★★ |
| `lid_reliable.npy` | npy (N, bool) | 클립별 LID 신뢰도 플래그. `r_max_dist < 0.6`이면 True. False인 클립은 LID 판정 신뢰 불가 → Q4/Q5로 분류 | ★★ |
| `lid_quartile.npy` | npy (N,) | 클립별 LID 4분위 등급. 0-E-1에서 시나리오별 LID 분포 집계에 사용 | ★ |
| `lid_k15.npy` | npy (N,) | k=15 LID 추정값. k-민감도 분석용 — k=20과 비교해 판정 뒤집힘 클립 수 측정 | ★ |
| `lid_k25.npy` | npy (N,) | k=25 LID 추정값. 동상 | ★ |
| `lid_stats.json` | JSON | **LID 분포 통계 요약.** mean/median/p10/p90, lid_reliable_ratio, k_sensitive_rate(GMM 확정값), k_sensitive_rate_approx(0-C 원본), flipd_recommended | ★★ |

#### [0-E] 6-분류 Action Map

| 파일 | 형식 | 내용 | 우선순위 |
|------|------|------|---------|
| `quadrant_assignment.npy` | npy (N,) | 클립별 최종 사분면 번호 (0-D-val FLIPD 적용 후). 0=KEEP·1=PRUNE·2=COLLECT·3=EVALUATE·4=LID_UNCERTAIN·5=PRUNE_UNCERTAIN | ★★★ |
| `quadrant_assignment_pre_flipd.npy` | npy (N,) | FLIPD 전 원본 사분면 번호. FLIPD 결과를 비교하거나 되돌릴 때 사용 | ★ |
| `quadrant_profile.json` | JSON | 6-분류 카운트·비율 (FLIPD 전 기준). 전역 Q5 비율 등 0-E-1 PRUNE 임계값 계산의 기준값 | ★★★ |
| `thresholds.json` | JSON | **GMM BIC 교차점 임계값.** `density_threshold`(0.9335)·`lid_threshold`(16.1994). q3_boundary_rate, k_sensitive_rate(확정), FLIPD 트리거 조건 기록. 0-E-2에서 재로드 | ★★★ |
| `lid_margin.npy` | npy (N,) | 클립별 LID 임계값 대비 여백 = `|lid - lid_threshold| / lid_threshold`. 값이 작을수록 임계값 근처 → 판정 불안정 | ★ |
| `lid_boundary_zone.npy` | npy (N, bool) | 클립별 LID 경계 구역 플래그 (margin ≤ 0.15). True인 클립이 FLIPD 검증 대상 | ★ |

#### [0-E-val] 조건부 FLIPD 검증

| 파일 | 형식 | 내용 | 우선순위 |
|------|------|------|---------|
| `flipd_validation.json` | JSON | FLIPD 적용 결과. `flipd_applied`, `upgrade_rate`, `median_correction` 포함. **이번 실행: upgrade_rate=1.0 → 수치 발산으로 신뢰도 낮음** | ★★ |
| `flipd_upgraded_clips.npy` | npy (M,) | Q3→Q2로 업그레이드된 클립 인덱스 배열. M=6,268개 (신뢰도 주의) | ★ |

#### [0-F-1] 시나리오 의미 지도

| 파일 | 형식 | 내용 | 우선순위 |
|------|------|------|---------|
| `scenario_labels.npy` | npy (N,) | 클립별 시나리오 번호 (TF-IDF K-Means K=12 결과). 0-E-2에서 재사용 | ★★★ |
| `scenario_profiles.json` | JSON | **12개 시나리오별 상세 프로파일.** 크기, 상위 키워드, 사분면 분포(Q0~Q5 %, 카운트), Effective N, Vendi(random/dedup/suppression_ratio), 평균 밀도·LID, prune_flag, ODD 다양성(odd_diversity — per-dim 엔트로피·고유 조합 수) | ★★★ |
| `scenario_diversity_summary.json` | JSON | 시나리오 간 Vendi 통계(mean/std/CV/Gini), 억압 계수 통계(mean/max/min/high_count), NMI·ARI 두 공간 독립성 | ★★ |
| `silhouette_scores.json` | JSON | K=6/8/10/12/15 실루엣 점수 비교 및 K 선택 근거. `flat_fallback=True` → 도메인 지식 K=12 사용 | ★ |
| `healthy_scenarios.json` | JSON | Q0 지배(≥40%) + 500클립 이상 건강한 시나리오 목록. **현재 비어 있음** — 어떤 시나리오도 기준 미달 | - |
| `caution_scenarios.json` | JSON | prune_flag=CAUTION/Q5_UNCERTAIN 시나리오 목록. 자동 PRUNE 금지 대상. **현재 비어 있음** | - |
| `boundary_sensitive_scenarios.json` | JSON | 전역 임계값 ±5% 이내 민감 시나리오. 임계값 조정 시 사분면 구성이 역전될 수 있는 시나리오 | ★ |
| `tfidf_vectorizer.joblib` | joblib | TF-IDF 벡터라이저 직렬화. 0-E-2 독립 실행 시 captions를 같은 피처 공간으로 변환하기 위해 로드 | ★ |

#### [0-F-2] 갭 슬라이스 정밀 분석

| 파일 | 형식 | 내용 | 우선순위 |
|------|------|------|---------|
| `collect_candidates.json` | JSON | **즉시 수집 대상 시나리오.** action=COLLECT/COLLECT_HIGH_PRIORITY. 각 항목에 scenario_context, gap_specifics, gap_count, q2_effective_n, mean_lid, vendi_suppression_ratio, priority 포함 | ★★★ |
| `synthetic_candidates.json` | JSON | **합성 데이터 생성 대상.** action=SYNTHETIC_OR_ACCEPT. `partial_collect_flag=True`이면 합성 전 Q2 클립 먼저 수집 권장 | ★★ |
| `uncertain_candidates.json` | JSON | LID 신뢰도 낮아 자동 판정 불가 시나리오. 수동 검토 필요. **현재 비어 있음** (lid_reliable_ratio=100%로 해당 없음) | - |
| `gap_slices.json` | JSON | 시나리오별 갭 상세 분석 원본. action·비율·LID·Vendi 억압 계수·임계값 민감도 전체 포함. collect_candidates/synthetic_candidates의 원천 | ★★ |
| `skipped_small_gaps.json` | JSON | MIN_GAP_SIZE=50 미달로 분석 제외된 시나리오 목록. 소규모 갭 존재 여부 추적 | ★ |

---

### 7.2 핵심 파일 주요 필드 설명

#### `diversity_profile.json`
```
effective_N_soft        : 실질 독립 클립 수 (고유성 가중치 합)
effective_N_hard        : 이진 임계값(sim>0.95) 기준 독립 클립 수
redundancy_ratio        : 중복률 = 1 - effective_N_soft / N
vendi_random.mean       : 현재 분포 Vendi — 모델이 실제로 받는 다양성 신호
vendi_dedup.mean        : 중복 제거 후 Vendi
vendi_topk.mean         : 상위 Effective_N 풀 Vendi 상한
vendi_suppression_ratio : dedup/random 비율 (≈1 → 커버리지 문제, >2 → 중복 억압)

odd_diversity
  .found_ratio          : ODD 파일 존재 클립 비율 → 1.0 (100,398/100,398, 전 클립 커버)
  .n_unique_combos      : 발견된 고유 ODD 조합 수 → 507 (최대 7,560 중 6.7%)
  .mean_norm_entropy    : 7개 차원 정규화 엔트로피 평균 → 0.412
  .per_dim              : 차원별 엔트로피·고유값 수 (이번 실행 결과)
    .road_type          : n_unique=6, norm_entropy=0.590  (중간)
    .weather            : n_unique=4, norm_entropy=0.206  (맑음 편중)
    .traffic_density    : n_unique=4, norm_entropy=0.488  (중간)
    .agent_type         : n_unique=7, norm_entropy=0.076  ⚠️ cars_only 극도 집중
    .lighting           : n_unique=3, norm_entropy=0.909  (비교적 고름)
    .scene_ambiguity    : n_unique=3, norm_entropy=0.035  ⚠️ 단일 카테고리 집중
    .road_divider       : n_unique=5, norm_entropy=0.580  (중간)
  .embedding_odd_alignment  : 임베딩–ODD 정렬 검증 (Spearman ρ)
    .spearman_rho       : ODD Hamming 거리 vs 임베딩 코사인 거리 상관계수
                          → 0.221 (partial)
                          ρ > 0.3 → aligned (임베딩이 ODD 변화 포착)
                          0.1 < ρ ≤ 0.3 → partial  ← 현재
                          ρ ≤ 0.1 → misaligned (Vendi가 ODD 다양성 ≠ 임베딩 다양성)
    .interpretation     : "partial"
    .n_pairs            : 10,000

vendi_odd_run_alignment     : per-run Vendi-ODD entropy 동시 비교 (n=30, 3전략)
  .random / .dedup / .topk
    .per_run_vendi        : 각 run의 Vendi score 목록
    .per_run_odd_entropy  : 동일 앵커로 계산한 ODD mean_norm_entropy 목록
    .spearman_rho         : Vendi ↔ ODD entropy Spearman ρ → 3전략 모두 ≈0
    .p_value              : 통계적 유의성 → 3전략 모두 >0.7 (무의미)
    .n_runs               : 30

odd_topk_diversity          : 고유성 상위 클립(uniqueness_weight 기준 상위 Effective_N개)의 ODD 분포
  .n_clips              : 6,022 (= Effective N, 전체의 6.0%)
  .n_unique_combos      : 267 (전체 507 중 52.7% 커버)
  .odd_effective_n      : 40.767 (전체 37.516보다 높음 → 고유 클립의 ODD 분포가 더 고름)
  .mean_norm_entropy    : 0.430 (전체 0.412보다 높음 → 고유 클립이 ODD 관점에서도 더 다양)
  .per_dim              : 차원별 상세 (전체 odd_diversity와 비교)
    .road_type          : norm_entropy=0.657  (전체 0.590 ↑)
    .weather            : norm_entropy=0.280  (전체 0.206 ↑)
    .traffic_density    : norm_entropy=0.496  (전체 0.488 ↑)
    .agent_type         : norm_entropy=0.149  (전체 0.076 ↑)
    .lighting           : norm_entropy=0.819  (전체 0.909 ↓ — 임베딩 고유성 무관)
    .scene_ambiguity    : norm_entropy=0.062  (전체 0.035 ↑)
    .road_divider       : norm_entropy=0.548  (전체 0.580 ↓ — 임베딩 고유성 무관)
```

#### `thresholds.json`
```
density_threshold  : 고밀도/저밀도 경계 (GMM BIC K=3 교차점) = 0.9363
lid_threshold      : 고LID/저LID 경계 (GMM BIC K=3 교차점)   = 16.8550
q3_boundary_rate   : Q3 내 경계 구역 클립 비율 → FLIPD 트리거 기준
k_sensitive_rate   : GMM 기반 k-민감도 (0-D에서 확정)
flipd_recommended  : FLIPD 실행 권고 여부
```

#### `scenario_profiles.json` (시나리오별)
```
size                    : 시나리오 내 클립 수
top_terms               : TF-IDF 상위 키워드 12개 (시나리오 의미 요약)
quadrant_distribution   : Q0~Q5 카운트 및 비율
effective_n             : 이 시나리오의 실질 독립 정보량
vendi_score             : Vendi random mean (하위 호환)
vendi_random / vendi_dedup : Sequential Stopping 결과 (mean/std/cv/n_runs)
vendi_suppression_ratio : 시나리오 내 억압 계수
prune_flag              : None/OK/CAUTION/Q5_UNCERTAIN
odd_diversity           : 이 시나리오 클립들의 ODD 다양성
  .found_ratio          : 시나리오 내 ODD 파일 존재 비율
  .n_unique_combos      : 시나리오 내 고유 ODD 조합 수
  .mean_norm_entropy    : 7개 ODD 차원 평균 정규화 엔트로피
  .per_dim              : 차원별 엔트로피 상세
                          (전역 odd_diversity.per_dim과 동일 구조)
```

#### `collect_candidates.json` (갭 항목별)
```
scenario_context        : 시나리오 대표 키워드 5개 (무엇에 대한 시나리오인가)
gap_specifics           : 갭 클립에서 두드러진 키워드 (무엇이 부족한가)
priority                : HIGH(즉시) / NORMAL
gap_count               : 갭(Q2+Q3+Q4) 클립 수
q2_effective_n          : 갭 내 Q2 클립의 독립 정보량 (수집 시 실질 기여량 추정)
mean_lid                : 갭 클립 평균 LID (높을수록 수집 가치 높음)
vendi_suppression_ratio : 시나리오 내 억압 계수 (≥2.0이면 HIGH_PRIORITY 승격)
odd_effective_n         : 시나리오의 ODD 실질 다양성 (≥22.0이면 HIGH_PRIORITY 승격)
collect_confidence      : HIGH(gap_q2_ratio≥0.5) / MED / LOW
lid_context_caution     : True이면 갭 LID > 시나리오 LID → 시나리오 내 희귀 케이스
```

---

### 7.3 빠른 확인 명령어

```bash
OUTPUT=experiments/EXP-003/phase0/output

# 전체 다양성 진단
cat $OUTPUT/diversity_profile.json

# GMM 임계값 확인
cat $OUTPUT/thresholds.json

# 6-분류 최종 분포 (FLIPD 반영)
python3 -c "
import numpy as np
q = np.load('$OUTPUT/quadrant_assignment.npy')
labels = ['KEEP','PRUNE','COLLECT','EVALUATE','LID_UNCERTAIN','PRUNE_UNCERTAIN']
for i, l in enumerate(labels):
    print(f'Q{i} {l}: {(q==i).sum():>6}개 ({(q==i).mean():.1%})')
"

# 수집 후보 확인
cat $OUTPUT/collect_candidates.json

# 시나리오 억압 계수 확인
python3 -c "
import json
sp = json.load(open('$OUTPUT/scenario_profiles.json'))
for k, v in sorted(sp.items(), key=lambda x: int(x[0])):
    print(f\"S{k}: vendi={v['vendi_score']}, sup={v['vendi_suppression_ratio']}, prune={v['prune_flag']}\")
"

# FLIPD 업그레이드 클립 확인
python3 -c "
import numpy as np
clip_ids = np.load('$OUTPUT/clip_ids.npy', allow_pickle=True)
upgraded = np.load('$OUTPUT/flipd_upgraded_clips.npy')
print(f'업그레이드 {len(upgraded)}개 (주의: 신뢰도 낮음)')
print('샘플:', clip_ids[upgraded[:5]])
"

# ODD 다양성 및 임베딩 정렬 확인 (전체 vs topk 비교)
python3 -c "
import json
dp   = json.load(open('$OUTPUT/diversity_profile.json'))
odd  = dp.get('odd_diversity', {})
topk = dp.get('odd_topk_diversity', {})
aln  = odd.get('embedding_odd_alignment', {})
print(f'ODD 커버리지: {odd.get(\"found_ratio\", \"N/A\"):.1%}')
print(f'임베딩 정렬: {aln.get(\"interpretation\", \"N/A\")} (rho={aln.get(\"spearman_rho\", \"N/A\")})')
print()
print(f'{'차원':<20} {'전체 norm_H':>12} {'topk norm_H':>12} {'변화':>6}')
for dim, v in odd.get('per_dim', {}).items():
    t = topk.get('per_dim', {}).get(dim, {})
    h_all  = v['norm_entropy']
    h_topk = t.get('norm_entropy', float('nan'))
    arrow  = '↑' if h_topk > h_all else '↓'
    print(f'{dim:<20} {h_all:>12.3f} {h_topk:>12.3f} {arrow:>6}')
print()
print(f'고유 ODD 조합 — 전체: {odd.get(\"n_unique_combos\", \"N/A\")}  topk: {topk.get(\"n_unique_combos\", \"N/A\")}')
print(f'mean_norm_entropy — 전체: {odd.get(\"mean_norm_entropy\", \"N/A\")}  topk: {topk.get(\"mean_norm_entropy\", \"N/A\")}')
"

# 시나리오별 ODD 다양성 비교
python3 -c "
import json
sp = json.load(open('$OUTPUT/scenario_profiles.json'))
print(f'{'S':>3} {'n_combos':>9} {'mean_norm_H':>11} {'vendi':>6}')
for k, v in sorted(sp.items(), key=lambda x: int(x[0])):
    odd = v.get('odd_diversity', {})
    print(f'S{k:>2} {odd.get(\"n_unique_combos\", \"N/A\"):>9} {odd.get(\"mean_norm_entropy\", \"N/A\"):>11} {v[\"vendi_score\"]:>6}')
"
```

---
