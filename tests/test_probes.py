"""Tests for the discourse probe set (gap G1): shipped file validity + conversion."""
import pytest

from aslgloss.data.probes import CATEGORIES, load_probes, probes_to_examples, target_keys


def test_shipped_probe_file_is_valid_and_covers_all_categories():
    probes = load_probes()
    assert len(probes) >= 50, "M3 calls for a 50-100 passage probe set"
    assert {p["category"] for p in probes} == CATEGORIES
    # every category has enough items to report a per-category rate
    for cat in CATEGORIES:
        assert sum(p["category"] == cat for p in probes) >= 5


def test_probes_flatten_to_runner_examples():
    probes = load_probes()
    exs = probes_to_examples(probes)
    assert len(exs) == sum(len(p["sentences"]) for p in probes)
    # doc_id boundaries = probe boundaries, sent_idx contiguous from 0
    first = [e for e in exs if e.doc_id == probes[0]["probe_id"]]
    assert [e.sent_idx for e in first] == list(range(len(probes[0]["sentences"])))
    assert all(e.gloss == "" for e in exs)  # human-coded, never BLEU-scored


def test_target_keys_match_probe_count():
    probes = load_probes()
    assert len(target_keys(probes)) == len(probes)


def test_validation_rejects_bad_probe(tmp_path):
    bad = tmp_path / "bad.jsonl"
    bad.write_text('{"probe_id": "x-001", "category": "pronoun_referent", '
                   '"sentences": ["only one"], "target_idx": 0, "phenomenon": "p", '
                   '"coder_question": "q", "correct_answer": "a"}')
    with pytest.raises(ValueError, match=">= 2 sentences"):
        load_probes(bad)
