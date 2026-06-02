# 문헌 관리 시스템 — 사용 가이드

이 가이드는 `literature/` 디렉토리 기반 논문 관리 워크플로우를 설명한다.  
새 논문을 추가할 때마다 이 절차를 따르면 위키 시스템이 일관되게 유지된다.

---

## 1. 디렉토리 구조

```
literature/
├── GUIDE.md                  ← 이 파일 (사용 가이드)
├── links.md                  ← 등록된 논문 목록 + 후보 자료 목록
└── papers/                   ← PDF 원본 저장소
    ├── aasi-2024-generating-out-of-distribution-scenarios.pdf
    ├── chodowiec-2026-odd-behaviour-scenario-coverage.pdf
    └── ...

docs/
└── wiki/
    ├── INDEX.md              ← 기술 카테고리별 인덱스 (갭-기술 대응표 포함)
    ├── embedding/            ← 임베딩 & 검색 기술
    ├── search/               ← 검색 방법론
    ├── tagging/              ← ODD 태깅 기술
    ├── evaluation/           ← 평가 방법론
    ├── data_distribution/    ← 데이터 분포 & 스케일링
    └── scenario_generation/  ← 시나리오 생성
```

---

## 2. 새 논문 추가 절차 (5단계)

### 2-1단계: PDF 파일 배치

파일명 규칙: `{성}-{연도}-{제목-키워드}.pdf`

```
# 예시
naumann-2025-data-scaling-laws-end-to-end.pdf
rivera-2025-scenario-understanding-traffic-scenes.pdf
```

`literature/papers/`에 PDF를 저장한다.

---

### 2-2단계: 논문 내용 파악

논문을 읽고 아래 항목을 파악한다:

| 항목 | 내용 |
|------|------|
| 저자 / 연도 / 학술대회 | 출처 식별 |
| 핵심 문제 | 이 논문이 해결하려는 것 |
| 핵심 방법 | 알고리즘·프레임워크·메트릭 |
| 주요 수치 | 성능 향상 수치, 데이터셋 규모 |
| 한계점 | 적용 시 주의사항 |
| **현재 프로젝트 적용 포인트** | Gap과의 연결점 |

Claude에게 논문 요약을 요청할 때 권장 프롬프트:
```
이 논문을 읽고 다음을 추출해줘:
1. 핵심 방법론 (수식·알고리즘 포함)
2. 주요 실험 결과 수치
3. 현재 프로젝트의 어떤 Gap에 해당하는지
4. 현재 83k 클립 검색 시스템에 적용할 수 있는 구체적인 아이디어
```

---

### 2-3단계: 위키 파일 생성

**위키 파일 저장 위치 결정:**

| 논문 주제 | 저장 디렉토리 |
|---------|------------|
| 임베딩 모델, Dense Retrieval | `docs/wiki/embedding/` |
| BM25, Hybrid Search | `docs/wiki/search/` |
| 씬 분류, 자동 태깅 | `docs/wiki/tagging/` |
| 평가 메트릭, 커버리지 측정 | `docs/wiki/evaluation/` |
| 데이터 선택, 스케일링 법칙 | `docs/wiki/data_distribution/` |
| 시나리오 생성, OOD 탐색 | `docs/wiki/scenario_generation/` |

**파일명 규칙:** `{주제-키워드}.md`

```
# 예시
lvlm-scene-tagging-catpipe.md
scaling-laws-e2e-nvidia.md
subjective-logic-ml-metrics.md
```

**위키 파일 템플릿:**

```markdown
# {기술명}

## 출처
- **저자**: {저자 목록} ({소속})
- **연도**: {연도}
- **학술대회/저널**: {출처}
- **논문**: {arXiv ID 또는 DOI}
- **파일**: `literature/papers/{파일명}.pdf`

---

## 핵심 아이디어

{2~3줄 요약}

### {핵심 구성 요소 1}

{설명, 수식, 표 등}

### {핵심 구성 요소 2}

{설명}

---

## 장단점

**장점**
- {장점 1}
- {장점 2}

**단점**
- {단점 1}
- {단점 2}

---

## 프로젝트 적용 포인트

### Gap-{N} ({갭 설명}) 연결

{적용 아이디어 설명}

```python
# 구체적인 적용 코드 예시
```

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-N | {어떻게 연결되는지} |

## 관련 실험
- EXP-00{N}: {실험명}
```

---

### 2-4단계: links.md 업데이트

`literature/links.md`의 `## 등록된 논문` 섹션에 아래 형식으로 추가:

```markdown
### {저자} et al. ({연도}) — {한 줄 제목}
- **출처**: {전체 저자}, {소속} — {학술대회} {연도}
- **파일**: `literature/papers/{파일명}.pdf`
- **관련 갭**: Gap-N, Gap-M
- **핵심 아이디어**: {한 줄 요약}
- **위키 파일**: `docs/wiki/{카테고리}/{파일명}.md`
```

알파벳 순서로 삽입하는 것을 권장한다.

---

### 2-5단계: INDEX.md 업데이트

`docs/wiki/INDEX.md`에서 두 곳을 수정한다.

**① 카테고리 기술 목록 테이블에 행 추가:**

```markdown
| **{기술명}** | [{파일명}.md]({카테고리}/{파일명}.md) | Gap-N, Gap-M | EXP-00N |
```

**② 문헌 → 기술 매핑 테이블에 행 추가:**

```markdown
| {저자} et al. ({연도}) | {핵심 기여 한 줄} | [{파일명}.md]({카테고리}/{파일명}.md) |
```

**③ 필요 시 갭-기술 대응표 업데이트:**

새 논문이 기존 갭에 새로운 접근법을 제시한다면 해당 갭 행의 "검토 중인 기술" 및 "관련 논문" 컬럼을 수정한다.

**④ 필요 시 실험 아이디어 백로그 추가:**

논문에서 실험 아이디어가 도출되면:
```markdown
| EXP-{N} | {아이디어 설명} | {출처 논문} | Gap-N | {난이도: 상/중/하} |
```

---

## 3. 파일명 작명 원칙

### PDF 파일
```
{제1저자 성 소문자}-{연도}-{제목 핵심 단어 2~4개 하이픈 연결}.pdf
```

| 올바른 예 | 잘못된 예 |
|---------|---------|
| `naumann-2025-data-scaling-laws-end-to-end.pdf` | `paper1.pdf` |
| `herd-2024-can-you-trust-your.pdf` | `Herd2024.pdf` |

### 위키 파일
```
{기술/주제 키워드 2~4개 하이픈 연결}.md
```

| 올바른 예 | 잘못된 예 |
|---------|---------|
| `mosaic-data-selection.md` | `dimlioglu2026.md` |
| `odd-coverage-framework.md` | `coverage.md` |

---

## 4. Gap 프레임워크

논문을 갭에 매핑할 때 참고:

| 갭 ID | 설명 | 관련 키워드 |
|-------|------|-----------|
| Gap-1 | 평가셋 편향 (키워드 기반 레이블) | relevance labeling, 불확실성, 커버리지 측정 |
| Gap-2 | Hybrid = Embedding (ODD 필터 무효) | 필터, 재랭킹, 소프트 가중치 |
| Gap-3 | ODD 커버리지 저조 (36~62%) | 씬 분류, ODD 태깅, 시나리오 생성 |
| Gap-4 | 분포 편향 (정상 과다, 희귀 과소) | 롱테일, 스케일링 법칙, 데이터 선택 |
| Gap-5 | 워밍업 미처리 (지연 왜곡) | 레이턴시, 캐시, 워밍업 |
| Gap-6 | 쿼리 다양성 부족 | 쿼리 증강, 동의어, 시나리오 유형 |

---

## 5. 실험과의 연결

위키 파일의 "관련 실험" 섹션에 실험 ID를 명시한다.  
실험이 아직 없다면 `experiments/experiment_log.md`에 백로그로 등록한다.

실험 로그 형식:
```markdown
## EXP-{N}: {실험명}
- **상태**: 백로그 / 진행중 / 완료
- **가설**: {검증하려는 내용}
- **출처 논문**: {저자 et al. 연도}
- **관련 갭**: Gap-N
```

---

## 6. 현재 등록 현황 (2026-06-02 기준)

| 논문 수 | 위키 파일 수 | 갭 커버리지 |
|--------|-----------|-----------|
| 14편 | 14개 | Gap-1~4, 6 (Gap-5 제외) |

### 등록된 논문 목록

| 저자 | 연도 | 핵심 주제 | 관련 갭 |
|------|------|---------|---------|
| Aasi et al. | 2024 | LLM 기반 OOD 시나리오 생성 | Gap-3, Gap-4 |
| Chodowiec et al. | 2026 | 4-Type ODD 커버리지 프레임워크 | Gap-1, Gap-3 |
| Dimlioglu et al. | 2026 | MOSAIC 스케일링 인식 데이터 선택 | Gap-4 |
| Herd & Burton | 2024 | Subjective Logic ML 메트릭 | Gap-1 |
| Naumann et al. | 2025 | E2E AV 스케일링 법칙 (NVIDIA) | Gap-4 |
| Rivera et al. | 2025 | CatPipe LVLM 씬 태깅 | Gap-3, Gap-6 |
| Schleiss et al. | 2022 | μODD 정량적 안전 검증 | Gap-1, Gap-3 |
| Song et al. | 2022 | TTC 시나리오 분포 모델 | Gap-4, Gap-6 |
| Xu et al. | 2025 | WOD-E2E 롱테일 데이터셋 | Gap-4, Gap-1 |
| Zheng et al. | 2025 | ONE-Drive 스케일링 법칙 | Gap-4, Gap-6 |

---

## 7. 빠른 참조 — 체크리스트

새 논문 추가 시 아래를 순서대로 완료한다:

- [ ] `literature/papers/`에 PDF 저장 (파일명 규칙 준수)
- [ ] 논문 내용 파악 (방법론, 수치, Gap 연결점)
- [ ] `docs/wiki/{카테고리}/{파일명}.md` 생성 (템플릿 사용)
- [ ] `literature/links.md` 업데이트 (## 등록된 논문 섹션)
- [ ] `docs/wiki/INDEX.md` 업데이트 (기술 목록 + 문헌 매핑)
- [ ] (선택) `experiments/experiment_log.md`에 실험 아이디어 백로그 추가
