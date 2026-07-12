"""Module 1, part 2: non-manual markers (ZERO-SHOT).

Zhang et al. classify four properties of the English sentence and report that zero-shot
was sufficient (GPT is heavily trained on English): yes/no question, wh-question,
conditional, negation. Primary realisation is eyebrow movement.

Paper's reported performance — our target: precision 0.91, recall 0.97 (averaged).
"""
from __future__ import annotations

import json

from ..config import NMM_LABELS, PROMPTS
from ..llm import LLMClient


class NMMClassifier:
    def __init__(self, llm: LLMClient, prompt_file: str = "baseline_nmm.md"):
        self.llm = llm
        self.system = (PROMPTS / prompt_file).read_text()

    def classify(self, text: str) -> dict:
        """Zero-shot detect the four non-manual markers in an English sentence.

        Returns a dict with one bool per NMM_LABELS entry, plus `_latency_s` / `_cost_usd`
        (underscore-prefixed so callers can filter them out). Strips ```json code fences before
        parsing; malformed JSON degrades to all-False (see the hardening item in ROADMAP.md).
        """
        r = self.llm.complete(self.system, f"Sentence: {text}\nJSON:")
        raw = r.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {}
        out = {label: bool(parsed.get(label, False)) for label in NMM_LABELS}
        out["_latency_s"] = r.latency_s
        out["_cost_usd"] = r.cost_usd
        return out
