#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# run_pipeline.sh — 전체 파이프라인 실행 (Phase 1+2+3 병렬, Phase 4 순차)
#
# 사용법:
#   # 포그라운드 (터미널에 출력 — 터미널 닫으면 중단됨)
#   bash scripts/run_pipeline.sh
#
#   # 백그라운드 (nohup — 터미널 닫아도 계속 실행됨)
#   nohup bash scripts/run_pipeline.sh > logs/pipeline_master.log 2>&1 &
#   echo "Pipeline PID: $!"
#
# 진행 확인:
#   tail -f logs/pipeline_master.log          # 전체 흐름
#   tail -f logs/phase2_embeddings.log        # Phase 2 세부 진행
#   cat  logs/pipeline_status.txt             # 완료 여부 요약
#   pgrep -af "avdata.phase"                  # 실행 중 프로세스 확인
#
# 의존성 그래프:
#   Phase 1 (BM25)  ─┐
#   Phase 2 (Embed) ─┼─ 모두 완료 후 → Phase 4 (분포 분석)
#   Phase 3 (ODD)   ─┘
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$REPO_ROOT/logs"
STATUS_FILE="$LOG_DIR/pipeline_status.txt"

mkdir -p "$LOG_DIR"

# ── 유틸 함수 ─────────────────────────────────────────────────────────────────

ts()  { date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(ts)] $*"; }

# 특정 Phase를 nohup 백그라운드로 실행하고 PID를 반환
# 사용법: PID=$(launch <log_name> <python_module> [args...])
launch() {
    local log_name="$1"; shift
    local log_file="$LOG_DIR/${log_name}.log"
    log "LAUNCH $log_name → $log_file"
    # 이미 실행 중이면 건너뜀
    if pgrep -f "avdata\.${log_name##phase?_}" > /dev/null 2>&1; then
        log "SKIP   $log_name — 이미 실행 중"
    fi
    nohup uv run python -m "$@" > "$log_file" 2>&1 &
    echo $!
}

# PID를 기다리며 성공/실패를 기록
# 사용법: await $PID <label>
await() {
    local pid="$1" label="$2"
    if wait "$pid"; then
        log "OK    $label"
        echo "$label: OK [$(ts)]" >> "$STATUS_FILE"
        return 0
    else
        local code=$?
        log "FAIL  $label (exit $code)"
        echo "$label: FAIL exit=$code [$(ts)]" >> "$STATUS_FILE"
        return $code
    fi
}

# ── 스킵 옵션 파싱 ────────────────────────────────────────────────────────────
SKIP_P1=false; SKIP_P2=false; SKIP_P3=false; SKIP_P4=false
EXP_ID=""
for arg in "$@"; do
    case "$arg" in
        --skip-bm25)    SKIP_P1=true ;;
        --skip-embed)   SKIP_P2=true ;;
        --skip-odd)     SKIP_P3=true ;;
        --skip-dist)    SKIP_P4=true ;;
        --exp-id=*)     EXP_ID="${arg#*=}" ;;
    esac
done

# ── 시작 ──────────────────────────────────────────────────────────────────────
> "$STATUS_FILE"
log "========================================="
log "Pipeline START"
log "  REPO : $REPO_ROOT"
log "  LOGS : $LOG_DIR"
[[ -n "$EXP_ID" ]] && log "  EXP  : $EXP_ID (완료 후 스냅샷)"
log "========================================="

# ── Phase 1 + 2 + 3: 병렬 실행 ───────────────────────────────────────────────
declare -a PIDS=()
declare -a LABELS=()

if [[ "$SKIP_P1" == false ]]; then
    PID1=$(launch "phase1_bm25" avdata.phase1.build_bm25)
    PIDS+=("$PID1"); LABELS+=("phase1_bm25")
else
    log "SKIP phase1_bm25 (--skip-bm25)"
fi

if [[ "$SKIP_P2" == false ]]; then
    PID2=$(launch "phase2_embeddings" avdata.phase2.build_embeddings --multi-gpu)
    PIDS+=("$PID2"); LABELS+=("phase2_embeddings")
else
    log "SKIP phase2_embeddings (--skip-embed)"
fi

if [[ "$SKIP_P3" == false ]]; then
    PID3=$(launch "phase3_odd" avdata.phase3.extract_odd_tags)
    PIDS+=("$PID3"); LABELS+=("phase3_odd")
else
    log "SKIP phase3_odd (--skip-odd)"
fi

log "-----------------------------------------"
log "Phase 1/2/3 PID: ${PIDS[*]:-없음 (모두 스킵)}"
log "완료 대기 중..."

# 병렬로 실행된 Phase들 모두 대기
FAILED=0
for i in "${!PIDS[@]}"; do
    await "${PIDS[$i]}" "${LABELS[$i]}" || FAILED=1
done

if [[ $FAILED -eq 1 ]]; then
    log "ERROR: Phase 1/2/3 중 실패 있음 — Phase 4 건너뜀"
    log "  로그 확인: tail -f $LOG_DIR/phase*.log"
    exit 1
fi

# ── Phase 4: 분포 분석 ────────────────────────────────────────────────────────
if [[ "$SKIP_P4" == false ]]; then
    PID4=$(launch "phase4_distribution" avdata.phase4.analyze_distribution)
    log "Phase 4 PID: $PID4"
    await "$PID4" "phase4_distribution" || { log "ERROR: Phase 4 실패"; exit 1; }
else
    log "SKIP phase4_distribution (--skip-dist)"
fi

# ── 스냅샷 (--exp-id 옵션 지정 시) ───────────────────────────────────────────
if [[ -n "$EXP_ID" ]]; then
    log "-----------------------------------------"
    log "스냅샷: $EXP_ID"
    bash "$REPO_ROOT/scripts/snapshot_artifacts.sh" "$EXP_ID" --activate \
        >> "$LOG_DIR/pipeline_master.log" 2>&1
    echo "snapshot: $EXP_ID [$(ts)]" >> "$STATUS_FILE"
fi

# ── 완료 ──────────────────────────────────────────────────────────────────────
log "========================================="
log "Pipeline COMPLETE"
log "  상태 파일: $STATUS_FILE"
log "  인덱스:    $REPO_ROOT/data/index/"
[[ -n "$EXP_ID" ]] && log "  아티팩트: $REPO_ROOT/data/artifacts/$EXP_ID/"
log "========================================="
echo "ALL: OK [$(ts)]" >> "$STATUS_FILE"
