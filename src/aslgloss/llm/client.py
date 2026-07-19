"""Provider-agnostic LLM client.

The paper used gpt-4o-2024-05-13. That snapshot may be deprecated, so we keep an
open-model path (vLLM / Ollama / TGI via an OpenAI-compatible endpoint) to protect
reproducibility. Every call reports token counts and latency so week-6 cost/latency
comparisons are free.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass

from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

# `openai` is imported lazily inside LLMClient.__init__ so that the pure-logic modules
# (vocab, context buffer, error analysis) remain importable and testable without API deps.

# USD per 1M tokens. Update from the provider's pricing page; recorded in each run manifest.
PRICING = {
    "gpt-4o-2024-05-13": {"in": 5.00, "out": 15.00},
    "gpt-4o": {"in": 2.50, "out": 10.00},
    "gpt-4o-mini": {"in": 0.15, "out": 0.60},
}


@dataclass
class LLMResponse:
    text: str
    prompt_tokens: int
    completion_tokens: int
    latency_s: float
    model: str

    @property
    def cost_usd(self) -> float:
        p = PRICING.get(self.model)
        if not p:
            return 0.0
        return (self.prompt_tokens * p["in"] + self.completion_tokens * p["out"]) / 1_000_000


class LLMClient:
    def __init__(self, provider: str = "openai", model: str = "gpt-4o-2024-05-13",
                 temperature: float = 0.0, max_tokens: int = 512, seed: int | None = 7):
        """Build a client for one model.

        provider="openai" uses OPENAI_API_KEY. provider="open" targets an OpenAI-compatible
        endpoint (vLLM / Ollama / TGI) via OPEN_MODEL_BASE_URL, preserving reproducibility if
        the paper's pinned snapshot is deprecated. `openai` is imported lazily so the pure-logic
        modules stay importable without the API dependency installed.
        """
        from openai import OpenAI

        self.provider = provider
        self.model, self.temperature, self.max_tokens, self.seed = model, temperature, max_tokens, seed
        if provider == "open":
            self.client = OpenAI(
                base_url=os.getenv("OPEN_MODEL_BASE_URL", "http://localhost:11434/v1"),
                api_key=os.getenv("OPENAI_API_KEY", "not-needed"),
            )
        else:
            self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    @retry(stop=stop_after_attempt(4), wait=wait_exponential(min=1, max=20))
    def complete_messages(self, messages: list[dict]) -> LLMResponse:
        """Run one chat completion over an explicit message list, with token/latency/cost accounting.

        This is the entry point for the paper's "multi-prompting" structure (gap G4): Phase A0
        recovered that Zhang et al. inject their ~1,474 in-context examples as a SEQUENCE OF
        REPEATED ASSISTANT MESSAGES, one per batch — not by iterative re-querying. See
        docs/primary_source_findings.md §2. Retries up to 4 times with exponential backoff.
        """
        # Local "thinking" models (e.g. gemma4 via Ollama) route their output to a reasoning channel
        # by default, leaving OpenAI-compat `content` empty. Disable it for the open provider so we
        # get the gloss back. (gpt-4o rejects reasoning_effort, so only send it for `open`.)
        extra = {"reasoning_effort": "none"} if self.provider == "open" else {}
        t0 = time.perf_counter()
        r = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            seed=self.seed,
            **extra,
        )
        return LLMResponse(
            text=(r.choices[0].message.content or "").strip(),
            prompt_tokens=r.usage.prompt_tokens,
            completion_tokens=r.usage.completion_tokens,
            latency_s=time.perf_counter() - t0,
            model=self.model,
        )

    def complete(self, system: str, user: str) -> LLMResponse:
        """Convenience wrapper: one system + one user message (retry lives in complete_messages)."""
        return self.complete_messages([{"role": "system", "content": system},
                                       {"role": "user", "content": user}])
