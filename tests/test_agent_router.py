"""Tests for agent intent and RAG-sufficiency routing."""

from src.agent.models import AgentIntent
from src.agent.router import classify_intent

def test_general_policy_question_uses_rag_only() -> None:
    result = classify_intent("What is the dress code?")

    assert result.intent == AgentIntent.POLICY_QUESTION
    assert result.rag_only is True
    assert result.selected_tools == ()

def test_pto_request_selects_pto_tools() -> None:
    result = classify_intent("What is my PTO balance?")

    assert result.intent == AgentIntent.PTO_GUIDANCE
    assert result.rag_only is False
    assert "lookup_employee_profile" in result.selected_tools
    assert "check_pto_balance" in result.selected_tools

def test_remote_request_selects_employee_tool() -> None:
    result = classify_intent("Am I eligible to work remotely?")

    assert result.intent == AgentIntent.REMOTE_WORK_ELIGIBILITY
    assert result.rag_only is False
    assert result.selected_tools == ("lookup_employee_profile",)

def test_mixed_workflow_request_requires_clarification() -> None:
    result = classify_intent(
        "Can I take PTO while working remotely?"
    )

    assert result.intent == AgentIntent.UNKNOWN
    assert result.clarification_question is not None

def test_empty_request_requires_clarification() -> None:
    result = classify_intent("   ")

    assert result.intent == AgentIntent.UNKNOWN
    assert result.clarification_question is not None
