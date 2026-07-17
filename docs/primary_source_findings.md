# Primary-source findings — Zhang et al. (CHI 2025) TeX source (Phase A0)

**Status:** Phase A0 of `docs/faithful_reproduction_plan.md` is complete (2026-07-16).
We downloaded the paper's arXiv source (arXiv 2502.05661) and read the method, evaluation, and
appendix files directly. This page records what that changes for us, **in our own words** — per
repo convention, no paper text or figures are reproduced in tracked files. Verbatim extractions
(exact prompt wording, appendix text, full tables) live in the gitignored
`data/paper_src/EXTRACTION_NOTES.md`; the raw TeX is under `data/paper_src/extracted/`.

---

## In plain words

We went to the paper's own source files instead of relying on second-hand summaries. Almost
everything we were missing is actually in there: the exact wording of the prompts, the exact
data-cleaning recipe, the gloss-writing rules, and the real score tables. Three things we thought
were unknowns are now known. One finding is uncomfortable but important: the paper's appendix
already tried the "retrieve similar examples" idea we planned as our first contribution — so we
must reframe that contribution honestly as a reproduction and extension, not an invention.

---

## 1. Target numbers — verified against the primary source ✅

- **BLEU-4 = 0.276** is confirmed as the headline text→gloss number (intro + main results table).
  The winning configuration is: data preprocessing ON, all ~1,474 examples (80% split),
  **dictionary-limited vocabulary ON, grammar rules OFF**.
- **NMM average precision 0.91 / recall 0.97** confirmed (intro). Per-category values (from the
  results figure): yes/no-question P 0.98 / R 0.93 · wh-question P 0.93 / R 0.98 · negation
  P 0.79 / R 1.00 · conditional P 0.95 / R ≈ 0.95.
  - The figure's alt-text says conditional recall "0.05"; that is arithmetically impossible given
    the claimed 0.97 average (the four recalls only average to ≈0.97 with ≈0.95) and contradicts
    the caption's "high performance across all categories." We treat it as a typo for ≈0.95 and
    will note this in the report.
- Known internal inconsistency: the RAG appendix's "no-RAG, all examples" baseline is ≈0.244
  (mean of 10 test-set repetitions), well below the main table's 0.276 for the nominally same
  configuration. The paper doesn't explain the gap. We will compare against 0.276 as published,
  and mention this discrepancy in the comparability statement.

## 2. The prompts are recoverable — deviation #2 mostly closes ✅

The paper's figure and appendix tables contain the actual prompt wording for both tasks:

- **Gloss task:** a SYSTEM message establishing the translator role and attaching the word→gloss
  dictionary; the example pairs injected as a **sequence of repeated ASSISTANT messages, one per
  batch** (this is what "multi-prompting" concretely means — not iterative re-querying); then one
  USER message per sentence asking for the translation, restricting output to the provided
  vocabulary, forbidding extra output, and forbidding trailing punctuation.
- **NMM task:** a SYSTEM message defining the four yes/no judgments (yes/no-question, wh-question,
  conditional, negation) and a USER message asking for a bare comma-separated 1/0 quadruple in
  that order.
- The appendix prompt-variants table gives the SYSTEM wording for all four ablation cells
  (± vocabulary, ± grammar rules), and the appendix contains the full ASL grammar-guidelines text
  used for the grammar-rules condition. Note the best configuration does **not** use the grammar
  rules — in their ablation the rules usually *lowered* BLEU.
- One wording discrepancy exists between the figure image (no trailing punctuation) and its
  alt-text (keep ASL punctuation at the end); the worked example follows the image, so we take the
  image as authoritative and log this as a residual uncertainty.

**Open team decision:** whether to commit faithful transcriptions of these three short prompt
templates as runnable files in `prompts/` (with citation), or keep the verbatim text gitignored
and load it at runtime. Until decided, verbatim wording stays only in `data/paper_src/`
(see `docs/decision_log.md`).

## 3. The paper already ran RAG — our contribution 1 must be reframed ⚠️

An appendix section ("Additional Experiments on English-to-Gloss Translation") implements
retrieval-augmented example selection: train sentences are anonymized (names → pronouns), embedded
with an OpenAI embedding model, and the top-N most cosine-similar examples are retrieved per test
sentence. Their findings: RAG with as few as 50 anonymized examples (BLEU-4 ≈ 0.279) beats feeding
all ~1,474 examples; anonymization helps because names dominate embedding similarity.

Consequences for us:
- Our RAG condition is a **reproduction/extension of their appendix**, not a novel contribution.
  Our honest framing: (i) we reproduce the retrieval effect; (ii) our extensions are what's new —
  ablating k, the leakage-guarded deduplicated split (they don't report one), cost accounting,
  and combining retrieval with the context buffer (they are explicitly context-free).
- Their anonymization trick is worth adopting/ablating in our retriever.
- The **paragraph-context buffer remains the standout novel contribution** — the paper states its
  scope is context-free, sentence-by-sentence translation.
- `docs/landscape_generative_slg.md` and `ROADMAP.md` framing needs this correction (logged in
  `docs/decision_log.md`).

## 4. Preprocessing recipe (Appendix B) — now concrete ✅

Four steps, all reproducible once ASLLRP access lands:
1. **Extract** from SignStream XML exports (DAI 2): English sentences + chronologically spliced
   English-based annotations (incl. fingerspelling, name signs, classifiers, locatives, gestures)
   → 2,119 pairs.
2. **Clean**: drop meaning-preserving annotations (repetition "+", one/two-hand markers,
   alternating-hands marker); normalize fingerspelling to letter-hyphenated form
   (fs-JOHN → fs-J-O-H-N); unify spatial-location indices; drop classifiers (too sparse)
   → 1,843 pairs.
3. **Dictionary**: build the word→gloss dictionary from the **ASLLRP Sign Bank** (not from the
   sentence pairs!), same normalization, one-to-many mappings allowed → 3,915 entries; 43 OOV
   words fall back to fingerspelling.
4. **Gold-label correction**: the XML sentence-type labels follow the *signing*, not the English
   text; four researchers re-labeled the **test set** so labels reflect the English text. These
   corrected labels are the ground truth behind P 0.91 / R 0.97.

Notes: split is random 80/20, no seed or method published (residual deviation). The dictionary
source being the Sign Bank means our ASLLRP data request should include the Sign Bank export
(it does — access request already covers it).

## 5. NMM gold-label plan is validated ✅

Step 4 (above) confirms the plan's §4.2 assumption: the paper's NMM ground truth is a property of
the **English sentence**, produced by human re-annotation — exactly what we can replicate without
ASLLRP. Their negation false-positives were negative-*sentiment* sentences (e.g. hate/blame
phrasings), which matches the "voted against" ambiguity we flagged in our own preliminary run and
is now encoded in our rubric (`docs/nmm_annotation_rubric.md`).

## 6. Gloss conventions (Appendix D) — PROVISIONAL flag can come off ✅

The conventions table is in the source: multiword signs hyphenated; slash alternates;
`fs-` letter-by-letter fingerspelling and `#` loan signs; `ns-` name signs; `+` compounds;
`QMwg` question marker; verb agreement indices (`i:VERB:j`, person forms); `IX-`/`POSS-`/`SELF-`
pronoun/possessive/reflexive families with person and locus suffixes; quoted locative/directional
adverbials; plural/arc forms; aspect suffixes (e.g. continuative, distributive); reciprocal forms.
As suspected, this is a different world from ASLG-PC12's rule-generated pseudo-gloss (`X-I`,
`DESC-`, kept punctuation) — the ASLLRP work needs its own prompt and a new section in
`docs/gloss_conventions.md` (plan Phase B), and BLEU across the two conventions is never
comparable.

## 7. Other pinned facts

- Example-count ambiguity resolved: §3.1 says 1,494; every ablation table uses 1,474 (80%).
  Both appear in the paper itself; we keep "≈1,474–1,494" and will match 1,474 in experiments.
- Model choice history: GPT-4o-2024-05-13 won their model bake-off (BLEU-4 0.226 at n=300 with
  vocabulary limit, vs 0.176 for GPT-4-0125-preview); GPT-3.5 fine-tuning reached only 0.161.
- Metrics suite: BLEU-1..4, ROUGE-L, METEOR, CHrF, TER; SacreBLEU equals their BLEU-4 (their
  footnote), which supports our exact-token sacrebleu setup.
- Test split ≈ 369 sentences (20% of 1,843).
- The paper is explicitly **context-free** (sentence-independent) by design — stated in their §3.
