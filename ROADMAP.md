# Roadmap

The plan for the coming weeks. Milestones follow the independent-study proposal; this file is the
working version the team executes against. Pair it with `PROGRESS.md` (status) and
`docs/decision_log.md` (why).

*As of 2026-07-12 the project is at **Week 1–2** (repository setup / baseline bring-up). Nothing has
been run yet — `data/` and `results/` are empty by design.*

---

## In plain words

Over the next several weeks we will, in order: (1) finish wiring up the machinery and get a first
honest baseline score, (2) turn on our two improvements one at a time and measure whether each
actually helps, (3) look carefully at *what kinds of mistakes* the system makes — not just the
average score, (4) test whether the same setup could work for Indian Sign Language (a "can this even
transfer?" probe, not a graded result), and (5) write it all up honestly, including the parts that
didn't work. The single most important rule throughout: **be honest about limitations** — a good
score on a flawed dataset is not a real win.

---

## Strategic framing (from the 2025 landscape review)

Full survey in `docs/landscape_generative_slg.md`. Four findings reshape how we position and evaluate:

1. **The context buffer (Contribution 2) is our strongest novelty.** No published work applies a
   paragraph/discourse context buffer to text→gloss *production* (context results exist only on the
   sign→text side). Zhang et al. explicitly work "context-free." → invest here; evaluate on a
   contrastive discourse set, not corpus BLEU.
2. **RAG retrieval (Contribution 1) is worthwhile but not unprecedented — reframe it.** A Nov-2025
   Bangla text→gloss paper already uses RAG few-shot, and retrieval-based example selection is standard
   in MT. Our honest delta: **first for ASL, integrated with non-manual markers, beating Zhang's random
   multi-prompting baseline.** Guard against **test-set leakage** with a de-duplicated split.
3. **Gloss ordering is the best-documented LLM failure** (English word order in gloss) → our optional
   **Phase 3 reordering pass** (M4.5) directly targets it.
4. **Metric hygiene over headline BLEU.** Corpus BLEU barely moves for the context contribution and
   undersells it. Adopt: fixed-tokenization SacreBLEU + a semantic metric + a contrastive discourse
   set; prefer **ASLLRP (Deaf-produced)** over **ASLG-PC12 (synthetic)** for credible claims; plan
   Deaf-led human evaluation.

Also correct an overstatement: our ISL docs say "no gloss annotations exist at all" — the safe claim is
"no *large, public, Deaf-produced* ISL gloss corpus exists" (small expert-built sets do exist).

---

## Milestones

### M0 — Foundations (now → next session) · unblocks everything
**Goal:** the pipeline runs end-to-end on a tiny sample and the two biggest measurement threats are
decided before any number is trusted.

Tasks:
- Decide **baseline fairness**: 8-shot static vs. reproducing the paper's ~1,474-shot multi-prompting.
  Recommended: run *both* and report both (an 8-shot baseline can flatter our RAG condition). → record in `docs/decision_log.md`.
- Define a **proper, documented test split** to replace the naive tail slice in
  `scripts/download_data.py`. → `scripts/download_data.py`, `docs/decision_log.md`.
- **Align gloss conventions to ASLG-PC12 — confirmed mismatch.** A real-data check (2026-07-12) shows
  the corpus uses `X-I`/`X-IT` (not our prompt's `IX`), a `DESC-` prefix for descriptors, and **keeps
  punctuation** (our prompt drops it). Left unfixed, BLEU penalizes the baseline on notation alone.
  → update `prompts/baseline_gloss.md` + `prompts/context_gloss.md`, finalize `docs/gloss_conventions.md`.
- Smoke-run `make data && make index && make baseline` on `n_examples: 5` with a cheap model.

**Exit criteria:** `make baseline` produces a `results/<run_id>/` with `predictions.jsonl` +
`manifest.json`; the split and gloss conventions are written down; the baseline-fairness decision is
logged.

---

### M1 — Baseline reproduction (toward Week 6)
**Goal:** a defensible reproduction of CHI 2025 Module 1 on ASLG-PC12.

Tasks:
- Run `configs/baseline.yaml` at full `n_examples` with `gpt-4o-2024-05-13` (and the open-model path
  as a reproducibility backup). → `scripts/run_experiment.py`.
- Report **BLEU-4** (target ≈ 0.276, *not* expected to match exactly — different corpus/preprocessing)
  and **NMM precision/recall** (target 0.91 / 0.97). State plainly why our numbers are not directly
  comparable to the paper's. → `scripts/evaluate.py`, `docs/decision_log.md`.

**Exit criteria:** baseline BLEU-4 + NMM P/R reported with the comparability caveat; cost/latency
recorded from the manifest.

---

### M2 — The four-condition experiment (Week 6 core)
**Goal:** isolate the effect of each contribution.

Tasks:
- `make all-conditions` → run `baseline`, `rag_only`, `context_only`, `context_plus_rag`.
- Run the **retrieval-order ablation** (`retrieval.order`: `similarity_desc` / `similarity_asc` /
  `random`) per KATE. Optionally test a second embedding model. → `configs/`, `retrieval/`.
- **De-duplicated split (leakage guard):** ensure retrieved examples are not near-duplicates of test
  items, or RAG BLEU is inflated. Report the dedup method. → `scripts/download_data.py`, `retrieval/`.
- **Metric hygiene:** fixed-tokenization SacreBLEU (record the signature), add a semantic metric, and
  do **not** lead with corpus BLEU for the context contribution — use the discourse set (M3).
- `make eval` → `results/summary.csv` with BLEU-4, ROUGE/exact-match, latency p50/p95, and cost per
  condition. (ROUGE/exact-match need wiring — see tech-debt track.)

**Exit criteria:** one table comparing all four conditions on quality + latency + cost; the ordering
ablation reported; the dedup guard documented; RAG framed against Zhang's random multi-prompting; every
row traceable to a manifest.

---

### M3 — Structured error analysis (Week 6, the part BLEU can't do)
**Goal:** say *which* errors changed, on *what* content — the evaluation that actually speaks to the
community critique.

Tasks:
- Build the **hand-curated discourse probe set** (~50–100 short passages where meaning genuinely
  depends on prior sentences). This is the highest-value unglamorous task; auto-chunked paragraphs
  are not real discourse. → `data/` (gitignored) + a documented builder; `data/paragraphs.py`.
- Run `tag_errors` triage, then have **two team members independently code** each flagged case plus a
  random sample of unflagged ones. Report **Cohen's κ**. → `evaluation/error_analysis.py`,
  `docs/error_taxonomy.md`.
- Report error counts **by condition** — did context actually reduce `pronoun_referent` errors, or
  just move BLEU? Watch for `context_leak` (a risk our own contribution introduces).

**Exit criteria:** error-rate-by-condition table with inter-rater agreement; explicit statement of
whether context reduced discourse errors.

---

### M3.5 — Gloss reordering pass (optional Phase 3)
**Goal:** attack the best-documented LLM-gloss failure — output following English word order instead
of sign order (Guo/Li/Cohn, NeurIPS 2025).

Tasks:
- Add a lightweight post-generation reordering/verification step: `gloss (raw) → reorder → gloss (final)`.
  → new module under `src/aslgloss/baseline/` (e.g. `reorder.py`), wired as an optional stage in
  `GlossGenerator.generate`.
- Measure whether it reduces `gloss_ordering` errors (the taxonomy category) vs. the un-reordered run,
  by condition.

**Exit criteria:** reordering on/off comparison showing the change in `gloss_ordering` error rate and
BLEU. Keep it optional — do not let it delay M1–M3. Ship as "future work" if time is short.

---

### M4 — ISL feasibility extension (Week 7, EXPLORATORY)
**Goal:** test *architectural transfer* to Indian Sign Language. **No benchmarked quality score is
possible** — no large, public, Deaf-produced ISL gloss corpus exists (small expert-built sets do; they
are not standard benchmarks and we do not have references to score against).

Tasks:
- Wire an ISL path (config + loader) using `prompts/isl_gloss.md` (SOV, sentence-final wh — marked
  PROVISIONAL), optionally **seeded by a small expert-verified ISL word–gloss dictionary** (analogous
  to the paper's ASL dictionary). → new `configs/isl_*.yaml`, `data/loaders.py`.
- Show the retrieval + context machinery *assembles* on ISL passages; human spot-checks only, small
  n, clearly labeled. If ISL-fluent reviewers can't be arranged, **say so** rather than substituting
  our own judgment.

**Exit criteria:** a written account of what transfers (infra, context mechanism) vs. what does not
(gloss conventions, evaluation) — reported as a **finding, not a failure**. See `docs/isl_extension.md`.

---

### M5 — Reflective analysis & report (Week 9)
**Goal:** an honest write-up that answers the field's critique of this kind of work.

Tasks:
- Answer Yin et al. (2021) and Desai et al. (2024) directly: gloss as a lossy scaffold; synthetic-data
  limits; Deaf involvement. → report + `ATTRIBUTION.md` §5.
- Fold `docs/decision_log.md` into a methods section.
- Fix the **"Kim et al." → "Guo, Li & Cohn"** citation error before the final bibliography.

**Exit criteria:** final report with results, honest limitations section, and corrected citations.

---

## Technical-debt / hardening track (do alongside, not blocking)

These are code-quality items surfaced during the codebase review. None change results on their own;
each needs its own small PR + test.

- [x] **Function-level docstrings** added across `src/aslgloss/**` (this pass).
- [ ] **Fix `evaluation/metrics.py::summarize_run`** — it reads `r.reference`, which `GlossResult`
      does not have, so it is currently dead/broken. Either give it the right inputs or remove it and
      rely on `scripts/evaluate.py`. **Add a test.**
- [ ] **Move hardcoded values into config:** `build_paragraphs(size=5)` and the `data/processed/*.jsonl`
      paths in `run_experiment.py`; pool size + tail-slice split in `download_data.py`.
- [ ] **Widen test coverage:** `GlossGenerator`, `NMMClassifier` (with a mocked LLM), `retrieval/`,
      `data/loaders.py`, `data/paragraphs.py`.
- [ ] **Wire ROUGE + exact-match** metrics (README promises them; only BLEU is implemented).
- [ ] **Harden output parsing:** `GlossGenerator.generate` assumes single-line output;
      `NMMClassifier.classify` silently returns all-False on malformed JSON — at least log these.
- [ ] **Update / extend the `PRICING` table** in `llm/client.py` when models change (unknown model →
      cost silently 0.0).
- [ ] **Implement `load_asllrp`** once Rutgers DAI access arrives (never commit ASLLRP data).

---

## The recurring rule

Every milestone ends the same way: **write down what we did and why** (`docs/decision_log.md`),
**keep the manifest** (so results are reproducible), and **state the limitation out loud**. A number
without those three things does not go in the report.
