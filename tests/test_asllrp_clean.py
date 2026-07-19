"""Tests for the paper's Step-2 gloss cleaning (gap G7; docs/primary_source_findings.md §4)."""
from aslgloss.data.asllrp_clean import (
    clean_examples, clean_gloss, is_classifier, normalize_fingerspelling,
    strip_hand_markers, strip_repetition, unify_spatial_indices,
)
from aslgloss.data.loaders import Example


def test_fingerspelling_expands_to_letter_hyphenated():
    # the paper's exact example: fs-JOHN -> fs-J-O-H-N
    assert normalize_fingerspelling("fs-JOHN") == "fs-J-O-H-N"
    # already letter-hyphenated passes through unchanged
    assert normalize_fingerspelling("fs-J-O-H-N") == "fs-J-O-H-N"
    # non-fs tokens untouched
    assert normalize_fingerspelling("DEAF") == "DEAF"


def test_hand_markers_dropped():
    assert strip_hand_markers("(2h)WANT") == "WANT"
    assert strip_hand_markers("(1h)KNOW") == "KNOW"
    assert strip_hand_markers("(alt.)MOVE") == "MOVE"


def test_repetition_stripped_but_compounds_kept():
    assert strip_repetition("STUDY+") == "STUDY"
    assert strip_repetition("WORK++") == "WORK"
    # internal '+' is compounding (Appendix D) — meaningful, kept
    assert strip_repetition("MOTHER+FATHER") == "MOTHER+FATHER"


def test_classifiers_detected_and_dropped():
    assert is_classifier('DCL:B"curved"')
    assert is_classifier("BCL:C")
    assert is_classifier('(2h)LCL:B"move-up"')
    assert not is_classifier("DEAF")
    assert "DCL" not in clean_gloss('DCL:B"curved" BOOK')


def test_spatial_indices_unify_but_preserve_coreference():
    # arbitrary letters -> canonical i, j …, same-locus tokens still share a label
    assert unify_spatial_indices(["IX-3p:m", "SELF-3p:m", "IX-3p:q"]) == \
        ["IX-3p:i", "SELF-3p:i", "IX-3p:j"]
    # multi-locus suffixes relabel per part
    assert unify_spatial_indices(["IX-loc:q/m"]) == ["IX-loc:i/j"]


def test_clean_gloss_end_to_end():
    raw = '(2h)IX-3p:m fs-JOHN STUDY+ DCL:B"desk" DEAF'
    assert clean_gloss(raw) == "IX-3p:i fs-J-O-H-N STUDY DEAF"


def test_clean_examples_drops_emptied_pairs_and_preserves_metadata():
    exs = [
        Example(text="He signs.", gloss="(2h)IX-3p:m SIGN", source="ncslgr",
                doc_id="d1", sent_idx=3),
        Example(text="A classifier only.", gloss='DCL:B"curved"', source="ncslgr"),
    ]
    out = clean_examples(exs)
    assert len(out) == 1  # classifier-only gloss cleans to empty -> dropped
    assert out[0].gloss == "IX-3p:i SIGN"
    assert (out[0].doc_id, out[0].sent_idx) == ("d1", 3)
