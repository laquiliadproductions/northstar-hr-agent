"""Nodes used by the Northstar HR agent graph."""



from __future__ import annotations

from config import RETRIEVAL_TOP_K



from src.agent.models import AgentResult, TraceEvent
from src.agent.policy_safety import (
    build_sensitive_policy_question,
    build_sensitive_refusal,
    is_sensitive_data_request,
    requires_policy_escalation,
)

from src.agent.rag_adapter import execute_policy_rag

from src.agent.router import classify_intent

from src.agent.state import AgentState

from src.rag.guardrails import AnswerStatus





def route_request(state: AgentState) -> dict:

    """Classify user intent and select required capabilities."""



    route = classify_intent(state["user_message"])



    event = TraceEvent(

        step="intent_routing",

        status="completed",

        tool_output={

            "intent": route.intent.value,

            "rag_only": route.rag_only,

            "selected_tools": list(route.selected_tools),

        },

        decision_basis=route.decision_basis,

    )



    return {

        "route": route,

        "intent": route.intent,

        "selected_tools": route.selected_tools,

        "trace": [event],

    }





def clarify_request(state: AgentState) -> dict:

    """Return a clarification request without calling any tools."""



    route = state["route"]

    answer = (

        route.clarification_question

        or "Please clarify the HR question you would like answered."

    )



    event = TraceEvent(

        step="response_synthesis",

        status="blocked",

        decision_basis=(

            "Required intent or workflow details were ambiguous."

        ),

        escalation_decision="Wait for user clarification.",

    )



    trace = tuple(state.get("trace", [])) + (event,)



    result = AgentResult(

        intent=route.intent,

        answer=answer,

        trace=trace,

        answer_basis=("Intent routing required clarification.",),

    )



    return {

        "trace": [event],

        "final_result": result,

    }





def answer_policy_question(state: AgentState) -> dict:

    """Answer a request that requires only policy RAG."""



    user_message = state["user_message"]
    sensitive_request = is_sensitive_data_request(
        user_message
    )
    rag_question = (
        build_sensitive_policy_question()
        if sensitive_request
        else user_message
    )

    rag_result, rag_event = execute_policy_rag(

        rag_question,
        top_k=state.get("retrieval_top_k", RETRIEVAL_TOP_K),

    )



    if rag_result is None:

        answer = (

            "The policy service is currently unavailable. "

            "Please try again later or contact HR if the matter is urgent."

        )

        escalation_required = True

        answer_basis = (

            "Policy RAG service failure.",

        )

        synthesis_status = "failed"

        synthesis_basis = (

            "No policy answer could be produced."

        )

    elif rag_result.status == AnswerStatus.GROUNDED:

        answer = (
            build_sensitive_refusal()
            if sensitive_request
            else rag_result.answer
        )

        escalation_required = requires_policy_escalation(
            user_message
        )

        answer_basis = (

            "Verified Northstar policy citations.",

            "Policy retrieval relevance gate.",

        )

        synthesis_status = "completed"

        synthesis_basis = (

            "The final answer uses grounded policy evidence."

        )

    else:

        answer = rag_result.answer

        escalation_required = True

        answer_basis = (

            f"Policy evidence status: {rag_result.status.value}.",

        )

        synthesis_status = "blocked"

        synthesis_basis = (

            "The policy evidence was insufficient for a grounded answer."

        )



    synthesis_event = TraceEvent(

        step="response_synthesis",

        status=synthesis_status,

        decision_basis=synthesis_basis,

        escalation_decision=(

            "Contact HR for authoritative guidance."

            if escalation_required

            else None

        ),

    )



    trace = (

        tuple(state.get("trace", []))

        + (rag_event, synthesis_event)

    )



    result = AgentResult(

        intent=state["intent"],

        answer=answer,

        trace=trace,

        answer_basis=answer_basis,

        escalation_required=escalation_required,

    )



    return {

        "rag_result": rag_result,

        "trace": [rag_event, synthesis_event],

        "final_result": result,

    }
