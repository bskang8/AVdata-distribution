#!/usr/bin/env bash
# deck.md(소스) → deck.html(산출물) 렌더. theme.css 반드시 --theme로 명시해야 적용됨.
# 사용: ./render.sh          # deck.html 생성
#       ./render.sh pdf      # deck.pdf 도 추가 생성 (chrome 필요)
set -euo pipefail
cd "$(dirname "$0")"

npx --yes @marp-team/marp-cli@4.5.0 deck.md --theme theme.css --html -o deck.html

if [[ "${1:-}" == "pdf" ]]; then
  npx --yes @marp-team/marp-cli@4.5.0 deck.md --theme theme.css --pdf -o deck.pdf
fi

echo "OK → deck.html"
