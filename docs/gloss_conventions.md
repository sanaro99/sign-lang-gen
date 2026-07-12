# Gloss Conventions

The written rules our system's gloss output must follow, why they have to match the dataset, and the
important catch about what these particular conventions do and do not represent.

> **Status (2026-07-12): VERIFIED against ASLG-PC12 on a real 10-example sample.** The rules below are
> confirmed, not provisional. They describe the **ASLG-PC12 corpus style**, which our bring-up baseline
> targets so BLEU is meaningful. See `docs/decision_log.md` (2026-07-12 entries) and
> `docs/landscape_generative_slg.md`.

---

## In plain words

**"Gloss"** normally means writing signs as CAPITALIZED words in the order a signer would sign them.
But the dataset we start with (ASLG-PC12) does **not** contain real ASL. Its "gloss" was produced by a
*rule* that walks through the English sentence, keeps the English word order, shortens each word to its
base form, and tags pronouns and describing-words with little prefixes. So `"I voted against this
report."` becomes `X-I VOTE AGAINST THIS REPORT .` — recognizably still English order, just relabeled.

Why does that matter? Because we grade the machine by comparing its output to this dataset's output.
If our machine produced *real* ASL (which reorders words and drops more of them), it would score badly
against ASLG-PC12 — not because it's wrong, but because the dataset isn't real ASL. So for this
**warm-up** stage we deliberately tell the model to imitate ASLG-PC12's style. When we later get the
real, Deaf-produced dataset (ASLLRP), we'll switch to real-ASL rules. **This file documents the warm-up
conventions and is explicit that they are not real ASL.**

---

## Why conventions must match the reference corpus

BLEU-4 (via `sacrebleu`, in `src/aslgloss/evaluation/metrics.py`) rewards **string-identical tokens in
the same order**. If the corpus writes `X-I` and the model writes `IX` (or `ME`), or the corpus keeps a
`.` and the model drops it, BLEU counts a miss even when meaning is identical. Therefore:

> **Our prompt conventions must match ASLG-PC12, or the BLEU comparison is meaningless** — decision-log
> open question #4, now resolved for the bring-up phase.

Steering happens two ways: the instruction block in `prompts/baseline_gloss.md` /
`prompts/context_gloss.md`, and the retrieved in-context examples (the model is told to match their
style). `src/aslgloss/baseline/vocab.py` then flags any output token outside the pool vocabulary.

## The conventions (ASLG-PC12 style — VERIFIED)

| # | Rule | Example |
|---|---|---|
| 1 | UPPERCASE tokens, single line, no punctuation stripping of `,` `.` | — |
| 2 | **Keep source English word order** (no ASL reordering) | `i think it is important` → `X-I THINK X-IT BE DESC-IMPORTANT` |
| 3 | **Lemmatize** to base form | `voted` → `VOTE`; `problems` → `PROBLEM`; `opposed` → `OPPOSE` |
| 4 | **Drop** articles (`a`/`an`/`the`) and the preposition **`of`** | `the creation of the eeas` → `CREATION EEAS` |
| 5 | **Keep** copula `BE`, modals (`WILL`, `MUST`, `SHOULD`), other prepositions (`IN`,`ON`,`TO`,`WITH`,`INTO`) | `it is` → `X-IT BE`; `should also` → `SHOULD DESC-ALSO` |
| 6 | **Pronouns → `X-` prefix**; possessive `X-MY` / `X-POSS` | `we` → `X-WE`; `group's` → `GROUP X-POSS` |
| 7 | **Descriptors (adj/adv) → `DESC-` prefix** | `external` → `DESC-EXTERNAL`; `still` → `DESC-STILL` |
| 8 | Numbers stay digits | `2013` → `2013` |
| 9 | **Punctuation kept** as separate tokens | `report .` → `REPORT .` |
| 10 | Fingerspell unknown proper nouns as `fs-WORD` | (vocab constraint treats `fs-` as always valid) |
| 11 | Whitespace tokenization (`str.split()`), consistent with `vocab.py` and BLEU | — |

## The load-bearing caveat (must appear in the report)

Rules 2, 3, 6, 7 mean the ASLG-PC12 target is **lemmatized, English-order pseudo-gloss with
morphological prefixes — not real ASL.** Making our model reproduce it turns the "baseline" into an
LLM imitation of a POS-tagging rule. That is acceptable *only* as pipeline bring-up and a
BLEU-reproduction sanity check. It does **not** demonstrate ASL quality (cf. Yin et al. 2021; Desai et
al. 2024). Real-ASL evaluation waits for **ASLLRP** (Deaf-produced), at which point a separate
real-ASL prompt (topic-comment reordering, dropped copula, `IX` indexing, `NOT` negation) replaces the
conventions above.

## Relationship to the paper

Zhang et al. constrained Module 1 to a 3,915-entry ASLLRP-derived word–gloss dictionary and handled 43
OOV words by fingerspelling. We approximate the constraint with a pool-derived vocabulary
(`build_gloss_vocab`). Their targets (BLEU-4 ≈ 0.276; NMM P 0.91 / R 0.97) were computed on ASLLRP with
their preprocessing and are **not directly comparable** to our ASLG-PC12 numbers — report that plainly.

## Remaining checks (before Week 6)

- [x] **Done (2026-07-12):** BLEU uses `sacrebleu` with `tokenize="none"`, so our whitespace tokens
      (`X-I`, `DESC-IMPORTANT`, `fs-WORD`, punctuation) are matched exactly, not re-split on hyphens.
- [ ] Spot-check the `X-POSS` / possessive handling and any rarer prefixes on a larger sample.
- [ ] When ASLLRP lands, author the real-ASL prompt variant and a matching conventions section.
