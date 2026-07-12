from aslgloss.context import ParagraphContextBuffer
from aslgloss.data import build_paragraphs
from aslgloss.data.loaders import Example


def _fixture():
    ex = [
        Example(text="The committee met on Monday.", gloss="MONDAY COMMITTEE MEET"),
        Example(text="It approved the budget.", gloss="IX APPROVE BUDGET"),
        Example(text="They did not discuss the amendment.", gloss="AMENDMENT DISCUSS NOT"),
    ]
    return ex, build_paragraphs(ex, size=3)


def test_buffer_includes_neighbors_and_marks_target():
    ex, paras = _fixture()
    buf = ParagraphContextBuffer(paras, window_before=1, window_after=1)
    block = buf.build(ex[1])
    assert "[TARGET] It approved the budget." in block
    assert "[prev]" in block and "[next]" in block


def test_prior_glosses_are_fed_back():
    ex, paras = _fixture()
    buf = ParagraphContextBuffer(paras, window_before=1, window_after=0,
                                 include_prior_glosses=True)
    block = buf.build(ex[1], prior_glosses={("doc_00000", 0): "MONDAY COMMITTEE MEET"})
    assert "already glossed as: MONDAY COMMITTEE MEET" in block


def test_isolated_sentence_returns_no_context():
    buf = ParagraphContextBuffer([], window_before=2, window_after=1)
    assert buf.build(Example(text="Hello.", gloss="HELLO")) is None
