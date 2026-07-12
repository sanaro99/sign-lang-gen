"""Embed the example pool and build the FAISS index (CONTRIBUTION 1)."""
import argparse

from aslgloss.config import ExperimentConfig
from aslgloss.data.loaders import load_example_pool
from aslgloss.retrieval import build_index


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()

    cfg = ExperimentConfig.from_yaml(args.config)
    pool = load_example_pool(cfg.retrieval.pool_path)
    print(f"Embedding {len(pool)} examples with {cfg.retrieval.embedding_model} ...")
    build_index(pool, cfg.retrieval.embedding_model, cfg.retrieval.index_path)
    print(f"Index written to {cfg.retrieval.index_path}")
    print("KATE (Liu et al. 2022): the embedding model matters. Try at least one alternative "
          "(e.g. all-mpnet-base-v2) and record both in the results table.")


if __name__ == "__main__":
    main()
