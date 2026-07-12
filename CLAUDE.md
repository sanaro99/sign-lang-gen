# CLAUDE.md

Guidance for any AI assistant or new developer working in this repository. Read this first.

---

## In plain words

This project teaches a computer to translate **written English into "ASL gloss"** — a written,
word-by-word shorthand for American Sign Language — and to spot the four grammar signals a signer
shows with their face and eyebrows (questions, negation, "if"). It is a **research reproduction**:
we are rebuilding one stage of a 2025 Apple research paper (whose code was never released) from the
paper's written description, and then adding two of our own improvements to see if they help. We are
**not** producing signing videos or avatars — only the text-to-gloss step. Everything here is a
careful, honest experiment, not a shipping product.

---

## What this repository is

An IMT 600 independent-study codebase (UW Information School, MSIM, Summer 2026). It **re-implements
and extends Stage 1 / Module 1** of:

> Zhang et al. (2025), *Towards AI-driven Sign Language Generation with Non-manual Markers*, CHI 2025.
> arXiv 2502.05661 · DOI 10.1145/3706598.3713855.

Module 1 is the LLM stage that turns **English text → ASL gloss + non-manual markers (NMM)**.

**No official code was ever released for that paper** (verified — see `ATTRIBUTION.md` §1). Every
line in `src/aslgloss/` is an **original re-implementation from the paper's method description**.
Nothing is copied from Apple. Methods are not copyrightable; the paper text/figures are not reproduced.

### Scope boundary (do not cross without discussion)
- ✅ **In scope:** Stage 1 only — text → gloss + NMM.
- ❌ **Out of scope:** Stage 2 (pose synthesis) and Stage 3 (video rendering). Both depend on
  internal Apple assets and are explicitly not attempted.

### The two contributions on top of the baseline
1. **RAG example retrieval** (`src/aslgloss/retrieval/`) — instead of stuffing ~1,474–1,494 static
   examples into the prompt (which forced the paper into a "multi-prompting" batching hack), retrieve
   the top-*k* most semantically similar English–gloss pairs per input. Aim: better *and* cheaper.
2. **Paragraph context buffer** (`src/aslgloss/context/`) — the paper glosses each sentence in
   isolation; we feed a window of neighboring sentences (and our own prior glosses) so discourse
   phenomena (pronouns, negation scope, topic continuity) survive.

Plus one **exploratory** Indian Sign Language (ISL) extension (Week 7) — architectural transfer only,
because **no gloss-annotated ISL data exists** (cannot be scored; label everything exploratory).

---

## Architecture at a glance

Config-driven experiment pattern. One YAML in `configs/` fully describes a run. Extension points are
**pluggable**: `GlossGenerator` takes an optional `retriever` and `context_builder` — `None` gives
the paper-faithful baseline, passing them in turns on a contribution.

```
scripts/download_data.py  → data/processed/{example_pool.jsonl, test.jsonl}
scripts/build_index.py    → data/processed/example_pool.faiss   (embeds the example pool)
scripts/run_experiment.py → results/<run_id>/{predictions.jsonl, manifest.json}
scripts/evaluate.py       → results/summary.csv
```

`src/aslgloss/` modules: `config` (dataclasses + YAML loader), `llm` (provider-agnostic client),
`data` (loaders + paragraph chunking), `baseline` (gloss generator + NMM classifier + vocab),
`retrieval` (embed → FAISS → top-k), `context` (paragraph buffer), `evaluation` (BLEU/NMM/error tags).

See **`docs/architecture.md`** for the full walkthrough and data-flow trace.

### The four experimental conditions
| Config | Retrieval | Context | Purpose |
|---|---|---|---|
| `configs/baseline.yaml` | off (static shots) | off | Reproduce CHI 2025 Module 1 (target BLEU-4 ≈ 0.276) |
| `configs/rag_only.yaml` | **on** | off | Isolate the effect of retrieval |
| `configs/context_only.yaml` | off | **on** | Isolate the effect of discourse context |
| `configs/context_plus_rag.yaml` | **on** | **on** | Our full proposed system |

---

## Commands

```bash
make setup          # pip install -r requirements.txt && pip install -e .
make data           # download ASLG-PC12 → data/ (gitignored)
make index          # embed example pool, build FAISS index
make baseline       # run the baseline condition
make rag            # run the rag_only condition
make all-conditions # run all four conditions
make eval           # aggregate results → results/summary.csv
make test           # pytest -q
make lint           # ruff check src/ scripts/ tests/
```

Requires a `.env` with `OPENAI_API_KEY` (copy `.env.example`), or point at an open model via
`OPEN_MODEL_BASE_URL` / `OPEN_MODEL_NAME` and set `provider: open` in the config.

---

## Conventions that MUST be honored

1. **Never commit `data/` or `.env`.** ASLLRP redistribution is prohibited by license; ASLG-PC12 is
   "no known license." `data/` is gitignored for this reason.
2. **Never commit PII.** Contributor names/emails/roles live only in the gitignored
   `docs/AUTHORS.local.md`. Tracked files refer to people by placeholder ("Student 1", "Student 2",
   "Student 3", "Professor", "Mentor"). Do not add real names to any tracked file, commit message, or
   PR. (Published paper-author names in citations are fine.)
3. **No AI-authorship signal.** Do not add "generated with / co-authored by an AI" lines to files,
   commits, or PRs. This is the team's own work.
4. **Prompts are source code.** They live in `prompts/`, are versioned, and every run logs the prompt
   hash (`scripts/run_experiment.py`). *A result without a prompt hash is not a result.*
5. **Every run writes a manifest** (`results/<run_id>/manifest.json`): git SHA, prompt hashes, model
   snapshot, config, seed, token counts, cost. Week 9 analysis depends on this.
6. **Notebooks explore; `src/` decides.** Anything relied upon graduates into `src/` **with a test**.
7. **Log non-obvious decisions** in `docs/decision_log.md` — one line, with the reason. It becomes
   the methods section of the report.
8. **`main` stays runnable.** Work on `feat/<thing>`, PR into `main`, one teammate reviews.

---

## Honesty constraints (this is a project about accessibility — get this right)

- **ASLG-PC12 glosses are synthetic** — rule-generated from POS-tagged English, *not* produced by
  Deaf signers. **High BLEU here does NOT prove real ASL quality.** Say so in every write-up. The
  structured error analysis (`docs/error_taxonomy.md`) exists partly to compensate.
- **The ISL extension cannot be scored** — no ISL gloss references exist anywhere. It tests
  *architectural transfer*, not translation quality. Label it exploratory; ISL grammar rules in
  `prompts/isl_gloss.md` are PROVISIONAL pending Deaf-community review.
- We **cite and answer** the critique that gloss is a lossy, non-standard intermediate (Yin et al.
  2021; Desai et al. 2024). Gloss is treated as an auditable engineering scaffold, not "the language."
- Bigham's rule to remember: *"works on average" is not good enough* — average accuracy can hide
  terrible performance for the exact community the tool is meant to serve. Report which errors, on
  what content — not just headline scores.

---

## Pointers

- `README.md` — public overview, provenance tables, quickstart.
- `ROADMAP.md` — the multi-week plan and technical-debt track.
- `PROGRESS.md` — current status, task board, changelog.
- `docs/architecture.md` — pipeline walkthrough + module map.
- `docs/gloss_conventions.md` — the gloss tokenization rules (so BLEU is meaningful).
- `docs/decision_log.md` — why we made each non-obvious choice, plus open questions.
- `docs/error_taxonomy.md` — the error categories BLEU hides.
- `docs/isl_extension.md` — scope and honesty constraints for the ISL work.
- `docs/related_work.md` — which paper touches which part of the code.
- `ATTRIBUTION.md` — full citations, licenses, and dataset terms.
