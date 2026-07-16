# Progress

A living status log. Update it whenever something meaningful changes. `ROADMAP.md` says what we plan
to do; this file says what we have actually done and what's next right now.

---

## In plain words

This page is the project's "you are here" marker. At a glance it tells anyone — a teammate returning
after a week, or the faculty supervisor checking in — what state the project is in, what's being
worked on, what's next, and what's stuck waiting on something. If you only read one file to catch up,
read this one, then `ROADMAP.md`.

---

## Current status

**Phase:** Bring-up complete — first (preliminary) four-condition comparison run.
**Last updated:** 2026-07-12.

- Code scaffolding is complete and modular: all `src/aslgloss/` modules, four scripts, four condition
  configs, and four prompt templates are in place.
- **Data pipeline is built** (local, gitignored): ASLG-PC12 downloaded → `example_pool.jsonl` (20,000
  pairs) + `test.jsonl` (1,000, **deduplicated, leakage-guarded** split) + `example_pool.faiss`.
- **First LLM runs done:** all four conditions ran on local `gemma3:4b` (N=20). Results in
  `results/summary.csv` and `docs/results_report.md`. **Labeled PRELIMINARY** — small local model, N=20,
  synthetic corpus; not the graded Week-6 evaluation.
- **Integrity audit (2026-07-12):** verified the four runs empirically — identical 20 test items/seed
  across conditions, on-disk split confirmed leakage-clean (0 pool neighbors ≥0.90 cosine to any test
  item), BLEU-4 ordering stable to dropping best/worst-2 sentences, 0/20 zero-4-gram outputs. See the
  changelog entry.
- **Landscape review complete** → `docs/landscape_generative_slg.md`; strategy folded into `ROADMAP.md`
  and `docs/decision_log.md`.
- Documentation baseline in place: `CLAUDE.md`, `ROADMAP.md`, `PROGRESS.md`, `docs/architecture.md`,
  `docs/gloss_conventions.md`, `docs/landscape_generative_slg.md`.

---

## Task board

### ✅ Done
- Repo structure, package `aslgloss`, four experiment configs, four prompts, three unit tests.
- Provenance & ethics docs: `README.md`, `ATTRIBUTION.md`, `docs/{decision_log,error_taxonomy,isl_extension,related_work}.md`.
- **Documentation & privacy pass (2026-07-12):** added `CLAUDE.md`, `ROADMAP.md`, `PROGRESS.md`,
  `docs/architecture.md`, `docs/gloss_conventions.md`; added function-level docstrings across
  `src/aslgloss/**`; scrubbed PII to role placeholders (real names → gitignored `docs/AUTHORS.local.md`);
  removed the accidental nested `asl-gloss-stage1/` duplicate.

### ▶ Next (toward a graded result — order: baseline fairness → discourse probe → M1 clean run)
- Decide **baseline fairness** (8-shot vs. paper's ~1,474-shot multi-prompting) and log it — the static
  8-shot baseline is currently a weak comparator that flatters RAG. **Still open.**
- Build the **hand-curated discourse probe set** (M3) so the context contribution can be honestly
  evaluated (auto-chunked paragraphs aren't real discourse).
- Run **M1**: a full baseline on a stronger model (gpt-4o and/or ASLLRP) — the preliminary local
  numbers are not comparable to the paper's.

### ✅ Recently done (M0 prerequisites)
- **Gloss conventions aligned to ASLG-PC12** (`X-I`/`DESC-`/kept punctuation) → `prompts/*`, `docs/gloss_conventions.md`.
- **Documented, deduplicated, leakage-guarded split** replaces the naive tail slice in `download_data.py`.
- **Exact-token BLEU** (`tokenize="none"`) so `X-I`/`DESC-…`/`fs-…`/punctuation match whole.

### ⏳ In progress
- *(none active — awaiting the team's call on baseline fairness / discourse probe / M1)*

### 🚧 Blocked / waiting
- **ASLLRP faithful baseline** — waiting on Rutgers DAI access request. `load_asllrp` is a stub;
  ASLLRP data must never be committed.
- **ISL feasibility (Week 7)** — needs ISL-fluent reviewer(s) for spot-checks; no gloss references
  exist, so this stays exploratory regardless.

---

## Open questions (mirror of `docs/decision_log.md`)

| # | Question | Why it matters |
|---|---|---|
| 1 | Baseline fairness: 8-shot vs. ~1,474-shot multi-prompting | Single biggest threat to our claims — decide and defend. |
| 2 | Proper documented test split | Current tail slice is a placeholder; no number should rest on it. |
| 3 | Hand-curated discourse probe set (~50–100 passages) | Auto-chunked paragraphs aren't real discourse; Contribution 2 can't be honestly evaluated without this. |
| 4 | Finalize gloss conventions vs. ASLG-PC12 tokenization | Otherwise BLEU is meaningless. |
| 5 | Email paper authors re: sharing Module 1 prompts? | Low cost, possible payoff. |
| — | Fix "Kim et al." → "Guo, Li & Cohn" citation | Bibliography correctness before final report. |

---

## Changelog

Newest first. One entry per meaningful change; keep it short.

- **2026-07-12** — **Integrity audit of the four-condition numbers** (no re-run; verification only).
  Confirmed from the manifests + on-disk data: all four runs used the **same 20 test items in the same
  order**, same seed (7), same model, same git SHA. Empirically re-measured leakage on the split the
  runs actually used — **0/1000** test items (and **0/20** scored) have a pool neighbor ≥0.90 cosine;
  max among the scored 20 is 0.874 — so the RAG gains are **not** inflated by near-duplicate leakage,
  even though the dedup *code* was committed after the run SHA (built from the working tree first).
  BLEU-4 ordering (`baseline < context_only < rag_only < context_plus_rag`) is **stable** to dropping
  the best-2 and worst-2 sentences per condition, and **0/20** outputs have zero 4-gram overlap, so the
  scores rest on real signal, not a couple of lucky matches. Corrected stale status headers in
  `PROGRESS.md`/`ROADMAP.md` that still said "nothing has been run."
- **2026-07-12** — Trustworthiness fixes + first four-condition comparison. Added a de-duplicated,
  leakage-guarded split (`download_data.py`), exact-token BLEU (`metrics.py`, `tokenize="none"`), and
  local-run overrides (`run_experiment.py`). Ran conditions on local `gemma3:4b`, N=20, deduped split:
  **baseline 0.249 < context_only 0.274 < rag_only 0.485 < context_plus_rag 0.529** (all N=20).
  Wrote `docs/results_report.md` (layman-first, every metric explained, heavy caveats). Key reads:
  retrieval helps most (~+95%; but baseline is a weak comparator + corpus is templated); context adds a
  small ~+10% additive gain (needs the real discourse probe set to show true value); full system best;
  OOV high across board; `context_plus_rag` raised 2 `context_leak` flags to watch as N grows.
- **2026-07-12** — Gloss-convention alignment + first live pipeline run. Rewrote `baseline_gloss.md` /
  `context_gloss.md` (v0.2) and `docs/gloss_conventions.md` to ASLG-PC12's verified style (English
  order, lemmatize, `X-`/`DESC-` prefixes, kept punctuation) — documented that this is synthetic
  pseudo-gloss, not real ASL. Ran one held-out example end-to-end via local Ollama (`gemma3:4b`,
  `rag_only`): exact match to reference. Confirmed two things live: alignment works, and **retrieval
  leakage is real** (near-duplicate pool items) → dedup split is a Phase-1 must. NMM flagged a
  debatable `negation:True` on "voted against" — review negation definition in Phase 1.
- **2026-07-12** — Data bring-up + landscape review. Installed deps, built the ASLG-PC12 example pool
  (20k) + test set (1k) + FAISS index locally (no LLM calls). Completed the generative-SLG landscape
  review (`docs/landscape_generative_slg.md`) and set the improvement plan: prerequisites → RAG →
  context buffer → optional reordering. Repositioned RAG (prior analogues exist) vs. the context buffer
  (genuine novelty); adopted metric-hygiene + dedup-split policy; refined the ISL claim. Confirmed the
  ASLG-PC12 gloss-convention mismatch on real data. Updated `ROADMAP.md` and `docs/decision_log.md`.
- **2026-07-12** — Documentation & privacy pass. Added `CLAUDE.md`, `ROADMAP.md`, `PROGRESS.md`,
  `docs/architecture.md`, `docs/gloss_conventions.md`. Added function-level docstrings throughout
  `src/aslgloss/`. Replaced contributor PII with role placeholders (real details moved to gitignored
  `docs/AUTHORS.local.md`); `LICENSE` copyright → "The asl-gloss-stage1 Authors"; renamed a test
  fixture token; gitignored `docs/AUTHORS.local.md` and `*.pdf`. Removed the duplicate nested
  `asl-gloss-stage1/` directory.
- **2026-07-11** — Initial repository scaffolding: `src/aslgloss/` modules, scripts, configs, prompts,
  tests, and provenance/ethics documentation.
