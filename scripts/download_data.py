"""Download ASLG-PC12 and materialize the example pool + evaluation split.

REMINDER: ASLG-PC12 glosses are rule-generated, not written by Deaf signers.
ASLLRP (the paper's real source) must be requested separately from the Rutgers DAI
and MUST NOT be committed to this repo.
"""
import argparse

from aslgloss.config import DATA_PROCESSED
from aslgloss.data.loaders import load_aslg_pc12, save_example_pool


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="aslg_pc12")
    ap.add_argument("--pool-size", type=int, default=20000, help="example pool for RAG retrieval")
    args = ap.parse_args()

    if args.dataset != "aslg_pc12":
        raise SystemExit("Only aslg_pc12 is wired up. ASLLRP requires DAI access; see ATTRIBUTION.md.")

    pool = load_aslg_pc12(split="train", limit=args.pool_size)
    path = save_example_pool(pool, DATA_PROCESSED / "example_pool.jsonl")
    print(f"Example pool: {len(pool)} pairs -> {path}")

    test = load_aslg_pc12(split="train", limit=None)[-1000:]  # ASLG-PC12 ships one split
    tpath = save_example_pool(test, DATA_PROCESSED / "test.jsonl")
    print(f"Held-out eval set: {len(test)} pairs -> {tpath}")
    print("\nNOTE: this is a naive tail split. Before week 6, define a proper split and record it "
          "in docs/decision_log.md. Also build the hand-curated discourse probe set — the auto "
          "paragraphs are pseudo-documents, not real discourse.")


if __name__ == "__main__":
    main()
