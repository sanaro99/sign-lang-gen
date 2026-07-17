"""NMM gold-label annotation workflow (replicates the paper's 4-researcher label correction).

The four NMM labels (yes/no-question, wh-question, conditional, negation) are properties of
the ENGLISH sentence, so gold labels need no ASLLRP data. Read docs/nmm_annotation_rubric.md
BEFORE filling a sheet.

Typical session (two annotators):

    python scripts/nmm_annotation.py sheets --n 100 --annotators 2
    # ... each annotator independently fills their CSV (0/1 per label, no peeking) ...
    python scripts/nmm_annotation.py agreement data/annotations/nmm_sheet_a1.csv \
                                               data/annotations/nmm_sheet_a2.csv
    # ... adjudicate the reported disagreements together into the emitted adjudication CSV ...
    python scripts/nmm_annotation.py merge data/annotations/nmm_sheet_a1.csv \
                                           data/annotations/nmm_sheet_a2.csv \
                                           --adjudicated data/annotations/nmm_adjudication.csv

Sheets contain corpus sentence text -> they live under gitignored data/, never committed.
"""
import argparse
import math
from pathlib import Path

from aslgloss.data import load_example_pool
from aslgloss.evaluation import (
    agreement_report, make_sheet_rows, merge_gold, read_sheet, save_gold, write_sheet,
)


def cmd_sheets(args):
    test = load_example_pool(args.test)
    if args.n:
        test = test[: args.n]
    rows = make_sheet_rows([ex.text for ex in test])
    out_dir = Path(args.out_dir)
    for i in range(1, args.annotators + 1):
        path = write_sheet(rows, out_dir / f"nmm_sheet_a{i}.csv")
        print(f"annotator {i}: {path}  ({len(rows)} sentences, labels blank)")
    print("\nFill each sheet INDEPENDENTLY per docs/nmm_annotation_rubric.md (0 or 1 per cell).")


def cmd_agreement(args):
    rows1, rows2 = read_sheet(args.sheet1), read_sheet(args.sheet2)
    rep = agreement_report(rows1, rows2)
    print(f"items in both sheets: {rep['n_common']}")
    for label, m in rep["labels"].items():
        kappa = "n/a (single class)" if math.isnan(m["kappa"]) else f"{m['kappa']:.3f}"
        print(f"  {label:16s}  kappa={kappa:>18s}  raw agreement={m['raw_agreement']:.3f}")
    if rep["disagreements"]:
        adj_rows = make_sheet_rows([d["source"] for d in rep["disagreements"]])
        path = write_sheet(adj_rows, Path(args.sheet1).parent / "nmm_adjudication.csv")
        print(f"\n{len(rep['disagreements'])} sentence(s) disagree -> adjudicate together in {path}")
        for d in rep["disagreements"]:
            print(f"  [{d['id']}] {', '.join(d['labels'])}: {d['source']}")
    else:
        print("\nno disagreements — merge directly (no --adjudicated needed).")


def cmd_merge(args):
    rows1, rows2 = read_sheet(args.sheet1), read_sheet(args.sheet2)
    adj = read_sheet(args.adjudicated) if args.adjudicated else None
    gold, unresolved = merge_gold(rows1, rows2, adj)
    if unresolved:
        for u in unresolved:
            print(f"UNRESOLVED [{u['id']}] {', '.join(u['labels'])}: {u['source']}")
        raise SystemExit(
            f"{len(unresolved)} disagreement(s) lack an adjudicated value; "
            "fill nmm_adjudication.csv and pass it via --adjudicated."
        )
    path = save_gold(gold, args.out)
    print(f"gold labels: {path}  ({len(gold)} sentences) — scripts/evaluate.py picks this up.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("sheets", help="emit blank annotation CSVs from the test split")
    s.add_argument("--test", default="data/processed/test.jsonl")
    s.add_argument("--n", type=int, default=None, help="first N test sentences (default: all)")
    s.add_argument("--annotators", type=int, default=2)
    s.add_argument("--out-dir", default="data/annotations/")
    s.set_defaults(func=cmd_sheets)

    s = sub.add_parser("agreement", help="Cohen's kappa + disagreement list for two filled sheets")
    s.add_argument("sheet1")
    s.add_argument("sheet2")
    s.set_defaults(func=cmd_agreement)

    s = sub.add_parser("merge", help="merge sheets (+ adjudication) into nmm_gold.jsonl")
    s.add_argument("sheet1")
    s.add_argument("sheet2")
    s.add_argument("--adjudicated", default=None, help="filled adjudication CSV for disagreements")
    s.add_argument("--out", default="data/processed/nmm_gold.jsonl")
    s.set_defaults(func=cmd_merge)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
