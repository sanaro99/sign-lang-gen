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

**Phase:** Week 1–2 — repository setup & baseline bring-up.
**Last updated:** 2026-07-12.

- Code scaffolding is complete and modular: all `src/aslgloss/` modules, four scripts, four condition
  configs, and four prompt templates are in place.
- **Nothing has been run yet.** `data/` and `results/` are intentionally empty (`.gitkeep` only) —
  ASLG-PC12 has not been downloaded, no index built, no experiment run.
- Documentation baseline is now in place (this pass): `CLAUDE.md`, `ROADMAP.md`, `PROGRESS.md`,
  `docs/architecture.md`, `docs/gloss_conventions.md`.

---

## Task board

### ✅ Done
- Repo structure, package `aslgloss`, four experiment configs, four prompts, three unit tests.
- Provenance & ethics docs: `README.md`, `ATTRIBUTION.md`, `docs/{decision_log,error_taxonomy,isl_extension,related_work}.md`.
- **Documentation & privacy pass (2026-07-12):** added `CLAUDE.md`, `ROADMAP.md`, `PROGRESS.md`,
  `docs/architecture.md`, `docs/gloss_conventions.md`; added function-level docstrings across
  `src/aslgloss/**`; scrubbed PII to role placeholders (real names → gitignored `docs/AUTHORS.local.md`);
  removed the accidental nested `asl-gloss-stage1/` duplicate.

### ▶ Next (M0 foundations — see ROADMAP)
- Decide **baseline fairness** (8-shot vs. paper's ~1,474-shot multi-prompting) and log it.
- Define a **documented test split** (replace the tail slice in `download_data.py`).
- **Finalize `docs/gloss_conventions.md`** against a real ASLG-PC12 sample.
- Smoke-run `make data && make index && make baseline` on `n_examples: 5`.

### ⏳ In progress
- *(none — M0 not started yet)*

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

- **2026-07-12** — Documentation & privacy pass. Added `CLAUDE.md`, `ROADMAP.md`, `PROGRESS.md`,
  `docs/architecture.md`, `docs/gloss_conventions.md`. Added function-level docstrings throughout
  `src/aslgloss/`. Replaced contributor PII with role placeholders (real details moved to gitignored
  `docs/AUTHORS.local.md`); `LICENSE` copyright → "The asl-gloss-stage1 Authors"; renamed a test
  fixture token; gitignored `docs/AUTHORS.local.md` and `*.pdf`. Removed the duplicate nested
  `asl-gloss-stage1/` directory.
- **2026-07-11** — Initial repository scaffolding: `src/aslgloss/` modules, scripts, configs, prompts,
  tests, and provenance/ethics documentation.
