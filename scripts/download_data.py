"""Download a corpus and build a documented, de-duplicated, leakage-filtered split.

Supported datasets (`--dataset`):
  - **aslg_pc12** — ~87.7k SYNTHETIC pairs (glosses rule-generated from POS-tagged English,
    NOT written by Deaf signers). Bring-up + cheap evaluation corpus. High BLEU here does not
    demonstrate real ASL quality.
  - **ncslgr** — ~1,875 REAL, Deaf-produced ASL pairs (Boston University / Neidle; the ASLLRP
    family). Real ASLLRP gloss conventions. Publicly mirrored, but treat like ASLLRP: local
    research/education only, gitignored, never committed. This is the real-ASL testbed for the
    Phase-B prompt — do NOT evaluate it with the ASLG-PC12-style prompt (notation mismatch scores
    near-zero on notation alone). See docs/datasets.md.

ASLLRP (the paper's real source) still requires Rutgers DAI access and MUST NOT be committed.

Split design (so RAG numbers are trustworthy — see docs/decision_log.md):
  - aslg_pc12: **test** = contiguous tail block (weak sentence adjacency preserved for the context
    conditions); **pool** = head of corpus. Both exact-deduplicated.
  - ncslgr: **document-level** split — whole stories are held out as test, the rest form the pool, so
    a document's sentences never straddle the two (stronger leakage guard) and within-document
    adjacency is preserved for the context conditions.
  - Both: **leakage filter** — any pool sentence whose embedding cosine similarity to *any* test
    sentence is >= --dedup-sim is dropped, so retrieval cannot hand the model a near-identical answer.
Everything removed is printed with counts.
"""
import argparse
import re
from pathlib import Path

from aslgloss.config import DATA_PROCESSED
from aslgloss.data.loaders import load_aslg_pc12, load_asllrp, load_ncslgr, save_example_pool


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


def _split_aslg_pc12(args):
    """Contiguous-tail test / head pool for the large synthetic corpus."""
    full = load_aslg_pc12(split="train", limit=None)
    print(f"Raw ASLG-PC12 rows: {len(full)}")
    test = _dedup_exact(full[-(args.test_size * 2):])[-args.test_size:]
    test_norms = {_norm(e.text) for e in test}
    head = _dedup_exact(full[: args.pool_size * 2])
    pool_candidates = [e for e in head if _norm(e.text) not in test_norms]
    return pool_candidates, test


def _split_ncslgr(args):
    """Document-level split: hold out whole stories as test so no document straddles pool/test."""
    full = _dedup_exact(load_ncslgr())
    print(f"NCSLGR real-ASL pairs (exact-deduped): {len(full)}")
    # Group by document, preserving order; last docs (up to ~test-size sentences) become test.
    docs: dict[str, list] = {}
    for e in full:
        docs.setdefault(e.doc_id, []).append(e)
    doc_ids = list(docs)
    test, test_docs = [], []
    for doc_id in reversed(doc_ids):
        if len(test) >= args.test_size:
            break
        test = docs[doc_id] + test
        test_docs.append(doc_id)
    test_doc_set = set(test_docs)
    pool_candidates = [e for e in full if e.doc_id not in test_doc_set]
    print(f"Held-out test documents: {len(test_docs)} stories -> {len(test)} sentences; "
          f"pool documents: {len(doc_ids) - len(test_docs)} stories -> {len(pool_candidates)} sentences")
    return pool_candidates, test


def _split_asllrp(args):
    """Document-level split for the ASLLRP DAI export (same rationale as NCSLGR).

    This is the paper's real source. NOTE: this produces the Step-1 pairs only — the faithful
    reproduction still needs the later preprocessing (clean to ~1,843; Sign Bank dictionary;
    the paper's own 80/20 split). See docs/faithful_reproduction_plan.md Phase A.
    """
    full = _dedup_exact(load_asllrp())
    print(f"ASLLRP real-ASL pairs (exact-deduped): {len(full)}")
    docs: dict[str, list] = {}
    for e in full:
        docs.setdefault(e.doc_id, []).append(e)
    doc_ids = list(docs)
    test, test_docs = [], []
    for doc_id in reversed(doc_ids):
        if len(test) >= args.test_size:
            break
        test = docs[doc_id] + test
        test_docs.append(doc_id)
    test_doc_set = set(test_docs)
    pool_candidates = [e for e in full if e.doc_id not in test_doc_set]
    print(f"Held-out test collections: {len(test_docs)} -> {len(test)} sentences; "
          f"pool collections: {len(doc_ids) - len(test_docs)} -> {len(pool_candidates)} sentences")
    return pool_candidates, test


_SPLITTERS = {
    "aslg_pc12": _split_aslg_pc12, "ncslgr": _split_ncslgr, "asllrp": _split_asllrp,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="aslg_pc12", choices=sorted(_SPLITTERS))
    ap.add_argument("--pool-size", type=int, default=20000, help="max example pool for RAG retrieval")
    ap.add_argument("--test-size", type=int, default=1000, help="held-out evaluation sentences")
    ap.add_argument("--dedup-sim", type=float, default=0.9,
                    help="drop pool items with cosine >= this to ANY test item (leakage guard)")
    ap.add_argument("--embedding-model", default="sentence-transformers/all-MiniLM-L6-v2")
    ap.add_argument("--out-dir", default=None,
                    help="where to write example_pool.jsonl/test.jsonl "
                         "(default: data/processed/ for aslg_pc12, data/processed/<dataset>/ otherwise, "
                         "so a second dataset never clobbers the primary split)")
    args = ap.parse_args()

    out_dir = Path(args.out_dir) if args.out_dir else (
        DATA_PROCESSED if args.dataset == "aslg_pc12" else DATA_PROCESSED / args.dataset)

    if args.dataset in {"ncslgr", "asllrp"} and args.test_size == 1000:
        args.test_size = 200  # these corpora are small; a 1000-sentence test would swallow them

    pool_candidates, test = _SPLITTERS[args.dataset](args)
    test_norms = {_norm(e.text) for e in test}
    pool_candidates = [e for e in pool_candidates if _norm(e.text) not in test_norms]
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

    out_dir.mkdir(parents=True, exist_ok=True)
    save_example_pool(pool, out_dir / "example_pool.jsonl")
    save_example_pool(test, out_dir / "test.jsonl")
    rel = out_dir.relative_to(DATA_PROCESSED.parent.parent)
    print(f"Example pool: {len(pool)} pairs -> {rel}/example_pool.jsonl")
    print(f"Held-out test: {len(test)} pairs -> {rel}/test.jsonl")
    print(f"\nDataset: {args.dataset}. Guarantees: exact duplicates removed; no pool sentence is "
          f">= {args.dedup_sim} cosine-similar to any test sentence. "
          f"{'Test = whole held-out documents (no cross-doc leakage).' if args.dataset in {'ncslgr', 'asllrp'} else 'Test is a contiguous block (weak discourse adjacency kept).'} "
          f"Rebuild the FAISS index after this (make index).")


if __name__ == "__main__":
    main()
