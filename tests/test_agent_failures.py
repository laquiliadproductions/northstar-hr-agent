"""Tests for agent clarification, failure, and safety paths."""



from __future__ import annotations



import asyncio



from src.agent.orchestrator import run_agent

from src.agent.pto_action import execute_pto_action

from src.mcp_server.client import call_hr_tool





def test_ambiguous_request_stops_for_clarification() -> None:

    result = asyncio.run(

        run_agent("Can I take PTO while working remotely?")

    )



    assert result.intent.value == "unknown"

    assert result.requires_confirmation is False

    assert [event.step for event in result.trace] == [

        "intent_routing",

        "response_synthesis",

    ]





def test_missing_employee_identifier_stops_workflow() -> None:

    result = asyncio.run(

        run_agent("What is my PTO balance?")

    )



    assert result.answer == (

        "Provide the employee's work email or exact full name."

    )

    assert result.escalation_required is False

    assert [event.step for event in result.trace] == [

        "intent_routing",

        "employee_lookup",

        "response_synthesis",

    ]





def test_unknown_mcp_tool_returns_controlled_error() -> None:

    result = asyncio.run(

        call_hr_tool("tool_that_does_not_exist")

    )



    assert result["status"] == "tool_error"

    assert result["tool"] == "tool_that_does_not_exist"





def test_pto_action_blocks_request_over_balance() -> None:

    state = {

        "requested_days": 20.0,

        "start_date": "2026-10-01",

        "end_date": "2026-10-20",

        "confirmed": True,

    }

    balance = {

        "employee_id": "NSA-0001",

        "available_after_pending_days": 16.9,

    }



    output, event = asyncio.run(

        execute_pto_action(state, balance)

    )



    assert output["status"] == "invalid_request"

    assert output["side_effects"] == "none"

    assert event.status == "blocked"

    assert event.step == "pto_action_guard"
