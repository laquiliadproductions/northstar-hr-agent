"""Safety gate for mock PTO actions."""



from __future__ import annotations



from typing import Any



from src.agent.models import TraceEvent

from src.agent.state import AgentState

from src.mcp_server.client import call_hr_tool





async def execute_pto_action(

    state: AgentState,

    balance: dict[str, Any],

) -> tuple[dict[str, Any], TraceEvent]:

    """Validate balance and call the confirmation-gated mock tool."""



    arguments = {

        "employee_id": balance["employee_id"],

        "start_date": state.get("start_date"),

        "end_date": state.get("end_date"),

        "requested_days": state.get("requested_days"),

        "confirmed": state.get("confirmed", False),

    }



    requested_days = state.get("requested_days")

    available_days = float(

        balance["available_after_pending_days"]

    )



    if (

        requested_days is not None

        and float(requested_days) > available_days

    ):

        output = {

            "status": "invalid_request",

            "message": (

                f"The request is for {requested_days} days, but only "

                f"{available_days} days are available after pending "

                "requests. No mock submission was performed."

            ),

            "side_effects": "none",

        }



        event = TraceEvent(

            step="pto_action_guard",

            status="blocked",

            selected_tool="mock_submit_pto_request",

            tool_arguments=arguments,

            tool_output=output,

            decision_basis=(

                "Requested days exceed the available PTO balance."

            ),

            escalation_decision=(

                "Contact HR to discuss other leave options."

            ),

        )

        return output, event



    output = await call_hr_tool(

        "mock_submit_pto_request",

        arguments,

    )



    output_status = str(output.get("status", "unknown"))



    if output_status == "mock_completed":

        event_status = "completed"

        basis = (

            "The user explicitly confirmed the mock action."

        )

        escalation = None

    elif output_status == "confirmation_required":

        event_status = "blocked"

        basis = (

            "The action stopped at the explicit confirmation gate."

        )

        escalation = "Wait for explicit user confirmation."

    elif output_status in {

        "needs_clarification",

        "invalid_request",

    }:

        event_status = "blocked"

        basis = (

            "The action requires corrected or additional inputs."

        )

        escalation = "Wait for corrected or additional user input."

    else:

        event_status = "failed"

        basis = "The MCP action tool did not complete."

        escalation = "Contact HR if the request is urgent."



    event = TraceEvent(

        step="mock_pto_submission",

        status=event_status,

        selected_tool="mock_submit_pto_request",

        tool_arguments=arguments,

        tool_output=output,

        decision_basis=basis,

        escalation_decision=escalation,

    )



    return output, event
