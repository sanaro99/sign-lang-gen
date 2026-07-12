from aslgloss.evaluation import tag_errors


def test_detects_dropped_negation():
    tags = tag_errors("They did not approve it.", "IX APPROVE", "IX APPROVE NOT")
    assert "negation_scope" in tags


def test_detects_gloss_ordering_error():
    tags = tag_errors("Monday the committee met.", "COMMITTEE MEET MONDAY", "MONDAY COMMITTEE MEET")
    assert "gloss_ordering" in tags


def test_clean_translation_has_no_tags():
    assert tag_errors("Cats sleep.", "CAT SLEEP", "CAT SLEEP") == []
