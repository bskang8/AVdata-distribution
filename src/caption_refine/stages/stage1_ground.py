"""
Stage 1 — Caption Grounding Check

기존 caption이 영상에 없는 내용(hallucination)을 담고 있는지 검증.
반환: {"grounded": [...], "hallucinated": [...], "missed": [...]}
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from caption_refine.cosmos_client import CosmosClient
from caption_refine.prompts import stage1_grounding

log = logging.getLogger(__name__)


@dataclass
class GroundingResult:
    grounded:     list[str] = field(default_factory=list)
    hallucinated: list[str] = field(default_factory=list)
    missed:       list[str] = field(default_factory=list)
    raw_response: str = ""

    def to_dict(self) -> dict:
        return {
            "grounded":     self.grounded,
            "hallucinated": self.hallucinated,
            "missed":       self.missed,
        }


async def run(
    client: CosmosClient,
    video_path: str | Path,
    existing_caption: str,
) -> GroundingResult:
    prompt = stage1_grounding(existing_caption)
    try:
        data = await client.chat_json(video_path, prompt)
    except Exception as exc:
        log.error("Stage 1 failed: %s", exc)
        return GroundingResult()

    if not isinstance(data, dict):
        log.warning("Stage 1: unexpected response type %s", type(data))
        return GroundingResult()

    return GroundingResult(
        grounded=data.get("grounded", []),
        hallucinated=data.get("hallucinated", []),
        missed=data.get("missed", []),
    )
