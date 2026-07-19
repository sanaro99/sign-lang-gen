# Discourse probe set (gap G1 / milestone M3)

**Status: DRAFT v0 — NOT yet team-reviewed. No graded number may rest on it
until at least two team members have reviewed every probe and the review is logged in
`docs/decision_log.md`.**

## Why this exists

The paragraph context buffer (Contribution 2) is this project's main novelty, and corpus BLEU
cannot detect what it does: auto-chunked ASLG-PC12 "paragraphs" are not real discourse, and the
real-ASL corpora are too small and too notation-heavy for sentence-averaged scores to move
(`docs/results_report_asllrp.md`). This probe set is the purpose-built instrument: short passages
where the correct gloss of ONE target sentence genuinely depends on the sentences before it.
A sentence-isolated system (the paper's setting) *cannot* get these right except by luck; a
context-aware system can. That contrast — not BLEU — is the honest evaluation.

These passages are **original English text written for this project** (that is why this folder is
tracked while `data/` is not). They contain no ASLLRP/ASLG-PC12 material and no real names of
team members.

## Schema (`discourse_probes_v0.jsonl`, one JSON object per line)

| Field | Meaning |
|---|---|
| `probe_id` | stable id, `<category-prefix>-NNN` |
| `category` | one of `pronoun_referent`, `negation_scope`, `topic_continuity`, `ellipsis`, `nmm_scope` |
| `sentences` | the passage, in order; the whole passage is fed to the context condition |
| `target_idx` | index into `sentences` of the sentence to gloss and score |
| `phenomenon` | what, precisely, depends on the prior sentences |
| `coder_question` | the question a human coder answers about the produced gloss (Week-9 pass) |
| `correct_answer` | the answer derivable ONLY with context — the scoring key for coders |

## Protocol (how these get used)

1. **Curation (before any run):** two team members independently review every probe: is the
   target sentence truly ambiguous without context, and truly resolvable with it? Edit or drop.
   Record reviewer initials-as-roles + date in the decision log; bump the version (v0 → v1).
2. **Runs:** gloss every passage under `baseline` and `context_only` (same model, same prompts,
   same seed) via `probes_to_examples()` → standard `run_experiment.py` machinery, manifests and all.
3. **Coding:** two coders answer `coder_question` for each target gloss, blind to condition.
   Report per-category accuracy by condition + Cohen's κ (reuse `evaluation/agreement.py`).
4. **Claim shape:** "context resolved X% of pronoun-referent probes the baseline could not,
   at the cost of Y context-leak errors" — never a bare BLEU delta.

## Honesty notes

- These are **constructed** probes, not naturally occurring discourse. They measure whether the
  mechanism *can* use context, not how often real text *needs* it (Tanzer et al. 2024 estimate
  ~33% of sentences need context; cite them for that number, not this set).
- v0 was drafted in one pass from the error taxonomy and is unreviewed. The
  curation step above is not optional.
- English-only. The probes test the text side; they say nothing about ASL production quality —
  Deaf-led review remains gap G13.
