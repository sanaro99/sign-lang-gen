"""Top-k retrieval of in-context examples. CONTRIBUTION 1."""
from __future__ import annotations

import random

from ..data.loaders import Example
from .index import load_index


class ExampleRetriever:
    def __init__(self, pool: list[Example], index_path: str, model_name: str,
                 k: int = 8, order: str = "similarity_desc"):
        from sentence_transformers import SentenceTransformer

        self.pool = pool
        self.index = load_index(index_path)
        self.encoder = SentenceTransformer(model_name)
        self.k = k
        self.order = order

    def retrieve(self, query: str) -> list[Example]:
        """Return the top-k example pairs most similar to `query` (cosine via a normalized-vector
        FAISS index). `order` reorders the hits for the KATE ablation: `similarity_desc` keeps
        most-similar first, `similarity_asc` reverses so the nearest sits last (closest to the query),
        `random` shuffles.
        """
        q = self.encoder.encode([query], convert_to_numpy=True,
                                normalize_embeddings=True).astype("float32")
        _scores, idx = self.index.search(q, self.k)
        hits = [self.pool[i] for i in idx[0] if i != -1]

        if self.order == "similarity_asc":
            # most-similar example placed LAST, i.e. nearest the query. Ablation, cf. KATE.
            hits = list(reversed(hits))
        elif self.order == "random":
            random.shuffle(hits)
        return hits
