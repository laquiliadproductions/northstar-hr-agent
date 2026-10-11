"""Tests for case-aware metrics in the chat endpoint."""

from unittest.mock import AsyncMock, patch

from src.agent.models import (
    AgentIntent,
    AgentResult,
    TraceEvent,
)
from src.web.app import app


def _policy_result() -> AgentResult:
    return AgentResult(
        intent=AgentIntent.POLICY_QUESTION,
        answer=(
            "Four scheduled workdays fall in the 3 through 10 "
            "workday tier and require at least 10 business days "
            "of advance notice [Source 1]."
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
                        "title": "Northstar PTO Policy",
                        "document": "pto-policy.md",
                        "section": "Planned PTO",
                        "page": None,
                        "row": None,
                        "snippet": (
                            "Four days require 10 business "
                            "days of advance notice."
                        ),
                    },
                ),
            ),
            TraceEvent(
                step="response_synthesis",
                status="completed",
            ),
        ),
    )


@patch("src.web.app.run_agent", new_callable=AsyncMock)
def test_chat_scores_known_evaluation_case(
    mock_run_agent,
) -> None:
    mock_run_agent.return_value = _policy_result()
    client = app.test_client()

    response = client.post(
        "/chat",
        json={
            "evaluation_case_id": "POL-01",
            "message": (
                "How much advance notice do I need "
                "for four days of planned PTO?"
            ),
            "run_condition": "warm",
        },
    )

    assert response.status_code == 200

    data = response.get_json()
    metrics = data["trace"][-1]["metrics"]

    assert metrics["evaluation_case_id"] == "POL-01"
    assert metrics["run_condition"] == "warm"
    assert metrics["groundedness"] == 1.0
    assert metrics["citation_accuracy"] == 1.0
    assert metrics["gold_answer_match"] > 0
    assert metrics["tool_selection_accuracy"] == 1.0


def test_chat_rejects_unknown_evaluation_case() -> None:
    client = app.test_client()

    response = client.post(
        "/chat",
        json={
            "evaluation_case_id": "NOT-A-CASE",
            "message": "Test message",
        },
    )

    assert response.status_code == 400
    assert "Unknown evaluation case ID" in (
        response.get_json()["error"]
    )
