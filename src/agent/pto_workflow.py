"""Multi-step PTO guidance workflow."""

from __future__ import annotations
import asyncio
from typing import Any
from src.agent.models import AgentResult, TraceEvent
from src.agent.rag_adapter import execute_policy_rag
from src.agent.state import AgentState
from src.agent.pto_action import execute_pto_action
from src.mcp_server.client import call_hr_tool
from src.rag.guardrails import AnswerStatus

def _tool_event(
    step: str,
    tool: str,
    arguments: dict[str, Any],
    output: dict[str, Any],
) -> TraceEvent:
    """Create an operational event for one MCP call."""

    output_status = str(output.get("status", "unknown"))

    if output_status == "ok":
        event_status = "completed"
        escalation = None
    elif output_status in {
        "needs_clarification",
        "not_found",
        "confirmation_required",
    }:
        event_status = "blocked"
        escalation = "Wait for corrected or additional user input."
    else:
        event_status = "failed"
        escalation = "Contact HR if the request is urgent."

    return TraceEvent(
        step=step,
        status=event_status,
        selected_tool=tool,
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
    """Finish a workflow that cannot safely continue."""

    synthesis_event = TraceEvent(
        step="response_synthesis",
        status="blocked",
        decision_basis=basis,
        escalation_decision=(
            "Contact HR for assistance."
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

async def run_pto_workflow(state: AgentState) -> dict:
    """Run employee, balance, and policy steps for PTO guidance."""

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
        _tool_event(
            step="employee_lookup",
            tool="lookup_employee_profile",
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

    balance_arguments = {
        "work_email": employee["work_email"],
    }

    pto_result = await call_hr_tool(
        "check_pto_balance",
        balance_arguments,
    )

    events.append(
        _tool_event(
            step="pto_balance_lookup",
            tool="check_pto_balance",
            arguments=balance_arguments,
            output=pto_result,
        )
    )

    if pto_result.get("status") != "ok":
        status = str(pto_result.get("status", "unknown"))
        blocked = _blocked_result(
            state=state,
            events=events,
            message=str(
                pto_result.get(
                    "message",
                    "The PTO balance could not be retrieved.",
                )
            ),
            basis="PTO balance retrieval did not complete.",
            escalation_required=status in {
                "unavailable",
                "tool_error",
                "tool_unavailable",
            },
        )
        blocked["employee_result"] = employee_result
        blocked["pto_result"] = pto_result
        return blocked

    balance = pto_result["pto_balance"]

    policy_question = (
        "Using Northstar Analytics policies, explain the PTO rules "
        "that apply to this employee. Address eligibility, accrual, "
        "request and approval requirements, notice expectations, and "
        "balance limits. "
        f"The employee has {balance['available_after_pending_days']} "
        f"days available after pending requests as of "
        f"{balance['as_of_date']}."
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
                "Please contact HR if guidance is needed urgently."
            )
        )
        blocked = _blocked_result(
            state=state,
            events=events,
            message=message,
            basis="Grounded PTO policy evidence was unavailable.",
            escalation_required=True,
        )
        blocked["employee_result"] = employee_result
        blocked["pto_result"] = pto_result
        blocked["rag_result"] = rag_result
        blocked["policy_question"] = policy_question
        return blocked

    action_result: dict[str, Any] | None = None



    if "mock_submit_pto_request" in state.get(

        "selected_tools",

        (),

    ):

        action_result, action_event = await execute_pto_action(

            state,

            balance,

        )

        events.append(action_event)

    balance_summary = (
        f"{balance['first_name']} {balance['last_name']} has "
        f"{balance['current_balance_days']} current PTO days and "
        f"{balance['available_after_pending_days']} days available "
        f"after pending requests, as of {balance['as_of_date']}."
    )

    answer_parts = [
        balance_summary,
        rag_result.answer,
    ]

    requires_confirmation = False
    escalation_required = False
    synthesis_status = "completed"
    synthesis_basis = (
        "The response combines verified employee data, PTO balance "
        "data, and grounded policy citations."
    )
    escalation_decision = None

    if action_result is not None:
        action_status = str(
            action_result.get("status", "unknown")
        )
        action_message = str(
            action_result.get(
                "message",
                "The mock PTO action did not return a message.",
            )
        )
        answer_parts.append(action_message)

        if action_status == "confirmation_required":
            requires_confirmation = True
            synthesis_status = "blocked"
            synthesis_basis = (
                "The workflow stopped at the explicit confirmation "
                "gate before the mock action."
            )
            escalation_decision = (
                "Wait for explicit user confirmation."
            )
        elif action_status == "mock_completed":
            mock_id = action_result.get("mock_request_id")
            if mock_id:
                answer_parts.append(
                    f"Mock request reference: {mock_id}"
                )
            synthesis_basis = (
                "The explicitly confirmed action completed only as "
                "a mock; no HR record changed."
            )
        elif action_status in {
            "needs_clarification",
            "invalid_request",
        }:
            synthesis_status = "blocked"
            synthesis_basis = (
                "The mock action requires corrected or additional "
                "request details."
            )
            escalation_required = (
                action_status == "invalid_request"
                and "available after pending" in action_message
            )
            escalation_decision = (
                "Contact HR to discuss other leave options."
                if escalation_required
                else "Wait for corrected or additional user input."
            )
        else:
            synthesis_status = "failed"
            synthesis_basis = (
                "The mock action tool did not complete."
            )
            escalation_required = True
            escalation_decision = (
                "Contact HR if the request is urgent."
            )

    answer = "\n\n".join(answer_parts)

    synthesis_event = TraceEvent(
        step="response_synthesis",
        status=synthesis_status,
        decision_basis=synthesis_basis,
        escalation_decision=escalation_decision,
    )
    events.append(synthesis_event)

    final_trace = (
        tuple(state.get("trace", []))
        + tuple(events)
    )

    answer_basis = [
        "Employee lookup through MCP.",
        "PTO balance lookup through MCP.",
        "Verified Northstar PTO policy citations.",
    ]

    if action_result is not None:
        answer_basis.append(
            "Confirmation-gated mock PTO action."
        )

    result = AgentResult(
        intent=state["intent"],
        answer=answer,
        trace=final_trace,
        answer_basis=tuple(answer_basis),
        requires_confirmation=requires_confirmation,
        escalation_required=escalation_required,
    )

    output = {
        "employee_result": employee_result,
        "pto_result": pto_result,
        "rag_result": rag_result,
        "policy_question": policy_question,
        "trace": events,
        "final_result": result,
    }

    if action_result is not None:
        output["action_result"] = action_result

    return output
