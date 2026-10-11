"""Tests for request-level retrieval depth."""

from unittest.mock import AsyncMock, patch

from src.agent.models import AgentIntent, AgentResult
from src.web.app import app


@patch("src.web.app.run_agent", new_callable=AsyncMock)
def test_chat_passes_retrieval_top_k_to_agent(
    mock_run_agent,
) -> None:
    mock_run_agent.return_value = AgentResult(
        intent=AgentIntent.POLICY_QUESTION,
        answer="A test answer.",
        trace=(),
    )
    client = app.test_client()

    response = client.post(
        "/chat",
        json={
            "message": "What is the dress code?",
            "retrieval_top_k": 3,
        },
    )

    assert response.status_code == 200
    assert (
        mock_run_agent.await_args.kwargs["retrieval_top_k"]
        == 3
    )
    assert (
        response.get_json()["trace"][-1]["metrics"][
            "retrieval_top_k"
        ]
        == 3
    )


def test_chat_rejects_invalid_retrieval_top_k() -> None:
    client = app.test_client()

    response = client.post(
        "/chat",
        json={
            "message": "What is the dress code?",
            "retrieval_top_k": 11,
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == (
        "retrieval_top_k must be between 1 and 10."
    )
