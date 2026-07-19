"""Derive a word->gloss dictionary from the ASLLRP corpus pairs.

This is a CORPUS-DERIVED APPROXIMATION of the paper's 3,915-entry ASLLRP Sign Bank
dictionary (which is a separate, gated download — see docs/faithful_reproduction_plan.md
Phase A4). It is NOT the Sign Bank. It is built only from the example POOL (never the test
set, to avoid leakage) by aligning English words to gloss tokens via a high-precision
normalization match: strip ASLLRP prefixes/affixes from each gloss token to a "core"
(fs-SENSORY -> sensory, COLLEGE -> college) and map the English word that matches it.

Output: data/processed/asllrp/gloss_dictionary.json
    {
      "entries": { "<english_word>": ["<GLOSS>", ...] },   # ranked by corpus count
      "vocab":   ["<GLOSS>", ...],                          # all gloss tokens seen, sorted
      "meta":    { ...provenance/coverage... }
    }

Also prints coverage of the held-out test set's reference gloss tokens, i.e. the ceiling
this dictionary could offer if injected as a prompt glossary.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

# ASLLRP gloss decorations to strip when reducing a gloss token to its lexical "core".
# (Spatial/reference/prosodic markers like IX-3p:i, SELF-3p:j, 5"pause" have NO English-word
#  core and are intentionally left uncovered — they are not text-derivable. See the report.)
_PREFIXES = ("fs-", "ns-", "#", "(1h)", "(2h)", "(2h)alt.", "DCL:", "BCL:", "ICL:", "SCL:")
_NONLEX = re.compile(r"^(IX|POSS|SELF|PART|DCL|BCL|ICL|SCL)\b|[:\"]|^\d")  # skip these tokens


def gloss_core(tok: str) -> str | None:
    """Reduce a gloss token to a lowercase lexical core, or None if it is non-lexical
    (spatial index, classifier, prosody, number-with-colon, etc.)."""
    t = tok
    for p in _PREFIXES:
        if t.startswith(p):
            t = t[len(p):]
    if not t or _NONLEX.search(t):
        return None
    # Compound/inflection markers: take the first sub-part (MOVING-ON-TO-NEXT -> moving).
    t = re.split(r"[+/]", t)[0]
    t = t.split("-")[0] if "-" in t and not t.startswith("-") else t
    core = re.sub(r"[^A-Za-z]", "", t).lower()
    return core or None


_WORD = re.compile(r"[A-Za-z]+")


def build(pool: list[dict]) -> tuple[dict, Counter]:
    """word -> Counter{gloss_token: count}, plus the global gloss-token frequency."""
    word2gloss: dict[str, Counter] = defaultdict(Counter)
    gloss_freq: Counter = Counter()
    for r in pool:
        english = {w.lower() for w in _WORD.findall(r["text"])}
        for tok in r["gloss"].split():
            gloss_freq[tok] += 1
            core = gloss_core(tok)
            if core and core in english:          # high-precision: gloss core is an English word here
                word2gloss[core][tok] += 1
    return word2gloss, gloss_freq


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data/processed/asllrp")
    ap.add_argument("--top-k", type=int, default=3, help="max gloss candidates kept per word")
    args = ap.parse_args()
    d = Path(args.data_dir)

    pool = [json.loads(ln) for ln in (d / "example_pool.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]
    test = [json.loads(ln) for ln in (d / "test.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]

    word2gloss, gloss_freq = build(pool)
    entries = {
        w: [g for g, _ in cnt.most_common(args.top_k)]
        for w, cnt in sorted(word2gloss.items())
    }
    vocab = sorted(gloss_freq)

    # Coverage of the held-out test references (the ceiling a prompt glossary could offer).
    covered_words = set(entries)
    test_words = Counter(w.lower() for r in test for w in _WORD.findall(r["text"]))
    word_cov = sum(c for w, c in test_words.items() if w in covered_words) / max(sum(test_words.values()), 1)

    ref_tokens = Counter(t for r in test for t in r["gloss"].split())
    ref_lex = {t: c for t, c in ref_tokens.items() if gloss_core(t)}      # lexical ref tokens only
    ref_lex_in_vocab = sum(c for t, c in ref_lex.items() if t in gloss_freq)
    lex_cov = ref_lex_in_vocab / max(sum(ref_lex.values()), 1)
    nonlex_share = 1 - sum(ref_lex.values()) / max(sum(ref_tokens.values()), 1)

    meta = {
        "source": "CORPUS-DERIVED APPROXIMATION (pool only) — NOT the ASLLRP Sign Bank",
        "pool_pairs": len(pool),
        "n_word_entries": len(entries),
        "n_gloss_vocab": len(vocab),
        "test_input_word_coverage": round(word_cov, 3),
        "test_ref_lexical_token_coverage": round(lex_cov, 3),
        "test_ref_nonlexical_share": round(nonlex_share, 3),
    }
    out = {"entries": entries, "vocab": vocab, "meta": meta}
    (d / "gloss_dictionary.json").write_text(json.dumps(out, indent=1), encoding="utf-8")

    print(json.dumps(meta, indent=2))
    print(f"\n-> {d / 'gloss_dictionary.json'}")
    print("\nInterpretation:")
    print(f"  * {meta['n_word_entries']} word->gloss entries derived from {len(pool)} pool pairs.")
    print(f"  * {word_cov:.0%} of test-input words have a dictionary entry (prompt-glossary reach).")
    print(f"  * {lex_cov:.0%} of *lexical* reference gloss tokens are in our vocab;")
    print(f"    but {nonlex_share:.0%} of reference tokens are NON-lexical (IX-/SELF-/prosody) and")
    print("    are not text-derivable from any dictionary — the BLEU ceiling this cannot lift.")


if __name__ == "__main__":
    main()
