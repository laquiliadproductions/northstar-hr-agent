"""Flask web application for the Northstar HR agent."""

import asyncio
from time import perf_counter

from flask import Flask, render_template, request

from config import RETRIEVAL_TOP_K

from src.agent.orchestrator import run_agent
from src.evaluation.cases import get_evaluation_case
from src.evaluation.runtime_metrics import build_runtime_metrics
from src.evaluation.scoring import build_case_metrics
from src.mcp_server.client import check_mcp_health
from src.rag.citations import extract_source_numbers

app = Flask(__name__)

@app.get("/")
def home():
    """Return the Northstar HR chat interface."""

    return render_template("index.html")

@app.get("/ready")
def ready():
    """Return lightweight application readiness status."""

    return {
        "status": "ok",
        "app": "northstar-hr-agent",
    }

@app.get("/health")
def health():
    """Return application and MCP connectivity status."""

    mcp_status = asyncio.run(check_mcp_health())

    return {
        "status": "ok",
        "app": "northstar-hr-agent",
        "mcp": mcp_status,
    }

@app.post("/chat")
def chat():
    """Accept a chat request and return the agent response."""

    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()

    try:
        retrieval_top_k = int(
            payload.get("retrieval_top_k", RETRIEVAL_TOP_K)
        )
    except (TypeError, ValueError):
        return {
            "error": "retrieval_top_k must be an integer."
        }, 400

    if not 1 <= retrieval_top_k <= 10:
        return {
            "error": (
                "retrieval_top_k must be between 1 and 10."
            )
        }, 400

    if not message:
        return {
            "error": "A non-empty message is required."
        }, 400

    evaluation_case_id = str(
        payload.get("evaluation_case_id", "")
    ).strip()
    evaluation_case = None

    if evaluation_case_id:
        try:
            evaluation_case = get_evaluation_case(
                evaluation_case_id
            )
        except KeyError as error:
            return {
                "error": error.args[0],
            }, 400

        expected_message = evaluation_case["request"]["message"]

        if message != expected_message:
            return {
                "error": (
                    "The message does not match the selected "
                    "evaluation case."
                )
            }, 400

    started_at = perf_counter()

    result = asyncio.run(
        run_agent(
            message,
            work_email=payload.get("work_email"),
            full_name=payload.get("full_name"),
            employee_id=payload.get("employee_id"),
            start_date=payload.get("start_date"),
            end_date=payload.get("end_date"),
            requested_days=payload.get("requested_days"),
            confirmed=bool(payload.get("confirmed", False)),
            retrieval_top_k=retrieval_top_k,
        )
    )

    latency_ms = (
        perf_counter() - started_at
    ) * 1000

    data = result.to_dict()

    cited_numbers = set(extract_source_numbers(result.answer))

    policy_sources = []
    for event in result.trace:
        policy_sources.extend(event.policy_sources)

    cited_sources = [
        source
        for source in policy_sources
        if source.get("rank") in cited_numbers
    ]

    data["citations"] = [
        {
            "marker": source["marker"],
            "title": source["title"],
            "document": source["document"],
            "section": source["section"],
            "page": source["page"],
            "row": source["row"],
        }
        for source in cited_sources
    ]

    data["snippets"] = [
        {
            "marker": source["marker"],
            "snippet": source["snippet"],
        }
        for source in cited_sources
    ]

    trace_data = [
        {
            "step": event.step,
            "status": event.status,
            "selected_tool": event.selected_tool,
        }
        for event in result.trace
    ]

    if evaluation_case is not None:
        metric_values = build_case_metrics(
            result,
            evaluation_case,
            cited_numbers=cited_numbers,
            latency_ms=latency_ms,
            run_condition=str(
                payload.get("run_condition", "evaluation")
            ),
            retrieval_top_k=retrieval_top_k,
        )
    else:
        metric_values = build_runtime_metrics(
            result,
            cited_numbers=cited_numbers,
            latency_ms=latency_ms,
            retrieval_top_k=retrieval_top_k,
        )

    trace_data.append(
        {
            "step": "evaluation_metrics",
            "status": "completed",
            "selected_tool": None,
            "metrics": metric_values,
        }
    )

    data["trace"] = trace_data

    return data

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
