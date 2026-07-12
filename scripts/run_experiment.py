"""Run one experimental condition end to end and write a manifest.

Every run writes results/<run_id>/manifest.json with the git SHA, prompt hash, model
snapshot, config, seed, token counts, and cost. A result without a manifest is not a result.
"""
import argparse
import dataclasses
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from aslgloss.baseline import GlossGenerator, NMMClassifier, build_gloss_vocab
from aslgloss.config import PROMPTS, RESULTS, ExperimentConfig
from aslgloss.context import ParagraphContextBuffer
from aslgloss.data import build_paragraphs, load_example_pool
from aslgloss.evaluation import tag_errors
from aslgloss.llm import LLMClient
from aslgloss.retrieval import ExampleRetriever


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def _prompt_hash(name: str) -> str:
    return hashlib.sha256((PROMPTS / name).read_bytes()).hexdigest()[:12]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()

    cfg = ExperimentConfig.from_yaml(args.config)
    run_id = f"{cfg.name}_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
    out_dir = RESULTS / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    pool = load_example_pool("data/processed/example_pool.jsonl")
    test = load_example_pool("data/processed/test.jsonl")
    if cfg.n_examples:
        test = test[: cfg.n_examples]

    paragraphs = build_paragraphs(test, size=5)  # assigns doc_id / sent_idx in place
    vocab = build_gloss_vocab(pool) if cfg.constrain_vocab else None

    llm = LLMClient(**dataclasses.asdict(cfg.llm))

    retriever = None
    if cfg.retrieval.enabled:
        retriever = ExampleRetriever(
            pool=pool,
            index_path=cfg.retrieval.index_path,
            model_name=cfg.retrieval.embedding_model,
            k=cfg.retrieval.k,
            order=cfg.retrieval.order,
        )

    context_builder = None
    if cfg.context.enabled:
        context_builder = ParagraphContextBuffer(
            paragraphs,
            window_before=cfg.context.window_before,
            window_after=cfg.context.window_after,
            include_prior_glosses=cfg.context.include_prior_glosses,
        )

    generator = GlossGenerator(
        llm=llm,
        static_shots=pool[: cfg.static_shots] if not cfg.retrieval.enabled else None,
        retriever=retriever,
        context_builder=context_builder,
        vocab=vocab,
        prompt_file=cfg.gloss_prompt,
    )
    nmm = NMMClassifier(llm, prompt_file=cfg.nmm_prompt)

    rows, prior_glosses = [], {}
    for i, ex in enumerate(test, 1):
        g = generator.generate(ex, prior_glosses=prior_glosses)
        prior_glosses[(ex.doc_id, ex.sent_idx)] = g.gloss
        markers = nmm.classify(ex.text)
        rows.append({
            "source": ex.text,
            "reference": ex.gloss,
            "hypothesis": g.gloss,
            "nmm": {k: v for k, v in markers.items() if not k.startswith("_")},
            "prompt_tokens": g.prompt_tokens,
            "completion_tokens": g.completion_tokens,
            "latency_s": g.latency_s,
            "cost_usd": g.cost_usd + markers["_cost_usd"],
            "n_shots": g.n_shots,
            "oov": g.oov,
            "error_tags": tag_errors(ex.text, g.gloss, ex.gloss, g.context_used, g.oov),
        })
        if i % 25 == 0:
            print(f"  {i}/{len(test)}  running cost ${sum(r['cost_usd'] for r in rows):.3f}")

    (out_dir / "predictions.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows)
    )
    manifest = {
        "run_id": run_id,
        "git_sha": _git_sha(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "config": dataclasses.asdict(cfg),
        "gloss_prompt_hash": _prompt_hash(cfg.gloss_prompt),
        "nmm_prompt_hash": _prompt_hash(cfg.nmm_prompt),
        "n": len(rows),
        "total_cost_usd": sum(r["cost_usd"] for r in rows),
        "total_prompt_tokens": sum(r["prompt_tokens"] for r in rows),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\n{run_id}: {len(rows)} rows, ${manifest['total_cost_usd']:.3f} -> {out_dir}")


if __name__ == "__main__":
    main()
