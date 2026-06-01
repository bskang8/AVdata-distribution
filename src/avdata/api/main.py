"""
AVdata Search API

Run:
  uv run uvicorn avdata.api.main:app --host 0.0.0.0 --port 8000 --reload
  uv run python -m avdata.api

Docs:
  http://localhost:8000/docs   (Swagger UI)
  http://localhost:8000/redoc  (ReDoc)
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from avdata.api.deps import init_searcher
from avdata.api.models import HealthResponse
from avdata.api.routes import clips, odd, search
from avdata.config import ACTIVE_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_searcher()
    yield


app = FastAPI(
    title="AVdata Search API",
    description="Semantic search over autonomous vehicle driving clips (BM25 / Embedding / Hybrid).",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/v1/search",      tags=["search"])
app.include_router(clips.router,  prefix="/v1/clips",       tags=["clips"])
app.include_router(odd.router,    prefix="/v1/odd",         tags=["odd"])


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health():
    return HealthResponse(
        status="ok",
        indices={
            "bm25":      (ACTIVE_DIR / "bm25s_index").exists(),
            "faiss":     (ACTIVE_DIR / "hnsw.index").exists(),
            "odd_tags":  (ACTIVE_DIR / "odd_tags.json").exists(),
        },
    )
