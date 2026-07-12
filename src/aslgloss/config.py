"""Central configuration. Every experiment is fully described by one YAML in configs/."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_INTERIM = ROOT / "data" / "interim"
DATA_PROCESSED = ROOT / "data" / "processed"
PROMPTS = ROOT / "prompts"
RESULTS = ROOT / "results"

# Non-manual markers modeled in Zhang et al. (CHI 2025), Module 1 — classified zero-shot.
NMM_LABELS = ["yes_no_question", "wh_question", "conditional", "negation"]


@dataclass
class RetrievalConfig:
    """Contribution 1: RAG-based few-shot example retrieval (replaces the paper's static pool)."""
    enabled: bool = False
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    k: int = 8
    index_path: str = "data/processed/example_pool.faiss"
    pool_path: str = "data/processed/example_pool.jsonl"
    # KATE (Liu et al. 2022) leaves ordering unexplored; we ablate it.
    order: str = "similarity_desc"  # similarity_desc | similarity_asc | random


@dataclass
class ContextConfig:
    """Contribution 2: paragraph-level context buffer (the paper is sentence-isolated)."""
    enabled: bool = False
    window_before: int = 2
    window_after: int = 1
    include_prior_glosses: bool = True  # feed back our own confident prior outputs (cf. Sincan 2023)


@dataclass
class LLMConfig:
    provider: str = "openai"           # openai | open
    model: str = "gpt-4o-2024-05-13"   # paper's exact snapshot; pin it, it may be deprecated
    temperature: float = 0.0
    max_tokens: int = 512
    seed: int | None = 7


@dataclass
class ExperimentConfig:
    name: str = "baseline"
    dataset: str = "aslg_pc12"         # aslg_pc12 | asllrp | isl
    split: str = "test"
    n_examples: int | None = 200       # None = full split
    static_shots: int = 8              # used when retrieval is disabled
    constrain_vocab: bool = True       # paper constrains output to the word-gloss dictionary
    gloss_prompt: str = "baseline_gloss.md"
    nmm_prompt: str = "baseline_nmm.md"
    llm: LLMConfig = field(default_factory=LLMConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    context: ContextConfig = field(default_factory=ContextConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "ExperimentConfig":
        """Load a config YAML, routing the nested `llm`/`retrieval`/`context` blocks into their
        sub-dataclasses so one file fully specifies an experimental condition."""
        raw = yaml.safe_load(Path(path).read_text())
        return cls(
            **{k: v for k, v in raw.items() if k not in {"llm", "retrieval", "context"}},
            llm=LLMConfig(**raw.get("llm", {})),
            retrieval=RetrievalConfig(**raw.get("retrieval", {})),
            context=ContextConfig(**raw.get("context", {})),
        )
