#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# snapshot_artifacts.sh — 실험 아티팩트 스냅샷 + 서비스 전환
#
# 사용법:
#   ./scripts/snapshot_artifacts.sh exp-002          # 스냅샷만 생성
#   ./scripts/snapshot_artifacts.sh exp-002 --activate  # 스냅샷 후 서비스 전환
#
# 동작:
#   1. data/index/ + data/tags/ 의 아티팩트를 data/artifacts/exp-NNN/ 에 하드링크
#   2. --activate 옵션 시 data/active 심볼릭 링크를 새 실험으로 교체
#   3. Streamlit 프로세스를 재시작해 캐시 초기화 (FastAPI는 재시작 불필요)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$REPO_ROOT/data"

# ── 인자 파싱 ─────────────────────────────────────────────────────────────────
EXP_ID="${1:-}"
ACTIVATE=false

if [[ -z "$EXP_ID" ]]; then
  echo "사용법: $0 <exp-id> [--activate]"
  echo "예시:   $0 exp-002 --activate"
  exit 1
fi

for arg in "${@:2}"; do
  [[ "$arg" == "--activate" ]] && ACTIVATE=true
done

ARTIFACT_DIR="$DATA_DIR/artifacts/$EXP_ID"

# ── 이미 존재하는 스냅샷 확인 ─────────────────────────────────────────────────
if [[ -d "$ARTIFACT_DIR" ]]; then
  echo "경고: $ARTIFACT_DIR 이미 존재합니다."
  read -rp "덮어쓰시겠습니까? (y/N): " confirm
  [[ "$confirm" != "y" && "$confirm" != "Y" ]] && echo "취소." && exit 0
  rm -rf "$ARTIFACT_DIR"
fi

# ── 스냅샷 생성 (하드링크 — 디스크 추가 사용 없음) ──────────────────────────
echo "→ 스냅샷 생성: $ARTIFACT_DIR"
mkdir -p "$ARTIFACT_DIR"

# BM25 인덱스 디렉토리
cp -al "$DATA_DIR/index/bm25s_index"    "$ARTIFACT_DIR/"
# 임베딩 + HNSW
cp -l  "$DATA_DIR/index/clip_ids.json"  "$ARTIFACT_DIR/"
cp -l  "$DATA_DIR/index/embeddings.npy" "$ARTIFACT_DIR/"
cp -l  "$DATA_DIR/index/hnsw.index"     "$ARTIFACT_DIR/"
# ODD 태그
cp -l  "$DATA_DIR/tags/odd_tags.json"   "$ARTIFACT_DIR/"

echo "✓ 스냅샷 완료: $(du -sh "$ARTIFACT_DIR" | cut -f1)"
echo "  포함 파일:"
ls -lh "$ARTIFACT_DIR" | awk '{print "    " $0}'

# ── 서비스 전환 ───────────────────────────────────────────────────────────────
if [[ "$ACTIVATE" == true ]]; then
  echo ""
  echo "→ 서비스 전환: data/active → artifacts/$EXP_ID"
  ln -sfn "artifacts/$EXP_ID" "$DATA_DIR/active"
  echo "✓ 심볼릭 링크 업데이트: $(readlink "$DATA_DIR/active")"

  # FastAPI: --reload 모드면 파일 변경 감지로 자동 재시작됨
  echo ""
  echo "→ FastAPI: 심볼릭 링크 변경 감지 후 자동 재로드 (--reload 모드)"

  # Streamlit: 캐시를 직접 비울 수 없으므로 프로세스 재시작
  STREAMLIT_PID=$(lsof -ti :8501 2>/dev/null || true)
  if [[ -n "$STREAMLIT_PID" ]]; then
    echo "→ Streamlit (PID $STREAMLIT_PID) 재시작 중..."
    kill "$STREAMLIT_PID" 2>/dev/null || true
    sleep 1
    nohup uv run streamlit run "$REPO_ROOT/src/avdata/ui/app.py" \
      --server.port 8501 \
      --server.fileWatcherType none \
      --server.headless true \
      > "$REPO_ROOT/logs/streamlit.log" 2>&1 &
    echo "✓ Streamlit 재시작 완료 (PID $!)"
  else
    echo "→ Streamlit 실행 중 아님 — 직접 시작하세요:"
    echo "  uv run streamlit run src/avdata/ui/app.py --server.port 8501"
  fi
fi

echo ""
echo "현재 active: $(readlink "$DATA_DIR/active")"
echo "완료."
