# Decision Log

One line per non-obvious choice, with the reason. This becomes the methods section
of the final report — future-us will not remember why we did any of this.

| Date | Decision | Why | Who |
|---|---|---|---|
| 2026-07-11 | Re-implement CHI 2025 Module 1 from the paper rather than forking code | No official code exists (verified: Apple ML page, arXiv, ACM DL, `apple/ml-*`, author GitHubs). Work was done entirely at Apple with internal assets. | team |
| 2026-07-11 | Start on ASLG-PC12; request ASLLRP access in parallel | ASLG-PC12 is instantly available and lets us build the pipeline this week. ASLLRP is what the paper actually used and is needed for a faithful baseline. | team |
| 2026-07-11 | `static_shots: 8` in the baseline config, not ~1,474 | Their full pool needed "multi-prompting" batching. Running that faithfully is expensive. **Open question — resolve before Week 6:** does our baseline use 8 shots (cheap, but not the paper's baseline) or reproduce multi-prompting (faithful, costly)? Recommend: run both, report both. An 8-shot static baseline is arguably a *strawman* that flatters our RAG condition. | team |
| 2026-07-11 | Pin `gpt-4o-2024-05-13`; keep an open-model path | The paper's snapshot may be deprecated mid-quarter. If it disappears, our baseline is unreproducible. | team |
| | | | |

## Open questions

- [ ] **Baseline fairness.** See above. This is the single biggest threat to our claims: if we compare RAG-8-shot against a static-8-shot baseline, we test retrieval; if we compare against the paper's ~1,474-shot multi-prompting, we test retrieval *and* efficiency. Decide explicitly and defend it.
- [ ] **Test split.** ASLG-PC12 ships a single split. `download_data.py` currently takes a naive tail slice. Define a proper, documented split before any number goes in the report.
- [ ] **Discourse probe set.** Auto-chunked ASLG-PC12 "paragraphs" are pseudo-documents — adjacent sentences aren't guaranteed to be coherent discourse. The context contribution cannot be honestly evaluated on them alone. **We need a hand-curated set (~50-100 short passages) where meaning genuinely depends on prior sentences.** This is the highest-value unglamorous task in the project.
- [ ] **Gloss conventions.** Ours must be written down (docs/gloss_conventions.md) and match ASLG-PC12's tokenization or the BLEU comparison is meaningless.
- [ ] Should we email Colin Lea / Han Zhang to ask whether the Module 1 prompts can be shared? Low cost, possible large payoff.
