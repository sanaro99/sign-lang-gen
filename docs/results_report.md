# Preliminary Results Report — Four-Condition Comparison

> **Status: PRELIMINARY.** Run on a small local model (`gemma3:4b` via Ollama), a small sample
> (N=20 sentences/condition), and the **synthetic** ASLG-PC12 corpus. These numbers exercise and
> validate the pipeline and show *relative* trends; they are **not** publishable findings and are
> **not** comparable to the paper's gpt-4o/ASLLRP numbers. See "How much to trust this" below.

*Generated 2026-07-12. Results table auto-produced by `scripts/evaluate.py` → `results/summary.csv`.*

---

## In plain words

We ran the same translation task four times, each time turning a small set of English sentences into
ASL gloss, and changed just two switches between runs:

- **Retrieval** — does the model get *hand-picked similar examples* to learn from (on), or a *fixed
  generic set* (off)?
- **Context** — does the model *see the neighboring sentences* for disambiguation (on) or not (off)?

By comparing the four runs we can start to see whether each switch helps. We also spent effort up
front making sure the comparison is *fair* — removing "cheat" examples that are near-copies of the
test sentences, and fixing how the score counts words — so the numbers mean what they appear to mean.
The headline score (BLEU) is deliberately **not** the main story: it only measures word overlap against
a synthetic reference, so we explain every number below and flag exactly what it can and cannot tell us.

---

## What we ran

**Task:** English sentence → ASL gloss (+ non-manual markers), i.e. Stage 1 / Module 1.

**The four conditions** (each = one row in the table; only the two switches differ):

| Condition | Retrieval | Context | What it isolates |
|---|---|---|---|
| `baseline` | off (fixed 8-shot set) | off | Reproduces the paper's sentence-isolated setup |
| `rag_only` | **on** (top-8 retrieved) | off | The effect of **retrieval** alone |
| `context_only` | off (fixed 8-shot set) | **on** | The effect of **context** alone |
| `context_plus_rag` | **on** | **on** | Both together (the proposed system) |

All four use a **matched 8-example budget** (fixed vs. retrieved), so any difference is attributable to
*where the examples come from* and *whether context is present* — not to how many examples the model saw.

**Model:** `gemma3:4b`, run locally via Ollama (free), same model for all four conditions.
**Data:** ASLG-PC12; 20,000-pair retrieval pool, 1,000-sentence held-out test, **N=20** scored here.
**Fairness fixes applied first:**
- **De-duplicated, leakage-guarded split** — exact duplicates removed; no pool sentence is ≥0.9 cosine-
  similar to any test sentence, so retrieval can't hand the model a near-identical answer to copy.
- **Exact BLEU tokenization** — `X-I`, `DESC-IMPORTANT`, `fs-WORD`, and punctuation count as whole tokens.
- **Conventions aligned** to ASLG-PC12's actual style so the score reflects translation, not notation.

## How to read each number

| Column | Plain-language meaning | Higher or lower better? | What it does NOT tell you |
|---|---|---|---|
| `bleu4` | How much the model's gloss overlaps the reference gloss in short word-sequences (0–1). | Higher | Whether the gloss is *good ASL* — it only checks overlap with a synthetic reference. |
| `avg_prompt_tokens` | Average size of the prompt sent to the model (proxy for input cost). | Lower = cheaper | Output quality. |
| `latency_p50_s` | Typical (median) seconds per sentence. | Lower = faster | Tail slowness. |
| `latency_p95_s` | Near-worst-case seconds (95th percentile). | Lower | — |
| `cost_usd` | API dollar cost. **$0 here** because the model is local. | Lower | Real cost on a paid model like gpt-4o. |
| `oov_rate` | Fraction of outputs containing a token outside the pool vocabulary. | Lower usually | Whether OOV tokens were *correct* (e.g. fingerspelling). |
| `err_*` | Counts from the heuristic error triage (`tag_errors`) — e.g. `err_gloss_ordering`. | Lower | Final error rates — these are *candidate* flags for human coding, not verdicts. |

## Results

From `results/summary.csv` (N=20 per condition, `gemma3:4b` local, deduplicated split, exact-token BLEU).
All four conditions completed (the `context_plus_rag` run took three tries — the machine slept between
the first two attempts; this is environmental, not a code issue).

| condition | BLEU-4 | avg prompt tokens | latency p50 (s) | latency p95 (s) | cost | OOV rate |
|---|---|---|---|---|---|---|
| `baseline` (fixed 8-shot, no context) | 0.249 | 860 | 19.7 | 30.2 | $0 | 0.85 |
| `context_only` (fixed 8-shot + context) | 0.274 | 851 | 34.6 | 48.8 | $0 | 0.90 |
| `rag_only` (retrieved 8-shot) | 0.485 | 972 | 23.6 | 40.2 | $0 | 0.85 |
| `context_plus_rag` (both) | **0.529** | 966 | 28.9 | 35.3 | $0 | 0.75 |

Ordering: `baseline` < `context_only` < `rag_only` < `context_plus_rag`.

Heuristic error-triage flags (candidate counts, not verdicts): `oov_fingerspell` ≈ 15–18 in every
condition; `pronoun_referent` was 3 (baseline), 2 (context_only), 0 elsewhere; and `context_plus_rag`
raised 2 `context_leak` flags — the one risk our own context contribution introduces (content from the
neighbor sentences bleeding into the target gloss). All counts are far too small to draw conclusions
from, but the `context_leak` flag is worth watching as N grows.

## Interpretation

**Read every delta as directional, not significant** — N=20 makes BLEU noisy. With that caveat:

- **Retrieval helped a lot (the clearest signal).** `rag_only` nearly doubled BLEU over baseline
  (0.249 → 0.485, +0.24 / ≈+95%) for a small token cost (+13% prompt tokens) and modest latency
  (+4 s p50). Retrieving similar English→gloss pairs gives the model a much better pattern to copy than
  a fixed generic set. **Two honest discounts on this number:**
  1. *The baseline is a weak comparator.* Its "fixed 8-shot set" is literally the first 8 pool
     examples (arbitrary, possibly off-topic), so some of the gap is baseline weakness, not retrieval
     strength — exactly the baseline-fairness concern in `docs/decision_log.md`. A representative/diverse
     static set would narrow the gap.
  2. *The corpus is highly templated.* ASLG-PC12 here is Europarl ("madam president , I voted …"), so
     retrieved neighbors are structurally very close and easy to imitate; retrieval gains on diverse text
     would likely be smaller. (The dedup guard removed near-identical copies, but same-genre similarity
     remains — which is realistic, not leakage.)

- **Context helped only slightly — as expected.** `context_only` edged baseline up (0.249 → 0.274,
  ≈+10%) while nearly doubling latency (19.7 → 34.6 s p50) from the larger prompt. This is the predicted
  result: the "paragraphs" are just adjacent corpus sentences, **not genuine discourse**, so there is
  little real context to exploit. The context contribution cannot be fairly judged until the hand-curated
  **discourse probe set** exists (roadmap M3) — corpus BLEU is the wrong instrument for it.

- **Both together scored highest** (`context_plus_rag` 0.529). The lift decomposes cleanly: retrieval
  does the heavy lifting (baseline 0.249 → rag_only 0.485), and adding context on top of retrieval gives
  a further small bump (0.485 → 0.529, ≈+9%) — the same ~10% marginal size context showed on its own.
  So the two contributions appear roughly **additive** here, with retrieval dominant. `context_plus_rag`
  also had the **lowest OOV (0.75)**, a hint that richer prompting kept outputs closer to the pool
  vocabulary — but it also raised the only `context_leak` flags (2), the expected side-effect of feeding
  neighbor sentences in.

- **OOV is high across the board (0.75–0.90)** and only weakly separates conditions. Most outputs contain
  at least one token outside the pool vocabulary — unsurprising given ASLG-PC12's large vocabulary and the
  `X-`/`DESC-` morphology; it's a pipeline observation to tighten later (e.g. larger/again-curated vocab),
  not a real differentiator.

**Bottom line (preliminary):** the pipeline works end-to-end and, even on a small local model, the
*shape* of the results matches expectations from the landscape review — retrieval moves the needle most,
context adds a small additive gain (and needs a real discourse test to show its true value), the full
system is best, and the static baseline should be strengthened before any headline "retrieval doubled
BLEU" claim.

## How much to trust this (and how to make it stronger)

**What IS trustworthy here:** the pipeline runs end-to-end and is reproducible (each run has a manifest
with git SHA + prompt hash + config); the comparison is *internally consistent* (identical model, data,
and example budget across conditions); and the two biggest fairness threats — retrieval leakage and
BLEU mis-tokenization — have been fixed and documented.

**What is NOT yet trustworthy (by design, this pass):**
- **Synthetic reference.** ASLG-PC12 gloss is rule-generated, not Deaf-produced. High BLEU here does
  not mean good ASL (Yin et al. 2021; Desai et al. 2024).
- **Small local model.** `gemma3:4b` ≠ the paper's gpt-4o; absolute scores are not comparable.
- **Small sample.** N=20 → BLEU is noisy; treat differences as directional only.
- **Pseudo-paragraphs.** The "context" is adjacent corpus sentences, not genuine discourse, so
  `context_only`/`context_plus_rag` cannot yet show the context contribution's real value.

**What would make it strong (roadmap):** run on **gpt-4o** and/or **ASLLRP** (Deaf-produced); scale N;
build the **hand-curated discourse probe set** (M3) and evaluate context there; add a **semantic metric**
and **Deaf-led human evaluation**; report significance. See `ROADMAP.md` and `docs/decision_log.md`.
