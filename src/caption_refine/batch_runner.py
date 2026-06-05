"""
배치 처리 + 진행 추적.

사용법:
  # gap 클립 200개만 처리
  uv run python -m caption_refine.batch_runner --source gap

  # longtail 클립 처리
  uv run python -m caption_refine.batch_runner --source longtail

  # clip_id 목록 파일로 처리
  uv run python -m caption_refine.batch_runner --ids-file my_clips.json

  # 전체 처리 (limit으로 수 제한)
  uv run python -m caption_refine.batch_runner --source all --limit 1000

  # 병렬 수 조정
  uv run python -m caption_refine.batch_runner --source gap --concurrent 4
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import time
from pathlib import Path

from caption_refine.config import (
    DEFAULT_CONCURRENT,
    INDEX_DIR,
    PROGRESS_FILE,
    SANFLOW_GAP_PATH,
)
from caption_refine.cosmos_client import CosmosClient
from caption_refine.pipeline import ClipResult, process_clip

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ── 진행 상태 관리 ─────────────────────────────────────────────────────────────

def _load_progress() -> dict:
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    return {"done": [], "error": [], "skipped": []}


def _save_progress(state: dict) -> None:
    PROGRESS_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


# ── clip_id 소스 로더 ─────────────────────────────────────────────────────────

def _load_clip_ids(source: str, ids_file: str | None, limit: int | None) -> list[str]:
    if ids_file:
        ids = json.loads(Path(ids_file).read_text())
    elif source == "gap":
        gaps = json.loads(SANFLOW_GAP_PATH.read_text())
        ids = [g["clip_id"] for g in gaps]
    elif source == "longtail":
        longtail_path = INDEX_DIR / "longtail_clips.json"
        ids = json.loads(longtail_path.read_text())
    elif source == "all":
        clip_ids_path = INDEX_DIR / "clip_ids.json"
        ids = json.loads(clip_ids_path.read_text())
    else:
        raise ValueError(f"Unknown source: {source}")

    if limit:
        ids = ids[:limit]
    return ids


# ── 배치 실행 ─────────────────────────────────────────────────────────────────

async def _run_batch(
    clip_ids: list[str],
    max_concurrent: int,
    state: dict,
) -> None:
    already_done = set(state["done"]) | set(state["error"])
    pending = [cid for cid in clip_ids if cid not in already_done]

    log.info("Total: %d  |  Already done: %d  |  Pending: %d",
             len(clip_ids), len(already_done), len(pending))

    if not pending:
        log.info("Nothing to process.")
        return

    sem = asyncio.Semaphore(max_concurrent)
    client = CosmosClient()

    ok_count = err_count = 0
    t0 = time.monotonic()

    async def _process(clip_id: str) -> ClipResult:
        async with sem:
            return await process_clip(clip_id, client)

    tasks = [asyncio.create_task(_process(cid)) for cid in pending]

    for i, coro in enumerate(asyncio.as_completed(tasks), 1):
        result: ClipResult = await coro

        if result.status == "ok":
            state["done"].append(result.clip_id)
            ok_count += 1
        else:
            state["error"].append(result.clip_id)
            err_count += 1
            log.warning("FAILED [%s]: %s / %s", result.clip_id[:8], result.status, result.error)

        # 10개마다 진행 저장
        if i % 10 == 0:
            _save_progress(state)
            elapsed = time.monotonic() - t0
            rate = i / elapsed
            eta = (len(pending) - i) / rate if rate > 0 else 0
            log.info("Progress: %d/%d  ok=%d err=%d  rate=%.1f/min  ETA=%.0fmin",
                     i, len(pending), ok_count, err_count, rate * 60, eta / 60)

    _save_progress(state)
    await client.aclose()

    elapsed = time.monotonic() - t0
    log.info("─" * 60)
    log.info("Complete: %d ok / %d error / %.1f min", ok_count, err_count, elapsed / 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Caption refinement batch runner")
    parser.add_argument(
        "--source",
        choices=["gap", "longtail", "all"],
        default="gap",
        help="clip_id 소스 (default: gap)",
    )
    parser.add_argument("--ids-file", type=str, default=None,
                        help="clip_id 목록 JSON 파일 경로 (--source 무시)")
    parser.add_argument("--limit", type=int, default=None,
                        help="처리할 최대 클립 수")
    parser.add_argument("--concurrent", type=int, default=DEFAULT_CONCURRENT,
                        help=f"동시 처리 클립 수 (default: {DEFAULT_CONCURRENT})")
    parser.add_argument("--reset", action="store_true",
                        help="진행 상태 초기화 후 처음부터 재시작")
    args = parser.parse_args()

    clip_ids = _load_clip_ids(args.source, args.ids_file, args.limit)
    log.info("Loaded %d clip IDs from source=%s", len(clip_ids), args.ids_file or args.source)

    state = {} if args.reset else _load_progress()
    if args.reset:
        state = {"done": [], "error": [], "skipped": []}
        log.info("Progress state reset.")

    asyncio.run(_run_batch(clip_ids, args.concurrent, state))


if __name__ == "__main__":
    main()
