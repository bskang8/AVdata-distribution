"""
Stage 4 — Caption Refinement

Stage 1·3 결과를 바탕으로 정제된 caption 생성.
"""
from __future__ import annotations

import logging
from pathlib import Path

from caption_refine.cosmos_client import CosmosClient
from caption_refine.prompts import stage4_refine
from caption_refine.stages.stage1_ground import GroundingResult

log = logging.getLogger(__name__)


async def run(
    client: CosmosClient,
    video_path: str | Path,
    original_caption: str,
    grounding: GroundingResult,
    verified_odd: dict,
) -> str:
    prompt = stage4_refine(
        original_caption=original_caption,
        verified_odd=verified_odd,
        hallucinated=grounding.hallucinated,
        missed=grounding.missed,
    )
    try:
        caption = await client.chat_text(video_path, prompt)
        return caption.strip()
    except Exception as exc:
        log.error("Stage 4 failed: %s — returning original caption", exc)
        return original_caption
