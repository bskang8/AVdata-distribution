"""GET /v1/clips/{clip_id} — clip detail endpoint."""
import json

from fastapi import APIRouter, HTTPException

from avdata.api.models import ClipDetail
from avdata.config import (
    CAPTION_SUFFIX,
    CAPTIONS_DIR,
    ODD_TAGS_PATH,
    VIDEO_SUFFIX,
    VIDEOS_DIR,
)

router = APIRouter()

_odd_tags: dict | None = None


def _get_odd_tags() -> dict:
    global _odd_tags
    if _odd_tags is None and ODD_TAGS_PATH.exists():
        _odd_tags = json.loads(ODD_TAGS_PATH.read_text())
    return _odd_tags or {}


@router.get("/{clip_id}", response_model=ClipDetail)
def get_clip(clip_id: str):
    cap_file   = CAPTIONS_DIR / (clip_id + CAPTION_SUFFIX)
    video_file = VIDEOS_DIR   / (clip_id + VIDEO_SUFFIX)

    if not cap_file.exists() and not video_file.exists():
        raise HTTPException(status_code=404, detail=f"Clip '{clip_id}' not found")

    caption    = cap_file.read_text(encoding="utf-8", errors="replace") if cap_file.exists() else None
    tags       = _get_odd_tags().get(clip_id, {})
    video_path = str(video_file) if video_file.exists() else None

    return ClipDetail(
        clip_id=clip_id,
        caption=caption,
        tags=tags,
        video_path=video_path,
    )
