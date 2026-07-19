"""Embed the example pool and build the FAISS index (CONTRIBUTION 1).

With `retrieval.anonymize: true` in the config, pool sentences are name-anonymized
(names -> pronouns, Zhang et al. appendix) before embedding. Point `retrieval.index_path`
at a DISTINCT file (e.g. example_pool.anon.faiss) so the two index variants coexist.
"""
import argparse
import dataclasses

from aslgloss.config import ExperimentConfig
from aslgloss.data.loaders import load_example_pool
from aslgloss.retrieval import build_index
from aslgloss.retrieval.anonymize import anonymize_text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()

    cfg = ExperimentConfig.from_yaml(args.config)
    pool = load_example_pool(cfg.retrieval.pool_path)
    if cfg.retrieval.anonymize:
        # Embed anonymized text; the pool file itself is untouched (shots keep original text).
        pool = [dataclasses.replace(e, text=anonymize_text(e.text)) for e in pool]
        print("Anonymization ON (names -> pronouns) for embeddings; "
              "ensure index_path differs from the un-anonymized index.")
    print(f"Embedding {len(pool)} examples with {cfg.retrieval.embedding_model} ...")
    build_index(pool, cfg.retrieval.embedding_model, cfg.retrieval.index_path)
    print(f"Index written to {cfg.retrieval.index_path}")
    print("KATE (Liu et al. 2022): the embedding model matters. Try at least one alternative "
          "(e.g. all-mpnet-base-v2) and record both in the results table.")


if __name__ == "__main__":
    main()
