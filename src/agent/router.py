"""Deterministic intent routing for the Northstar HR agent."""

from __future__ import annotations
from dataclasses import dataclass
from src.agent.models import AgentIntent

PTO_TERMS = (
    "pto",
    "paid time off",
    "vacation",
    "vacation balance",
)

PTO_ACTION_TERMS = (
    "request",
    "submit",
    "book",
    "schedule",
    "take time off",
)

PTO_EMPLOYEE_TERMS = (
    "my pto",
    "my paid time off",
    "my vacation",
    "pto balance",
    "vacation balance",
    "available pto",
    "remaining pto",
    "how much pto do i have",
    "do i have enough pto",
    "how much pto can i use",
    "pto available",
    "any pto",
    "days off",
)

REMOTE_WORK_TERMS = (
    "remote work",
    "work remotely",
    "work from home",
    "hybrid work",
    "remote eligibility",
    "working remotely",
)

@dataclass(frozen=True)

class RouteDecision:
    """A concise, observable routing decision."""

    intent: AgentIntent
    rag_only: bool
    selected_tools: tuple[str, ...]
    decision_basis: str
    clarification_question: str | None = None

def classify_intent(user_message: str) -> RouteDecision:
    """Classify a request and identify the required capabilities."""

    normalized = " ".join(user_message.casefold().split())

    if not normalized:
        return RouteDecision(
            intent=AgentIntent.UNKNOWN,
            rag_only=False,
            selected_tools=(),
            decision_basis="The request contained no usable text.",
            clarification_question="What HR question can I help with?",
        )

    has_pto_terms = any(term in normalized for term in PTO_TERMS)
    has_remote_terms = any(
        term in normalized for term in REMOTE_WORK_TERMS
    )

    if has_pto_terms and has_remote_terms:
        return RouteDecision(
            intent=AgentIntent.UNKNOWN,
            rag_only=False,
            selected_tools=(),
            decision_basis=(
                "The request combines PTO and remote-work topics."
            ),
            clarification_question=(
                "Should we handle the PTO request or remote-work "
                "eligibility first?"
            ),
        )

    has_pto_action = any(
        term in normalized
        for term in PTO_ACTION_TERMS
    )
    has_pto_employee_context = any(
        term in normalized
        for term in PTO_EMPLOYEE_TERMS
    )

    if has_pto_terms and (
        has_pto_action
        or has_pto_employee_context
    ):
        selected_tools = [
            "lookup_employee_profile",
            "check_pto_balance",
        ]

        if has_pto_action:
            selected_tools.append("mock_submit_pto_request")

        return RouteDecision(
            intent=AgentIntent.PTO_GUIDANCE,
            rag_only=False,
            selected_tools=tuple(selected_tools),
            decision_basis=(
                "The employee-specific PTO request requires "
                "employee data, balance data, and policy evidence."
            ),
        )

    if has_pto_terms:
        return RouteDecision(
            intent=AgentIntent.POLICY_QUESTION,
            rag_only=True,
            selected_tools=(),
            decision_basis=(
                "The request asks about PTO policy without "
                "requiring employee-specific data or an action."
            ),
        )

    if has_remote_terms:
        return RouteDecision(
            intent=AgentIntent.REMOTE_WORK_ELIGIBILITY,
            rag_only=False,
            selected_tools=("lookup_employee_profile",),
            decision_basis=(
                "Remote-work eligibility requires employee context "
                "and policy evidence."
            ),
        )

    return RouteDecision(
        intent=AgentIntent.POLICY_QUESTION,
        rag_only=True,
        selected_tools=(),
        decision_basis=(
            "No supported employee-specific workflow was detected; "
            "policy RAG is sufficient."
        ),
    )
