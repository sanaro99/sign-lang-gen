"""Tests for the paper's multi-prompting structure (gap G4) and prompt resolution."""
import pytest

from aslgloss.baseline.gloss import GlossGenerator, resolve_prompt
from aslgloss.data.loaders import Example
from aslgloss.llm.client import LLMResponse


class DummyLLM:
    """Captures the exact message list sent, returns a fixed gloss."""

    def __init__(self):
        self.messages = None

    def complete_messages(self, messages):
        self.messages = messages
        return LLMResponse(text="GLOSS OUT", prompt_tokens=10, completion_tokens=2,
                           latency_s=0.0, model="dummy")

    def complete(self, system, user):
        return self.complete_messages([{"role": "system", "content": system},
                                       {"role": "user", "content": user}])


def _shots(n):
    return [Example(text=f"english {i}.", gloss=f"GLOSS-{i}") for i in range(n)]


def test_multiprompt_batches_shots_into_repeated_assistant_messages():
    llm = DummyLLM()
    gen = GlossGenerator(llm=llm, static_shots=_shots(5),
                         shots_as_messages=True, shot_batch_size=2)
    result = gen.generate(Example(text="A test sentence.", gloss=""))

    roles = [m["role"] for m in llm.messages]
    # system + ceil(5/2)=3 assistant batches + final user message (paper's structure)
    assert roles == ["system", "assistant", "assistant", "assistant", "user"]
    assert "GLOSS-0" in llm.messages[1]["content"]
    assert "GLOSS-4" in llm.messages[3]["content"]
    assert "Translate this sentence" in llm.messages[-1]["content"]
    # examples must NOT be inlined into the user message in this mode
    assert "GLOSS-0" not in llm.messages[-1]["content"]
    assert result.gloss == "GLOSS OUT"
    assert result.n_shots == 5


def test_default_mode_keeps_single_user_message():
    llm = DummyLLM()
    gen = GlossGenerator(llm=llm, static_shots=_shots(3))
    gen.generate(Example(text="A test sentence.", gloss=""))
    roles = [m["role"] for m in llm.messages]
    assert roles == ["system", "user"]
    assert "### Examples" in llm.messages[1]["content"]


def test_resolve_prompt_prefers_tracked_then_root_relative():
    # tracked prompts/ name
    assert resolve_prompt("baseline_gloss.md").name == "baseline_gloss.md"
    # repo-root-relative path (how a gitignored faithful transcription would be referenced)
    assert resolve_prompt("prompts/baseline_gloss.md").exists()
    with pytest.raises(FileNotFoundError):
        resolve_prompt("no_such_prompt.md")
