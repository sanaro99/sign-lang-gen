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

import logging
from dataclasses import dataclass

from ..config import PROMPTS, ROOT
from ..data.loaders import Example
from ..llm import LLMClient
from .vocab import oov_tokens

logger = logging.getLogger(__name__)


def resolve_prompt(name: str):
    """Resolve a prompt file: tracked `prompts/` first, then repo-root-relative.

    The fallback lets a config point at a gitignored faithful transcription of the paper's
    prompt wording (e.g. `data/paper_src/prompts/gloss_faithful.md`) without committing paper
    text — open team decision #6 in docs/decision_log.md. Raises if neither exists.
    """
    for candidate in (PROMPTS / name, ROOT / name):
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"Prompt {name!r} not found in {PROMPTS} or under {ROOT}. If this is a faithful "
        "paper-prompt transcription, it lives gitignored under data/paper_src/ on the machine "
        "that mined the TeX source (docs/primary_source_findings.md §2)."
    )


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
                 prompt_file: str = "baseline_gloss.md",
                 shots_as_messages: bool = False, shot_batch_size: int = 200):
        """Assemble the generator. `retriever` and `context_builder` are the pluggable
        extension points: both None reproduces the paper-faithful, sentence-isolated baseline;
        supplying a retriever enables Contribution 1 (RAG) and a context_builder enables
        Contribution 2 (paragraph context). `vocab`, when given, is used to flag OOV output.

        `shots_as_messages` switches to the paper's recovered "multi-prompting" structure
        (gap G4): examples are injected as repeated ASSISTANT messages, `shot_batch_size` pairs
        per message, instead of inlined into the user prompt. This is what makes a faithful
        ~1,474-static-shot baseline runnable. See docs/primary_source_findings.md §2.
        """
        self.llm = llm
        self.static_shots = static_shots or []
        self.retriever = retriever              # contribution 1 — None => paper-style static
        self.context_builder = context_builder  # contribution 2 — None => sentence-isolated
        self.vocab = vocab
        self.shots_as_messages = shots_as_messages
        self.shot_batch_size = max(1, shot_batch_size)
        self.system = resolve_prompt(prompt_file).read_text()

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

        target_parts = []
        if context_block:
            target_parts.append(
                f"### Surrounding discourse (for disambiguation only — do NOT gloss this)\n{context_block}")
        target_parts.append(f"### Translate this sentence\nEnglish: {example.text}\nGloss:")

        if self.shots_as_messages:
            # Paper's multi-prompting: examples as repeated assistant messages, one per batch.
            messages = [{"role": "system", "content": self.system}]
            for i in range(0, len(shots), self.shot_batch_size):
                messages.append({"role": "assistant",
                                 "content": format_shots(shots[i:i + self.shot_batch_size])})
            messages.append({"role": "user", "content": "\n\n".join(target_parts)})
            r = self.llm.complete_messages(messages)
        else:
            user = "\n\n".join([f"### Examples\n{format_shots(shots)}", *target_parts])
            r = self.llm.complete(self.system, user)
        lines = r.text.replace("Gloss:", "").strip().splitlines() if r.text else []
        gloss = lines[0].strip() if lines else ""
        if len(lines) > 1:
            # Multi-line output means the model ignored the single-line instruction; we keep only
            # the first line, which can silently truncate a gloss — surface it (ROADMAP hardening).
            logger.warning("Multi-line gloss output (%d lines); keeping first. text=%r first=%r",
                           len(lines), example.text[:80], gloss[:120])
        if not gloss:
            logger.warning("Empty gloss output for text=%r", example.text[:80])

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
