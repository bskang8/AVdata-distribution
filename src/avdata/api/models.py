"""Pydantic request/response models for the AVdata search API."""
from typing import Literal

from pydantic import BaseModel, Field


# ── Request models ─────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=512)
    method: Literal["bm25", "embedding", "hybrid"] = "hybrid"
    odd_filter: dict[str, str | list[str]] | None = None
    top_k: int = Field(default=10, ge=1, le=100)
    include_caption: bool = False


# ── Response models ────────────────────────────────────────────────────────────

class SearchResultItem(BaseModel):
    clip_id: str
    score: float
    rank: int
    method: str
    tags: dict = {}
    caption: str | None = None


class SearchResponse(BaseModel):
    results: list[SearchResultItem]
    latency_ms: float
    total: int
    query: str
    method: str


class ClipDetail(BaseModel):
    clip_id: str
    caption: str | None
    tags: dict
    video_path: str | None


class OddFieldInfo(BaseModel):
    fields: dict[str, list[str]]


class OddCoverageItem(BaseModel):
    coverage_pct: float
    distribution: dict[str, int]


class OddCoverageResponse(BaseModel):
    coverage: dict[str, OddCoverageItem]


class LongtailResponse(BaseModel):
    clip_ids: list[str]
    total: int


class HealthResponse(BaseModel):
    status: str
    indices: dict[str, bool]
