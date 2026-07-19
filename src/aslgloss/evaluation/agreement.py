"""NMM gold-label annotation: sheets, inter-rater agreement, and gold merging.

Replicates the paper's ground-truth correction step (their Appendix, preprocessing Step 4):
the four NMM labels are properties of the ENGLISH sentence, hand-labeled by multiple
annotators and adjudicated. Workflow (driven by scripts/nmm_annotation.py):

    1. `make_sheet_rows` -> one blank CSV per annotator (identical items, blank labels).
    2. Humans fill 0/1 per label following docs/nmm_annotation_rubric.md. No peeking.
    3. `agreement_report` -> per-label Cohen's kappa + raw agreement + disagreement rows.
    4. Disagreements are adjudicated together (a third sheet with just those rows).
    5. `merge_gold` -> data/processed/nmm_gold.jsonl, consumed by scripts/evaluate.py.

Sheets contain ASLG-PC12 sentence text, so they live under gitignored data/ — never commit them.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from ..config import NMM_LABELS

SHEET_FIELDS = ["id", "source", *NMM_LABELS]


def _norm(text: str) -> str:
    """Whitespace-normalized sentence text, the join key everywhere in this module."""
    return " ".join(text.split())


def item_id(text: str) -> str:
    """Stable short id for a sentence (survives resorting / re-export of sheets)."""
    return hashlib.sha256(_norm(text).encode()).hexdigest()[:10]


def make_sheet_rows(texts: list[str]) -> list[dict]:
    """Blank annotation rows (label cells empty) for the given English sentences."""
    return [
        {"id": item_id(t), "source": _norm(t), **{label: "" for label in NMM_LABELS}}
        for t in texts
    ]


def write_sheet(rows: list[dict], path: str | Path) -> Path:
    """Write annotation rows as CSV (Excel/Sheets-friendly); returns the path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SHEET_FIELDS)
        w.writeheader()
        w.writerows(rows)
    return path


def read_sheet(path: str | Path, require_complete: bool = True) -> list[dict]:
    """Read a (filled) annotation sheet; label cells become bools.

    With `require_complete`, any cell not exactly 0/1 raises with the offending ids,
    so a half-filled sheet cannot silently produce gold labels.
    """
    rows, bad = [], []
    with Path(path).open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            row = {"id": r["id"], "source": r["source"]}
            for label in NMM_LABELS:
                v = (r.get(label) or "").strip()
                if v in ("0", "1"):
                    row[label] = v == "1"
                else:
                    row[label] = None
                    bad.append((r["id"], label, v))
            rows.append(row)
    if require_complete and bad:
        detail = ", ".join(f"{i}:{lab}={v!r}" for i, lab, v in bad[:10])
        raise ValueError(
            f"{path}: {len(bad)} label cell(s) not 0/1 ({detail}{'...' if len(bad) > 10 else ''})"
        )
    return rows


def cohen_kappa(a: list[bool], b: list[bool]) -> float:
    """Cohen's kappa for two binary label sequences.

    Implemented directly (not sklearn) so the edge case is explicit: when both raters
    use a single identical category throughout, chance agreement is 1 and kappa is
    undefined -> returns float('nan'); report raw agreement alongside it.
    """
    if len(a) != len(b) or not a:
        raise ValueError("need two equal-length, non-empty label sequences")
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum(
        (sum(x == c for x in a) / n) * (sum(y == c for y in b) / n)
        for c in (True, False)
    )
    if pe == 1.0:
        return float("nan")
    return (po - pe) / (1 - pe)


def agreement_report(rows1: list[dict], rows2: list[dict]) -> dict:
    """Per-label Cohen's kappa + raw agreement between two filled sheets, plus disagreements.

    Sheets are joined on `id`; items missing from either sheet are ignored (reported in
    'n_common'). Returns {'n_common', 'labels': {label: {kappa, raw_agreement}},
    'disagreements': [row dicts with both annotators' values]}.
    """
    by_id2 = {r["id"]: r for r in rows2}
    common = [(r, by_id2[r["id"]]) for r in rows1 if r["id"] in by_id2]
    report = {"n_common": len(common), "labels": {}, "disagreements": []}
    if not common:
        return report
    for label in NMM_LABELS:
        a = [r1[label] for r1, _ in common]
        b = [r2[label] for _, r2 in common]
        report["labels"][label] = {
            "kappa": cohen_kappa(a, b),
            "raw_agreement": sum(x == y for x, y in zip(a, b)) / len(a),
        }
    for r1, r2 in common:
        diff = [lab for lab in NMM_LABELS if r1[lab] != r2[lab]]
        if diff:
            report["disagreements"].append({
                "id": r1["id"],
                "source": r1["source"],
                "labels": diff,
                "annotator1": {lab: r1[lab] for lab in diff},
                "annotator2": {lab: r2[lab] for lab in diff},
            })
    return report


def merge_gold(
    rows1: list[dict],
    rows2: list[dict],
    adjudicated: list[dict] | None = None,
) -> tuple[list[dict], list[dict]]:
    """Merge two filled sheets (plus an optional adjudication sheet) into gold rows.

    Where annotators agree, the agreed value wins. Where they disagree, the value must
    come from `adjudicated` (same sheet format, only disputed items need rows). Returns
    (gold_rows, unresolved) — unresolved lists disagreements with no adjudicated value;
    callers must treat a non-empty unresolved as an error, mirroring the paper's
    discuss-until-resolved protocol.
    """
    by_id2 = {r["id"]: r for r in rows2}
    by_id_adj = {r["id"]: r for r in (adjudicated or [])}
    gold, unresolved = [], []
    for r1 in rows1:
        r2 = by_id2.get(r1["id"])
        if r2 is None:
            continue
        out = {"id": r1["id"], "source": r1["source"]}
        missing = []
        for label in NMM_LABELS:
            if r1[label] == r2[label]:
                out[label] = r1[label]
            else:
                adj = by_id_adj.get(r1["id"], {}).get(label)
                if adj is None:
                    missing.append(label)
                else:
                    out[label] = adj
        if missing:
            unresolved.append({"id": r1["id"], "source": r1["source"], "labels": missing})
        else:
            gold.append(out)
    return gold, unresolved


def save_gold(rows: list[dict], path: str | Path) -> Path:
    """Write gold rows as JSONL (the format scripts/evaluate.py consumes)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return path


def load_gold(path: str | Path) -> dict[str, dict]:
    """Load gold JSONL into {normalized source text: {label: bool}}."""
    out = {}
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                out[_norm(r["source"])] = {label: bool(r[label]) for label in NMM_LABELS}
    return out
