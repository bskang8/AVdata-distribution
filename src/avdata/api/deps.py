"""Shared application state — Searcher singleton loaded at startup."""
from avdata.search.searcher import Searcher

_searcher: Searcher | None = None


def get_searcher() -> Searcher:
    if _searcher is None:
        raise RuntimeError("Searcher not initialised — did lifespan run?")
    return _searcher


def init_searcher() -> None:
    global _searcher
    _searcher = Searcher()
