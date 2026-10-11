"""Tests for loading the Section 9 evaluation set."""

import pytest

from src.evaluation.cases import (
    get_evaluation_case,
    load_evaluation_cases,
)


def test_evaluation_set_contains_25_unique_cases() -> None:
    cases = load_evaluation_cases()

    assert len(cases) == 25
    assert len(set(cases)) == 25


def test_policy_case_contains_gold_and_behavior() -> None:
    case = get_evaluation_case("POL-01")

    assert case["request"]["message"] == (
        "How much advance notice do I need "
        "for four days of planned PTO?"
    )
    assert case["expected_behavior"]["intent"] == (
        "policy_question"
    )
    assert case["expected_behavior"]["required_tools"] == [
        "policy_rag"
    ]
    assert case["gold_answer"]["required_points"]


def test_unknown_evaluation_case_raises_key_error() -> None:
    with pytest.raises(
        KeyError,
        match="Unknown evaluation case ID",
    ):
        get_evaluation_case("NOT-A-CASE")
