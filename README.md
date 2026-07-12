# asl-gloss-stage1

**Paragraph-Level Context and RAG-Based Example Retrieval for Improved ASL Gloss Generation**
*with an exploratory feasibility extension to Indian Sign Language*

IMT 600 Independent Study — MSIM, University of Washington Information School — Summer 2026

| | |
|---|---|
| **Team** | Student 1, Student 2, Student 3 |
| **Faculty supervisor** | Professor |
| **Expert guidance** | Mentor |
| **Status** | Week 1–2: repository setup, baseline reproduction |

> Contributor names, emails, and roles are kept out of this public repository. Team members: see the private `docs/AUTHORS.local.md` (gitignored, not committed).

---

## What this repository is

This project reproduces and extends **Stage 1 (Module 1)** of the pipeline in Zhang et al., *Towards AI-driven Sign Language Generation with Non-manual Markers* (CHI 2025) — the stage that translates **English text → ASL gloss + non-manual markers** using an LLM.

We deliberately scope *down* to Stage 1. We do not attempt Stage 2 (pose synthesis) or Stage 3 (video rendering), both of which depend on internal Apple tooling.

We then add two contributions on top of the baseline:

1. **Paragraph-level context buffer** — the CHI 2025 pipeline translates each sentence in isolation ("context-free setting"). We give the LLM a rolling window of neighboring sentences so discourse phenomena (pronoun resolution, negation scope, topic continuity) can survive translation.
2. **RAG-based few-shot example retrieval** — the CHI 2025 pipeline packs ~1,474–1,494 static in-context examples into the prompt, and had to invent a "multi-prompting" batching workaround because they don't fit in a single context window. We replace this with per-input retrieval of the top-*k* most semantically similar English–gloss example pairs. This should improve quality *and* cut token cost.

A third, explicitly **exploratory** outcome tests whether the same architecture transfers to **Indian Sign Language (ISL)**, where no gloss-annotated data exists.

---

## ⚠️ Code provenance — read this first

**There is no official code release for the CHI 2025 paper.** We verified this against the Apple Machine Learning Research page, the arXiv listing (2502.05661), the ACM DL entry, the `apple/ml-*` GitHub org, and the authors' personal GitHub accounts and homepages. The paper states the work was "done entirely at Apple" and depends on internal assets (a Motion Matching module, an internal image-generation model, a licensed ASLLRP-derived signing dictionary).

**Therefore: every line of code in `src/` is our own re-implementation**, written from the method description in the paper. Nothing here is copied from Apple. The table below records exactly what each part of the codebase is derived from, so that our final report and any future reader can audit it.

| Component | Path | Source / derivation | License situation |
|---|---|---|---|
| Baseline gloss prompt (few-shot English→gloss) | `prompts/baseline_gloss.md`, `src/aslgloss/baseline/` | **Our re-implementation** from Zhang et al. CHI 2025, §3.1 and **Appendix B** (data prep, ASL grammar guidelines B.2, prompting examples B.3.2 / Table 6). Model in paper: `gpt-4o-2024-05-13`. | Paper is CC BY-NC-ND 4.0 — we cite it and reimplement the *method* (methods are not copyrightable). We do not reproduce its text or figures. |
| Non-manual marker classifier (zero-shot) | `prompts/baseline_nmm.md`, `src/aslgloss/baseline/nmm.py` | **Our re-implementation** from Zhang et al. §3.1: zero-shot classification of yes/no-question, wh-question, conditional, negation. | As above. |
| Repo structure / pipeline staging | overall layout | **Structural inspiration** from `sign-language-processing/spoken-to-signed-translation` (Moryossef et al., AT4SSL 2023, arXiv 2305.17714) — its pluggable `text_to_gloss` → pose → video staging. No code copied. | Paper CC BY-SA 4.0; repo is open source. Consulted, not vendored. |
| RAG example retriever (embed → FAISS → top-*k*) | `src/aslgloss/retrieval/` | **Our implementation.** Method justified by Liu et al., *What Makes Good In-Context Examples for GPT-3?* (KATE, DeeLIO@ACL 2022) and Lewis et al., *RAG* (NeurIPS 2020). Reference implementation consulted: `kevinjosethomas/sign-language-processing` (arXiv 2408.09311), which uses GPT-4o + `all-MiniLM-L6-v2` embeddings + pgvector for semantic pose retrieval. | Open source; consulted for approach, not vendored. |
| Paragraph context buffer | `src/aslgloss/context/` | **Our implementation.** Conceptually grounded in Sincan, Camgöz & Bowden, *Is Context All You Need?* (ICCVW 2023, arXiv 2308.09622) — no public code exists for that paper, and it is video→text, so this is our own design in the text→gloss direction. | N/A — original code. |
| Pseudo-gloss prompting pattern (comparison baseline) | `docs/related_work.md` | Guo, Li & Cohn, *Bridging Sign and Spoken Languages: Pseudo Gloss Generation for SLT* (NeurIPS 2025, arXiv 2505.15438). **No public repo exists.** Prompt *pattern* (a few text–gloss pairs guiding an LLM) documented in their Fig. 4 caption. | N/A — we reimplement the pattern. **Note:** our proposal bibliography cites this as "Kim et al." — the actual authors are **Guo, Li, and Cohn**. Fix before final report. |
| Evaluation (BLEU-4, NMM precision/recall) | `src/aslgloss/evaluation/` | **Our implementation** using `sacrebleu` + `scikit-learn`. Targets from the paper: **BLEU-4 = 0.276** (text→gloss), **precision 0.91 / recall 0.97** (non-manual detection). | Open-source libraries. |
| Non-LLM comparison baseline | `configs/` (optional) | `AchrafAzzaouiRiceU/t5-english-to-asl-gloss-aslg-pc12-only-v1` on Hugging Face — a T5 fine-tuned on ASLG-PC12. | Hugging Face model; check card before use. |

### Data provenance

| Dataset | Use | Access | License / constraint |
|---|---|---|---|
| **ASLLRP** (American Sign Language Linguistic Research Project) | The paper's actual source for its ~1,474–1,494 in-context example pairs and its 3,915-entry word–gloss dictionary. Our **faithful** baseline needs this. | Rutgers Data Access Interface: `dai.cs.rutgers.edu/dai/s/dai` | **Research and education only. No commercial use. No redistribution without permission.** → **Never commit ASLLRP data to this repo.** Citation of the ASLLRP reports/URLs is required. |
| **ASLG-PC12** | Fast pipeline bring-up, our RAG example pool, and week-6 evaluation. ~87,710 English–gloss pairs. | HF: `achrafothman/aslg_pc12` | Listed as **"no known license"** — provenance is ambiguous. Research use only; don't assume commercial rights. **Glosses are rule-generated, not written by Deaf signers** — see the caveat below. |
| **ISLTranslate** (~31k ISL–English pairs) | Week 7 ISL feasibility extension. | `aclanthology.org/2023.findings-acl.665/` | Check dataset terms. **No gloss annotations exist.** |
| **iSign** (~118k ISL video–sentence pairs) | Week 7 ISL feasibility extension. | `aclanthology.org/2024.findings-acl.643/` | Check dataset terms. **No gloss annotations exist.** |

> **Standing caveat we must state loudly in the final report:** ASLG-PC12's glosses are *synthetic*, produced by a rule-based algorithm rather than by Deaf signers. High BLEU on ASLG-PC12 does **not** demonstrate real ASL quality. Yin et al. (ACL 2021) and Desai et al. (LREC-COLING 2024) warn about exactly this class of dataset. Our error analysis exists partly to compensate for it.

---

## Repository layout

```
asl-gloss-stage1/
├── README.md                  ← you are here
├── LICENSE                    ← MIT, covers OUR code only
├── ATTRIBUTION.md             ← full citation list + license notes
├── requirements.txt
├── .env.example               ← copy to .env, never commit .env
├── Makefile                   ← make setup / baseline / rag / eval
│
├── prompts/                   ← versioned prompt templates (treat as source code)
│   ├── baseline_gloss.md      ← few-shot English→gloss (CHI 2025 Module 1)
│   ├── baseline_nmm.md        ← zero-shot non-manual marker classifier
│   ├── context_gloss.md       ← + paragraph-level context buffer  [our contribution]
│   └── isl_gloss.md           ← exploratory ISL variant
│
├── src/aslgloss/
│   ├── config.py              ← paths, model names, k, window size
│   ├── llm/                   ← provider-agnostic LLM client (OpenAI + open models)
│   ├── data/                  ← ASLG-PC12 / ASLLRP loaders, paragraph chunking
│   ├── baseline/              ← Module 1 re-implementation (gloss + NMM)
│   ├── retrieval/             ← embed → FAISS index → top-k retriever  [contribution 1]
│   ├── context/               ← paragraph context buffer                [contribution 2]
│   └── evaluation/            ← BLEU-4, NMM P/R, latency, cost, error analysis
│
├── configs/                   ← one YAML per experimental condition
│   ├── baseline.yaml
│   ├── rag_only.yaml
│   ├── context_only.yaml
│   └── context_plus_rag.yaml
│
├── scripts/                   ← CLI entrypoints (build index, run, evaluate)
├── notebooks/                 ← exploration only; anything reusable graduates to src/
├── docs/                      ← lit review, decision log, error taxonomy, ISL notes
├── tests/
├── data/                      ← GITIGNORED. Nothing in here is committed.
└── results/                   ← run outputs, results tables (committed: small CSVs only)
```

---

## Quickstart

```bash
git clone https://github.com/sanaro99/sign-lang-gen.git && cd sign-lang-gen
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

cp .env.example .env          # add your OPENAI_API_KEY (or point at an open model)

make data                     # download ASLG-PC12 into data/raw/ (gitignored)
make index                    # embed the example pool, build the FAISS index
make baseline                 # run the CHI-2025-style baseline on the dev split
make eval                     # BLEU-4, NMM precision/recall, latency, cost
```

Then compare conditions:

```bash
python scripts/run_experiment.py --config configs/baseline.yaml
python scripts/run_experiment.py --config configs/rag_only.yaml
python scripts/run_experiment.py --config configs/context_only.yaml
python scripts/run_experiment.py --config configs/context_plus_rag.yaml
python scripts/evaluate.py --results-dir results/ --out results/summary.csv
```

---

## The four experimental conditions

This is the core experimental design (proposal Week 6). Everything in `configs/` maps to one row.

| Condition | Examples in prompt | Context | Purpose |
|---|---|---|---|
| `baseline` | static few-shot set (paper-style) | none — sentence in isolation | Reproduce CHI 2025 Module 1. Target: BLEU-4 ≈ 0.276 |
| `rag_only` | top-*k* retrieved per input | none | Isolate the effect of retrieval |
| `context_only` | static few-shot set | paragraph buffer (±*n* sentences) | Isolate the effect of discourse context |
| `context_plus_rag` | top-*k* retrieved | paragraph buffer | Our full proposed system |

Measured for each: **gloss quality** (BLEU-4, plus ROUGE / exact-match), **latency** (p50/p95), **estimated API cost** (prompt + completion tokens × price), and **structured error analysis** on discourse-sensitive cases.

**Error taxonomy** (see `docs/error_taxonomy.md`) — the categories BLEU hides:
- pronoun / referent resolution across sentences
- negation scope
- **gloss ordering** (Guo et al. found LLMs systematically get this wrong — ready-made error category)
- topic-comment structure
- OOV / fingerspelling handling
- non-manual marker false positives & false negatives

---

## Notes on reproducing the baseline faithfully

From the paper (§3.1, Appendix B):

- Model: **GPT-4o**, specifically `gpt-4o-2024-05-13`, chosen after comparing GPT versions (App. B.3.1). ⚠️ This snapshot may be deprecated — **pin the version in `configs/`** and also wire in an open model (Gemma 2 / Llama) so our results remain reproducible after the snapshot disappears.
- Few-shot pool: **≈1,474–1,494 English–gloss pairs** (an 80% split of their ASLLRP-derived set). *The paper is internally inconsistent here* — §3.1 says 1,494, the ablation says 1,474. Record whichever we use; don't paper over it.
- Because the pool exceeds the usable context window, they used **"multi-prompting"**: batch the examples, prompt iteratively. **This is precisely the inefficiency our RAG layer removes** — say so explicitly in the report.
- Output was **constrained to the vocabulary of their word–gloss dictionary** (3,915 entries). We approximate this with a vocabulary constraint built from our example pool (`src/aslgloss/baseline/vocab.py`).
- Non-manual markers were done **zero-shot** — the paper reports that GPT's English training made few-shot unnecessary there.

---

## Rules of the road (team conventions)

1. **Never commit data or `.env`.** `data/` and `.env` are gitignored. ASLLRP redistribution is prohibited by its license.
2. **Prompts are source code.** They live in `prompts/`, are version-controlled, and every experiment logs the prompt hash it used. A result without a prompt hash is not a result.
3. **Every run writes a manifest** (`results/<run_id>/manifest.json`): git SHA, prompt hash, model + snapshot, config, seed, timestamp, token counts, cost. Week 9 depends on this.
4. **Notebooks explore; `src/` decides.** Anything we rely on gets promoted into `src/` with a test.
5. **Log decisions, not just code.** `docs/decision_log.md` — one line per non-obvious choice, with the reason. This becomes the methods section.
6. Branches: `main` stays runnable. Work on `feat/<thing>`, PR into `main`, one teammate reviews.

---

## Citation

If we publish, cite the work we build on — at minimum:

```bibtex
@inproceedings{zhang2025asl,
  title     = {Towards AI-driven Sign Language Generation with Non-manual Markers},
  author    = {Zhang, Han and Shalev-Arkushin, Rotem and Baltatzis, Vasileios and
               Gillis, Connor and Laput, Gierad and Kushalnagar, Raja and
               Quandt, Lorna and Findlater, Leah and Bedri, Abdelkareem and Lea, Colin},
  booktitle = {Proceedings of the 2025 CHI Conference on Human Factors in Computing Systems},
  year      = {2025},
  doi       = {10.1145/3706598.3713855}
}
```

Full list in [`ATTRIBUTION.md`](ATTRIBUTION.md).

## License

Our code: MIT (see `LICENSE`). This does **not** extend to the datasets or to the papers we build on — see the data provenance table above and `ATTRIBUTION.md`.
