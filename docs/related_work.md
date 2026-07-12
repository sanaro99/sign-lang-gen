# Related Work — quick map for the team

Where each paper actually touches the code. Full annotations live in the Week 1-2 lit review;
full citations and licenses in `../ATTRIBUTION.md`.

| Paper | Touches |
|---|---|
| **Zhang et al., CHI 2025** (arXiv 2502.05661) | `prompts/baseline_*.md`, `src/aslgloss/baseline/`. THE paper. No code released. Know its pipeline diagram and user study cold. Targets: BLEU-4 0.276; NMM P 0.91 / R 0.97. |
| **Sincan et al., ICCVW 2023** (arXiv 2308.09622) | `src/aslgloss/context/`. Discourse context ~doubled BLEU-4 in SLT. Our scientific ancestor. No public code; video->text, so our design is original. |
| **Liu et al., KATE, DeeLIO 2022** | `src/aslgloss/retrieval/`. Retrieved > random examples. Two actionable takeaways we implement: test multiple sentence-transformers; ablate example ordering (`retrieval.order` in configs). |
| **Lewis et al., RAG, NeurIPS 2020** | `src/aslgloss/retrieval/index.py`. embed -> index -> top-k -> generate. |
| **Guo, Li & Cohn, NeurIPS 2025** (arXiv 2505.15438) | The closest published cousin: LLM + few text-gloss pairs -> pseudo-gloss. **No public repo.** Their LLM-mis-orders-gloss finding -> our `gloss_ordering` error category. ⚠️ Proposal miscites this as "Kim et al." — fix. |
| **Othman & Jemni, LREC 2012** | `src/aslgloss/data/loaders.py`. ASLG-PC12. **Synthetic, rule-generated glosses.** Our biggest evaluation limitation. |
| **Yin et al., ACL 2021** | The strongest critique of *our own design choice* (gloss as intermediate). Cite it and answer it. |
| **Desai et al., LREC-COLING 2024** | The Deaf-led critique our Week 9 reflection must answer. Our dataset has exactly the annotation problems it describes. |
| **Joshi et al., ISLTranslate (2023) / iSign (2024)** | Week 7. No ISL gloss annotations exist anywhere — this constrains what the feasibility test can even claim. |
| **Bragg et al., ASSETS 2019** | Predicted our two biggest risks (gloss is lossy; eval datasets are tiny). Limitations section. |
| **Moryossef et al., AT4SSL 2023** (`spoken-to-signed-translation`) | Structural inspiration for repo layout only. Nothing vendored. |
| **Thomas, arXiv 2408.09311** (`kevinjosethomas/sign-language-processing`) | Reference implementation for GPT-4o gloss + MiniLM semantic retrieval. |
