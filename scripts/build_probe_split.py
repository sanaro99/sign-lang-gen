"""Materialize the discourse probe set as a runnable split + a blank human-coding sheet (G1/M3).

Writes:
  data/processed/probes/test.jsonl   — every probe sentence as an Example row (doc_id = probe_id),
                                       consumable by run_experiment.py with a probes_* config.
  data/processed/probes/coding_sheet.csv
                                     — one row per TARGET sentence: probe_id, category, target,
                                       coder_question, correct_answer, plus empty columns per
                                       condition for the two blind coders (Week-9 pass).

The example pool is COPIED from an existing split (default: the ASLG-PC12 pool) because
run_experiment.py reads `<data_dir>/example_pool.jsonl` for static shots; probes themselves
have no reference glosses and never join a pool.
"""
import argparse
import csv
import shutil
from pathlib import Path

from aslgloss.data.probes import load_probes, probes_to_examples, target_keys
from aslgloss.data.loaders import save_example_pool


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probes", default=None, help="probe JSONL (default: probes/discourse_probes_v0.jsonl)")
    ap.add_argument("--out-dir", default="data/processed/probes")
    ap.add_argument("--conditions", nargs="*", default=["baseline", "context_only"],
                    help="condition columns to include in the coding sheet")
    ap.add_argument("--pool-from", default="data/processed/example_pool.jsonl",
                    help="existing example pool to copy in for static shots "
                         "(run_experiment.py reads <data_dir>/example_pool.jsonl)")
    args = ap.parse_args()

    probes = load_probes(args.probes) if args.probes else load_probes()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    examples = probes_to_examples(probes)
    save_example_pool(examples, out / "test.jsonl")
    targets = target_keys(probes)
    print(f"{len(probes)} probes -> {len(examples)} sentence rows "
          f"({len(targets)} targets) -> {out / 'test.jsonl'}")

    pool_src = Path(args.pool_from)
    if pool_src.exists():
        shutil.copy(pool_src, out / "example_pool.jsonl")
        print(f"Example pool copied from {pool_src} (for static shots)")
    else:
        print(f"WARNING: no pool at {pool_src} — build one first (make data), or pass --pool-from; "
              "run_experiment.py needs <data_dir>/example_pool.jsonl for shots.")

    sheet = out / "coding_sheet.csv"
    cols = ["probe_id", "category", "target_sentence", "coder_question", "correct_answer"]
    for cond in args.conditions:
        cols += [f"gloss_{cond}", f"coder1_{cond}", f"coder2_{cond}"]
    with sheet.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for p in probes:
            w.writerow([p["probe_id"], p["category"], p["sentences"][p["target_idx"]],
                        p["coder_question"], p["correct_answer"]]
                       + [""] * 3 * len(args.conditions))
    print(f"Blank coding sheet -> {sheet}")
    print("\nProtocol (probes/README.md): (1) TEAM REVIEW of v0 before any run; "
          "(2) run baseline + context_only on this split; (3) paste target glosses into the "
          "sheet; (4) two coders answer blind; (5) report per-category accuracy by condition + kappa.")


if __name__ == "__main__":
    main()
