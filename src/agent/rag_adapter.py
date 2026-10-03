"""Adapt the existing RAG pipeline for agent orchestration."""

from __future__ import annotations
from typing import Any
from src.agent.models import TraceEvent
from src.rag.citations import create_snippet
from src.rag.guardrails import AnswerStatus
from src.rag.pipeline import RAGAnswer, answer_question
from src.retrieval.retriever import RetrievalResult

def _source_summary(
    result: RetrievalResult,
) -> dict[str, Any]:
    """Create concise trace metadata for one retrieved policy chunk."""

    metadata = result.metadata

    return {
        "rank": result.rank,
        "marker": f"[Source {result.rank}]",
        "chunk_id": result.chunk_id,
        "title": str(metadata.get("title", "Unknown title")),
        "document": str(metadata.get("source", "Unknown source")),
        "section": str(metadata.get("section", "Unknown section")),
        "snippet": create_snippet(result),
        "page": metadata.get("page"),
        "row": metadata.get("row"),
        "similarity": round(result.similarity, 4),
    }

def execute_policy_rag(
    question: str,
) -> tuple[RAGAnswer | None, TraceEvent]:

    """Run policy RAG and produce an operational trace event."""

    try:
        result = answer_question(question)
    except Exception as exc:
        event = TraceEvent(
            step="policy_retrieval_and_answering",
            status="failed",
            selected_tool="policy_rag",
            tool_arguments={"question": question},
            tool_output={
                "status": "unavailable",
                "error_type": type(exc).__name__,
            },
            decision_basis=(
                "The policy RAG service could not complete the request."
            ),
            escalation_decision=(
                "Escalate if the policy answer is time-sensitive."
            ),
        )
        return None, event

    sources = tuple(
        _source_summary(source) for source in result.sources
    )

    if result.status == AnswerStatus.GROUNDED:
        event_status = "completed"
        basis = (
            "The answer is supported by verified policy citations."
        )
        escalation = None
    elif result.status == AnswerStatus.OUT_OF_CORPUS:
        event_status = "blocked"
        basis = (
            "Retrieved policy evidence did not meet the relevance gate."
        )
        escalation = (
            "Ask a narrower policy question or contact HR."
        )
    else:
        event_status = "blocked"
        basis = (
            "The generated answer contained no verified citations."
        )
        escalation = (
            "Do not rely on the answer; contact HR for clarification."
        )

    event = TraceEvent(
        step="policy_retrieval_and_answering",
        status=event_status,
        selected_tool="policy_rag",
        tool_arguments={"question": question},
        tool_output={
            "status": result.status.value,
            "best_similarity": round(result.best_similarity, 4),
            "citation_count": len(result.citations),
        },
        policy_sources=sources,
        decision_basis=basis,
        escalation_decision=escalation,
    )

    return result, event
