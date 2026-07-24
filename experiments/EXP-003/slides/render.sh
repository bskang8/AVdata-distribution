#!/usr/bin/env bash
# <phase>/deck.md(소스) → <phase>/deck.html(산출물) 렌더. theme.css 반드시 --theme로 명시해야 적용됨.
# 사용: ./render.sh              # phase0/deck.html 생성 (기본 phase0)
#       ./render.sh phase1       # phase1/deck.html 생성
#       ./render.sh phase0 pdf   # deck.pdf 도 추가 생성 (chrome 필요)
set -euo pipefail
cd "$(dirname "$0")"

D="${1:-phase0}"
[[ -f "$D/deck.md" ]] || { echo "없음: $D/deck.md" >&2; exit 1; }

npx --yes @marp-team/marp-cli@4.5.0 "$D/deck.md" --theme theme.css --html -o "$D/deck.html"

if [[ "${2:-}" == "pdf" ]]; then
  npx --yes @marp-team/marp-cli@4.5.0 "$D/deck.md" --theme theme.css --pdf -o "$D/deck.pdf"
fi

echo "OK → $D/deck.html"
