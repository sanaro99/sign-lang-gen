"""Build a FAISS index over the English side of the example pool.

CONTRIBUTION 1. Pattern from Lewis et al. (RAG, NeurIPS 2020): embed -> index ->
top-k -> generate. Our twist: we retrieve WORKED EXAMPLES (English-gloss pairs),
not knowledge passages. Justified by Liu et al. (KATE, DeeLIO 2022): semantically
similar examples beat random/static ones, often by a lot.

KATE's practical advice, which we act on:
  - the embedding model matters -> test more than one (see configs/)
  - ordering and diversity are unexplored -> run the ordering ablation
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from ..data.loaders import Example


def embed(texts: list[str], model_name: str) -> np.ndarray:
    """Encode texts into L2-normalized float32 vectors so inner product == cosine similarity."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    vecs = model.encode(texts, batch_size=64, show_progress_bar=True,
                        convert_to_numpy=True, normalize_embeddings=True)
    return vecs.astype("float32")


def build_index(examples: list[Example], model_name: str, index_path: str | Path):
    """Embed the English side of the example pool, build a FAISS cosine index, and write it to disk."""
    import faiss

    vecs = embed([e.text for e in examples], model_name)
    index = faiss.IndexFlatIP(vecs.shape[1])  # cosine sim, vectors are normalized
    index.add(vecs)
    index_path = Path(index_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_path))
    return index


def load_index(index_path: str | Path):
    """Load a FAISS index previously written by `build_index`."""
    import faiss

    return faiss.read_index(str(index_path))
