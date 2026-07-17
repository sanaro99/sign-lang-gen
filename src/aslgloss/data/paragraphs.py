"""Paragraph construction for the context buffer.

ASLG-PC12 sentences are isolated, so it CANNOT natively test discourse phenomena.
We build paragraph-level test sets ourselves. Two routes:

  1. `build_paragraphs`  — chunk consecutive corpus sentences into pseudo-documents.
     Cheap, but adjacency is not guaranteed to be genuinely coherent. Say so in the report.
  2. Hand-curated discourse set — the honest one. Author ~50-100 short paragraphs where
     meaning genuinely depends on prior sentences (pronoun antecedents, negation scope,
     topic continuity), gloss them against our conventions, and keep them as a held-out
     probe. This is what the week-6 error analysis really rests on.
"""
from __future__ import annotations

from dataclasses import dataclass

from .loaders import Example


@dataclass
class Paragraph:
    doc_id: str
    sentences: list[Example]


def _finish_paragraph(doc_id: str, chunk: list[Example]) -> Paragraph:
    """Reindex a paragraph's sentences to contiguous 0..n-1 (the buffer uses sent_idx as a
    list index into the paragraph) and stamp the shared doc_id."""
    for j, ex in enumerate(chunk):
        ex.doc_id, ex.sent_idx = doc_id, j
    return Paragraph(doc_id=doc_id, sentences=chunk)


def build_paragraphs(examples: list[Example], size: int = 5) -> list[Paragraph]:
    """Group sentences into paragraphs for the context buffer.

    If the corpus already carries real document structure (every Example has a `doc_id` — e.g.
    ASLLRP collections / narratives), **honor those real boundaries**: group consecutive sentences
    by `doc_id` so context windows never cross a narrative boundary. Real discourse is the entire
    point of the context contribution, so we must not discard it. Only when there is no `doc_id`
    (e.g. ASLG-PC12's isolated sentences) do we fall back to fixed-size pseudo-paragraphs, which are
    not genuine discourse (say so in the report)."""
    if examples and all(ex.doc_id is not None for ex in examples):
        paras: list[Paragraph] = []
        cur_id, chunk = examples[0].doc_id, []
        for ex in examples:
            if ex.doc_id != cur_id:
                paras.append(_finish_paragraph(cur_id, chunk))
                cur_id, chunk = ex.doc_id, []
            chunk.append(ex)
        paras.append(_finish_paragraph(cur_id, chunk))
        return paras

    paras = []
    for i in range(0, len(examples), size):
        paras.append(_finish_paragraph(f"doc_{i // size:05d}", examples[i : i + size]))
    return paras
