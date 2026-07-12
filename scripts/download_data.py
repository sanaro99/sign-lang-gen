"""Download ASLG-PC12 and build a documented, de-duplicated, leakage-filtered split.

REMINDER: ASLG-PC12 glosses are rule-generated, not written by Deaf signers.
ASLLRP (the paper's real source) must be requested separately from the Rutgers DAI and MUST NOT be
committed to this repo.

Split design (so RAG numbers are trustworthy — see docs/decision_log.md):
  - **test set**: a CONTIGUOUS block from the end of the corpus, so the weak sentence-to-sentence
    adjacency the context conditions rely on is preserved. Exact duplicates removed.
  - **example pool** (for RAG retrieval): taken from the start of the corpus, exact-deduplicated,
    then **leakage-filtered** — any pool sentence whose embedding cosine similarity to *any* test
    sentence is >= --dedup-sim is dropped, so retrieval cannot hand the model a near-identical
    "answer" to copy. (We saw this leakage live: retrieval returned a near-duplicate of the input.)
Everything removed is printed with counts.
"""
import argparse
import re

from aslgloss.config import DATA_PROCESSED
from aslgloss.data.loaders import load_aslg_pc12, save_example_pool


def _norm(text: str) -> str:
    """Normalization key for exact-duplicate detection: lowercase, collapse whitespace, strip."""
    return re.sub(r"\s+", " ", text.strip().lower())


def _dedup_exact(examples):
    """Drop exact-duplicate sentences (by normalized text), preserving first-seen order."""
    seen, out = set(), []
    for e in examples:
        k = _norm(e.text)
        if k and k not in seen:
            seen.add(k)
            out.append(e)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="aslg_pc12")
    ap.add_argument("--pool-size", type=int, default=20000, help="example pool for RAG retrieval")
    ap.add_argument("--test-size", type=int, default=1000, help="held-out evaluation sentences")
    ap.add_argument("--dedup-sim", type=float, default=0.9,
                    help="drop pool items with cosine >= this to ANY test item (leakage guard)")
    ap.add_argument("--embedding-model", default="sentence-transformers/all-MiniLM-L6-v2")
    args = ap.parse_args()

    if args.dataset != "aslg_pc12":
        raise SystemExit("Only aslg_pc12 is wired up. ASLLRP requires DAI access; see ATTRIBUTION.md.")

    full = load_aslg_pc12(split="train", limit=None)
    print(f"Raw ASLG-PC12 rows: {len(full)}")

    # Test: contiguous tail block, exact-deduplicated (adjacency preserved for context conditions).
    test = _dedup_exact(full[-(args.test_size * 2):])[-args.test_size:]
    test_norms = {_norm(e.text) for e in test}

    # Pool candidates: head of corpus, exact-deduplicated, minus anything already in the test set.
    head = _dedup_exact(full[: args.pool_size * 2])
    pool_candidates = [e for e in head if _norm(e.text) not in test_norms]
    print(f"After exact-dedup: {len(pool_candidates)} pool candidates, {len(test)} test sentences")

    # Leakage guard: embed both sides and drop pool items too similar to ANY test item.
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(args.embedding_model)
    enc = lambda xs: model.encode(  # noqa: E731
        xs, convert_to_numpy=True, normalize_embeddings=True, batch_size=64, show_progress_bar=True
    ).astype("float32")
    pv = enc([e.text for e in pool_candidates])
    tv = enc([e.text for e in test])
    max_sim = (pv @ tv.T).max(axis=1)  # cosine to nearest test item (vectors are normalized)
    kept = [e for e, s in zip(pool_candidates, max_sim) if s < args.dedup_sim]
    dropped = len(pool_candidates) - len(kept)
    pool = kept[: args.pool_size]
    print(f"Leakage guard (cosine >= {args.dedup_sim}): dropped {dropped} near-duplicate candidates")

    save_example_pool(pool, DATA_PROCESSED / "example_pool.jsonl")
    save_example_pool(test, DATA_PROCESSED / "test.jsonl")
    print(f"Example pool: {len(pool)} pairs -> data/processed/example_pool.jsonl")
    print(f"Held-out test: {len(test)} pairs -> data/processed/test.jsonl")
    print(f"\nGuarantees: exact duplicates removed; no pool sentence is >= {args.dedup_sim} cosine-"
          f"similar to any test sentence. Test is a contiguous block (weak discourse adjacency kept). "
          f"Rebuild the FAISS index after this (make index).")


if __name__ == "__main__":
    main()
