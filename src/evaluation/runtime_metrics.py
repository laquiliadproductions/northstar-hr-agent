"""Runtime metrics displayed in the chatbot Agent Trace."""

from __future__ import annotations

from typing import Any, Collection

from config import RETRIEVAL_TOP_K

from src.agent.models import AgentResult, TraceEvent


NOT_APPLICABLE = "N/A"


def _resolved_citation_ratio(
    cited_numbers: Collection[int],
    trace: tuple[TraceEvent, ...],
) -> float | str:
    """Return the fraction of answer citations found in retrieved sources."""

    available_ranks = {
        source.get("rank")
        for event in trace
        for source in event.policy_sources
        if isinstance(source.get("rank"), int)
    }

    if not cited_numbers:
        return 0.0 if available_ranks else NOT_APPLICABLE

    resolved_count = sum(
        number in available_ranks
        for number in cited_numbers
    )

    return round(
        resolved_count / len(cited_numbers),
        4,
    )


def _groundedness_score(
    cited_numbers: Collection[int],
    trace: tuple[TraceEvent, ...],
) -> float | str:
    """Return a deterministic citation-grounding check."""

    has_policy_sources = any(
        event.policy_sources
        for event in trace
    )

    if not has_policy_sources:
        return NOT_APPLICABLE

    citation_ratio = _resolved_citation_ratio(
        cited_numbers,
        trace,
    )

    if citation_ratio == NOT_APPLICABLE:
        return 0.0

    return 1.0 if citation_ratio == 1.0 else 0.0


def _workflow_completion(
    result: AgentResult,
) -> float:
    """Return one when the workflow produced an answer without failure."""

    failed = any(
        event.status.lower() in {"failed", "error"}
        for event in result.trace
    )

    return 1.0 if result.answer.strip() and not failed else 0.0


def _action_safety(
    result: AgentResult,
) -> float | str:
    """Verify that a completed mock action had explicit confirmation."""

    action_events = [
        event
        for event in result.trace
        if event.selected_tool == "mock_submit_pto_request"
    ]

    if not action_events:
        return NOT_APPLICABLE

    unsafe_completion = any(
        event.status == "completed"
        and not bool(event.tool_arguments.get("confirmed"))
        for event in action_events
    )

    return 0.0 if unsafe_completion else 1.0


def build_runtime_metrics(
    result: AgentResult,
    *,
    cited_numbers: Collection[int],
    latency_ms: float,
    retrieval_top_k: int = RETRIEVAL_TOP_K,
) -> dict[str, Any]:
    """Build metrics available without an evaluation gold record."""

    return {
        "groundedness": _groundedness_score(
            cited_numbers,
            result.trace,
        ),
        "citation_accuracy": _resolved_citation_ratio(
            cited_numbers,
            result.trace,
        ),
        "gold_answer_match": NOT_APPLICABLE,
        "tool_selection_accuracy": NOT_APPLICABLE,
        "workflow_completion": _workflow_completion(result),
        "clarification_or_escalation_accuracy": NOT_APPLICABLE,
        "action_safety": _action_safety(result),
        "latency_ms": round(latency_ms, 2),
        "run_condition": "interactive",
        "retrieval_top_k": retrieval_top_k,
        "evaluation_case_id": NOT_APPLICABLE,
    }
