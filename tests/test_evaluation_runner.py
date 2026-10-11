"""Tests for evaluation result aggregation."""

from scripts.run_evaluation import (
    case_passed,
    percentile,
)
from src.evaluation.cases import get_evaluation_case


def test_percentile_interpolates_values() -> None:
    values = [100.0, 200.0, 300.0, 400.0]

    assert percentile(values, 0.50) == 250.0
    assert percentile(values, 0.95) == 385.0


def test_policy_case_passes_required_metrics() -> None:
    case = get_evaluation_case("POL-01")
    metrics = {
        "groundedness": 1.0,
        "citation_accuracy": 1.0,
        "gold_answer_match": 0.5,
        "tool_selection_accuracy": 1.0,
        "workflow_completion": "N/A",
        "clarification_or_escalation_accuracy": "N/A",
        "action_safety": "N/A",
    }

    assert case_passed(case, metrics) is True


def test_policy_case_fails_incorrect_tool_selection() -> None:
    case = get_evaluation_case("POL-01")
    metrics = {
        "groundedness": 1.0,
        "citation_accuracy": 1.0,
        "gold_answer_match": 0.5,
        "tool_selection_accuracy": 0.0,
        "workflow_completion": "N/A",
        "clarification_or_escalation_accuracy": "N/A",
        "action_safety": "N/A",
    }

    assert case_passed(case, metrics) is False
