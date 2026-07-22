# Phase 0 슬라이드 덱 — 구성과 렌더링

[Marp](https://marp.app/)(Markdown Presentation) 기반 덱. **소스는 `deck.md` 하나**, 나머지는 테마와 산출물이다.

## 파일 구성

| 파일 | 정체 | 편집? |
|---|---|---|
| `deck.md` | **소스**. Marp 마크다운. 프론트매터 + `---`로 나눈 슬라이드 + 인라인 `<style scoped>`/HTML | ✅ 내용은 여기서 |
| `theme.css` | **커스텀 테마** (`/* @theme disc */`). 전역 디자인 — 색·폰트·h1/h2·`.title`/`.section`/`.kpi` 등 | 디자인 바꿀 때만 |
| `deck.html` | **산출물**. `deck.md`를 marp-cli가 컴파일한 자립형 HTML(CSS·JS 인라인) | ❌ 직접 편집 금지(재렌더 시 덮어써짐) |
| `render.sh` | 렌더 스크립트 (아래) | — |
| `chrome/` | marp-cli가 pptx/pdf 렌더용으로 받은 헤드리스 크로미움 | — |

## 렌더링 흐름

```
  deck.md  ──┐
             ├─(marp-cli)──▶  deck.html
  theme.css ─┘
```

- `deck.md` 프론트매터의 `theme: disc`는 **이름만 가리킬 뿐, 파일을 등록하지 않는다.**
  marp-cli에 `--theme theme.css`를 넘겨야 그 CSS가 실제로 적용된다. 빼먹으면 Marp
  기본 테마로 렌더되어 타이틀 그라디언트·섹션 배경·kpi 카드 등이 빠진다.
- `deck.md`의 슬라이드 지시문이 테마 클래스와 연결된다:
  `<!-- _class: title -->` → `theme.css`의 `section.title { … }`.

## 사용법

```bash
./render.sh        # deck.md → deck.html
./render.sh pdf    # deck.html + deck.pdf
```

**수정 워크플로우:** `deck.md`(또는 디자인이면 `theme.css`) 수정 → `./render.sh` → `deck.html` 갱신.
`deck.html`은 산출물이라 직접 고치지 말 것.
