from unittest.mock import AsyncMock, patch

from src.agent.models import AgentIntent, AgentResult, TraceEvent
from src.web.app import app


def test_chat_rejects_empty_message():
    """Chat endpoint should reject an empty request."""

    client = app.test_client()

    response = client.post("/chat", json={})

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "A non-empty message is required."
    }


@patch("src.web.app.run_agent", new_callable=AsyncMock)
def test_chat_returns_expected_response_shape(mock_run_agent):
    """Chat endpoint should return answer, citations, snippets, and trace."""

    mock_run_agent.return_value = AgentResult(
        intent=AgentIntent.POLICY_QUESTION,
        answer="Northstar prohibits harassment [Source 1].",
        answer_basis=("Verified Northstar policy citations.",),
        requires_confirmation=False,
        escalation_required=False,
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
                        "chunk_id": "chunk-test",
                        "title": "Test Policy",
                        "document": "test-policy.md",
                        "section": "Harassment",
                        "snippet": "Northstar prohibits harassment.",
                        "page": None,
                        "row": None,
                        "similarity": 0.9,
                    },
                ),
            ),
            TraceEvent(
                step="response_synthesis",
                status="completed",
            ),
        ),
    )

    client = app.test_client()

    response = client.post(
        "/chat",
        json={"message": "What is the harassment policy?"},
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["intent"] == "policy_question"
    assert data["answer"] == "Northstar prohibits harassment [Source 1]."

    assert data["citations"] == [
        {
            "marker": "[Source 1]",
            "title": "Test Policy",
            "document": "test-policy.md",
            "section": "Harassment",
            "page": None,
            "row": None,
        }
    ]

    assert data["snippets"] == [
        {
            "marker": "[Source 1]",
            "snippet": "Northstar prohibits harassment.",
        }
    ]

    assert data["trace"] == [
        {
            "step": "intent_routing",
            "status": "completed",
            "selected_tool": None,
        },
        {
            "step": "policy_retrieval_and_answering",
            "status": "completed",
            "selected_tool": "policy_rag",
        },
        {
            "step": "response_synthesis",
            "status": "completed",
            "selected_tool": None,
        },
    ]

@patch("src.web.app.run_agent", new_callable=AsyncMock)
def test_chat_passes_employee_email_to_agent(mock_run_agent):
    """Chat endpoint should pass employee identity to the agent."""

    mock_run_agent.return_value = AgentResult(
        intent=AgentIntent.PTO_GUIDANCE,
        answer="Maya Chen has 16.9 days available.",
        answer_basis=("Employee lookup through MCP.",),
        requires_confirmation=False,
        escalation_required=False,
        trace=(
            TraceEvent(
                step="employee_lookup",
                status="completed",
                selected_tool="lookup_employee_profile",
            ),
            TraceEvent(
                step="pto_balance_lookup",
                status="completed",
                selected_tool="check_pto_balance",
            ),
        ),
    )

    client = app.test_client()

    response = client.post(
        "/chat",
        json={
            "message": "How much PTO do I have available?",
            "work_email": "maya.chen@northstaranalytics.com",
        },
    )

    assert response.status_code == 200

    mock_run_agent.assert_awaited_once_with(
        "How much PTO do I have available?",
        work_email="maya.chen@northstaranalytics.com",
        full_name=None,
        employee_id=None,
        start_date=None,
        end_date=None,
        requested_days=None,
        confirmed=False,
    )

    data = response.get_json()

    assert data["intent"] == "pto_guidance"
    assert data["answer"] == "Maya Chen has 16.9 days available."


