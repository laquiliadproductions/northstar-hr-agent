"""LangGraph orchestrator for the Northstar HR agent."""



from __future__ import annotations



from langgraph.graph import END, START, StateGraph



from src.agent.models import AgentIntent, AgentResult

from src.agent.nodes import (

    answer_policy_question,

    clarify_request,

    route_request,

)

from src.agent.pto_workflow import run_pto_workflow

from src.agent.remote_workflow import run_remote_workflow

from src.agent.state import AgentState





def _select_workflow(state: AgentState) -> str:

    """Choose the next graph node from the classified intent."""



    intent = state["intent"]



    if intent == AgentIntent.PTO_GUIDANCE:

        return "pto_workflow"



    if intent == AgentIntent.REMOTE_WORK_ELIGIBILITY:

        return "remote_workflow"



    if intent == AgentIntent.POLICY_QUESTION:

        return "policy_rag"



    return "clarify"





def build_agent_graph():

    """Build and compile the Northstar agent workflow graph."""



    builder = StateGraph(AgentState)



    builder.add_node("route_request", route_request)

    builder.add_node("clarify", clarify_request)

    builder.add_node("policy_rag", answer_policy_question)

    builder.add_node("pto_workflow", run_pto_workflow)

    builder.add_node(

        "remote_workflow",

        run_remote_workflow,

    )



    builder.add_edge(START, "route_request")



    builder.add_conditional_edges(

        "route_request",

        _select_workflow,

        {

            "clarify": "clarify",

            "policy_rag": "policy_rag",

            "pto_workflow": "pto_workflow",

            "remote_workflow": "remote_workflow",

        },

    )



    builder.add_edge("clarify", END)

    builder.add_edge("policy_rag", END)

    builder.add_edge("pto_workflow", END)

    builder.add_edge("remote_workflow", END)



    return builder.compile()





agent_graph = build_agent_graph()





async def run_agent(

    user_message: str,

    *,

    work_email: str | None = None,

    full_name: str | None = None,

    employee_id: str | None = None,

    start_date: str | None = None,

    end_date: str | None = None,

    requested_days: float | None = None,

    confirmed: bool = False,

) -> AgentResult:

    """Run one user request through the agent orchestrator."""



    initial_state: AgentState = {

        "user_message": user_message,

        "work_email": work_email,

        "full_name": full_name,

        "employee_id": employee_id,

        "start_date": start_date,

        "end_date": end_date,

        "requested_days": requested_days,

        "confirmed": confirmed,

        "trace": [],

    }



    final_state = await agent_graph.ainvoke(initial_state)



    return final_state["final_result"]
