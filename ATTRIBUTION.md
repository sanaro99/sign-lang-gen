# Attribution, Sources, and Licenses

Everything this project is built on, and what we are and aren't allowed to do with it.
Maintained alongside the code — if you add a dependency, dataset, or borrowed idea, add it here.

---

## 1. The paper we reimplement

**Zhang, H., Shalev-Arkushin, R., Baltatzis, V., Gillis, C., Laput, G., Kushalnagar, R., Quandt, L. C., Findlater, L., Bedri, A., & Lea, C. (2025). *Towards AI-driven Sign Language Generation with Non-manual Markers*. CHI 2025 (Best Paper Honorable Mention).**
arXiv: 2502.05661 · DOI: 10.1145/3706598.3713855

- **Code released: NO.** Verified against the Apple Machine Learning Research publication page, the arXiv abstract page, the ACM Digital Library entry (no supplementary code), the `apple` and `apple/ml-*` GitHub organizations, and the personal GitHub accounts / homepages of the authors (incl. Colin Lea `colincsl`, Han Zhang). No project webpage exists. No author has publicly promised a release.
- **Why not:** the work was done entirely at Apple and depends on internal assets — a Motion Matching module, an internal UNet-style image generation model, and a 12,681-clip signing dictionary derived from licensed ASLLRP video.
- **License:** the arXiv paper is **CC BY-NC-ND 4.0**. We may read, cite, and reimplement the *method* (methods are not copyrightable). We may **not** redistribute modified versions of its text or figures.
- **What we use from it:** §3.1 (Module 1 design), **Appendix B** (data preprocessing steps 1–4, ASL grammar guidelines B.2, model-selection experiments B.3.1, prompting examples B.3.2 / Table 6), Appendix D (gloss annotation conventions), Appendix A (survey of public ASL datasets).
- **Reported numbers we target:** BLEU-4 **0.276** on text→gloss; non-manual marker detection precision **0.91**, recall **0.97**.
- **Known internal inconsistency:** §3.1 states 1,494 in-context examples ("80% of the dataset"); the ablation section states 1,474 for the same 80% split. We use "≈1,474–1,494" and record the exact number we actually use.

*Optional low-cost step: email the corresponding authors (Colin Lea / Han Zhang) to ask whether Module 1 prompts can be shared. Worst case they say no.*

---

## 2. Prior work our contributions come from

| Work | What we take |
|---|---|
| Sincan, Camgöz & Bowden (2023). *Is Context All You Need? Scaling Neural SLT to Large Domains of Discourse.* ICCVW. arXiv 2308.09622 | The evidence that discourse context roughly doubles BLEU-4 in SLT. Motivates our **paragraph context buffer**. **No public code**; it is video→text, so our text→gloss design is original. |
| Liu, Shen, Zhang, Dolan, Carin & Chen (2022). *What Makes Good In-Context Examples for GPT-3?* (KATE). DeeLIO@ACL. | The evidence that semantically-retrieved examples beat random/static ones. Direct justification for our **RAG example retrieval**. Practical takeaways we act on: test more than one sentence-transformer; run an example-ordering ablation. |
| Lewis et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.* NeurIPS. arXiv 2005.11401 | The embed → index → top-*k* → generate pattern. Our twist: we retrieve **worked examples** (English–gloss pairs), not knowledge passages. |
| **Guo, J., Li, P. & Cohn, T. (2025).** *Bridging Sign and Spoken Languages: Pseudo Gloss Generation for Sign Language Translation.* NeurIPS 2025. arXiv 2505.15438 | The closest published cousin to our Stage 1: an LLM prompted with a few text–gloss pairs generates pseudo-glosses. **No public repo.** Their finding that LLMs systematically mis-order glosses gives us a ready-made error category. ⚠️ **Our proposal cites this as "Kim et al." — the actual authors are Guo, Li & Cohn. Fix the bibliography.** |

---

## 3. Open-source code we consulted (structure/approach only — nothing vendored)

| Repo | Relevance |
|---|---|
| `sign-language-processing/spoken-to-signed-translation` (Moryossef et al., AT4SSL 2023, arXiv 2305.17714) | Working `text_to_gloss` → pose → video pipeline with a *pluggable glosser*. We borrowed the staging idea for our repo layout. |
| `kevinjosethomas/sign-language-processing` (arXiv 2408.09311) | Open-source ASL system using GPT-4o for gloss + `all-MiniLM-L6-v2` embeddings + pgvector for semantic retrieval. Closest existing reference for our retrieval layer. |
| `sign-language-processing/sign-gpt` | Multi-task GPT framing for sign-language tasks. |
| `AchrafAzzaouiRiceU/t5-english-to-asl-gloss-aslg-pc12-only-v1` (HF) | A T5 fine-tuned on ASLG-PC12 — optional **non-LLM comparison baseline**. |

---

## 4. Datasets

### ASLLRP — American Sign Language Linguistic Research Project
The paper's actual data source. Needed for a *faithful* baseline.
- Access: Rutgers Data Access Interface — `dai.cs.rutgers.edu/dai/s/dai`, Sign Bank at `dai.cs.rutgers.edu/dai/s/signbank`.
- **Terms (bu.edu/asllrp/dai-terms.html):** usable for **research and education**, but **cannot be redistributed without permission**; **commercial use is not allowed** without explicit permission, nor are patents/copyrights based on the material. Citation of the ASLLRP reports and URLs is required.
- **Consequence for us: ASLLRP data must never be committed to this repository.** `data/` is gitignored for this reason.

### ASLG-PC12 — English–ASL Gloss Parallel Corpus 2012
Othman & Jemni, LREC 2012 workshop. HF: `achrafothman/aslg_pc12` (~87,710 rows, ~7.6 MB).
- **License: "no known license"** (per the TFDS community catalog). Provenance ambiguous — research use only; do not assume commercial rights.
- **Critical limitation:** glosses are **rule-generated from POS-tagged English**, not produced by Deaf signers. They encode a simplified, English-shaped approximation of ASL. **High BLEU here does not demonstrate real ASL quality.** Every sentence is isolated, so the corpus cannot natively test discourse phenomena — we must construct paragraph-level test sets ourselves.
- This is exactly the dataset problem that Yin et al. (ACL 2021) and Desai et al. (LREC-COLING 2024) criticize. **Our report must own this openly.**

### ISLTranslate (Findings of ACL 2023) and iSign (Findings of ACL 2024)
Joshi et al., IIT Kanpur. ~31k and ~118k ISL video–English pairs respectively.
- **No gloss annotations exist for ISL, at all.** Our week-7 output therefore cannot be scored against references. The feasibility test must be designed around that fact and labeled **exploratory**, not validated.
- Signing is largely by interpreters on educational content, not natural Deaf-community signing; domains are narrow.

---

## 5. Framing and community critique (must be answered in the final report)

- Padden, C. & Humphries, T. (1988). *Deaf in America: Voices from a Culture.* Harvard UP. — Why we target ASL gloss rather than signed English.
- Bragg, D., Koller, O., Bellard, M., et al. (2019). *Sign Language Recognition, Generation, and Translation: An Interdisciplinary Perspective.* ASSETS. — Data bottleneck; gloss is lossy; Deaf involvement is non-negotiable.
- Yin, K., Moryossef, A., Hochgesang, J., Goldberg, Y. & Alikhani, M. (2021). *Including Signed Languages in NLP.* ACL (Best Theme Paper). — **The sharpest critique of our own design choice.** Gloss is a lossy, non-standardized transcription; treating it as "the language" bakes in error, especially the loss of spatial grammar, which no amount of English-side context recovers. We cite it *and answer it*: gloss is a pragmatic, auditable engineering scaffold in a modular pipeline.
- Desai, A., De Meulder, M., Hochgesang, J. A., Kocab, A. & Lu, A. X. (2024). *Systemic Biases in Sign Language AI Research: A Deaf-Led Call to Reevaluate Research Agendas.* LREC-COLING sign-language workshop. — The current community critique our Week 9 reflective analysis must respond to.
- Ladner, R. E. & Ludi, S. *Foundations: Disability and Accessibility*; Zolyomi, A. *Accessible HCI + Inclusive Design*; Bigham, J. P. *AI/ML + Accessibility* — in *Teaching Accessible Computing* (eds. Oleson, Ko, Ladner), Bookish Press.
- Parthasarathy, P. D. & Joshi, S. (2024). *Teaching Digital Accessibility in Computing Education: Views of Educators in India.* ICER. arXiv 2407.15013. — Grounds the ISL extension: India's accessibility ecosystem is thinner, so a pipeline that transfers with minimal modification has real value — and we must not assume ISL has ASL's datasets, annotators, or Deaf-community review infrastructure.

---

## 6. Third-party software

`openai`, `sentence-transformers`, `faiss-cpu`, `datasets`, `sacrebleu`, `scikit-learn`, `pandas`, `nltk` — each under its own OSS license (Apache-2.0 / MIT / BSD). No modified redistribution.

**Model access:** GPT-4o via the OpenAI API is metered and subject to OpenAI's terms. The paper's exact snapshot (`gpt-4o-2024-05-13`) may be deprecated — we pin it in config where possible and maintain an open-model path (Gemma 2 / Llama) so results stay reproducible.
