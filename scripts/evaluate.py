"""Score every run and emit the Week 6 results table.

BLEU-4 is always reported. NMM precision/recall (the paper's second metric: P 0.91 / R 0.97)
is reported only when human-adjudicated gold labels exist at --nmm-gold
(produced by scripts/nmm_annotation.py; see docs/nmm_annotation_rubric.md). Without gold
labels the NMM columns are simply absent — model self-predictions are never scored
against themselves.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

import pandas as pd

from aslgloss.config import NMM_LABELS
from aslgloss.evaluation import corpus_bleu, load_gold, nmm_scores


def _nmm_row(preds: list[dict], gold: dict[str, dict]) -> tuple[dict, dict]:
    """Match a run's predictions to gold by sentence text; return (summary cols, per-label scores).

    Only items present in the gold file are scored; `nmm_n` says how many, so a partial
    annotation set can't masquerade as full-test-split coverage.
    """
    matched = [
        (p["nmm"], gold[" ".join(p["source"].split())])
        for p in preds
        if " ".join(p["source"].split()) in gold
    ]
    if not matched:
        return {"nmm_n": 0}, {}
    scores = nmm_scores([m[0] for m in matched], [m[1] for m in matched])
    cols = {
        "nmm_n": len(matched),
        "nmm_precision": round(scores["macro"]["precision"], 4),
        "nmm_recall": round(scores["macro"]["recall"], 4),
        "nmm_f1": round(scores["macro"]["f1"], 4),
    }
    return cols, scores


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", default="results/")
    ap.add_argument("--out", default="results/summary.csv")
    ap.add_argument("--nmm-gold", default="data/processed/nmm_gold.jsonl",
                    help="human-adjudicated NMM labels (JSONL); NMM P/R is skipped if absent")
    args = ap.parse_args()

    gold = load_gold(args.nmm_gold) if Path(args.nmm_gold).exists() else None

    rows, nmm_rows = [], []
    for run in sorted(Path(args.results_dir).glob("*/manifest.json")):
        manifest = json.loads(run.read_text())
        preds = [json.loads(l) for l in (run.parent / "predictions.jsonl").read_text().splitlines() if l]
        lat = sorted(p["latency_s"] for p in preds)
        tags = Counter(t for p in preds for t in p["error_tags"])

        row = {
            "condition": manifest["config"]["name"],
            # Self-label the dataset so a preliminary run (e.g. real-ASL NCSLGR) can never sit in the
            # summary as a bare number next to the ASLG-PC12 baseline. BLEU across datasets/conventions
            # is NOT comparable — see docs/datasets.md.
            "dataset": manifest["config"].get("dataset", "aslg_pc12"),
            "n": len(preds),
            "bleu4": round(corpus_bleu([p["hypothesis"] for p in preds],
                                       [p["reference"] for p in preds]), 4),
            "avg_prompt_tokens": round(sum(p["prompt_tokens"] for p in preds) / len(preds)),
            "latency_p50_s": round(lat[len(lat) // 2], 2),
            "latency_p95_s": round(lat[int(len(lat) * 0.95)], 2),
            "cost_usd": round(manifest["total_cost_usd"], 4),
            "oov_rate": round(sum(bool(p["oov"]) for p in preds) / len(preds), 3),
            **{f"err_{k}": v for k, v in tags.items()},
            "prompt_hash": manifest["gloss_prompt_hash"],
            "model": manifest["config"]["llm"]["model"],
        }
        if gold is not None:
            cols, scores = _nmm_row(preds, gold)
            row.update(cols)
            for label in NMM_LABELS:
                if label in scores:
                    nmm_rows.append({
                        "condition": manifest["config"]["name"],
                        "run_id": manifest["run_id"],
                        "label": label,
                        "n": cols["nmm_n"],
                        **{k: round(v, 4) for k, v in scores[label].items()},
                    })
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(args.out, index=False)
    print(df.to_string(index=False))
    print(f"\n-> {args.out}")

    if gold is None:
        print(f"\nNMM P/R not scored: no gold labels at {args.nmm_gold}. "
              "Build them with scripts/nmm_annotation.py (rubric: docs/nmm_annotation_rubric.md); "
              "paper targets are precision 0.91 / recall 0.97.")
    elif nmm_rows:
        nmm_out = Path(args.out).parent / "nmm_summary.csv"
        nmm_df = pd.DataFrame(nmm_rows)
        nmm_df.to_csv(nmm_out, index=False)
        print(f"\nPer-label NMM scores (paper per-label targets: y/n-Q .98/.93, wh-Q .93/.98, "
              f"negation .79/1.00, conditional .95/~.95):")
        print(nmm_df.to_string(index=False))
        print(f"-> {nmm_out}")

    print("\nReminder: BLEU here is measured against RULE-GENERATED ASLG-PC12 glosses. "
          "It is not evidence of ASL quality. The error columns and the human coding pass "
          "are what the argument actually rests on.")


if __name__ == "__main__":
    main()
