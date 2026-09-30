"""Deterministic tests for both multi-step HR workflows."""



from __future__ import annotations



import asyncio

from types import SimpleNamespace



from src.agent.models import AgentIntent, TraceEvent

from src.agent.pto_workflow import run_pto_workflow

from src.agent.remote_workflow import run_remote_workflow

from src.rag.guardrails import AnswerStatus





def _fake_rag(question: str):

    """Return a grounded policy result without calling an LLM."""



    result = SimpleNamespace(

        status=AnswerStatus.GROUNDED,

        answer="Grounded policy guidance [Source 1].",

    )

    event = TraceEvent(

        step="policy_retrieval_and_answering",

        status="completed",

        selected_tool="policy_rag",

        tool_arguments={"question": question},

        tool_output={

            "status": "grounded",

            "best_similarity": 0.9,

            "citation_count": 1,

        },

        policy_sources=(

            {

                "rank": 1,

                "document": "test-policy.md",

                "similarity": 0.9,

            },

        ),

        decision_basis=(

            "The answer is supported by verified policy citations."

        ),

    )

    return result, event





def test_pto_workflow_combines_mcp_and_rag(

    monkeypatch,

) -> None:

    async def fake_call(tool_name, arguments):

        if tool_name == "lookup_employee":

            return {

                "status": "ok",

                "employee": {

                    "first_name": "Maya",

                    "last_name": "Chen",

                    "work_email": (

                        "maya.chen@northstaranalytics.com"

                    ),

                    "start_date": "02/12/2018",

                    "job_title": "Chief Executive Officer",

                    "department": "Executive",

                    "employment_type": "Salary",

                    "office_location": "Seattle HQ",

                    "work_arrangement": "Hybrid",

                    "country": "United States",

                    "us_international": "US",

                    "management_level": "Executive",

                },

            }



        if tool_name == "get_pto_balance":

            return {

                "status": "ok",

                "pto_balance": {

                    "employee_id": "NSA-0001",

                    "first_name": "Maya",

                    "last_name": "Chen",

                    "current_balance_days": 16.9,

                    "available_after_pending_days": 16.9,

                    "as_of_date": "09/26/2026",

                },

            }



        raise AssertionError(f"Unexpected tool: {tool_name}")



    monkeypatch.setattr(

        "src.agent.pto_workflow.call_hr_tool",

        fake_call,

    )

    monkeypatch.setattr(

        "src.agent.pto_workflow.execute_policy_rag",

        _fake_rag,

    )



    state = {

        "intent": AgentIntent.PTO_GUIDANCE,

        "work_email": "maya.chen@northstaranalytics.com",

        "selected_tools": (

            "lookup_employee",

            "get_pto_balance",

        ),

        "trace": [],

    }



    output = asyncio.run(run_pto_workflow(state))

    result = output["final_result"]



    assert result.escalation_required is False

    assert "16.9 days available" in result.answer

    assert [event.step for event in result.trace] == [

        "employee_lookup",

        "pto_balance_lookup",

        "policy_retrieval_and_answering",

        "response_synthesis",

    ]





def test_remote_workflow_combines_mcp_and_rag(

    monkeypatch,

) -> None:

    async def fake_call(tool_name, arguments):

        assert tool_name == "lookup_employee"



        return {

            "status": "ok",

            "employee": {

                "first_name": "Maya",

                "last_name": "Chen",

                "work_email": (

                    "maya.chen@northstaranalytics.com"

                ),

                "start_date": "02/12/2018",

                "job_title": "Chief Executive Officer",

                "department": "Executive",

                "employment_type": "Salary",

                "office_location": "Seattle HQ",

                "work_arrangement": "Hybrid",

                "country": "United States",

                "us_international": "US",

                "management_level": "Executive",

            },

        }



    monkeypatch.setattr(

        "src.agent.remote_workflow.call_hr_tool",

        fake_call,

    )

    monkeypatch.setattr(

        "src.agent.remote_workflow.execute_policy_rag",

        _fake_rag,

    )



    state = {

        "intent": AgentIntent.REMOTE_WORK_ELIGIBILITY,

        "work_email": "maya.chen@northstaranalytics.com",

        "trace": [],

    }



    output = asyncio.run(run_remote_workflow(state))

    result = output["final_result"]



    assert result.escalation_required is False

    assert result.answer.startswith("Employee context:")

    assert result.answer.endswith(

        "review must still occur."

    )

    assert [event.step for event in result.trace] == [

        "employee_lookup",

        "policy_retrieval_and_answering",

        "response_synthesis",

    ]
