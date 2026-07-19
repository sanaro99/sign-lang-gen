"""Name anonymization for retrieval embeddings (gap G8).

Zhang et al.'s appendix ("Additional Experiments") anonymizes train sentences —
names -> pronouns — BEFORE embedding, because proper names dominate embedding similarity:
un-anonymized retrieval fetches "sentences about the same person" instead of "sentences with
similar structure". Their result: top-50 anonymized examples (BLEU-4 ≈ 0.279) beat all ~1,474.
See docs/primary_source_findings.md §3. This module lets us reproduce/ablate that choice
(`retrieval.anonymize` in the config).

HEURISTIC, not NER: we replace mid-sentence capitalized tokens with "they" ("their" for
possessives). The paper does not state its method. Known limitations, accepted for the ablation
and documented here so nobody mistakes this for entity recognition:
  - sentence-initial names are missed (indistinguishable from ordinary capitalization);
  - non-name capitalized words not in the keep-list (e.g. place/product names) are replaced —
    which is actually close to the paper's intent (any proper noun hijacks similarity);
  - multi-word names become repeated pronouns ("John Smith" -> "they they").
Scope: applied to the ENGLISH side for EMBEDDING ONLY — both the indexed pool (build_index.py)
and the query (ExampleRetriever). The retrieved shots shown to the LLM keep their original text.
"""
from __future__ import annotations

import string

# Capitalized mid-sentence words that are not names in this project's data.
_KEEP = {
    "i", "i'm", "i'll", "i've", "i'd",
    "deaf", "asl", "english", "american", "america",
    "ok", "okay", "tv", "monday", "tuesday", "wednesday", "thursday", "friday",
    "saturday", "sunday", "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
}
_SENT_END = (".", "!", "?", ":", ";")


def anonymize_text(text: str) -> str:
    """Replace likely proper names with pronouns ("they" / possessive "their")."""
    out = []
    sentence_start = True
    for tok in text.split():
        core = tok.strip(string.punctuation)
        trailing = tok[len(tok.rstrip(string.punctuation)):] if core else ""
        leading = tok[: len(tok) - len(tok.lstrip(string.punctuation))] if core else ""
        is_name = (
            not sentence_start
            and core
            and core[0].isupper()
            and core.lower() not in _KEEP
        )
        if is_name:
            if core.endswith("'s") or core.endswith("’s"):
                out.append(f"{leading}their{trailing}")
            else:
                out.append(f"{leading}they{trailing}")
        else:
            out.append(tok)
        sentence_start = tok.endswith(_SENT_END)
    return " ".join(out)
