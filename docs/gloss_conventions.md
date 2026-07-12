# Gloss Conventions

The written rules our system's gloss output is supposed to follow, and why they have to match the
dataset's rules exactly.

> **Status:** several rules below are marked **PROVISIONAL** — they state our intended convention but
> have **not yet been verified against ASLG-PC12's actual tokenization** on a real sample. Verifying
> and finalizing this file is a Week-6 blocker (see `ROADMAP.md` and `docs/decision_log.md`).

---

## In plain words

**"Gloss"** is a way of writing down signs using CAPITALIZED English words — one word per sign — in
the order a signer would actually sign them. It is *not* English. For example, the English sentence
*"I do not like coffee"* might be glossed `COFFEE ME LIKE NOT`.

Here's the catch that makes this document necessary: we grade our system by comparing its gloss to a
"correct" gloss from a dataset, using a score called **BLEU** that basically counts matching words in
matching order. If the dataset writes a sign one way (say `IX-1`) and our system writes it another
way (say `ME`), BLEU marks it wrong **even when the meaning is identical** — purely because the
spellings differ. So before any score means anything, our writing rules have to line up with the
dataset's writing rules. That alignment is what this file pins down.

---

## Why conventions must match the reference corpus

BLEU-4 (via `sacrebleu`, in `src/aslgloss/evaluation/metrics.py`) is a surface n-gram overlap metric.
It rewards **string-identical tokens in the same order**. Two glosses that are semantically identical
but tokenized differently (`DON'T` vs `NOT`; `IX` vs `IX-1`; `COFFEE` vs `coffee`) score as
mismatches. Therefore:

> **Our gloss conventions must match ASLG-PC12's tokenization, or the BLEU comparison is meaningless.**
> This is open question #4 in `docs/decision_log.md`.

The model is steered toward these conventions two ways: (1) the instruction block in
`prompts/baseline_gloss.md`, and (2) the in-context examples themselves (the model is told to *"match
the style, tokenization, and conventions of the examples you are given"*). The vocabulary constraint
in `src/aslgloss/baseline/vocab.py` then flags any output token outside the study-set vocabulary.

---

## The conventions

These reconcile `prompts/baseline_gloss.md`, `prompts/context_gloss.md`, and the OOV logic in
`baseline/vocab.py`.

| # | Rule | Status | Notes / where enforced |
|---|---|---|---|
| 1 | **Tokens are UPPERCASE** English words standing for signs. | Stable | Prompt rule; `oov_tokens` is case-sensitive. |
| 2 | **Follow ASL grammar, not English word order.** Prefer topic–comment; time markers first. | Stable (intent) | Prompt rule. Correctness is an error-analysis category (`topic_comment`), not a tokenization rule. |
| 3 | **Drop English function words** ASL does not sign (articles, copulas, most auxiliaries). | PROVISIONAL | Must confirm ASLG-PC12 drops the same set; mismatches inflate/deflate BLEU. |
| 4 | **Do not transliterate word-for-word.** Signed English ≠ ASL. | Stable (intent) | Prompt rule. |
| 5 | **Indexing / pointing → `IX`.** | PROVISIONAL | Confirm whether ASLG-PC12 uses `IX`, `IX-1`, `PRO`, etc. If the corpus differs, adopt the corpus form. |
| 6 | **Negation → `NOT`.** | PROVISIONAL | The error heuristic `NEG` (`evaluation/error_analysis.py`) already keys on negation; confirm the corpus token. |
| 7 | **Out-of-vocabulary proper nouns → fingerspelled as `fs-WORD`.** | Stable | `oov_tokens` explicitly ignores any token starting with `fs-`; the vocab constraint treats fingerspelling as always-valid. |
| 8 | **Output is a single line**, no punctuation, no preamble, no explanation. | Stable | Prompt rule; `GlossGenerator.generate` takes only the first line and strips a leading `Gloss:`. |
| 9 | **Whitespace tokenization.** Tokens are split on spaces. | Stable | Both `build_gloss_vocab` and `oov_tokens` use `str.split()`; BLEU tokenization must be consistent with this. |

---

## Verification checklist (Week 6)

Before any BLEU number goes in the report, confirm on a real ASLG-PC12 sample:

- [ ] Sample 50–100 corpus gloss strings and record their **actual** tokens for: indexing, negation,
      function-word dropping, and fingerspelling notation.
- [ ] Reconcile rules 3, 5, 6 above with what the corpus actually does; update this table and, if
      needed, `prompts/baseline_gloss.md`.
- [ ] Confirm `sacrebleu`'s tokenizer does not silently re-split our tokens (e.g. on hyphens in
      `fs-WORD` or `IX-1`). If it does, choose a tokenizer or pre-tokenization that preserves them.
- [ ] Record the final decision in `docs/decision_log.md`.

## Relationship to the paper

Zhang et al. constrained Module 1's output to a **3,915-entry ASLLRP-derived word–gloss dictionary**
and handled **43 OOV words by fingerspelling**. We approximate the dictionary constraint by building a
vocabulary from our example pool (`build_gloss_vocab`). When ASLLRP access arrives, the faithful
baseline should adopt the paper's dictionary and its exact gloss conventions (Appendix D) — at which
point this file must be updated to match.
