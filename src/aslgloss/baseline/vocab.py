"""Gloss vocabulary constraint.

Zhang et al. constrained Module 1's output to the vocabulary of their word-gloss
dictionary (3,915 entries derived from ASLLRP). We approximate that by building a
vocabulary from our example pool, and we FLAG out-of-vocabulary glosses rather than
silently dropping them — the paper handled 43 OOV words via fingerspelling, and OOV
handling is one of our error-analysis categories.
"""
from __future__ import annotations

from collections import Counter

from ..data.loaders import Example


def build_gloss_vocab(examples: list[Example], min_count: int = 1) -> set[str]:
    """Build the permitted gloss vocabulary from the example pool (our stand-in for the paper's
    3,915-entry word-gloss dictionary). Tokens appearing at least `min_count` times are kept."""
    counts = Counter(tok for e in examples for tok in e.gloss.split())
    return {tok for tok, c in counts.items() if c >= min_count}


def oov_tokens(gloss: str, vocab: set[str]) -> list[str]:
    """Tokens the model produced that are outside the permitted gloss vocabulary."""
    return [t for t in gloss.split() if t not in vocab and not t.startswith("fs-")]
