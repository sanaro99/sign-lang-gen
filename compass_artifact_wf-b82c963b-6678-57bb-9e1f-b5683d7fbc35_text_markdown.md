# Reproducing Stage 1 of Apple's "AI-driven Sign Language Generation with Non-manual Markers": Code Availability & Baseline Plan

## TL;DR
- **No official code, model weights, or datasets were released for arXiv 2502.05661 (CHI 2025).** The Apple Machine Learning Research page and the arXiv abstract page link only to the PDF/HTML and BibTeX — there is no "Code" link, no `apple/ml-*` repo, no Hugging Face artifacts, and no author repo. The paper states the work was "done entirely at Apple," and it depends on internal tooling, so it is effectively proprietary/internal.
- **The paper itself is your most valuable released artifact:** the arXiv PDF and its Appendix B fully document Stage 1 (Module 1) — GPT-4o (`gpt-4o-2024-05-13`), a few-shot in-context prompt with English→gloss example pairs from the ASLLRP dataset, a "multi-prompting" batching strategy, a constrained word-gloss dictionary vocabulary, and a separate zero-shot prompt for non-manual markers (yes/no question, wh-question, conditional, negation). Reproduce from this.
- **Build your baseline by re-implementing Module 1 from the paper text**, using the ASLLRP dataset (research/education license, via the Rutgers DAI) for few-shot examples, and use `sign-language-processing/spoken-to-signed-translation` and `achrafothman/aslg_pc12` as ready-to-clone scaffolding. The closest related LLM-prompting paper (Guo et al., PGG-SLT) has **no public repo** either.

## Key Findings

### 1. Official code release: NO
- The **Apple ML Research page** for the paper exposes only "View publication" (→ arXiv) and "Copy Bibtex." There is no code/dataset/weights link. (It does note the paper won a CHI 2025 Best Paper Honorable Mention.)
- The **arXiv abstract page** (abs/2502.05661) shows only View PDF, HTML, and TeX Source, under a CC BY-NC-ND 4.0 license. The "Code, Data and Media" widgets (CatalyzeX, Papers with Code, Hugging Face) are auto-generated toggles present on every arXiv page and surface no actual repo.
- **GitHub `apple` / `ml-explore` orgs:** no sign-language repo exists. Apple's ML research code convention is `apple/ml-*` (e.g., `apple/ml-mobileclip`); no such repo for this paper.
- **Author accounts:** Colin Lea's GitHub (`colincsl`) has no repo for this work; Han Zhang's homepage (micohan.github.io) and GitHub list no repo for it. No project webpage exists.
- The paper relies on internal assets (a Motion Matching pipeline, an internal image-generation model, and a curated ASLLRP-derived signing dictionary). This makes a full release unlikely.
- **No author statement promising a code release** was found on any homepage, arXiv, or social media.

### 2. What IS publicly available from the paper
- **The full paper**: arXiv PDF (arxiv.org/pdf/2502.05661), experimental HTML (arxiv.org/html/2502.05661v1), the TeX source (arxiv.org/src/2502.05661), and the ACM DL version (dl.acm.org/doi/10.1145/3706598.3713855). The TeX source is worth downloading because it contains the exact prompt figures/tables as text.
- **Appendix B** ("Module 1: English Text-to-ASL Gloss") documents: data preprocessing (Steps 1–4), the ASL grammar guidelines given to the LLM (B.2), model-selection experiments across GPT versions (B.3.1), and prompting examples (B.3.2, Table 6). **Appendix D** gives the gloss annotation conventions. **Appendix A** reviews publicly available ASL datasets.
- **No released dataset, dictionary, weights, or prompts-as-files.** The in-context example pairs, the 3,915-entry word-gloss dictionary, and the 12,681-clip signing dictionary are all derived from ASLLRP but were not released as artifacts. The ACM DL entry carries no supplementary code either.

### 3. Stage 1 (Module 1) design — enough to reproduce
From Section 3.1 and Appendix B:
- **LLM:** GPT-4o, specifically `gpt-4o-2024-05-13`. Per the paper (§3.1): *"GPT-4o was selected based on our preliminary experiments with various versions of the GPT models. Detailed experimental results are presented in Section B.3."*
- **Task 1 — English→ASL gloss (few-shot / in-context learning):** English sentence–gloss example pairs are injected into the prompt. **Note a figure discrepancy in the sources:** the paper's main text (§3.1) states "1,494 in-context examples … representing 80% of the dataset," while the ablation section states the 80% split as **1,474** sentences (*"we experimented with 600 (33% of dataset) and 1,474 (80% of dataset) sentences from ASLLRP. The dataset was randomly split into an 80/20 ratio"*). Treat "≈1,474–1,494 pairs (80% split)" as the intended quantity. Because GPT-4o's 128k-token window cannot hold all examples at once, they used a **"multi-prompting" approach** — splitting examples into batches and iteratively prompting. Output was **constrained to the vocabulary of their word-gloss dictionary**.
- **Task 2 — non-manual markers (zero-shot):** the model classifies whether a sentence (1) is a yes/no question, (2) is a wh-question, (3) is a conditional, and/or (4) contains negation. Zero-shot sufficed because GPT was extensively trained on English. Focus is on eyebrow movements as the primary non-manual marker.
- **Reported results (per the ACM CHI 2025 paper):** BLEU-4 of 0.276 for text→gloss; average precision 0.91 and recall 0.97 for detecting non-manual information from English text.
- **Data source:** ASLLRP. They extracted 2,119 sentence-gloss pairs, cleaned to 1,843, built a 3,915-entry word-gloss dictionary, used fingerspelling for 43 OOV words, and did a 4-researcher ground-truth correction of the non-manual labels.

### 4. Datasets
- **ASLLRP** (the paper's source): access via the Rutgers **Data Access Interface (DAI 2)** at dai.cs.rutgers.edu/dai/s/dai and the ASLLRP Sign Bank at dai.cs.rutgers.edu/dai/s/signbank. Data is browsable and downloadable (annotations in XML export). **License (verbatim, bu.edu/asllrp/dai-terms.html):** *"The data available from these pages can be used for research and education purposes, but cannot be redistributed without permission. Commercial use, without explicit permission, is not allowed, nor are any patents and copyrights based on this material."* Citation of the ASLLRP reports and URLs is required; no account/registration gate was found.
- **ASLG-PC12** (best drop-in substitute for quick prototyping): `achrafothman/aslg_pc12` on Hugging Face. The dataset card lists **"Number of rows: 87,710"** and **"Size of downloaded dataset files: 7.58 MB"** of English-text ↔ ASL-gloss pairs. It is a **rule-based synthetic** corpus (Othman & Jemni, "English-ASL Gloss Parallel Corpus 2012: ASLG-PC12," LREC 2012 workshop), simpler than ASLLRP's human glosses. The TensorFlow Datasets community catalog states *"Description: Synthetic English-ASL Gloss Parallel Corpus 2012 … License: No known license."* Good for pipeline bring-up; weaker for evaluating true ASL grammar, and its licensing/provenance is ambiguous.

### 5. Related open-source code you can actually clone
- **`sign-language-processing/spoken-to-signed-translation`** (ZurichNLP; Moryossef et al., AT4SSL 2023, arXiv 2305.17714; paper CC BY-SA 4.0): a working `text_to_gloss` → `pose` → `video` pipeline with a pluggable glosser (`simple|spacylemma|rules|nmt`) and a Colab demo. Best scaffolding for structuring your repo.
- **`kevinjosethomas/sign-language-processing`** (arXiv 2408.09311): open-source two-way ASL–English system that uses **GPT-4o with a rule-based prompt** to produce ASL gloss, then embeds glosses with `all-MiniLM-L6-v2` and does semantic pose retrieval from a `pgvector` database. Directly relevant to your RAG extension — it already does embedding-based retrieval.
- **`sign-language-processing/sign-gpt`**: multi-task GPT model for sign-language tasks (useful reference for prompt/task framing).
- **`AchrafAzzaouiRiceU/t5-english-to-asl-gloss-aslg-pc12-only-v1`** (Hugging Face): a T5 model fine-tuned on ASLG-PC12 for English→ASL gloss — a non-LLM baseline to benchmark against.
- **Guo, Li, Cohn — "Bridging Sign and Spoken Languages: Pseudo Gloss Generation" (arXiv 2505.15438, "PGG-SLT"):** Jianyuan Guo (City University of Hong Kong), Peike Li and Trevor Cohn (Google); work done during Guo's Google internship. **Caveat on venue:** the arXiv metadata labels it "Technical report, 21 pages" (cs.CV); the NeurIPS proceedings site also lists it as a NeurIPS 2025 main-track paper, so the "NeurIPS 2025" label appears correct but the arXiv version is styled as a technical report. **No official public repo exists** (verified against arXiv, the author's homepage ggjy.github.io — where the paper is not even listed, the NeurIPS proceedings page, OpenReview, and GitHub search). It is still a strong methodological template: per its Figure 4 caption, it uses an *"Example prompt used for pseudo gloss generation with Gemini 1.5 Pro. The prompt contains a few example text-gloss pairs to guide the LLM in generating well-structured glosses for the query text,"* evaluated on Phoenix14T and How2Sign. (Its downstream translator uses mBART / Gemma2-2B and an S3D visual encoder — not needed for your text-only Stage 1.)
- **Sincan et al. "Is Context All You Need?" (ICCV-W 2023, arXiv 2308.09622):** relevant to your paragraph-level context-buffer extension, but **no public code repo was found**; it is a BSL/BOBSL video-based SLT system, not a text-to-gloss prompt, so its value is conceptual (context-aware translation) rather than as clonable code.

### 6. Licensing flags
- **The Apple paper is CC BY-NC-ND 4.0** — you may read, cite, and reproduce ideas, but the text/figures are non-commercial/no-derivatives. Re-implementing the *method* is fine (methods aren't copyrightable); do not republish modified paper text/figures.
- **ASLLRP:** research/education only, no commercial use or redistribution without permission — fine for an IMT 600 academic study; do not commit the data to your public repo.
- **ASLG-PC12:** "No known license" — usable for research but provenance is ambiguous; don't assume commercial rights.
- **GPT-4o / OpenAI:** API use incurs cost and is subject to OpenAI's terms; note that `gpt-4o-2024-05-13` may be deprecated, so pin the version or plan a swap to an open model for reproducibility.

## Details

**Why there is almost certainly no release.** The system is a three-module pipeline: (1) GPT-4o text→gloss+non-manual, (2) a Computer-Graphics "Motion Matching" module that stitches an ASLLRP-derived dictionary of 12,681 pose clips, and (3) an internal UNet-style image-generation model for photorealistic frames. Modules 2 and 3 depend on internal Apple tooling and licensed ASLLRP video, so even a partial release would be encumbered. The good news for your project: **Stage 1 is the most reproducible module** because it is essentially prompt engineering over GPT-4o plus a public dataset (ASLLRP), and the paper documents it in unusual detail (Appendix B).

**Mapping your extensions to the paper.**
- Your **paragraph-level context buffer** directly addresses the paper's stated design choice that it operates in a "context-free setting, where each sentence is translated independently." This is a clean, well-motivated novelty. Sincan et al. (2308.09622) and "Reconsidering Sentence-Level SLT" (arXiv 2406.11049) provide conceptual grounding.
- Your **RAG-based retrieval of few-shot examples** directly attacks the paper's "multi-prompting" hack (they batched ~1,474–1,494 examples because they wouldn't fit in one context window). Retrieving the k most relevant example pairs per input sentence is a strictly better, cheaper design. `kevinjosethomas/sign-language-processing`'s MiniLM + pgvector retrieval is a concrete reference implementation, and Guo et al.'s PGG-SLT confirms that small numbers of well-chosen in-context text-gloss pairs are effective.

## Recommendations

**This week (repo setup):**
1. Do **not** wait for or keep searching for an official Apple repo — it does not exist. Start a fresh repo.
2. Download three things now: the **arXiv PDF and TeX source** of 2502.05661 (for the exact Appendix B prompts/tables), the **ASLG-PC12** dataset from Hugging Face (`achrafothman/aslg_pc12`) for immediate pipeline bring-up, and clone **`sign-language-processing/spoken-to-signed-translation`** as structural scaffolding.
3. Request **ASLLRP** access via the Rutgers DAI (dai.cs.rutgers.edu/dai/s/dai) in parallel — it is the paper's actual data source and you'll want it for a faithful baseline. Budget time for the citation/usage requirements and keep the data out of your public repo.

**Baseline (reproduce Module 1):**
4. Implement two prompts exactly as described: (a) a few-shot English→gloss prompt with retrieved/batched example pairs and a constrained gloss vocabulary; (b) a zero-shot non-manual classifier (yes/no-Q, wh-Q, conditional, negation). Start with GPT-4o for fidelity to the paper, but also wire in an open model (Gemma2/Llama) so results survive `gpt-4o-2024-05-13` deprecation.
5. Evaluate with **BLEU-4** for gloss and **precision/recall** for non-manual markers, targeting the paper's 0.276 / 0.91 / 0.97 benchmarks.

**Extensions:**
6. Add the **RAG few-shot retriever** first (embed example pairs with MiniLM or similar; retrieve top-k per sentence). Lowest-risk, highest-payoff extension; it replaces the paper's multi-prompting.
7. Add the **paragraph context buffer** second; measure whether cross-sentence context changes gloss/non-manual decisions (topic continuity, referent tracking).

**Thresholds that change the plan:**
- If ASLLRP access is delayed, proceed on ASLG-PC12 for the baseline and swap datasets later — but its synthetic glosses will inflate BLEU and won't test true ASL grammar, so don't over-index on that number.
- If GPT-4o API cost is a constraint, switch the baseline to an open model from the start; the method is model-agnostic.

## Caveats
- Absence of a repo is established from the primary sources (Apple ML page, arXiv, GitHub orgs, author profiles). It remains possible (though unlikely) that code could be released later or shared on request. Emailing the corresponding authors (Colin Lea / Han Zhang) is a reasonable low-cost step.
- There is an internal source discrepancy on the number of few-shot examples (1,494 in the method text vs. 1,474 in the ablation); use "≈1,474–1,494 (80% split)" and verify against Appendix B if exactness matters.
- The paper's BLEU-4 of 0.276 was computed on their specific ASLLRP-derived test split; your numbers won't be directly comparable unless you replicate their preprocessing and split.
- ASLG-PC12 and ASLLRP differ in kind (synthetic rule-based vs. human-annotated linguistic corpus); results do not transfer cleanly between them.
- Licenses restrict redistribution: keep ASLLRP data out of your public repo, and treat the Apple paper text as CC BY-NC-ND (cite, don't copy).