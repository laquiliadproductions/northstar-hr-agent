"""Tests for targeted policy retrieval-query expansion."""

from src.agent.rag_adapter import _expand_retrieval_question


def test_expands_performance_review_acknowledgment_query() -> None:
    question = (
        "Does acknowledging a performance review mean I agree with it?"
    )

    expanded = _expand_retrieval_question(question)

    assert expanded.startswith(question)
    assert "receipt" in expanded
    assert "written response" in expanded


def test_leaves_unrelated_policy_query_unchanged() -> None:
    question = "How much notice is required for four days of PTO?"

    assert _expand_retrieval_question(question) == question
