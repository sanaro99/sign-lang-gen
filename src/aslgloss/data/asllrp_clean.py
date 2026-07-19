"""Faithful Step-2 cleaning of ASLLRP gloss (Zhang et al. CHI 2025, Appendix B).

Implements the paper's recovered preprocessing recipe (docs/primary_source_findings.md §4)
on our own ASLLRP/NCSLGR loader output, closing gap G7 of the architecture map:

  Step 1  extract English + spliced annotations from SignStream XML  -> data/loaders.py
  Step 2  clean the gloss (THIS MODULE):
            - drop meaning-preserving annotations: repetition "+", one/two-hand markers
              ((2h)/(1h)), alternating-hands marker ((alt.))
            - normalize fingerspelling to letter-hyphenated form: fs-JOHN -> fs-J-O-H-N
            - unify spatial-location indices (locus letters -> canonical per-sentence i, j, k …)
            - drop classifier signs (DCL/LCL/SCL/BCL/ICL/BPCL/PCL — too sparse to learn)
  Step 3  word→gloss dictionary from the Sign Bank  -> BLOCKED on the Sign Bank download (G5)
  Step 4  human re-labeling of NMM gold on the test set  -> scripts/nmm_annotation.py (G3)

PROVISIONAL: written from our own summary of the paper's TeX (`docs/primary_source_findings.md`),
not from the verbatim extraction notes (gitignored `data/paper_src/EXTRACTION_NOTES.md`, which
live on the machine that mined the source). Two documented interpretations to verify there:
  (1) "unify spatial-location indices" is implemented as per-sentence canonical relabeling
      (first locus seen -> i, second -> j, …), preserving coreference structure but not the
      annotator's arbitrary letter choice;
  (2) trailing "+" is treated as the repetition marker and stripped; INTERNAL "+" (compounds,
      e.g. MOTHER+FATHER) is kept, since Appendix D lists compounding as meaningful.
Log any correction in docs/decision_log.md.

Direction note: this is DATA-PREP normalization (expands fs-JOHN -> fs-J-O-H-N, as the paper
does so dictionary entries align). It is the opposite direction from the *scoring* transform
`evaluation.metrics.normalize_real_asl`, which collapses notation to English-reachable tokens.
The two serve different stages; do not merge them.
"""
from __future__ import annotations

import re
import string

from .loaders import Example

# Classifier sign families per ASLLRP conventions (paper drops them in Step 2).
_CLASSIFIER_RE = re.compile(r'^(?:\((?:2h|1h|alt\.?)\))?(?:D|L|S|B|I|BP|P)CL\b')
# One-hand / two-hand / alternating-hands markers (meaning-preserving; dropped in Step 2).
_HAND_MARKER_RE = re.compile(r'\((?:2h|1h|alt\.?)\)')
# fs- followed by a plain word (not already letter-hyphenated single letters).
_FS_WORD_RE = re.compile(r'^fs-([A-Za-z]{2,})$')
# A locus suffix at token end: :i, :j, :i/j …
_LOCUS_RE = re.compile(r':([a-z](?:/[a-z])*)$')


def normalize_fingerspelling(token: str) -> str:
    """fs-JOHN -> fs-J-O-H-N (paper Step 2). Already-hyphenated fs-J-O-H-N passes through."""
    m = _FS_WORD_RE.match(token)
    if not m:
        return token
    word = m.group(1)
    return "fs-" + "-".join(word.upper())


def strip_hand_markers(token: str) -> str:
    """Remove (2h)/(1h)/(alt.) anywhere in the token — meaning-preserving articulation detail."""
    return _HAND_MARKER_RE.sub("", token)


def strip_repetition(token: str) -> str:
    """Strip trailing repetition '+'. Internal '+' (compounds) is meaningful and kept."""
    return token.rstrip("+")


def is_classifier(token: str) -> bool:
    """True for classifier/depiction signs (DCL:, BCL:, (2h)LCL: …) — dropped per Step 2."""
    return bool(_CLASSIFIER_RE.match(token))


def unify_spatial_indices(tokens: list[str]) -> list[str]:
    """Relabel locus letters to a canonical per-sentence sequence (first seen -> i, then j, k …).

    Keeps WHO corefers with whom (`IX-3p:i … SELF-3p:i` still share a locus) while removing the
    annotator's arbitrary choice of letters, so identical coreference structures compare equal.
    Interpretation of the paper's "unify spatial-location indices" — see module docstring.
    """
    canon: dict[str, str] = {}
    letters = string.ascii_lowercase[8:]  # i, j, k, …

    def _relabel(match: re.Match) -> str:
        parts = []
        for locus in match.group(1).split("/"):
            if locus not in canon:
                canon[locus] = letters[len(canon)] if len(canon) < len(letters) else locus
            parts.append(canon[locus])
        return ":" + "/".join(parts)

    return [_LOCUS_RE.sub(_relabel, t) for t in tokens]


def clean_gloss(gloss: str) -> str:
    """Apply the full Step-2 cleaning to one gloss string. Order matters:
    drop classifiers first (their markers would otherwise be half-stripped), then per-token
    normalization, then sentence-level locus unification."""
    tokens = [t for t in gloss.split() if not is_classifier(t)]
    tokens = [strip_repetition(strip_hand_markers(t)) for t in tokens]
    tokens = [normalize_fingerspelling(t) for t in tokens]
    tokens = unify_spatial_indices([t for t in tokens if t])
    return " ".join(tokens)


def clean_examples(examples: list[Example]) -> list[Example]:
    """Step-2-clean a batch of loader output, dropping pairs whose gloss cleans to empty.

    (The paper's 2,119 -> 1,843 reduction also involved manual curation we cannot replicate;
    we only drop what cleaning empties, and report our own counts.)
    """
    out = []
    for e in examples:
        g = clean_gloss(e.gloss)
        if g:
            out.append(Example(text=e.text, gloss=g, source=e.source,
                               doc_id=e.doc_id, sent_idx=e.sent_idx))
    return out
