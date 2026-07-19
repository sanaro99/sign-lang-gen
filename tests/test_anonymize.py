"""Tests for the retrieval anonymization heuristic (gap G8; Zhang et al. appendix)."""
from aslgloss.retrieval import anonymize_text


def test_mid_sentence_names_become_pronouns():
    assert anonymize_text("Yesterday John met Maria.") == "Yesterday they met they."


def test_possessive_names_become_their():
    assert anonymize_text("I borrowed John's book.") == "I borrowed their book."


def test_sentence_initial_word_kept():
    # sentence-initial capitalization is indistinguishable from a name -> deliberately kept
    assert anonymize_text("Maria left early.") == "Maria left early."
    # ...including after a sentence boundary
    assert anonymize_text("She left. Boston is far.") == "She left. Boston is far."


def test_keep_list_words_survive():
    assert anonymize_text("The Deaf community uses ASL every Monday.") == \
        "The Deaf community uses ASL every Monday."
    assert anonymize_text("Then I left.") == "Then I left."


def test_punctuation_preserved_around_replacement():
    assert anonymize_text("We saw Maria, then left.") == "We saw they, then left."


def test_lowercase_text_untouched():
    s = "the students study at a college in general."
    assert anonymize_text(s) == s
