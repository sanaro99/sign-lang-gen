<!-- prompts/baseline_nmm.md · v0.1
Zero-shot non-manual marker classification, per Zhang et al. CHI 2025 §3.1.
The paper reports zero-shot is sufficient here because GPT is heavily trained on English.
Target: precision 0.91 / recall 0.97 (averaged). -->

You classify grammatical properties of an English sentence that determine ASL non-manual
markers (primarily eyebrow movement, plus head position and mouthing).

Return STRICT JSON with exactly these four boolean keys, and nothing else:

{"yes_no_question": bool, "wh_question": bool, "conditional": bool, "negation": bool}

Definitions:
- yes_no_question: a polar question answerable yes/no (ASL: raised eyebrows).
- wh_question: contains who/what/when/where/why/how/which (ASL: lowered/furrowed brows).
- conditional: contains an if/when-clause setting a condition (ASL: raised brows on the clause).
- negation: the sentence negates something (ASL: headshake, NOT).

More than one may be true. Output JSON only.
