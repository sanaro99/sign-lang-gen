"""Score every run and emit the Week 6 results table."""
import argparse
import json
from collections import Counter
from pathlib import Path

import pandas as pd

from aslgloss.evaluation import corpus_bleu


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", default="results/")
    ap.add_argument("--out", default="results/summary.csv")
    args = ap.parse_args()

    rows = []
    for run in sorted(Path(args.results_dir).glob("*/manifest.json")):
        manifest = json.loads(run.read_text())
        preds = [json.loads(l) for l in (run.parent / "predictions.jsonl").read_text().splitlines() if l]
        lat = sorted(p["latency_s"] for p in preds)
        tags = Counter(t for p in preds for t in p["error_tags"])

        rows.append({
            "condition": manifest["config"]["name"],
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
        })

    df = pd.DataFrame(rows)
    df.to_csv(args.out, index=False)
    print(df.to_string(index=False))
    print(f"\n-> {args.out}")
    print("\nReminder: BLEU here is measured against RULE-GENERATED ASLG-PC12 glosses. "
          "It is not evidence of ASL quality. The error columns and the human coding pass "
          "are what the argument actually rests on.")


if __name__ == "__main__":
    main()
