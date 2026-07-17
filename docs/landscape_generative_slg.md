# Landscape: Generative Sign Language (Text → Sign), 2023–2025

A survey of where the research field stands, prepared to guide this project's improvement plan.
Emphasis on 2023–2025 work in sign language **production/generation** (text → sign), not recognition.

> **Citation caveat:** these references were gathered via web search. A few were flagged as
> uncertain during collection (see **Uncertainties** at the end) — verify each source before citing
> it in the final report. Do not treat this file as a vetted bibliography yet.

---

## In plain words

There are two big ways researchers currently turn written language into sign language by computer:

1. **The step-by-step ("cascade") way** — first translate English into *gloss* (a written shorthand
   for signs), then turn gloss into body/hand poses, then render those poses as video or an avatar.
   **Our project sits at the very first step of this path** (English → gloss).
2. **The all-at-once ("gloss-free") way** — skip gloss entirely and generate the signing motion
   directly from text with a big neural network.

The all-at-once way is fashionable, but it needs huge amounts of data and produces something you
can't easily inspect or correct. The step-by-step way is criticized because gloss loses information —
but it has one big advantage for a small, responsible team: **a Deaf collaborator can actually read
and fix a gloss**, which you cannot do with a hidden numerical representation. That inspectability is
a legitimate reason to choose the gloss path, and it's worth stating as a deliberate choice.

The most important takeaways for us: our **paragraph-context idea is genuinely new** for this step;
our **example-retrieval (RAG) idea was already tried — including by the very paper we reproduce**
(discovered 2026-07-16 in their appendix; see §5), so we frame it as reproduction + extension; and
**the usual scoreboard metric (BLEU) hides most of what matters**, so we need better ways to
measure success.

---

## 1. The pipeline landscape

Three dominant paradigms, plus rendering as a cross-cutting fourth:

- **(a) Cascaded text → gloss → pose → video/avatar.** The classic decomposition. Text→gloss is a
  low-resource machine-translation problem; gloss→pose is sequence-to-sequence motion generation;
  pose→video is rendering. Progressive Transformers (Saunders et al., ECCV 2020) is the canonical
  model and introduced the still-common **back-translation** evaluation. Zhang et al. (CHI 2025) is a
  modern cascade of exactly this shape — and **our Stage 1 is the front of it**.
- **(b) Gloss-free end-to-end text → pose/video.** Motivated by the argument that the gloss bottleneck
  discards source information. Recent systems are diffusion- or vector-quantization-based: T2S-GPT
  (ACL 2024), SignDiff (2023), Text2Sign Diffusion (2025).
- **(c) LLM-prompted gloss / pseudo-gloss generation.** Prompt an LLM (GPT-4o/Gemini) with in-context
  examples to produce gloss (for production) or *pseudo-gloss* (as a training signal for translation).
  **This is where our Stage 1 and Guo/Li/Cohn (NeurIPS 2025) sit.**
- **(d) Rendering / avatars** (orthogonal): skeleton poses → photorealistic video or 3D avatars.
  Out of our Stage-1 scope.

**Why gloss-based text→gloss survives its critics:** modularity/inspectability (a Deaf collaborator
can read and correct gloss); it decouples the linguistic problem from motion synthesis; it is
data-efficient (works with a few hundred prompted pairs); and non-manual markers map cleanly onto
discrete gloss annotations. Our gloss-based, ASL-first framing is defensible on these grounds — state
it as a deliberate, ethically motivated choice, not a default.

## 2. Key systems & papers (2023–2025)

| System / paper | Venue | Paradigm | Code/data released? |
|---|---|---|---|
| Zhang et al., "Towards AI-driven SLG with Non-manual Markers" | CHI 2025 (Best Paper Hon. Mention) | Cascade; GPT-4o text→gloss+NMM → pose → video; 30-DHH user study | Apple project page; **no public code/model** found. Uses ASLLRP. |
| Guo, Li & Cohn, "Pseudo Gloss Generation" | NeurIPS 2025 | LLM (Gemini) in-context pseudo-gloss + weakly-supervised **reordering** for SLT | Code release not confirmed. |
| SignLLM | 2024 (arXiv) | Multilingual LLM-style production; Prompt2Sign dataset | Project page/dataset claimed; results **independently unverified**. |
| Progressive Transformers | ECCV 2020 | text→gloss→pose; back-translation metric | Code on GitHub. |
| Ham2Pose | CVPR 2023 | HamNoSys → pose; language-agnostic | Code on GitHub. (First author co-authored Zhang et al.) |
| T2S-GPT | ACL 2024 | Dynamic VQ, autoregressive gloss-free production | Paper available. |
| SignDiff | 2023 (arXiv) | Diffusion text2pose ASL + photoreal rendering | Paper available. |
| Text2Sign Diffusion | 2025 (arXiv) | Gloss-free latent diffusion + cross-modal aligner | Paper available. |
| "Lost in Translation, Found in Context" | 2025 (arXiv) | SLT (sign→text) using **contextual cues** (prior sentence, background) | Paper available. |
| Tanzer et al., "Reconsidering Sentence-Level SLT" | EMNLP 2024 | Human baseline; **33% of sentences need discourse context** | Paper available. |

Trend: pose/rendering papers tend to release code; the newest LLM-in-the-loop and industry systems
(Zhang et al., some diffusion works) often do **not** — a reproducibility gap our re-implementation
helps close.

## 3. Datasets & benchmarks

| Dataset | Language | Annotation | Size | Key limitation |
|---|---|---|---|---|
| RWTH-PHOENIX-2014T | DGS | video + gloss + text | 8,257 segments | Narrow weather domain; the over-used SLP benchmark. |
| How2Sign | ASL | video + English transcripts | 80+ hrs | **Gloss effectively absent** in standard release; instructional domain. |
| ASLLRP (DAI/SignStream) | ASL | **Deaf-native**, linguistically grounded | thousands of utterances | Small; but the quality asset — what Zhang et al. used (~1,843 pairs after prep). |
| **ASLG-PC12** (ours) | ASL "gloss" | **rule-generated**, synthetic | 100M+ synthetic pairs | High BLEU here means little linguistically — a known trap. |
| YouTube-ASL | ASL | video + English captions | 984 hrs, 2,500+ signers | Captions not gloss; alignment noise. |
| YouTube-SL-25 | 25+ SLs | video + captions | 3,000+ hrs | Caption-level; minimal ISL. |
| ISLTranslate | ISL | video ↔ English | 31k pairs | **No gloss** (deliberate). |
| iSign | ISL | benchmark aggregate | 118k pairs | **No gloss layer.** |
| CISLR | ISL | isolated word–video dictionary | ~7k | Isolated signs, not continuous/parallel. |

**The distinction that matters for us:** synthetic/rule-based gloss (ASLG-PC12) vs. Deaf-produced,
linguistically annotated gloss (ASLLRP). Metrics on synthetic gloss inflate without capturing real
ASL grammar. Use ASLG-PC12 for bring-up; move to ASLLRP for any credible claim.

## 4. Evaluation practices — and why "high BLEU ≠ good ASL"

Common metrics: BLEU-1–4, ROUGE-L, METEOR, chrF, TER (text↔gloss); back-translation and pose-distance
(DTW) for motion output; human comprehension/naturalness ratings (Zhang's 30-participant study is a
strong example). Why the headline score misleads:

- **Metric-implementation noise:** BLEU shifts >1 point with tokenization/tool choice, rarely stated.
- **Surface n-gram overlap ignores grammar:** blind to spatial referencing, classifiers, non-manual scope.
- **Back-translation compounds errors** and depends on a weak scoring model.
- **Synthetic-gloss inflation** (ASLG-PC12).
- **Sentence-level framing is itself wrong for discourse:** Tanzer et al. — only ~33% of clips are
  fully understandable without context, so sentence-isolated metrics systematically mismeasure.

**The critique canon to cite and answer:** Bragg et al. (ASSETS 2019); Yin et al. (ACL 2021,
"Including Signed Languages in NLP"); Desai et al. (2024, Deaf-led call — flags non-representative data
and linguistically ungrounded annotations); emerging semantic metrics (SiLVERScore, 2025) to watch.

## 5. LLMs for gloss — and the novelty test for our contributions

**Capabilities:** GPT-4o-class models produce draft gloss via in-context learning; Zhang et al. reach
BLEU-4 ≈ 0.276 with GPT-4o few-shot + a curated word-gloss dictionary. **Documented failures:**
- **Gloss ordering** — LLM output follows *spoken* word order, not sign order. The central problem
  Guo/Li/Cohn attack with a weakly-supervised reordering step. → motivates our optional **Phase 3**.
- **In-context-example sensitivity** — choice/number of examples materially moves scores.
- Non-manual grammar and spatial/classifier constructions are largely beyond current LLM gloss.

**Do our two contributions already exist?**
- **RAG example-retrieval for text→gloss: ALREADY EXISTS — in Zhang et al. themselves.**
  **Correction (2026-07-16, Phase A0):** reading the paper's arXiv TeX source revealed an appendix
  ("Additional Experiments") that implements exactly this: names→pronouns anonymization, OpenAI
  embeddings, cosine top-N retrieval; N=50 anonymized examples (BLEU-4 ≈ 0.279) beat all ~1,474.
  The earlier claim below ("first for ASL") is therefore **withdrawn**. A Nov-2025 **Bangla** paper
  also uses RAG + few-shot for text→gloss; retrieval-based example selection is standard in MT.
  **Our remaining defensible delta:** reproduction of their appendix effect + a **leakage-guarded
  de-duplicated split** (they report none), **k-ablation, anonymization ablation, cost accounting**,
  and **combining retrieval with the context buffer**. See `docs/primary_source_findings.md` §3.
  **Risk:** test-set leakage — retrieving near-duplicate pairs inflates BLEU; report a **de-duplicated
  split**.
- **Paragraph/discourse context for gloss *production*: essentially a gap.** Strong context results
  exist only on the *translation* (sign→text) side (Tanzer; "Lost in Translation" +5 BLEURT). No
  located work applies a paragraph context buffer to text→gloss *generation*, and Zhang et al.
  explicitly disclaim it. **This is our strongest, most defensible contribution.**

## 6. ASL vs ISL

- **Safe claim:** *no large, public, Deaf-produced ISL gloss corpus exists.* The flagship ISL
  resources (ISLTranslate 31k, iSign 118k) deliberately omit gloss.
- **Do not overstate:** small rule-based / expert-built ISL gloss sets *do* exist (e.g. a ~10,368-pair
  English–ISL set, IJSAT 2025; a rule-based converter, Springer 2022) — small, non-standardized, not
  benchmarks. → **Correct our `docs/isl_extension.md` / `ATTRIBUTION.md`**, which currently say "no
  gloss annotations exist at all."
- **Implication:** a benchmarked ISL gloss result is not feasible. A realistic angle is **exploratory
  architectural transfer** — English→ISL-gloss via LLM prompting seeded by a small expert-built
  dictionary, validated by ISL-fluent reviewers, explicitly labeled proof-of-concept.

## 7. Open problems & where the field is heading (2025+)

Gloss-vs-gloss-free tension unresolved (momentum toward gloss-free diffusion/VQ, but gloss retains
value for low-resource/modular settings); **discourse-level modeling is the frontier** (mostly
explored for translation, open for production); non-manual and spatial/classifier grammar
under-modeled; **evaluation reform** toward semantic metrics and Deaf-led human eval; push for larger,
representative, Deaf-produced data and participatory design.

## 8. Implications for THIS project

- **Context buffer (contribution 2) — invest here; it's the real novelty.** Borrow the mechanism from
  "Lost in Translation": feed **previous-sentence gloss + a short topic cue** into the prompt. Target
  pronoun/referent consistency, topicalization, negation/NMM scope. **Evaluate on a contrastive
  discourse test set, not corpus BLEU** (which will barely move and undersell it).
- **RAG retrieval (contribution 1) — now a reproduction + extension, not an invention.**
  *(Reframed 2026-07-16 after Phase A0 — Zhang et al.'s own appendix already does anonymized-embedding
  top-N retrieval; see §5 correction.)* Cite their appendix, the Bangla RAG-gloss, and MT
  example-selection work. Position as: reproducing their appendix effect under a leakage-guarded
  dedup split, plus k/anonymization ablations, cost accounting, and the retrieval×context combination.
- **ISL transfer — exploratory only.** Qualitative demo seeded by a small expert dictionary; ISL-fluent
  review; no quality claims.
- **Adjacent ideas:** add the **reordering pass** (our Phase 3); budget **Deaf-led evaluation**; adopt
  **metric hygiene** (fixed-tokenization SacreBLEU + a semantic metric + the discourse set); prefer
  **ASLLRP over ASLG-PC12** for credible claims; consider **open-sourcing the Stage-1 pipeline** since
  Zhang et al. released none.

**Bottom line:** the context buffer is the standout contribution; RAG is a faithful
reproduction + extension of Zhang et al.'s own appendix experiment (framed against that, the Bangla
RAG-gloss work, and their random multi-prompting baseline); ISL stays exploratory.

---

## References

Verify before citing. (arXiv / ACL Anthology / venue links as gathered.)

1. Zhang et al., CHI 2025 — arXiv 2502.05661 · machinelearning.apple.com/research/ai-sign-language-generation
2. Guo, Li & Cohn, NeurIPS 2025 — arXiv 2505.15438
3. Fang et al., SignLLM, 2024 — arXiv 2405.10718 · signllm.github.io
4. Saunders et al., Progressive Transformers, ECCV 2020 — arXiv 2004.14874
5. Shalev-Arkushin et al., Ham2Pose, CVPR 2023 — arXiv 2211.13613
6. Yin et al., T2S-GPT, ACL 2024 — arXiv 2406.07119
7. SignDiff, 2023 — arXiv 2308.16082
8. Text2Sign Diffusion, 2025 — arXiv 2509.10845
9. Tanzer et al., "Reconsidering Sentence-Level SLT," EMNLP 2024 — aclanthology.org/2024.emnlp-main.360
10. "Lost in Translation, Found in Context," 2025 — arXiv 2501.09754
11. Bragg et al., ASSETS 2019 — arXiv 1908.08597
12. Yin et al., "Including Signed Languages in NLP," ACL 2021 — aclanthology.org/2021.acl-long.570
13. Desai et al., Deaf-Led Call, 2024 — aclanthology.org/2024.signlang-1.6 · arXiv 2403.02563
14. Uthus et al., YouTube-ASL, NeurIPS 2023 — arXiv 2306.15162
15. YouTube-SL-25, ICLR 2025 — arXiv 2407.11144
16. Duarte et al., How2Sign, CVPR 2021 — arXiv 2008.08143
17. Joshi et al., ISLTranslate, ACL Findings 2023 — aclanthology.org/2023.findings-acl.665
18. iSign, ACL Findings 2024 — aclanthology.org/2024.findings-acl.643
19. Othman & Jemni, ASLG-PC12, LREC 2012
20. ASLLRP / DAI, Boston University — bu.edu/asllrp
21. Bangla Sentence–Gloss (RAG text→gloss), 2025 — arXiv 2511.08507
22. Example selection for retrieval-augmented MT, 2024 — arXiv 2405.15070
23. SiLVERScore, 2025 — arXiv 2509.03791

## Uncertainties flagged during collection

- **How2Sign gloss:** standard release appears to be English-translation only; a snippet claiming gloss
  looks erroneous. Treat How2Sign as *no gloss* unless verified.
- **SignLLM** SOTA-across-8-languages claims are from the authors' own materials, not independently verified.
- **Code-release status** for Zhang et al. and Guo/Li/Cohn: no public repo confirmed as of this search.
- A few **2026-dated arXiv IDs** surfaced (post-knowledge-cutoff); not relied upon for load-bearing claims.
