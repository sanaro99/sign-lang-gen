"""Module 1, part 1: English text -> ASL gloss.

Re-implemented from Zhang et al. (CHI 2025) §3.1 + Appendix B. No Apple code exists.

Baseline behaviour (paper-faithful): a large STATIC set of in-context English-gloss
example pairs. The paper used ~1,474-1,494 pairs (80% split of their ASLLRP set) and,
because that exceeds the usable context window, resorted to "multi-prompting" —
batching examples and prompting iteratively.

That workaround is exactly what our RAG layer removes: retrieve the top-k most similar
examples per input instead of shipping the whole pool. Set `retriever` to enable it.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..config import PROMPTS
from ..data.loaders import Example
from ..llm import LLMClient
from .vocab import oov_tokens


@dataclass
class GlossResult:
    text: str
    gloss: str
    prompt_tokens: int
    completion_tokens: int
    latency_s: float
    cost_usd: float
    n_shots: int
    oov: list[str]
    context_used: str | None = None


def format_shots(examples: list[Example]) -> str:
    """Render in-context examples as alternating 'English:' / 'Gloss:' blocks for the prompt."""
    return "\n\n".join(f"English: {e.text}\nGloss: {e.gloss}" for e in examples)


class GlossGenerator:
    def __init__(self, llm: LLMClient, static_shots: list[Example] | None = None,
                 retriever=None, context_builder=None, vocab: set[str] | None = None,
                 prompt_file: str = "baseline_gloss.md"):
        """Assemble the generator. `retriever` and `context_builder` are the pluggable
        extension points: both None reproduces the paper-faithful, sentence-isolated baseline;
        supplying a retriever enables Contribution 1 (RAG) and a context_builder enables
        Contribution 2 (paragraph context). `vocab`, when given, is used to flag OOV output.
        """
        self.llm = llm
        self.static_shots = static_shots or []
        self.retriever = retriever              # contribution 1 — None => paper-style static
        self.context_builder = context_builder  # contribution 2 — None => sentence-isolated
        self.vocab = vocab
        self.system = (PROMPTS / prompt_file).read_text()

    def _shots(self, text: str) -> list[Example]:
        """Pick the in-context examples: retrieved top-k if a retriever is set, else the static set."""
        if self.retriever is not None:
            return self.retriever.retrieve(text)
        return self.static_shots

    def generate(self, example: Example, prior_glosses: dict | None = None) -> GlossResult:
        """Gloss one sentence.

        Builds the prompt (examples + optional discourse context + target), calls the LLM, keeps
        only the first output line (stripping a leading 'Gloss:'), and flags OOV tokens. `prior_glosses`
        maps (doc_id, sent_idx) -> earlier gloss so the context buffer can feed back our own outputs.
        Returns a GlossResult with the gloss plus token/latency/cost accounting.
        """
        shots = self._shots(example.text)

        context_block = None
        if self.context_builder is not None:
            context_block = self.context_builder.build(example, prior_glosses=prior_glosses)

        parts = [f"### Examples\n{format_shots(shots)}"]
        if context_block:
            parts.append(f"### Surrounding discourse (for disambiguation only — do NOT gloss this)\n{context_block}")
        parts.append(f"### Translate this sentence\nEnglish: {example.text}\nGloss:")
        user = "\n\n".join(parts)

        r = self.llm.complete(self.system, user)
        gloss = r.text.replace("Gloss:", "").strip().splitlines()[0].strip() if r.text else ""

        return GlossResult(
            text=example.text,
            gloss=gloss,
            prompt_tokens=r.prompt_tokens,
            completion_tokens=r.completion_tokens,
            latency_s=r.latency_s,
            cost_usd=r.cost_usd,
            n_shots=len(shots),
            oov=oov_tokens(gloss, self.vocab) if self.vocab else [],
            context_used=context_block,
        )
