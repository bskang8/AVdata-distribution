"""POST /v1/search — unified search endpoint."""
from fastapi import APIRouter, Depends, HTTPException

from avdata.api.deps import get_searcher
from avdata.api.models import SearchRequest, SearchResponse, SearchResultItem
from avdata.config import CAPTION_SUFFIX, CAPTIONS_DIR
from avdata.search.searcher import Searcher

router = APIRouter()


@router.post("", response_model=SearchResponse)
def search(req: SearchRequest, searcher: Searcher = Depends(get_searcher)):
    try:
        results, latency_ms = searcher.search(
            query=req.query,
            method=req.method,
            odd_filter=req.odd_filter,
            top_k=req.top_k,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

    items: list[SearchResultItem] = []
    for r in results:
        caption = None
        if req.include_caption:
            cap_file = CAPTIONS_DIR / (r.clip_id + CAPTION_SUFFIX)
            if cap_file.exists():
                caption = cap_file.read_text(encoding="utf-8", errors="replace")
        items.append(SearchResultItem(
            clip_id=r.clip_id,
            score=r.score,
            rank=r.rank,
            method=r.method,
            tags=r.tags,
            caption=caption,
        ))

    return SearchResponse(
        results=items,
        latency_ms=round(latency_ms, 2),
        total=len(items),
        query=req.query,
        method=req.method,
    )
