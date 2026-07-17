# Plan — Faithful Reproduction of CHI 2025 Module 1

> **Purpose of this doc.** Lay out everything needed to turn our current *preliminary bring-up* into a
> **faithful reproduction** of Zhang et al. (CHI 2025) Module 1 — the experiment that can actually be
> compared to the paper's reported numbers (BLEU-4 ≈ 0.276; NMM precision 0.91 / recall 0.97). This is
> a **plan only** — no implementation yet. This doc fleshes out milestone **M1** in `ROADMAP.md`.
>
> Status: **Phase A0 COMPLETE; Phase A STARTED (2026-07-16)** — the paper's TeX source is mined
> (`docs/primary_source_findings.md`); **DAI access granted and `load_asllrp()` implemented** against
> the real DAI 2 XML (156 pairs from the first 4 collections downloaded). Remaining Phase-A gates:
> export the rest of the 84-file corpus, do the Step-1/2 cleaning, and **download the Sign Bank** for
> the dictionary (A4 — still blocked on that separate download). Decisions marked ⛔ are blocking.

---

## In plain words

Right now our numbers are a *warm-up*: a small local model, a **synthetic** dataset (ASLG-PC12), only
20 sentences, and we only scored one of the paper's two metrics. That's fine for testing the plumbing,
but it is **not** a reproduction — so we can't honestly say whether we hit the paper's result.

To make it a real reproduction, we have to rebuild the experiment on the **same footing** as the paper:
the **same dataset** (ASLLRP — the real, Deaf-produced data), the **same way of feeding examples** to
the model (all ~1,474 of them, not our 8), the **same gloss-writing rules**, the **same allowed
vocabulary**, and we have to score **both** of the paper's metrics — the translation score *and* the
face-marker score. The one thing we're allowed to change is the model itself (GPT-4o if we can get it,
otherwise another large model), because that snapshot may not be available — and we'll label that swap
honestly as our single deliberate deviation.

The single biggest gate: **we need ASLLRP access.** Without it, a faithful reproduction is impossible —
everything else waits on that.

---

## 1. What "faithful" means here

A reproduction is *faithful* if **every experimental choice matches the paper except ones we cannot
control, each of which is documented as a labeled deviation.** The user has authorized exactly one
deviation up front: **the model** (GPT-4o may be deprecated/unavailable; a comparable large model is
acceptable). Everything else — data, split, prompting strategy, vocabulary constraint, gloss
conventions, metrics — stays as close to the paper as the public description allows.

---

## 2. The target: the paper's Module 1 spec

Sourced from Zhang et al. §3.1 and Appendix B/D (see `ATTRIBUTION.md`, `compass_artifact_*.md`).

| Element | Paper's choice | Notes |
|---|---|---|
| **Model** | `gpt-4o-2024-05-13` | Chosen after comparing GPT versions (App. B.3.1). |
| **Task 1 — gloss** | Few-shot English→ASL gloss | In-context example pairs injected into the prompt. |
| **Few-shot pool** | **~1,474–1,494 pairs** (80% split) | §3.1 says 1,494; ablation says 1,474. Use "≈1,474–1,494". |
| **Prompting strategy** | **"Multi-prompting"** | Examples don't fit one context window → batched, iterative prompting. |
| **Vocabulary constraint** | **3,915-entry word–gloss dictionary** | Output constrained to this vocab; 43 OOV words → fingerspelling. |
| **Task 2 — NMM** | Zero-shot, 4 labels | yes/no-Q, wh-Q, conditional, negation. Primary marker: eyebrows. |
| **NMM labels** | 4-researcher ground-truth correction | Human-corrected gold labels — needed to score P/R. |
| **Data source** | **ASLLRP** | 2,119 pairs → cleaned to **1,843** → 80/20 split. |
| **Gloss conventions** | Appendix conventions table (real ASL) | **VERIFIED (A0.2)** — ASLLRP notation: `fs-X-X-X`, `#loan`, `ns-`, `+` compounds, `QMwg`, `i:VERB:j` agreement, `IX-/POSS-/SELF-` families, aspect suffixes. Confirmed: nothing like ASLG-PC12 pseudo-gloss. See `docs/primary_source_findings.md` §6. |
| **Metric 1** | **BLEU-4 = 0.276** | **VERIFIED (A0.3).** On their ASLLRP test split (~369) — best config is data-prep ON + 1,474 examples + limited vocab ON + **grammar rules OFF** (rules mostly hurt BLEU in their ablation). Known wrinkle: their RAG appendix's own "no-RAG" baseline is ≈0.244 over 10 reps — unexplained gap vs 0.276; state it in the comparability note. |
| **Metric 2** | **NMM precision 0.91 / recall 0.97** | **VERIFIED (A0.3).** Per-label: y/n-Q 0.98/0.93 · wh-Q 0.93/0.98 · negation 0.79/1.00 · conditional 0.95/≈0.95 (figure alt-text "0.05" is a typo — only ≈0.95 averages to 0.97). |
| **RAG (appendix!)** | Anonymized-embedding top-N retrieval | **NEW FINDING (A0):** the paper's appendix already implements RAG (names→pronouns anonymization, OpenAI embeddings, cosine top-N; N=50 anon ≈ 0.279 beats all-1,474). Our contribution 1 must be reframed as reproduction + extension. See `docs/primary_source_findings.md` §3. |

---

## 3. Where we are now vs. the paper (the gap)

| Element | Current state | Paper | Gap to close |
|---|---|---|---|
| Model | `gemma3:4b` (local) | `gpt-4o-2024-05-13` | **Authorized deviation** — use GPT-4o or a large substitute. |
| Dataset | ASLG-PC12 (synthetic) | ASLLRP (Deaf-produced) | ⛔ **Need ASLLRP access.** `load_asllrp()` is a stub. |
| Examples fed | 8 static shots | ~1,474 via multi-prompting | Build the multi-prompting batching path. |
| Vocab constraint | pool-derived approximation | 3,915-entry dictionary | Build/derive the dictionary from ASLLRP; wire as the constraint. |
| Gloss conventions | ASLG-PC12 pseudo-gloss (`X-I`/`DESC-`) | Real-ASL (App. D) | **New prompt + conventions** for real ASL. |
| Test split | dedup tail of ASLG-PC12, N=20 | ASLLRP 20% (~369) | Replicate their 80/20 split + preprocessing. |
| Metric — BLEU | ✅ measured (0.249) | 0.276 | Re-measure on ASLLRP test split. |
| Metric — NMM P/R | ❌ **not measured** | 0.91 / 0.97 | Need gold NMM labels + wire `nmm_scores` into `evaluate.py`. **Not gated on ASLLRP** — see below. |
| Sample size | N=20 (preliminary) | full test split | Score the whole test split. |

**Hard blocker (⛔):** ASLLRP data access gates the *gloss/BLEU* half. The **NMM half is NOT gated on
ASLLRP** — the four labels (yes/no-Q, wh-Q, conditional, negation) are properties of the *English*
sentence, not of the ASLLRP glosses, so gold labels can be produced on any English sentences and the
NMM P/R reproduction can proceed *in parallel* while ASLLRP access is pending.

---

## 4. Blockers & prerequisites (settle these FIRST)

1. ⛔ **ASLLRP access.** Request via the Rutgers Data Access Interface (`dai.cs.rutgers.edu/dai/s/dai`).
   License = research/education only, **no redistribution** → data stays local, gitignored, never
   committed. *This is the critical path — start it before anything else.* If access is delayed, the
   faithful reproduction cannot proceed; see Fallback below.
2. **NMM gold labels** (NOT blocked by ASLLRP — can start now). The paper hand-corrected NMM labels with
   4 researchers. The four labels are English-syntax properties (wh-word present, negation present,
   if-clause present, polar-question form), so they can be annotated on any English sentence set —
   independent of the ASLLRP glosses. Decide the source:
   - (a) Hand-annotate a set of English sentences ourselves (mechanical/objective; tractable) with a
     documented rubric and inter-rater agreement (Cohen's κ), mirroring the paper's multi-annotator setup.
   - (b) If/when ASLLRP lands, check whether its annotations already encode question/conditional/negation
     structure we can derive — but do not wait on this to start (a).
3. **Model decision.** GPT-4o (`gpt-4o-2024-05-13` if still served, else current GPT-4o) vs. a large
   substitute (e.g. a frontier API model or a large open model). Record the exact model + snapshot in
   the manifest. This is the one authorized deviation — **label it as such in every write-up.**
4. **Budget.** Multi-prompting with ~1,474 examples over a test set on a paid API has real token cost.
   Estimate before running; the manifest already logs per-run cost.

---

## 5. The reproduction plan (phased — no code yet)

### Phase A0 — Pull the primary source ✅ DONE 2026-07-16
- A0.1. ✅ TeX source downloaded to gitignored `data/paper_src/` (tarball + `extracted/`).
- A0.2. ✅ Appendices extracted: preprocessing Steps 1–4, grammar-guidelines text, model-selection
  table, prompt variants table, gloss-conventions table, **plus the exact prompt wording for both
  tasks** (from the Module-1 figure) and the previously unknown **RAG appendix**. Verbatim →
  `data/paper_src/EXTRACTION_NOTES.md` (gitignored); own-words summary →
  `docs/primary_source_findings.md` (tracked).
- A0.3. ✅ Targets verified (0.276; 0.91/0.97 with per-label breakdown; conditional-recall alt-text
  typo identified and resolved arithmetically).
Deviation #2 is now closed to a residual (one figure-vs-alt-text punctuation discrepancy; no
published split seed), and the Phase-B PROVISIONAL flag is removed.

### Phase A — Data (unblocks everything)
- A1. ✅ **DONE (2026-07-16):** DAI access granted; first collection zips downloaded to gitignored
  `data/dai/`. `load_asllrp()` implemented — parses DAI 2 `xml_extract_*.xml` (`<UTTERANCE>` →
  `<TRANSLATION>` + ordered `<SIGN><LABEL>` gloss), with optional signing-NMM from the sentence-type
  `<NON_MANUAL>` tiers. Verified on 4 Ben-narrative collections → **156 real English↔gloss pairs**
  (real conventions: `fs-`, `IX-3p:i`, `DCL:B"…"`, `(2h)`). Test: `tests/test_asllrp.py`. **Only 4 of
  the corpus's 84 SignStream files are downloaded so far — export the rest the same way to approach
  the paper's ~2,119.**
- A2. Replicate the paper's preprocessing: 2,119 → 1,843 cleaned pairs (Appendix B, Steps 1–2:
  drop meaning-preserving markers; normalize fingerspelling to letter-hyphenated `fs-J-O-H-N`; unify
  spatial indices; drop classifiers). Sign types are available per token (`SIGN_TYPE`), so this is now
  implementable.
- A3. Reproduce the **80/20 split** (~1,474 train / ~369 test). Record the seed and method. Guard against
  the same leakage class we already fixed for ASLG-PC12. *(A document-level split path is wired in
  `download_data.py --dataset asllrp` as a starting point.)*
- A4. Build the **3,915-entry word–gloss dictionary** from the **ASLLRP Sign Bank** — ⛔ **official
  version still blocked:** the downloaded `data/dai/` zips are the continuous-signing corpus, NOT the
  Sign Bank. The web Sign Bank (`dai.cs.rutgers.edu/dai/s/signbank`) is a search UI with **no bulk
  export**; requested a machine-readable export from Carol Neidle (carol@bu.edu) on 2026-07-17.
  - **Interim (2026-07-17):** built a **corpus-derived approximation** from the pool only (no leakage)
    via `scripts/build_gloss_dictionary.py` → `data/processed/asllrp/gloss_dictionary.json`: **909
    word→gloss entries**, 3,202-token gloss vocab. Coverage of the held-out test set: **59% of input
    words** have an entry; **80% of *lexical* reference gloss tokens** are in-vocab, but **20% of all
    reference tokens are non-lexical** (`IX-`/`SELF-`/prosody) and are not text-derivable — a hard BLEU
    ceiling no dictionary can lift. **Decision (team): HOLD** — do the real vocabulary work once, with
    the official Sign Bank, rather than ship an exploratory glossary-hint condition now. The dictionary
    is NOT the Sign Bank and must not be labeled as such.

### Phase B — Prompts & conventions (real ASL, not pseudo-gloss)
- B1. Author a **real-ASL gloss prompt** matching the now-verified conventions table (A0.2 ✅ —
  see `docs/primary_source_findings.md` §6; verbatim wording in `data/paper_src/EXTRACTION_NOTES.md`)
  — distinct from the current ASLG-PC12-style `baseline_gloss.md`. Keep both; select by dataset.
  Blocked only on the team's call about committing transcribed prompt text (see deviations register #2).
- B2. Write a matching **real-ASL conventions section** in `docs/gloss_conventions.md` (we flagged this
  as future work there).
- B3. NMM prompt (`baseline_nmm.md`) already matches the paper's 4-label zero-shot design — review only.

### Phase C — Faithful few-shot mechanism
- C1. Implement the **multi-prompting** batching path: feed ~1,474 examples in batches, not 8 static
  shots. This is the paper's actual baseline; our 8-shot config is a separate (weaker) comparator.
- C2. Wire the **dictionary vocabulary constraint** (from A4) into generation + OOV→fingerspelling.

### Phase D — Evaluation (both metrics, full split)
- D1. Run BLEU-4 on the full ASLLRP **test split** (~369), `tokenize="none"` (already in `metrics.py`).
- D2. **Wire NMM P/R into `evaluate.py`** — `nmm_scores()` exists in `metrics.py` but is not currently
  called by the eval script; connect it and feed the gold labels from prerequisite #2.
- D3. Report BLEU-4 + NMM precision/recall/F1 side-by-side with the paper's 0.276 / 0.91 / 0.97, with the
  comparability statement (below).

### Phase E — Honesty & write-up
- E1. Fill the **deviations register** (§6) with every actual deviation.
- E2. State plainly: even a faithful reproduction on ASLLRP is *approximate* — we lack the paper's exact
  prompt text (never released), their exact preprocessing details beyond Appendix B, and (if applicable)
  their exact model. Proximity to 0.276 is evidence of a sound re-implementation, **not** proof of
  identity.

---

## 6. Deviations register (fill during implementation)

Every row is a place where we could not match the paper exactly. Keep it honest and complete.

| # | Element | Paper | Ours | Why we deviated | Effect on comparability |
|---|---|---|---|---|---|
| 1 | Model | `gpt-4o-2024-05-13` | *(TBD — GPT-4o or substitute)* | Snapshot may be unavailable (user-authorized) | Absolute scores shift; document model. |
| 2 | Prompt text | In the Module-1 figure + prompt-variants table, not as runnable files | Faithful transcription (verbatim in gitignored `data/paper_src/EXTRACTION_NOTES.md`; whether transcriptions may be committed to `prompts/` is an open team decision) | Not released as files; recovered via A0 | Minor. Residual: figure image vs alt-text disagree on trailing-punctuation instruction (we follow the updated image). |
| 3 | NMM gold labels | 4-researcher corrected | *(TBD — derived or self-annotated)* | Their labels unreleased | Our P/R rests on our labels. |
| … | | | | | |

---

## 7. Definition of done (M1 faithful baseline)

- [ ] Running on **ASLLRP** with the paper's preprocessing + 80/20 split (data local, uncommitted).
- [ ] **Multi-prompting** few-shot (~1,474 examples), dictionary-constrained vocab, fingerspelled OOV.
- [ ] **Real-ASL** gloss conventions (App. D), not ASLG-PC12 pseudo-gloss.
- [ ] **Both** metrics reported on the full test split: BLEU-4 **and** NMM precision/recall/F1.
- [ ] Every run has a manifest; the deviations register is complete; the comparability caveat is stated.
- [ ] The one authorized deviation (model) is labeled as such wherever the number appears.

---

## 8. Fallback if ASLLRP access is delayed

A faithful reproduction **cannot** be done on ASLG-PC12 — it is synthetic, has no NMM gold labels, and
uses different gloss conventions. If access stalls:
- Do **not** relabel ASLG-PC12 numbers as a "reproduction." They stay explicitly preliminary.
- **Make real progress in parallel** — two tracks don't need ASLLRP: (i) **Phase A0** (pull the paper's
  TeX prompts/conventions/targets), and (ii) the **NMM P/R reproduction** (self-annotated English
  sentences + κ, then wire `nmm_scores` into `evaluate.py`). Both directly advance M1 while data access
  is pending.
- Optionally strengthen the *internal* comparison meanwhile (a representative static baseline, larger N,
  a bigger model on ASLG-PC12) — useful, but clearly *not* the paper reproduction.
- Consider the low-cost step already noted in `ATTRIBUTION.md`: email the corresponding authors
  (Colin Lea / Han Zhang) to ask whether the Module 1 prompts can be shared.

---

## 9. Open questions for the next session

- ⛔ Is ASLLRP access obtained yet? (Critical path. **Requested 2026-07-16 — pending.**)
- ~~⛔ Where do NMM gold labels come from?~~ **ANSWERED (A0):** the paper's gold labels are
  English-text properties, hand-corrected by 4 researchers on the test set (Appendix, Step 4).
  We replicate with self-annotation + κ — kit in `docs/nmm_annotation_rubric.md` + `scripts/nmm_annotation.py`.
- **NEW (A0):** how do we reframe contribution 1 given the paper's own RAG appendix? (Reproduce
  their anonymized-embedding variant? Ablate anonymization as one of our extensions?)
- Which model, exactly, and is `gpt-4o-2024-05-13` still served?
- Do we reproduce **multi-prompting** faithfully, *and* keep the cheaper 8-shot as a labeled separate
  comparator? (Recommended: yes to both — see the baseline-fairness open question in `decision_log.md`.)
- Token-cost budget ceiling for the multi-prompting run?

---

## Honesty constraints (carry over from CLAUDE.md)

- ASLLRP data is **never committed** (license forbids redistribution).
- The model swap is the **only** authorized deviation and must be labeled everywhere the result appears.
- A number without a manifest, a stated limitation, and a decision-log entry does not go in the report.
- Even a clean ASLLRP reproduction is *approximate* (unreleased prompts/preprocessing) — never claim identity.
