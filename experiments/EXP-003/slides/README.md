# EXP-003 슬라이드 덱 — 구성과 렌더링

[Marp](https://marp.app/)(Markdown Presentation) 기반. **phase별 덱은 `<phase>/deck.md` 하나씩**,
`theme.css`·`render.sh`는 전 phase가 공유하는 도구다.

## phase별 덱 (인덱스)

| 경로 | 내용 | 상태 |
|---|---|---|
| `phase0/deck.md` | Phase 0 — ODD 커버리지 · 임베딩 다양성 · 두 렌즈 상호보완 | ✅ |
| `phase1/deck.md` | Phase 1 — 획득함수 조립 · leave-out · 중간결론 | (예정) |

새 phase 덱 추가 = `<phase>/deck.md` 생성 → `./render.sh <phase>`. 공유 도구는 건드릴 필요 없음.

## 파일 구성

| 파일 | 정체 | 편집? |
|---|---|---|
| `<phase>/deck.md` | **소스**. Marp 마크다운. 프론트매터 + `---`로 나눈 슬라이드 + 인라인 `<style scoped>`/HTML | ✅ 내용은 여기서 |
| `<phase>/deck.html` | **산출물**. marp-cli가 컴파일한 자립형 HTML(CSS·JS 인라인) | ❌ 직접 편집 금지(재렌더 시 덮어써짐) |
| `theme.css` | **공유 커스텀 테마** (`/* @theme disc */`). 색·폰트·`.title`/`.section`/`.kpi` 등 | 디자인 바꿀 때만 |
| `render.sh` | **공유** 렌더 스크립트 (phase 인자) | — |
| `chrome/` | marp-cli가 pptx/pdf 렌더용으로 받은 헤드리스 크로미움 | — |
| `html_sample.html` · `ppt_sample.pptx` | 디자인 참고용 레퍼런스(소스 아님) | — |

## 렌더링 흐름

```
  <phase>/deck.md ──┐
                    ├─(marp-cli)──▶  <phase>/deck.html
  theme.css ────────┘
```

- `deck.md` 프론트매터의 `theme: disc`는 **이름만 가리킬 뿐, 파일을 등록하지 않는다.**
  marp-cli에 `--theme theme.css`를 넘겨야 그 CSS가 실제 적용된다(render.sh가 처리). 빼먹으면
  Marp 기본 테마로 렌더되어 타이틀 그라디언트·섹션 배경·kpi 카드 등이 빠진다.
- `deck.md`의 슬라이드 지시문이 테마 클래스와 연결된다:
  `<!-- _class: title -->` → `theme.css`의 `section.title { … }`.

## 사용법

```bash
./render.sh              # phase0/deck.md → phase0/deck.html (기본 phase0)
./render.sh phase1       # phase1/deck.md → phase1/deck.html
./render.sh phase0 pdf   # deck.html + deck.pdf
```

**수정 워크플로우:** `<phase>/deck.md`(또는 디자인이면 `theme.css`) 수정 → `./render.sh <phase>` →
`<phase>/deck.html` 갱신. `deck.html`은 산출물이라 직접 고치지 말 것.
