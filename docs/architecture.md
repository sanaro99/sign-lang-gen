# Architecture

How the code is organized and how a sentence flows through it.

---

## In plain words

Think of this project as a small **assembly line** for translating English into ASL gloss:

1. **Get the raw material.** Download a public English↔gloss dataset and split it into a "study set"
   (examples the system can learn from) and a "test set" (sentences we quiz it on).
2. **Build a lookup table.** Turn every study-set example into a list of numbers ("embedding") so the
   system can later find the examples most similar to whatever sentence it's translating.
3. **Do the translation.** For each test sentence, gather a few helpful examples (and, optionally, the
   surrounding sentences for context), ask the language model for the gloss, and also ask it whether
   the sentence is a question, a negation, etc.
4. **Grade the results.** Compare the machine's gloss to the reference gloss, measure speed and cost,
   and flag likely error types for humans to review.

Each of the four "conditions" we test is just the same assembly line with two switches flipped on or
off: *use smart example lookup?* and *use surrounding-sentence context?*

---

## Pipeline (data flow)

```
 ┌─────────────────────┐   data/processed/
 │ download_data.py    │──▶ example_pool.jsonl   (study set: English–gloss pairs)
 │                     │──▶ test.jsonl           (held-out sentences to translate)
 └─────────────────────┘
            │
 ┌─────────────────────┐
 │ build_index.py      │──▶ example_pool.faiss   (vector index over the study set)
 └─────────────────────┘
            │
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ run_experiment.py  (one config = one condition)                            │
 │                                                                             │
 │   for each test sentence:                                                   │
 │     shots     = retriever.retrieve(text)   ── OR ── static few-shot set     │  ← Contribution 1
 │     context   = context_builder.build(ex, prior_glosses)  (optional)       │  ← Contribution 2
 │     response  = llm.complete(system_prompt, user_prompt)                    │
 │     gloss     = post-process(response)                                      │
 │     oov       = oov_tokens(gloss, vocab)                                    │
 │     prior_glosses[(doc_id, sent_idx)] = gloss   (self-conditioning)         │
 │     markers   = nmm.classify(text)                                          │
 │     tags      = tag_errors(...)                                             │
 │                                                                             │
 │   → results/<run_id>/predictions.jsonl                                      │
 │   → results/<run_id>/manifest.json  (git SHA, prompt hashes, cfg, cost)     │
 └───────────────────────────────────────────────────────────────────────────┘
            │
 ┌─────────────────────┐
 │ evaluate.py         │──▶ results/summary.csv  (BLEU-4, latency, cost, error tags per run)
 └─────────────────────┘
```

---

## Module map (`src/aslgloss/`)

| Module | File(s) | Responsibility |
|---|---|---|
| **config** | `config.py` | Path constants, `NMM_LABELS`, and the dataclasses (`ExperimentConfig`, `LLMConfig`, `RetrievalConfig`, `ContextConfig`) that a YAML deserializes into. One YAML = one fully-specified run. |
| **llm** | `llm/client.py` | Provider-agnostic client over the OpenAI SDK. Supports OpenAI and any OpenAI-compatible open model (Ollama/vLLM/TGI). Reports tokens, latency, and cost per call; retries with backoff. |
| **data** | `data/loaders.py`, `data/paragraphs.py` | `Example` data unit; ASLG-PC12 loader; JSONL pool round-trip; ASLLRP loader stub (awaiting license access); paragraph chunking that assigns `doc_id`/`sent_idx`. |
| **baseline** | `baseline/gloss.py`, `baseline/nmm.py`, `baseline/vocab.py` | Module 1 re-implementation: `GlossGenerator` (assembles prompt, calls LLM, post-processes, flags OOV), `NMMClassifier` (zero-shot JSON classifier for the 4 markers), and the gloss vocabulary constraint. |
| **retrieval** | `retrieval/index.py`, `retrieval/retriever.py` | **Contribution 1.** Embed the study set with a sentence-transformer, build a FAISS cosine index, retrieve top-*k* per query with an order ablation knob. |
| **context** | `context/buffer.py` | **Contribution 2.** Build a windowed discourse block around the target sentence, optionally feeding back the system's own prior glosses. For disambiguation only — never glossed itself. |
| **evaluation** | `evaluation/metrics.py`, `evaluation/error_analysis.py` | BLEU-4, NMM precision/recall/F1, run summaries; plus heuristic error triage across the taxonomy categories. |

Design notes:
- **Pluggable extension points.** `GlossGenerator(retriever=None, context_builder=None)` — `None`
  gives the paper-faithful baseline; passing an object turns on a contribution. This is what lets one
  code path serve all four conditions.
- **Lazy heavy imports.** `openai`, `sentence_transformers`, `faiss`, `datasets` are imported inside
  functions/`__init__`, so the pure-logic modules (vocab, context buffer, error analysis) stay
  importable and unit-testable with no API keys or ML deps installed.

---

## How the four conditions map to config switches

Each `configs/*.yaml` differs only in three fields:

| Field | baseline | rag_only | context_only | context_plus_rag |
|---|---|---|---|---|
| `retrieval.enabled` | `false` | `true` | `false` | `true` |
| `context.enabled` | `false` | `false` | `true` | `true` |
| `gloss_prompt` | `baseline_gloss.md` | `baseline_gloss.md` | `context_gloss.md` | `context_gloss.md` |

Everything else (model `gpt-4o-2024-05-13`, `temperature: 0.0`, `seed: 7`, `n_examples: 200`) is held
constant so differences are attributable to the two switches.

---

## Reproducibility model

Every run is auditable from its manifest alone:

- **`git_sha`** — exact code state.
- **`gloss_prompt_hash` / `nmm_prompt_hash`** — SHA-256 of the prompt files actually used (prompts are
  source code; editing one changes the hash and is visible in the manifest).
- **`config`** — the full deserialized `ExperimentConfig` (model, seed, k, window sizes, …).
- **token counts + cost** — from the per-call accounting in `llm/client.py`.

This is why the team rule is *"a result without a manifest is not a result."*

---

## Known gaps (tracked in `ROADMAP.md`)

- `evaluation/metrics.py::summarize_run` references a `reference` attribute that `GlossResult` does not
  have — it is currently dead/broken; `scripts/evaluate.py` does the real aggregation. To be fixed.
- Several values are hardcoded rather than config-driven: `build_paragraphs(size=5)` in
  `run_experiment.py`, the pool size and tail-slice test split in `download_data.py`, and the
  `data/processed/*.jsonl` paths.
- Test coverage is limited to pure-logic modules; the LLM/retrieval/loader paths are untested.
- ROUGE / exact-match metrics and the ISL config are mentioned but not yet wired in.
