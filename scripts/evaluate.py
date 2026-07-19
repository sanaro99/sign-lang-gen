"""Score every run and emit the Week 6 results table.

Reported per run: BLEU-4 with its parts (1-gram precision + brevity penalty — they discriminate
where BLEU-4 floors out), chrF, exact-match, ROUGE-L, latency, cost, and error tags. For
real-ASL datasets (ASLLRP-notation: ncslgr/asllrp) a SECONDARY "reachable-token" score pair
(bleu4_norm / chrf_norm) is added, computed after `normalize_real_asl` strips notation that is
un-generatable from English text (spatial loci, handedness, classifiers, prosody). Report it
alongside — never instead of — the raw score, and never against the paper's 0.276.

Condition-vs-baseline deltas ship with a paired bootstrap 95% CI and p-value (Koehn 2004),
computed on the intersection of test sentences shared with the same-dataset baseline run.
A delta without an interval is how the n=50 "RAG dominates" artifact happened.

NMM precision/recall (the paper's second metric: P 0.91 / R 0.97) is reported only when
human-adjudicated gold labels exist at --nmm-gold (produced by scripts/nmm_annotation.py;
see docs/nmm_annotation_rubric.md). Without gold labels the NMM columns are simply absent —
model self-predictions are never scored against themselves.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

import pandas as pd

from aslgloss.config import NMM_LABELS
from aslgloss.evaluation import (
    bleu_components, corpus_chrf, exact_match, load_gold, nmm_scores,
    normalize_real_asl, paired_bootstrap_bleu, rouge_l,
)

# Datasets whose references use real ASLLRP-family notation (vs. ASLG-PC12 pseudo-gloss).
REAL_ASL_DATASETS = {"ncslgr", "asllrp"}


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


def _significance_cols(rows: list[dict], run_preds: dict[int, list[dict]]) -> None:
    """Attach paired-bootstrap delta / CI / p-value vs. the same-dataset baseline, in place.

    Pairing is by source sentence (intersection), so runs on partially different slices are
    compared only on shared items; `sig_n` records how many. Baseline rows get blank cells.
    """
    by_dataset: dict[str, list[int]] = {}
    for i, row in enumerate(rows):
        by_dataset.setdefault(row["dataset"], []).append(i)

    for dataset, idxs in by_dataset.items():
        base_i = next((i for i in idxs if "baseline" in rows[i]["condition"]), None)
        if base_i is None:
            continue
        base = {" ".join(p["source"].split()): p for p in run_preds[base_i]}
        for i in idxs:
            if i == base_i:
                continue
            paired = [
                (base[k]["hypothesis"], p["hypothesis"], p["reference"])
                for p in run_preds[i]
                if (k := " ".join(p["source"].split())) in base
            ]
            if len(paired) < 10:
                continue
            hyps_a, hyps_b, refs = map(list, zip(*paired))
            r = paired_bootstrap_bleu(hyps_a, hyps_b, refs)
            rows[i]["delta_vs_baseline"] = round(r["delta"], 4)
            rows[i]["delta_ci95"] = f"[{r['ci_low']:+.4f},{r['ci_high']:+.4f}]"
            rows[i]["p_vs_baseline"] = round(r["p_value"], 3)
            rows[i]["sig_n"] = r["n"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", default="results/")
    ap.add_argument("--out", default="results/summary.csv")
    ap.add_argument("--nmm-gold", default="data/processed/nmm_gold.jsonl",
                    help="human-adjudicated NMM labels (JSONL); NMM P/R is skipped if absent")
    args = ap.parse_args()

    gold = load_gold(args.nmm_gold) if Path(args.nmm_gold).exists() else None

    rows, nmm_rows, run_preds = [], [], {}
    for run in sorted(Path(args.results_dir).glob("*/manifest.json")):
        manifest = json.loads(run.read_text())
        preds = [json.loads(ln) for ln in (run.parent / "predictions.jsonl").read_text().splitlines() if ln]
        lat = sorted(p["latency_s"] for p in preds)
        tags = Counter(t for p in preds for t in p["error_tags"])

        hyps = [p["hypothesis"] for p in preds]
        refs = [p["reference"] for p in preds]
        dataset = manifest["config"].get("dataset", "aslg_pc12")
        bc = bleu_components(hyps, refs)

        row = {
            "condition": manifest["config"]["name"],
            # Self-label the dataset so a preliminary run (e.g. real-ASL NCSLGR) can never sit in the
            # summary as a bare number next to the ASLG-PC12 baseline. BLEU across datasets/conventions
            # is NOT comparable — see docs/datasets.md.
            "dataset": dataset,
            "n": len(preds),
            "bleu4": round(bc["bleu4"], 4),
            "p1": round(bc["p1"], 1),
            "brevity": round(bc["brevity_penalty"], 3),
            "chrf": round(corpus_chrf(hyps, refs), 4),
            "exact_match": round(exact_match(hyps, refs), 4),
            "rougeL": round(rouge_l(hyps, refs), 4),
            "avg_prompt_tokens": round(sum(p["prompt_tokens"] for p in preds) / len(preds)),
            "latency_p50_s": round(lat[len(lat) // 2], 2),
            "latency_p95_s": round(lat[int(len(lat) * 0.95)], 2),
            "cost_usd": round(manifest["total_cost_usd"], 4),
            "oov_rate": round(sum(bool(p["oov"]) for p in preds) / len(preds), 3),
            **{f"err_{k}": v for k, v in tags.items()},
            "prompt_hash": manifest["gloss_prompt_hash"],
            "model": manifest["config"]["llm"]["model"],
        }
        if dataset in REAL_ASL_DATASETS:
            n_hyps = [normalize_real_asl(h) for h in hyps]
            n_refs = [normalize_real_asl(r) for r in refs]
            row["bleu4_norm"] = round(bleu_components(n_hyps, n_refs)["bleu4"], 4)
            row["chrf_norm"] = round(corpus_chrf(n_hyps, n_refs), 4)
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
        run_preds[len(rows)] = preds
        rows.append(row)

    _significance_cols(rows, run_preds)

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
        print("\nPer-label NMM scores (paper per-label targets: y/n-Q .98/.93, wh-Q .93/.98, "
              "negation .79/1.00, conditional .95/~.95):")
        print(nmm_df.to_string(index=False))
        print(f"-> {nmm_out}")

    print("\nReminders: (1) bleu4_norm/chrf_norm are the deliberately lossy reachable-token "
          "scores for real-ASL notation — report alongside raw, never against the paper's 0.276. "
          "(2) A delta with p_vs_baseline > 0.05 or a CI spanning zero is NOT a finding. "
          "(3) BLEU on ASLG-PC12 is measured against RULE-GENERATED glosses — not ASL quality; "
          "the error columns and the human coding pass are what the argument actually rests on.")


if __name__ == "__main__":
    main()
