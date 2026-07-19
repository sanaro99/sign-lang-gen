"""Discourse probe set loading + conversion (gap G1 / milestone M3).

The probes live TRACKED in `probes/discourse_probes_v0.jsonl` (original English written for this
project — unlike `data/`, there is nothing license-encumbered about them). See probes/README.md
for the schema, the curation protocol, and the honesty notes. DRAFT v0 is unreviewed and
must be team-reviewed before any graded number rests on it.

Pipeline fit: `probes_to_examples()` emits standard `Example` rows with doc_id = probe_id, so
`build_paragraphs` keeps each probe as one real document and the ordinary `run_experiment.py`
machinery (manifests included) runs them under any condition. Only target sentences are scored —
by HUMAN CODERS answering `coder_question`, not by BLEU (there are no reference glosses here,
deliberately: constructing them ourselves would just encode our own assumptions).
"""
from __future__ import annotations

import json
from pathlib import Path

from ..config import ROOT
from .loaders import Example

PROBES_PATH = ROOT / "probes" / "discourse_probes_v0.jsonl"

CATEGORIES = {"pronoun_referent", "negation_scope", "topic_continuity", "ellipsis", "nmm_scope"}
_REQUIRED = {"probe_id", "category", "sentences", "target_idx",
             "phenomenon", "coder_question", "correct_answer"}


def load_probes(path: str | Path = PROBES_PATH) -> list[dict]:
    """Load and validate the probe file. Raises ValueError on any malformed probe —
    a silently broken probe set would corrupt the M3 evaluation."""
    probes, seen = [], set()
    for i, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        p = json.loads(line)
        missing = _REQUIRED - p.keys()
        if missing:
            raise ValueError(f"{path}:{i}: probe missing fields {sorted(missing)}")
        if p["category"] not in CATEGORIES:
            raise ValueError(f"{path}:{i}: unknown category {p['category']!r}")
        if not isinstance(p["sentences"], list) or len(p["sentences"]) < 2:
            raise ValueError(f"{path}:{i}: a probe needs >= 2 sentences (context + target)")
        if not (0 <= p["target_idx"] < len(p["sentences"])):
            raise ValueError(f"{path}:{i}: target_idx {p['target_idx']} out of range")
        if p["probe_id"] in seen:
            raise ValueError(f"{path}:{i}: duplicate probe_id {p['probe_id']!r}")
        seen.add(p["probe_id"])
        probes.append(p)
    if not probes:
        raise ValueError(f"{path}: no probes found")
    return probes


def probes_to_examples(probes: list[dict]) -> list[Example]:
    """Flatten probes into Example rows (doc_id = probe_id) for the standard runner.

    Every sentence becomes a row so the context condition has real neighbors; gloss is empty —
    the probe evaluation is human-coded, never BLEU-scored."""
    return [
        Example(text=s, gloss="", source="probe", doc_id=p["probe_id"], sent_idx=j)
        for p in probes
        for j, s in enumerate(p["sentences"])
    ]


def target_keys(probes: list[dict]) -> set[tuple[str, int]]:
    """(probe_id, target_idx) pairs — the only rows the coding pass looks at."""
    return {(p["probe_id"], p["target_idx"]) for p in probes}
