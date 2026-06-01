"""
Phase 2 — Extract sentence embeddings and build Faiss HNSW index.

Run:
  uv run python -m avdata.phase2.build_embeddings
  uv run python -m avdata.phase2.build_embeddings --limit 5000  # quick test
  uv run python -m avdata.phase2.build_embeddings --multi-gpu   # use both GPUs

Produces:
  data/index/embeddings.npy   (float32, shape [N, 1024])
  data/index/hnsw.index       (Faiss HNSW)
  data/index/clip_ids.json    (shared with Phase 1)

OOM fixes applied:
  1. Sort texts by length before encoding — prevents short texts being padded
     to the longest sequence in the batch (O(n²) attention).
  2. batch_size=32 — safer for very long captions (up to 5,400 tokens).
  3. fp16 loading — halves model memory (2.27GB → 1.1GB).
  4. --multi-gpu uses spawn-based workers that each load the model with fp16
     explicitly, instead of the deprecated encode_multi_process which ignored
     the parent's torch_dtype setting and reloaded in fp32.
"""
import argparse
import json
import multiprocessing as mp
import os

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from avdata.config import (
    CAPTION_SUFFIX,
    CAPTIONS_DIR,
    CLIP_IDS_PATH,
    EMBED_BATCH_SIZE,
    EMBED_DIM,
    EMBED_MODEL_NAME,
    EMBEDDINGS_NPY_PATH,
    FAISS_INDEX_PATH,
    HNSW_EF_CONSTRUCTION,
    HNSW_M,
)


def _gpu_worker(gpu_id: int, texts: list[str], batch_size: int, out_path: str) -> None:
    """Spawn-safe worker: loads model with fp16 explicitly and saves results."""
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    model = SentenceTransformer(
        EMBED_MODEL_NAME,
        model_kwargs={"torch_dtype": "float16"},
        device=f"cuda:{gpu_id}",
    )
    embs = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=(gpu_id == 0),
        normalize_embeddings=True,
        convert_to_numpy=True,
    ).astype(np.float32)
    np.save(out_path, embs)


def build(limit: int | None = None, multi_gpu: bool = False):
    caption_files = sorted(CAPTIONS_DIR.glob(f"*{CAPTION_SUFFIX}"))
    if limit:
        caption_files = caption_files[:limit]

    clip_ids = [f.name[: -len(CAPTION_SUFFIX)] for f in caption_files]
    texts    = [f.read_text(encoding="utf-8", errors="replace")
                for f in tqdm(caption_files, desc="Reading captions")]

    # Sort by character length to group similar-length texts in the same batch.
    # Prevents a single long caption (5,400 tokens) from padding an entire batch
    # of 32–64 sequences, which would cause O(n²) attention OOM.
    order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
    sorted_texts = [texts[i] for i in order]
    inv_order = np.argsort(order)  # inverse permutation to restore original order

    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

    if multi_gpu:
        import torch
        n_gpu = torch.cuda.device_count()
        print(f"Multi-GPU mode: {n_gpu} GPUs  (each loads model in fp16 independently)")
        splits = np.array_split(np.arange(len(sorted_texts)), n_gpu)
        tmp_paths = [str(EMBEDDINGS_NPY_PATH) + f".gpu{i}.tmp.npy" for i in range(n_gpu)]

        ctx = mp.get_context("spawn")
        procs = []
        for gpu_id, indices in enumerate(splits):
            chunk = [sorted_texts[int(j)] for j in indices]
            print(f"  GPU {gpu_id}: {len(chunk):,} texts  (batch={EMBED_BATCH_SIZE})")
            p = ctx.Process(target=_gpu_worker,
                            args=(gpu_id, chunk, EMBED_BATCH_SIZE, tmp_paths[gpu_id]))
            p.start()
            procs.append(p)

        for gpu_id, p in enumerate(procs):
            p.join()
            if p.exitcode != 0:
                raise RuntimeError(f"GPU {gpu_id} worker exited with code {p.exitcode}")

        parts = [np.load(tmp_paths[i]) for i in range(n_gpu)]
        for tmp in tmp_paths:
            os.remove(tmp)
        embeddings_sorted = np.vstack(parts)
    else:
        print(f"Loading model: {EMBED_MODEL_NAME}")
        model = SentenceTransformer(EMBED_MODEL_NAME, model_kwargs={"torch_dtype": "float16"})
        print(f"Encoding {len(sorted_texts):,} captions (batch={EMBED_BATCH_SIZE}) …")
        embeddings_sorted = model.encode(
            sorted_texts,
            batch_size=EMBED_BATCH_SIZE,
            show_progress_bar=True,
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).astype(np.float32)

    # Restore original clip_ids order
    embeddings = embeddings_sorted[inv_order]

    # ── Save raw embeddings ────────────────────────────────────────────
    EMBEDDINGS_NPY_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.save(EMBEDDINGS_NPY_PATH, embeddings)
    print(f"  Embeddings  → {EMBEDDINGS_NPY_PATH}  shape={embeddings.shape}")

    # ── Build Faiss HNSW index ─────────────────────────────────────────
    dim   = embeddings.shape[1]
    assert dim == EMBED_DIM, f"Expected dim={EMBED_DIM}, got {dim}"
    index = faiss.IndexHNSWFlat(dim, HNSW_M)
    index.hnsw.efConstruction = HNSW_EF_CONSTRUCTION
    index.add(embeddings)

    faiss.write_index(index, str(FAISS_INDEX_PATH))
    print(f"  Faiss index → {FAISS_INDEX_PATH}  ntotal={index.ntotal:,}")

    # ── Save clip ID list (overwrite Phase 1's if different subset) ────
    CLIP_IDS_PATH.write_text(json.dumps(clip_ids, ensure_ascii=False))
    print(f"  Clip IDs    → {CLIP_IDS_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--multi-gpu", action="store_true",
                        help="Distribute encoding across all available CUDA GPUs")
    args = parser.parse_args()
    build(limit=args.limit, multi_gpu=args.multi_gpu)
