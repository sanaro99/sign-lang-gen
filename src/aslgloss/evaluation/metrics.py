"""Quality, latency, and cost metrics.

Targets from Zhang et al. (CHI 2025):
    text -> gloss           BLEU-4 = 0.276
    non-manual detection    precision = 0.91, recall = 0.97

Their numbers were computed on their ASLLRP-derived split with their preprocessing.
Ours will NOT be directly comparable unless we replicate both. Report that plainly.
And remember: BLEU on ASLG-PC12 rewards matching RULE-GENERATED glosses, which is not
the same as ASL quality. This is why the error analysis exists.
"""
from __future__ import annotations

import statistics

import sacrebleu
from sklearn.metrics import precision_recall_fscore_support

from ..config import NMM_LABELS


def corpus_bleu(hypotheses: list[str], references: list[str]) -> float:
    """Corpus BLEU-4 (sacrebleu), rescaled to 0–1 to match the paper's 0.276 target."""
    return sacrebleu.corpus_bleu(hypotheses, [references]).score / 100.0


def nmm_scores(preds: list[dict], golds: list[dict]) -> dict:
    """Per-label and macro-averaged precision/recall/F1 for the non-manual markers.

    Targets from the paper: precision 0.91, recall 0.97. `preds`/`golds` are dicts keyed by
    NMM_LABELS with boolean values.
    """
    out = {}
    for label in NMM_LABELS:
        y_pred = [int(p.get(label, False)) for p in preds]
        y_true = [int(g.get(label, False)) for g in golds]
        p, r, f1, _ = precision_recall_fscore_support(
            y_true, y_pred, average="binary", zero_division=0
        )
        out[label] = {"precision": p, "recall": r, "f1": f1}
    out["macro"] = {
        m: statistics.mean(out[l][m] for l in NMM_LABELS)
        for m in ("precision", "recall", "f1")
    }
    return out


def summarize_run(results: list) -> dict:
    """Aggregate a run into headline metrics (BLEU-4, latency p50/p95, cost, avg tokens/shots, OOV rate).

    NOTE (known defect, see ROADMAP.md): this reads `r.reference`, which `GlossResult` does not
    expose, so it is currently unused/broken — `scripts/evaluate.py` performs the real aggregation.
    Fix or remove before relying on it.
    """
    lat = sorted(r.latency_s for r in results)
    return {
        "n": len(results),
        "bleu4": corpus_bleu([r.gloss for r in results], [r.reference for r in results]),
        "latency_p50_s": lat[len(lat) // 2] if lat else 0.0,
        "latency_p95_s": lat[int(len(lat) * 0.95)] if lat else 0.0,
        "total_cost_usd": sum(r.cost_usd for r in results),
        "avg_prompt_tokens": statistics.mean(r.prompt_tokens for r in results) if results else 0,
        "avg_shots": statistics.mean(r.n_shots for r in results) if results else 0,
        "oov_rate": sum(bool(r.oov) for r in results) / len(results) if results else 0.0,
    }
