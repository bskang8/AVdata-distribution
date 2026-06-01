"""
Unified search interface — three strategies:
  A. BM25 (keyword)
  B. Embedding ANN (semantic)
  C. Hybrid layered: ODD tag filter → embedding re-rank

Usage:
  from avdata.search.searcher import Searcher
  s = Searcher()
  results = s.search("pedestrian crossing at night", method="hybrid",
                     odd_filter={"time_of_day": "night", "agent_type": "pedestrian"})
"""
import json
import time
from dataclasses import dataclass, field
from typing import Literal

import bm25s
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from avdata.config import ACTIVE_DIR, EMBED_MODEL_NAME, HNSW_EF_SEARCH

# 서비스는 data/active (심볼릭 링크) 에서 아티팩트를 읽는다.
# 실험 전환: ln -sfn artifacts/exp-NNN data/active
_BM25_INDEX_DIR = ACTIVE_DIR / "bm25s_index"
_CLIP_IDS_PATH  = ACTIVE_DIR / "clip_ids.json"
_FAISS_PATH     = ACTIVE_DIR / "hnsw.index"
_ODD_TAGS_PATH  = ACTIVE_DIR / "odd_tags.json"


@dataclass
class SearchResult:
    clip_id:  str
    score:    float
    rank:     int
    method:   str
    tags:     dict = field(default_factory=dict)


class Searcher:
    def __init__(self):
        self._bm25_data  = None
        self._emb_model  = None
        self._faiss_idx  = None
        self._clip_ids   = None
        self._odd_tags   = None
        self._id_to_idx  = None

    # ── Lazy loaders ──────────────────────────────────────────────────
    def _load_bm25(self):
        if self._bm25_data is None:
            retriever = bm25s.BM25.load(str(_BM25_INDEX_DIR), load_corpus=False)
            clip_ids  = json.loads(_CLIP_IDS_PATH.read_text())
            self._bm25_data = {"retriever": retriever, "clip_ids": clip_ids}

    def _load_faiss(self):
        if self._faiss_idx is None:
            self._faiss_idx = faiss.read_index(str(_FAISS_PATH))
            self._faiss_idx.hnsw.efSearch = HNSW_EF_SEARCH
            self._clip_ids  = json.loads(_CLIP_IDS_PATH.read_text())
            self._id_to_idx = {cid: i for i, cid in enumerate(self._clip_ids)}

    def _load_emb_model(self):
        if self._emb_model is None:
            self._emb_model = SentenceTransformer(EMBED_MODEL_NAME)

    def _load_odd(self):
        if self._odd_tags is None:
            self._odd_tags = json.loads(_ODD_TAGS_PATH.read_text())

    # ── Search methods ────────────────────────────────────────────────
    def search_bm25(self, query: str, top_k: int = 10) -> list[SearchResult]:
        self._load_bm25()
        query_tokens = bm25s.tokenize([query], stopwords="en", show_progress=False)
        results, scores = self._bm25_data["retriever"].retrieve(
            query_tokens, k=min(top_k, len(self._bm25_data["clip_ids"]))
        )
        clip_ids = self._bm25_data["clip_ids"]
        return [
            SearchResult(
                clip_id=clip_ids[results[0][rank]],
                score=float(scores[0][rank]),
                rank=rank + 1,
                method="bm25",
            )
            for rank in range(len(results[0]))
        ]

    def search_embedding(self, query: str, top_k: int = 10) -> list[SearchResult]:
        self._load_faiss()
        self._load_emb_model()
        q_emb  = self._emb_model.encode(
            [query], normalize_embeddings=True
        ).astype(np.float32)
        scores, indices = self._faiss_idx.search(q_emb, top_k)
        return [
            SearchResult(
                clip_id=self._clip_ids[idx],
                score=float(scores[0][rank]),
                rank=rank + 1,
                method="embedding",
            )
            for rank, idx in enumerate(indices[0])
        ]

    def search_hybrid(
        self,
        query: str,
        odd_filter: dict[str, str | list[str]] | None = None,
        top_k: int = 10,
    ) -> list[SearchResult]:
        """
        Level 1: ODD tag pre-filter (optional)
        Level 2: Embedding re-rank on filtered candidates
        Falls back to full embedding search if filter yields no candidates.
        """
        self._load_faiss()
        self._load_emb_model()
        self._load_odd()

        candidate_ids: list[str] = []

        if odd_filter:
            for cid, tags in self._odd_tags.items():
                if cid not in self._id_to_idx:
                    continue
                match = True
                for key, val in odd_filter.items():
                    tag_val = tags.get(key, "unknown")
                    if isinstance(val, list):
                        if isinstance(tag_val, list):
                            if not set(val) & set(tag_val):
                                match = False; break
                        elif tag_val not in val:
                            match = False; break
                    else:
                        if isinstance(tag_val, list):
                            if val not in tag_val:
                                match = False; break
                        elif tag_val != val:
                            match = False; break
                if match:
                    candidate_ids.append(cid)

        # Fallback to full search if filter is empty / too restrictive
        if not candidate_ids:
            return self.search_embedding(query, top_k)

        # Reconstruct embeddings for candidates and score
        cand_indices = [self._id_to_idx[cid] for cid in candidate_ids
                        if cid in self._id_to_idx]
        cand_embs    = np.vstack(
            [self._faiss_idx.reconstruct(i) for i in cand_indices]
        )
        q_emb = self._emb_model.encode(
            [query], normalize_embeddings=True
        ).astype(np.float32)
        sims  = (cand_embs @ q_emb.T).flatten()
        top_i = sims.argsort()[::-1][:top_k]

        return [
            SearchResult(
                clip_id=candidate_ids[i],
                score=float(sims[i]),
                rank=rank + 1,
                method="hybrid",
                tags=self._odd_tags.get(candidate_ids[i], {}),
            )
            for rank, i in enumerate(top_i)
        ]

    def search(
        self,
        query: str,
        method: Literal["bm25", "embedding", "hybrid"] = "hybrid",
        odd_filter: dict | None = None,
        top_k: int = 10,
    ) -> tuple[list[SearchResult], float]:
        """Returns (results, latency_ms)."""
        t0 = time.perf_counter()
        if method == "bm25":
            results = self.search_bm25(query, top_k)
        elif method == "embedding":
            results = self.search_embedding(query, top_k)
        else:
            results = self.search_hybrid(query, odd_filter, top_k)
        latency_ms = (time.perf_counter() - t0) * 1000
        return results, latency_ms
