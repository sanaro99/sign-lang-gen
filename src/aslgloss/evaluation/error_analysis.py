"""Structured error analysis — the part BLEU cannot do.

Gap #3 in our lit review: BLEU-style scores on the synthetic ASLG-PC12 corpus say
nothing about whether pronouns or negation survive translation. These heuristics are a
TRIAGE layer to surface candidate errors for human coding. They are not the analysis.
Two team members code each flagged case independently; report inter-rater agreement.
"""
from __future__ import annotations

import re

ERROR_CATEGORIES = {
    "pronoun_referent": "Pronoun/referent lost or wrongly resolved across sentences",
    "negation_scope": "Negation dropped, added, or scoped to the wrong constituent",
    "gloss_ordering": "Tokens correct but ordered wrongly (Guo et al. found LLMs do this systematically)",
    "topic_comment": "Topic-comment structure flattened into English SVO word order",
    "oov_fingerspell": "Out-of-vocabulary gloss produced / fingerspelling mishandled",
    "context_leak": "Content from the surrounding context buffer leaked into the target gloss",
    "nmm_false_pos": "Non-manual marker asserted where none exists",
    "nmm_false_neg": "Non-manual marker missed",
}

NEG = re.compile(r"\b(not|no|never|none|nothing|cannot|n't|nobody)\b", re.I)
PRON = re.compile(r"\b(he|she|it|they|them|his|her|their|this|that|these|those)\b", re.I)


def tag_errors(source: str, hypothesis: str, reference: str,
               context: str | None = None, oov: list[str] | None = None) -> list[str]:
    """Heuristic triage. Flags candidates for human coding — never the final word."""
    tags: list[str] = []

    if NEG.search(source) and not NEG.search(hypothesis) and NEG.search(reference):
        tags.append("negation_scope")

    if PRON.search(source) and not PRON.search(hypothesis):
        tags.append("pronoun_referent")

    h, r = hypothesis.split(), reference.split()
    if h and r and sorted(h) == sorted(r) and h != r:
        tags.append("gloss_ordering")

    if oov:
        tags.append("oov_fingerspell")

    if context:
        ctx_only = set(context.lower().split()) - set(source.lower().split())
        if len(ctx_only & set(hypothesis.lower().split())) >= 2:
            tags.append("context_leak")

    return tags
