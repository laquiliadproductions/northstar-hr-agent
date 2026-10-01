"""Multi-step remote-work eligibility workflow."""

from __future__ import annotations
import asyncio
from typing import Any
from src.agent.models import AgentResult, TraceEvent
from src.agent.rag_adapter import execute_policy_rag
from src.agent.state import AgentState
from src.mcp_server.client import call_hr_tool
from src.rag.guardrails import AnswerStatus

def _employee_tool_event(
    arguments: dict[str, Any],
    output: dict[str, Any],
) -> TraceEvent:
    """Create the employee-lookup operational event."""

    output_status = str(output.get("status", "unknown"))

    if output_status == "ok":
        event_status = "completed"
        escalation = None
    elif output_status in {"needs_clarification", "not_found"}:
        event_status = "blocked"
        escalation = "Wait for corrected or additional user input."
    else:
        event_status = "failed"
        escalation = "Contact HR if the request is urgent."

    return TraceEvent(
        step="employee_lookup",
        status=event_status,
        selected_tool="lookup_employee_profile",
        tool_arguments=arguments,
        tool_output=output,
        decision_basis=f"The MCP tool returned {output_status}.",
        escalation_decision=escalation,
    )

def _blocked_result(
    state: AgentState,
    events: list[TraceEvent],
    message: str,
    basis: str,
    escalation_required: bool,
) -> dict:
    """Finish a remote-work workflow that cannot continue."""

    synthesis_event = TraceEvent(
        step="response_synthesis",
        status="blocked",
        decision_basis=basis,
        escalation_decision=(
            "Contact HR for authoritative guidance."
            if escalation_required
            else "Wait for additional user information."
        ),
    )

    final_trace = (
        tuple(state.get("trace", []))
        + tuple(events)
        + (synthesis_event,)
    )

    result = AgentResult(
        intent=state["intent"],
        answer=message,
        trace=final_trace,
        answer_basis=(basis,),
        escalation_required=escalation_required,
    )

    return {
        "trace": events + [synthesis_event],
        "final_result": result,
    }

async def run_remote_workflow(state: AgentState) -> dict:
    """Evaluate remote-work guidance using employee and policy data."""

    events: list[TraceEvent] = []

    employee_arguments = {
        key: value
        for key, value in {
            "work_email": state.get("work_email"),
            "full_name": state.get("full_name"),
        }.items()
        if value
    }

    employee_result = await call_hr_tool(
        "lookup_employee_profile",
        employee_arguments,
    )

    events.append(
        _employee_tool_event(
            arguments=employee_arguments,
            output=employee_result,
        )
    )

    if employee_result.get("status") != "ok":
        status = str(employee_result.get("status", "unknown"))
        blocked = _blocked_result(
            state=state,
            events=events,
            message=str(
                employee_result.get(
                    "message",
                    "The employee could not be identified.",
                )
            ),
            basis="Employee identification did not complete.",
            escalation_required=status in {
                "unavailable",
                "tool_error",
                "tool_unavailable",
            },
        )
        blocked["employee_result"] = employee_result
        return blocked

    employee = employee_result["employee"]

    policy_question = (
        "Using Northstar Analytics remote, hybrid, information "
        "security, and international remote-work policies, provide "
        "preliminary eligibility guidance for this employee. "
        f"Job title: {employee['job_title']}. "
        f"Department: {employee['department']}. "
        f"Current work arrangement: "
        f"{employee['work_arrangement']}. "
        f"Office location: {employee['office_location']}. "
        f"Country: {employee['country']}. "
        f"US or international: {employee['us_international']}. "
        "Explain approval requirements, location restrictions, "
        "security obligations, and when HR escalation is required. "
        "Do not present the guidance as final approval."
    )

    rag_result, rag_event = await asyncio.to_thread(
        execute_policy_rag,
        policy_question,
    )
    events.append(rag_event)

    if (
        rag_result is None
        or rag_result.status != AnswerStatus.GROUNDED
    ):
        message = (
            rag_result.answer
            if rag_result is not None
            else (
                "The policy service is currently unavailable. "
                "Please contact HR for remote-work guidance."
            )
        )
        blocked = _blocked_result(
            state=state,
            events=events,
            message=message,
            basis=(
                "Grounded remote-work policy evidence was unavailable."
            ),
            escalation_required=True,
        )
        blocked["employee_result"] = employee_result
        blocked["rag_result"] = rag_result
        blocked["policy_question"] = policy_question
        return blocked

    employee_summary = (
        f"Employee context: {employee['first_name']} "
        f"{employee['last_name']} is a {employee['job_title']} in "
        f"{employee['department']}, currently classified as "
        f"{employee['work_arrangement']} and based in "
        f"{employee['country']}."
    )

    answer = (
        f"{employee_summary}\n\n"
        f"{rag_result.answer}\n\n"
        "This is preliminary policy guidance, not approval. "
        "Any required manager, People Operations, Security, Tax, "
        "Legal, or Compliance review must still occur."
    )

    synthesis_event = TraceEvent(
        step="response_synthesis",
        status="completed",
        decision_basis=(
            "The response combines verified employee context with "
            "grounded remote-work policy citations."
        ),

        escalation_decision=(
            "Escalate when policy requires review or facts are incomplete."
        ),
    )
    events.append(synthesis_event)

    final_trace = (
        tuple(state.get("trace", []))
        + tuple(events)
    )

    result = AgentResult(
        intent=state["intent"],
        answer=answer,
        trace=final_trace,
        answer_basis=(
            "Employee lookup through MCP.",
            "Verified remote-work policy citations.",
            "Preliminary guidance only; no approval action occurred.",
        ),
    )

    return {
        "employee_result": employee_result,
        "rag_result": rag_result,
        "policy_question": policy_question,
        "trace": events,
        "final_result": result,
    }
