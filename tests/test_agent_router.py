"""Tests for agent intent and RAG-sufficiency routing."""

from src.agent.models import AgentIntent
from src.agent.router import classify_intent

def test_general_policy_question_uses_rag_only() -> None:
    result = classify_intent("What is the dress code?")

    assert result.intent == AgentIntent.POLICY_QUESTION
    assert result.rag_only is True
    assert result.selected_tools == ()


def test_general_pto_policy_question_uses_rag_only() -> None:
    result = classify_intent(
        "How much advance notice do I need "
        "for four days of planned PTO?"
    )

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


def test_employee_specific_pto_phrases_select_guidance_tools() -> None:
    messages = (
        "How much PTO can I use?",
        "Do I have any PTO available?",
        (
            "I need six days off for surgery. "
            "How do PTO and medical leave apply?"
        ),
    )

    for message in messages:
        result = classify_intent(message)

        assert result.intent == AgentIntent.PTO_GUIDANCE
        assert result.rag_only is False
        assert "lookup_employee_profile" in result.selected_tools
        assert "check_pto_balance" in result.selected_tools
        assert (
            "mock_submit_pto_request"
            not in result.selected_tools
        )
