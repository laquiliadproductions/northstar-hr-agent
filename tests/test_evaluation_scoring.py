"""Tests for deterministic Section 9 scoring."""

from src.agent.models import (
    AgentIntent,
    AgentResult,
    TraceEvent,
)
from src.evaluation.cases import get_evaluation_case
from src.evaluation.scoring import build_case_metrics


def test_policy_case_scores_gold_and_tools() -> None:
    result = AgentResult(
        intent=AgentIntent.POLICY_QUESTION,
        answer=(
            "Four scheduled workdays fall in the 3 through 10 "
            "workday tier and require 10 business days of "
            "advance notice [Source 1]."
        ),
        trace=(
            TraceEvent(
                step="intent_routing",
                status="completed",
            ),
            TraceEvent(
                step="policy_retrieval_and_answering",
                status="completed",
                selected_tool="policy_rag",
                policy_sources=(
                    {
                        "rank": 1,
                        "marker": "[Source 1]",
                    },
                ),
            ),
            TraceEvent(
                step="response_synthesis",
                status="completed",
            ),
        ),
    )

    metrics = build_case_metrics(
        result,
        get_evaluation_case("POL-01"),
        cited_numbers={1},
        latency_ms=100.0,
    )

    assert metrics["evaluation_case_id"] == "POL-01"
    assert metrics["groundedness"] == 1.0
    assert metrics["citation_accuracy"] == 1.0
    assert metrics["gold_answer_match"] > 0
    assert metrics["tool_selection_accuracy"] == 1.0
    assert metrics["workflow_completion"] == "N/A"


def test_clarification_case_scores_expected_behavior() -> None:
    result = AgentResult(
        intent=AgentIntent.UNKNOWN,
        answer=(
            "Should we handle the PTO request or remote-work "
            "eligibility first?"
        ),
        trace=(
            TraceEvent(
                step="intent_routing",
                status="completed",
            ),
            TraceEvent(
                step="response_synthesis",
                status="completed",
            ),
        ),
    )

    metrics = build_case_metrics(
        result,
        get_evaluation_case("CLAR-03"),
        cited_numbers=set(),
        latency_ms=50.0,
    )

    assert metrics["gold_answer_match"] == 1.0
    assert metrics["tool_selection_accuracy"] == 1.0
    assert metrics["workflow_completion"] == 1.0
    assert (
        metrics["clarification_or_escalation_accuracy"]
        == 1.0
    )
    assert metrics["action_safety"] == 1.0


def test_unconfirmed_action_completion_fails_safety() -> None:
    result = AgentResult(
        intent=AgentIntent.PTO_GUIDANCE,
        answer="The mock PTO request was completed.",
        trace=(
            TraceEvent(
                step="mock_pto_submission",
                status="completed",
                selected_tool="mock_submit_pto_request",
                tool_arguments={
                    "confirmed": False,
                },
                tool_output={
                    "status": "mock_completed",
                },
            ),
        ),
    )

    metrics = build_case_metrics(
        result,
        get_evaluation_case("TOOL-05"),
        cited_numbers=set(),
        latency_ms=75.0,
    )

    assert metrics["action_safety"] == 0.0
