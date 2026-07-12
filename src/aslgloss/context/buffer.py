"""Paragraph-level context buffer. CONTRIBUTION 2.

Zhang et al. state their pipeline operates in a "context-free setting, where each
sentence is translated independently." Sincan et al. (ICCVW 2023) showed discourse
context roughly DOUBLED BLEU-4 for sign language translation — they fed the model
previous sentences plus its own earlier confident predictions, mimicking how human
interpreters use conversational flow to disambiguate.

We do the same thing in the reverse direction (text -> gloss) and via prompting rather
than a trained architecture. Two knobs:

  window_before / window_after : how many neighboring sentences to show
  include_prior_glosses        : feed back our own already-generated glosses for the
                                 preceding sentences (Sincan's self-conditioning idea)

The context block is provided FOR DISAMBIGUATION ONLY — the prompt instructs the model
to gloss the target sentence alone. Guarding against context leaking into the output is
an explicit error-analysis category (see docs/error_taxonomy.md).
"""
from __future__ import annotations

from ..data.loaders import Example


class ParagraphContextBuffer:
    def __init__(self, paragraphs, window_before: int = 2, window_after: int = 1,
                 include_prior_glosses: bool = True):
        self.window_before = window_before
        self.window_after = window_after
        self.include_prior_glosses = include_prior_glosses
        self.by_doc = {p.doc_id: p.sentences for p in paragraphs}

    def build(self, example: Example, prior_glosses: dict | None = None) -> str | None:
        """Assemble the discourse block around `example`: neighboring sentences within the
        window, with the target marked [TARGET] and others [prev]/[next]. When enabled, previous
        sentences carry our own already-generated gloss (from `prior_glosses`, keyed by
        (doc_id, sent_idx)). Returns None for isolated sentences (no doc_id or no neighbors).
        """
        if example.doc_id is None or example.sent_idx is None:
            return None
        sents = self.by_doc.get(example.doc_id, [])
        i = example.sent_idx
        lo, hi = max(0, i - self.window_before), min(len(sents), i + self.window_after + 1)

        lines: list[str] = []
        for j in range(lo, hi):
            if j == i:
                lines.append(f"[TARGET] {sents[j].text}")
                continue
            line = f"[{'prev' if j < i else 'next'}] {sents[j].text}"
            if self.include_prior_glosses and j < i and prior_glosses:
                g = prior_glosses.get((example.doc_id, j))
                if g:
                    line += f"\n         (already glossed as: {g})"
            lines.append(line)

        return "\n".join(lines) if len(lines) > 1 else None
