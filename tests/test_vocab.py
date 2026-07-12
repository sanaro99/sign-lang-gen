from aslgloss.baseline.vocab import build_gloss_vocab, oov_tokens
from aslgloss.data.loaders import Example


def test_oov_detection_ignores_fingerspelling():
    pool = [Example(text="a", gloss="CAT SLEEP"), Example(text="b", gloss="DOG RUN")]
    vocab = build_gloss_vocab(pool)
    assert oov_tokens("CAT fs-SMITH RUN", vocab) == []
    assert oov_tokens("CAT ELEPHANT", vocab) == ["ELEPHANT"]
