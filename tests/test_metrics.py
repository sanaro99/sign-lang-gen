"""Tests for the measurement stack (gap G2): normalization, chrF, EM/ROUGE, bootstrap."""
import pytest

from aslgloss.evaluation import (
    bleu_components, corpus_chrf, exact_match,
    normalize_real_asl, paired_bootstrap_bleu, rouge_l,
)


# ---------- normalize_real_asl ----------

def test_normalize_strips_locus_suffixes():
    assert normalize_real_asl("IX-3p:i SELF-3p:j IX-loc:i/j") == "IX-3p SELF-3p IX-loc"


def test_normalize_strips_handedness_prefixes():
    assert normalize_real_asl("(2h)WANT (1h)KNOW (alt.)MOVE") == "WANT KNOW MOVE"


def test_normalize_drops_classifiers_and_quoted_prosody():
    # classifiers (paper Step 2 drops them) and quoted gesture/prosody are un-generatable
    assert normalize_real_asl('DCL:B"curved" BOOK 5"pause" READ') == "BOOK READ"


def test_normalize_unifies_name_loan_fingerspelling():
    # ns-/# map to fs-; letter-by-letter fs collapses, so name choice can match across conventions
    assert normalize_real_asl("ns-GALLAUDET #JOB fs-J-O-H-N") == "fs-GALLAUDET fs-JOB fs-JOHN"


def test_normalize_strips_repetition_plus():
    assert normalize_real_asl("STUDY+ WORK++") == "STUDY WORK"


def test_normalize_keeps_plain_tokens():
    assert normalize_real_asl("DEAF COLLEGE IX-3p") == "DEAF COLLEGE IX-3p"


def test_normalized_pair_scores_higher_than_raw():
    # the whole point: reachable-token scoring separates notation misses from content misses
    ref = ['ns-GALLAUDET IX-loc:i SELF-3p:j DEAF COLLEGE (1h)IX-3p:i']
    hyp = ['fs-GALLAUDET DEAF COLLEGE IX-3p']
    raw = corpus_chrf(hyp, ref)
    norm = corpus_chrf([normalize_real_asl(h) for h in hyp],
                       [normalize_real_asl(r) for r in ref])
    assert norm > raw


# ---------- components / chrF / EM / ROUGE ----------

def test_bleu_components_shape():
    c = bleu_components(["A B C D", "E F G H"], ["A B C D", "E F G H"])
    assert c["bleu4"] == pytest.approx(1.0)
    assert c["p1"] == pytest.approx(100.0)
    assert c["brevity_penalty"] == pytest.approx(1.0)


def test_exact_match_counts_whitespace_insensitively():
    assert exact_match(["A  B", "A B"], ["A B", "C D"]) == pytest.approx(0.5)


def test_rouge_l_keeps_gloss_tokens_whole():
    # identical strings -> 1.0; hyphenated tokens must not be split into subwords
    assert rouge_l(["fs-JOHN LIKE X-I"], ["fs-JOHN LIKE X-I"]) == pytest.approx(1.0)
    # completely disjoint -> 0.0 (would be nonzero if fs-/X- fragments were split off and matched)
    assert rouge_l(["fs-JOHN"], ["fs-MARY"]) == pytest.approx(0.0)


# ---------- paired bootstrap ----------

def test_paired_bootstrap_identical_systems_is_null():
    hyps = ["A B C D"] * 20
    refs = ["A B C D"] * 20
    r = paired_bootstrap_bleu(hyps, hyps, refs, n_samples=100)
    assert r["delta"] == pytest.approx(0.0)
    assert r["p_value"] >= 0.05  # cannot call identical systems different


def test_paired_bootstrap_detects_clear_winner():
    refs = [f"A{i} B{i} C{i} D{i}" for i in range(30)]
    good = list(refs)                       # perfect system
    bad = ["X Y Z W"] * 30                  # useless system
    r = paired_bootstrap_bleu(bad, good, refs, n_samples=200)
    assert r["delta"] > 0.9
    assert r["p_value"] < 0.05
    assert r["ci_low"] > 0


def test_paired_bootstrap_requires_alignment():
    with pytest.raises(AssertionError):
        paired_bootstrap_bleu(["A"], ["A", "B"], ["A", "B"])
