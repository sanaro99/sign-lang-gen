# Results Report — ASLLRP Four-Condition Pilot (Module 1: English → ASL gloss)

**Date:** 2026-07-17
**Model:** `gemma4:latest` (local, via Ollama) — *not* the paper's gpt-4o
**Data:** ASLLRP DAI 2 continuous-signing corpus, 51 of ~84 collections
**Test set:** 220 held-out sentences (whole documents held out, no cross-doc leakage)
**Metric:** BLEU-4 (sacrebleu, `tokenize="none"`) against real Deaf-signer gloss transcriptions

> **One-line verdict:** This is a **working pilot, not a reproduction**. The full four-condition
> pipeline now runs end-to-end on *real* ASL data — but neither of our two contributions (RAG, context)
> improved the score, and the absolute score is far below the paper's target for reasons we can name.

*(The companion report `results_report.md` covers the earlier ASLG-PC12 **synthetic** pilot. That data
is rule-generated, this one is Deaf-produced; the two sets of numbers are NOT comparable.)*

---

## 1. In plain words

We taught a computer to turn English sentences into "ASL gloss" (a written, word-by-word shorthand for
sign language), and we tested it four ways — with and without two ideas of ours: **retrieval** (feed the
model similar past examples) and **context** (let it see neighboring sentences). We scored each version by
how closely its output matched gloss written by real Deaf signers.

**The short answer:** the machinery all works, but on the real data our two ideas didn't measurably help,
and the overall match score is low — mostly because the human reference gloss contains detailed
"stage directions" (where a sign points in space, which hand, pauses) that simply **can't be guessed from
English text**. That inflates the number of "misses" no matter how good the translation is. We are honest
that a low score here does **not** prove the output is bad — and equally, we make **no claim** that it's
good, because no Deaf signer has reviewed it yet.

---

## 2. Did we have "all the data"? — No, still partial.

| Piece | Status |
|---|---|
| ASLLRP continuous-signing corpus | **51 of ~84** collections → 2,286 English↔gloss pairs (pool 2,066 / test 220) |
| ASLLRP **Sign Bank dictionary** (3,915 word→gloss entries) | **Missing** — it's a *separate* download, not yet obtained |
| The paper's model (gpt-4o) | Not used — running a small local model instead |

So this is a **pilot on ~61% of the corpus, with no dictionary and a smaller model**. Valid engineering
test of the pipeline; **not** a faithful reproduction of the paper.

---

## 3. The numbers (full 220-sentence real-ASL test set)

| Condition | Retrieval | Context | **BLEU-4** | 1-gram | 2-gram | 3-gram | 4-gram | Brevity |
|---|---|---|---|---|---|---|---|---|
| `baseline` | off | off | **0.043** | 36.8 | 10.8 | 3.1 | 1.1 | 0.71 |
| `rag` | **on** | off | **0.042** | 36.3 | 9.5 | 2.8 | 1.0 | 0.74 |
| `context` | off | **on** | **0.041** | 35.3 | 9.1 | 2.6 | 1.0 | 0.76 |
| `context_rag` | **on** | **on** | **0.042** | 36.5 | 9.6 | 2.8 | 0.8 | 0.77 |

**All four conditions are indistinguishable** — one narrow band (0.041–0.043) sitting on BLEU-4's noise
floor. Neither retrieval nor context moved the score.

> ⚠️ An earlier n=50 pilot *appeared* to show "RAG dominates" (0.016 → 0.058). That was a **small-sample
> artifact** of the first 50 sentences (a question-heavy slice). On the full 220 it disappears — which is
> exactly why we scaled to the whole test set.

### What the precision breakdown tells us (measured, not guessed)
The precisions fall off a cliff: **~37% of single tokens** match a reference token, but only **~1% of
4-word sequences** do. That steep **37 → 11 → 3 → 1** shape means the model often picks *plausible content
words* but almost never reproduces the reference's exact multi-word sequence. Two objective reasons:

1. **Un-generatable notation.** The references encode articulatory / spatial detail not recoverable from
   English text — spatial coreference indices (`IX-3p:i`, `SELF-3p:j`, `:i/j`), name-sign markers (`ns-`),
   two-handedness (`(2h)`, `(1h)`), prosody (`5"pause"`, `QUOTE/TOPIC`). A text-only model cannot invent
   these, so they count as misses against every hypothesis.
2. **Brevity penalty ≈ 0.73.** Hypotheses average ~9 tokens vs. ~12 in the references (the references
   carry the markers above), so BLEU is additionally docked for being too short.

This is **not** "the model is secretly good and BLEU can't see it." We have **no Deaf-signer evaluation**,
so we make no claim about ASL quality. It means: *notation and coreference that can't be produced from text
are one measurable contributor to the low BLEU — on top of genuine translation errors visible in the
samples (dropped function words, reordered clauses, lost repetition).*

**Illustrative example:**
```
English : Gallaudet tends to be a Deaf college in general.
Reference: ns-GALLAUDET IX-loc:i/j SELF-3p:j (1h)QUOTE/TOPIC DEAF COLLEGE IX-3p:i MAJOR+fs-LY ...
Model    : fs-GALLAUDET TEND DEAF COLLEGE GENERAL
```
The content is largely there; the spatial/prosodic scaffolding is not — and can't be, from text alone.

---

## 4. The one behavioral signal worth chasing (heuristic — not human-coded)

Our automatic error tagger (`docs/error_taxonomy.md`; a rule-based tagger, **not** a human rater) flags:

| Condition | pronoun-referent errors | context-leak errors |
|---|---|---|
| `baseline` | 56 | — |
| `context` | **41** | **57** |
| `rag` | 75 | — |
| `context_rag` | 64 | 66 |

Adding the paragraph **context buffer** appears to **reduce pronoun-referent errors (56 → 41)** — the
discourse window is doing something plausible — but it introduces a **new failure mode**: in ~57/220 cases
the model glosses the *surrounding* sentences instead of only the target one ("context leak"). RAG, by
contrast, slightly *raised* pronoun errors (56 → 75). This is the most interesting real difference between
conditions, and a **hypothesis for the Week-9 human coding pass**, not a proven win. BLEU cannot see it.

---

## 5. Honesty caveats (must ride with every number above)

- **Real references, low ceiling.** These BLEU scores are against *real Deaf-signer* transcriptions — more
  meaningful than the synthetic ASLG-PC12 numbers, but the ceiling is capped by the missing dictionary, the
  provisional prompt, and the small local model.
- **PROVISIONAL prompt.** `prompts/asllrp_gloss.md` was hand-written from the conventions, not recovered
  from the paper; wording is unvalidated.
- **Error tags are heuristic.** The pronoun/leak signal is from a rule-based tagger, not a human.
- **No NMM scoring.** Runs used `--no-nmm`; the four non-manual markers are not evaluated here (no gold
  labels yet).

---

## 6. Were we successful? — Split verdict

| Dimension | Verdict | Why |
|---|---|---|
| **Reproduce the paper (BLEU-4 ≈ 0.276)** | ❌ **No** | We are at ~0.04. Pipeline is incomplete: no Sign Bank dictionary, 51/84 collections, small local model (not gpt-4o), provisional prompt. We do **not** claim reproduction. |
| **Build the infrastructure** | ✅ **Yes** | The full four-condition pipeline runs end-to-end on real ASLLRP data with per-run manifests, a document-level leakage-guarded split, and error taxonomy. Reproducible and re-runnable. |
| **Support our two contributions (RAG, context)** | ⚠️ **Not on this evidence** | Neither moved BLEU on the full real-ASL set. Context shows a *mixed* behavioral signal (fewer pronoun errors, new context-leak errors) worth a human-coded follow-up. The earlier "RAG wins" was a small-sample artifact. |

---

## 7. What would actually change the result (priority order)

1. **Add the Sign Bank dictionary** (Phase A4) — gives the model the ASLLRP lexicon so sign choice /
   `fs-` / `ns-` can match; most likely single lever on absolute BLEU.
2. **Run on gpt-4o** (the paper's model) — isolates "small local model" as a cause.
3. **Human-coded error analysis** (Week 9) — the only honest way to judge ASL quality and to test the
   context pronoun/leak tradeoff. BLEU cannot arbitrate this.
4. **Finish the corpus** — export the remaining ~33 collections.
5. **Report 1-gram precision alongside BLEU-4** going forward — it discriminates where BLEU-4 floors out.

---

*Artifacts: `results/summary.csv` (aggregate); `results/asllrp_*_2026*/` (per-run predictions + manifests
with git SHA, prompt hash, model, seed, token counts).*
