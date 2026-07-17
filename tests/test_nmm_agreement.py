import math

import pytest

from aslgloss.config import NMM_LABELS
from aslgloss.evaluation import (
    agreement_report, cohen_kappa, load_gold, make_sheet_rows, merge_gold,
    nmm_scores, read_sheet, save_gold, write_sheet,
)


def _filled(rows, values):
    """Copy blank sheet rows with every label set to the given per-row dicts."""
    return [{**r, **v} for r, v in zip(rows, values)]


def test_cohen_kappa_known_values():
    # Perfect agreement with both classes present -> 1.0
    assert cohen_kappa([True, False, True], [True, False, True]) == pytest.approx(1.0)
    # Systematic disagreement -> negative kappa
    assert cohen_kappa([True, False], [False, True]) < 0
    # Both raters constant single class -> chance agreement is 1, kappa undefined
    assert math.isnan(cohen_kappa([False, False], [False, False]))


def test_sheet_roundtrip_and_incomplete_detection(tmp_path):
    rows = make_sheet_rows(["Did the kids  play at the park?", "I have no pets."])
    assert rows[0]["source"] == "Did the kids play at the park?"  # whitespace normalized
    path = write_sheet(rows, tmp_path / "sheet.csv")

    # Unfilled sheet must refuse to load as complete
    with pytest.raises(ValueError, match="not 0/1"):
        read_sheet(path)

    filled = _filled(rows, [
        {l: "1" if l == "yes_no_question" else "0" for l in NMM_LABELS},
        {l: "1" if l == "negation" else "0" for l in NMM_LABELS},
    ])
    write_sheet(filled, path)
    back = read_sheet(path)
    assert back[0]["yes_no_question"] is True
    assert back[0]["negation"] is False
    assert back[1]["negation"] is True


def test_agreement_and_merge_with_adjudication(tmp_path):
    rows = make_sheet_rows(["Is mom sick?", "If it rains, I stay home.", "Where did Sue move?"])
    a1 = _filled(rows, [
        {"yes_no_question": True, "wh_question": False, "conditional": False, "negation": False},
        {"yes_no_question": False, "wh_question": False, "conditional": True, "negation": False},
        {"yes_no_question": False, "wh_question": True, "conditional": False, "negation": False},
    ])
    a2 = _filled(rows, [
        {"yes_no_question": True, "wh_question": False, "conditional": False, "negation": False},
        {"yes_no_question": False, "wh_question": False, "conditional": True, "negation": True},  # disagrees
        {"yes_no_question": False, "wh_question": True, "conditional": False, "negation": False},
    ])

    rep = agreement_report(a1, a2)
    assert rep["n_common"] == 3
    assert len(rep["disagreements"]) == 1
    assert rep["disagreements"][0]["labels"] == ["negation"]
    assert rep["labels"]["wh_question"]["raw_agreement"] == 1.0

    # Merge without adjudication leaves the disputed item unresolved
    gold, unresolved = merge_gold(a1, a2)
    assert len(gold) == 2 and len(unresolved) == 1

    # Adjudicated value resolves it
    adj = _filled(make_sheet_rows(["If it rains, I stay home."]),
                  [{"yes_no_question": False, "wh_question": False, "conditional": True, "negation": False}])
    gold, unresolved = merge_gold(a1, a2, adj)
    assert len(gold) == 3 and not unresolved

    # Gold roundtrip -> keyed by normalized source, bools preserved
    path = save_gold(gold, tmp_path / "gold.jsonl")
    loaded = load_gold(path)
    assert loaded["Is mom sick?"]["yes_no_question"] is True
    assert loaded["If it rains, I stay home."]["conditional"] is True


def test_nmm_scores_against_gold_matches_hand_computation():
    golds = [
        {"yes_no_question": True, "wh_question": False, "conditional": False, "negation": False},
        {"yes_no_question": False, "wh_question": True, "conditional": False, "negation": True},
    ]
    preds = [
        {"yes_no_question": True, "wh_question": False, "conditional": False, "negation": True},  # neg FP
        {"yes_no_question": False, "wh_question": True, "conditional": False, "negation": True},
    ]
    s = nmm_scores(preds, golds)
    assert s["yes_no_question"]["precision"] == pytest.approx(1.0)
    assert s["wh_question"]["recall"] == pytest.approx(1.0)
    # negation: 2 predicted positive, 1 true positive -> P=0.5, R=1.0
    assert s["negation"]["precision"] == pytest.approx(0.5)
    assert s["negation"]["recall"] == pytest.approx(1.0)
    assert s["macro"]["precision"] == pytest.approx((1.0 + 1.0 + 0.0 + 0.5) / 4)
