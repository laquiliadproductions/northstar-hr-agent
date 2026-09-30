"""Shared state passed through the agent workflow graph."""



from __future__ import annotations



import operator

from typing import Annotated, Any, TypedDict



from src.agent.models import AgentIntent, AgentResult, TraceEvent

from src.agent.router import RouteDecision

from src.rag.pipeline import RAGAnswer





class AgentState(TypedDict, total=False):

    """State accumulated while processing one HR request."""



    user_message: str

    work_email: str | None

    full_name: str | None

    employee_id: str | None

    start_date: str | None

    end_date: str | None

    requested_days: float | None

    confirmed: bool



    route: RouteDecision

    intent: AgentIntent

    selected_tools: tuple[str, ...]



    employee_result: dict[str, Any]

    pto_result: dict[str, Any]

    action_result: dict[str, Any]

    rag_result: RAGAnswer | None

    policy_question: str



    trace: Annotated[list[TraceEvent], operator.add]

    final_result: AgentResult
