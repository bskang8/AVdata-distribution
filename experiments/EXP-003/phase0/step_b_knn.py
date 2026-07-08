"""0-A: FAISS k-NN Foundation — 이후 모든 서브 실험의 단일 계산 앵커"""

import numpy as np
import os
from config import K_KNN, OUTPUT_DIR
from utils import P, load_captions, already_done


def run(force=False):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if not force and already_done('0-B', 'knn_foundation.npz', 'embeddings.npy'):
        return
    print("[0-B] FAISS k-NN Foundation 시작")

    captions, clip_ids = load_captions()
    print(f"  캡션 로드: {len(captions):,}개")
    np.save(P('clip_ids.npy'), np.array(clip_ids, dtype=object))

    from sentence_transformers import SentenceTransformer
    import faiss

    model      = SentenceTransformer('BAAI/bge-m3')
    embeddings = model.encode(captions, batch_size=256, normalize_embeddings=True)
    embeddings_f32 = embeddings.astype(np.float32)

    index = faiss.IndexFlatIP(embeddings_f32.shape[1])
    index.add(embeddings_f32)
    sim, idx = index.search(embeddings_f32, K_KNN + 1)

    knn_sim = sim[:, 1:]   # (N, K_KNN) — 자기 자신 제외
    knn_idx = idx[:, 1:]

    np.savez(P('knn_foundation.npz'), knn_sim=knn_sim, knn_idx=knn_idx)
    np.save(P('embeddings.npy'), embeddings_f32)
    print(f"[0-B] 완료: knn_foundation.npz, embeddings.npy  "
          f"(N={len(embeddings_f32):,}, dim={embeddings_f32.shape[1]})")


if __name__ == '__main__':
    run()
