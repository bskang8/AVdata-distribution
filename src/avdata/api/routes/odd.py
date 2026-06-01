"""ODD taxonomy and coverage endpoints, plus distribution longtail."""
import json

from fastapi import APIRouter, HTTPException

from avdata.api.models import LongtailResponse, OddCoverageItem, OddCoverageResponse, OddFieldInfo
from avdata.config import INDEX_DIR, ODD_FIELDS, ODD_TAGS_PATH, TAGS_DIR

router = APIRouter()

ODD_COVERAGE_PATH = TAGS_DIR / "odd_coverage.json"
LONGTAIL_PATH     = INDEX_DIR / "longtail_clips.json"


@router.get("/fields", response_model=OddFieldInfo)
def get_odd_fields():
    return OddFieldInfo(fields=ODD_FIELDS)


@router.get("/coverage", response_model=OddCoverageResponse)
def get_odd_coverage():
    if not ODD_COVERAGE_PATH.exists():
        raise HTTPException(status_code=404, detail="ODD coverage not built yet. Run phase3.")
    raw = json.loads(ODD_COVERAGE_PATH.read_text())
    coverage = {
        field: OddCoverageItem(
            coverage_pct=data["coverage_pct"],
            distribution=data["distribution"],
        )
        for field, data in raw.items()
    }
    return OddCoverageResponse(coverage=coverage)


@router.get("/distribution/longtail", response_model=LongtailResponse)
def get_longtail():
    if not LONGTAIL_PATH.exists():
        raise HTTPException(status_code=404, detail="Longtail data not built yet. Run phase4.")
    clip_ids = json.loads(LONGTAIL_PATH.read_text())
    return LongtailResponse(clip_ids=clip_ids, total=len(clip_ids))
