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

**Phase:** Faithful-reproduction prep (plan M1) — Phase A0 complete; NMM evaluation track built;
ASLLRP access requested and pending.
**Last updated:** 2026-07-16.

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

### ✅ Recently done (2026-07-16 — faithful-reproduction prep, no ASLLRP needed)
- **Phase A0 complete:** the paper's arXiv TeX source is downloaded and mined (gitignored
  `data/paper_src/`). Exact prompts recovered (both tasks + ablation variants + grammar-rules text);
  preprocessing Steps 1–4 and the gloss-conventions table extracted; targets verified against the
  primary source (BLEU-4 0.276; NMM macro P 0.91 / R 0.97, per-label breakdown known). Tracked
  summary: `docs/primary_source_findings.md`.
- **Major finding:** the paper's own appendix already implements RAG (anonymized embeddings,
  top-N cosine; N=50 beat all ~1,474 examples) → contribution 1 reframed as reproduction +
  extension across `ROADMAP.md`, `docs/landscape_generative_slg.md`, `docs/decision_log.md`.
- **NMM P/R track built** (was: "not measured"): `evaluate.py` now scores NMM precision/recall/F1
  (macro in `summary.csv`, per-label in `results/nmm_summary.csv`) against human gold labels when
  `data/processed/nmm_gold.jsonl` exists, and says plainly when it doesn't. Annotation kit:
  `docs/nmm_annotation_rubric.md` (paper-informed edge cases: sentiment ≠ negation) +
  `scripts/nmm_annotation.py` (blank sheets → Cohen's κ → adjudication → gold merge) +
  `src/aslgloss/evaluation/agreement.py` with tests (11 pass). **Next human step: two people fill
  the sheets in `data/annotations/`.**

### ✅ Recently done (2026-07-16 — real-ASL testbed while ASLLRP is pending)
- **NCSLGR wired as a real-ASL testbed** (Boston University / Neidle; the ASLLRP family). ~1,875
  **real, Deaf-produced** ASL gloss pairs, publicly mirrored (DePaul ELAN export, no video), loaded
  by `load_ncslgr()` (stdlib + `defusedxml`, cached to gitignored `data/raw/ncslgr/`). Gloss is true
  ASLLRP notation (`fs-`, `IX-`, `POSS-`, `#loan`, `DCL:`/`BCL:`, `5"…"`) — the honest gap ASLG-PC12
  (synthetic) leaves. `scripts/download_data.py --dataset ncslgr` builds a **document-level** split
  (~1,432 pool / ~249 test) into `data/processed/ncslgr/` without clobbering the ASLG-PC12 split.
  Real-ASL prompt `prompts/asllrp_gloss.md` (PROVISIONAL) + `configs/ncslgr_rag.yaml`; parser test
  `tests/test_ncslgr.py`. Full picture: `docs/datasets.md`. **13 tests pass.**
  - **Honesty:** NCSLGR is *not* independent of the gated data (same project family), licence terms
    are unstated (treated like ASLLRP — local, gitignored, never committed), and it must **not** be
    scored with the ASLG-PC12 prompt (notation mismatch → near-zero BLEU on notation alone). Any BLEU
    is preliminary. Its signing-based NMM tiers are a comparison only, not text-NMM gold.
  - **PHOENIX-2014T** (real DGS gloss) evaluated and **deferred** — German makes our English→ASL
    prompt and NMM labels inapplicable; documented as an option in `docs/datasets.md`.
- **Fixed a real `.gitignore` bug:** the bare `data/` rule also matched `src/aslgloss/data/`, so the
  entire data-loader module was **never tracked** (a fresh clone would fail to import). Anchored to
  `/data/` — corpus stays ignored, module is restored to git. **Needs committing** (see below).

### ⏳ In progress
- **NMM gold-label annotation** — sheets generated; needs two annotators + κ + adjudication
  (see `docs/nmm_annotation_rubric.md`).
- **Uncommitted:** this session's work (NCSLGR loader/split/prompt/config/docs + the `.gitignore`
  fix that finally makes `src/aslgloss/data/` trackable) is in the working tree, not yet committed.

### ✅ Recently done (2026-07-16 — ASLLRP access granted, Phase A started)
- **DAI access approved; `load_asllrp()` implemented.** First 4 collection zips downloaded to
  gitignored `data/dai/`. The loader parses DAI 2 `xml_extract_*.xml` (`<UTTERANCE>` → English
  `<TRANSLATION>` + ordered `<SIGN><LABEL>` gloss; optional signing-NMM from sentence-type
  `<NON_MANUAL>` tiers) → **156 real English↔gloss pairs** with real conventions (`fs-`, `IX-3p:i`,
  `DCL:B"…"`, `(2h)`). `tests/test_asllrp.py`; `download_data.py --dataset asllrp` builds a split into
  `data/processed/asllrp/`. **15 tests pass.**

### ✅ Recently done (2026-07-17 — four-condition ASLLRP pilot, full 220-sentence test set)
- **Four-condition ASLLRP evaluation on the full 220-sentence test set** (51 collections → 2,286 pairs;
  local **gemma4**, `--no-nmm`). BLEU-4 vs. **real** Deaf-signer glosses: baseline **0.043**, rag
  **0.042**, context **0.041**, context+rag **0.042** — **all four indistinguishable at BLEU-4's noise
  floor; neither contribution moved the score.** Full write-up: `docs/results_report_asllrp.md`.
  - **The earlier n=50 "RAG dominates" signal was a small-sample artifact** (question-heavy first-50
    slice); it disappears on the full test set. Corrected here.
  - n-gram precision falls 37 → 11 → 3 → 1 (1→4-gram) with brevity penalty ≈0.73 — objectively "right
    vocabulary, wrong exact sequence": references carry un-generatable spatial/prosodic notation
    (`IX-3p:i`, `SELF-3p:j`, `ns-`, `(2h)`, `5"pause"`) that no text-only model can produce. Low BLEU
    here does NOT prove poor ASL (no Deaf-signer eval done) — and we make no quality claim either way.
  - Heuristic error tagger (not human-coded): context buffer **cuts pronoun-referent errors 56→41** but
    adds **context-leak (57/220)**; RAG *raises* pronoun errors (56→75). Hypothesis for Week-9 human pass.
  - **Verdict:** reproduction ❌ (0.04 vs paper 0.276; incomplete pipeline); infrastructure ✅ (runs
    end-to-end on real data w/ manifests); contributions ⚠️ not supported on BLEU.

### 🚧 Blocked / waiting
- **Full ASLLRP corpus** — 51 of 84 SignStream files downloaded (~2,286 of ~2,119+ pairs). Export the
  rest from the DAI the same way. ASLLRP data must never be committed.
- **ASLLRP Sign Bank dictionary (Phase A4)** — the `data/dai/` zips are the continuous-signing corpus,
  NOT the Sign Bank. The 3,915-entry word→gloss dictionary needs a **separate** Sign Bank download
  (`dai.cs.rutgers.edu/dai/s/signbank`; ASLLRP Report 20).
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
| 5 | ~~Email paper authors re: sharing Module 1 prompts?~~ | **Mostly moot (2026-07-16):** prompts recovered from the paper's own TeX (Phase A0). |
| 6 | Commit transcribed paper prompts to `prompts/`, or keep verbatim text gitignored? | Repo convention says no paper text in tracked files; the reproduction needs the prompt wording. Team call. |
| — | Fix "Kim et al." → "Guo, Li & Cohn" citation | Bibliography correctness before final report. |

---

## Changelog

Newest first. One entry per meaningful change; keep it short.

- **2026-07-17** — **Four-condition ASLLRP pilot, FULL 220-sentence test set** (51 collections, local
  gemma4). BLEU-4: baseline 0.043 / rag 0.042 / context 0.041 / context+rag 0.042 — **all tied; neither
  contribution moved BLEU.** Overturns the earlier n=50 "RAG dominates" (small-sample artifact). Verdict:
  reproduction ❌, infrastructure ✅, contributions ⚠️ unsupported on BLEU. Report:
  `docs/results_report_asllrp.md`.
- ~~**2026-07-17** — First four-condition ASLLRP pilot (n=50): apparent "RAG dominates" — **superseded**
  by the full 220-sentence run above (artifact of a question-heavy 50-sentence slice).~~
- **2026-07-16** — **Phase A0 + NMM evaluation track** (ASLLRP-independent M1 work, per
  `docs/faithful_reproduction_plan.md` §8). Downloaded and mined the paper's arXiv TeX source
  (gitignored `data/paper_src/`): exact prompts for both Module-1 tasks recovered (incl. the
  multi-prompting structure — batches go in as repeated ASSISTANT messages), preprocessing
  Steps 1–4, grammar-rules text, gloss-conventions table, and all target numbers verified
  (BLEU-4 0.276 = data-prep + 1,474 examples + limited vocab + **no** grammar rules; NMM macro
  0.91/0.97; figure alt-text "0.05" conditional recall shown to be a typo for ≈0.95).
  **Discovered the paper's appendix already implements RAG** (anonymized embeddings, top-N;
  N=50 ≈ 0.279 beats all-1,474) → reframed contribution 1 as reproduction + extension in
  `ROADMAP.md` / landscape / decision log; context buffer stays the primary novelty. Wrote
  `docs/primary_source_findings.md`. Built the NMM gold-label pipeline: annotation rubric
  (`docs/nmm_annotation_rubric.md`), sheet/κ/adjudication/merge tooling
  (`scripts/nmm_annotation.py`, `src/aslgloss/evaluation/agreement.py`), and wired
  `nmm_scores` into `scripts/evaluate.py` (macro columns + `results/nmm_summary.csv`;
  clean skip when no gold exists). 4 new tests; 11 total pass. End-to-end smoke-tested the
  full sheets→κ→merge→evaluate loop on scratch data (never written to the real gold path).
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
