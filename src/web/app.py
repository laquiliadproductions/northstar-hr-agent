"""Flask web application for the Northstar HR agent."""

import asyncio

from flask import Flask, render_template, request

from src.agent.orchestrator import run_agent
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

    if not message:
        return {
            "error": "A non-empty message is required."
        }, 400

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
        )
    )

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

    data["trace"] = [
        {
            "step": event.step,
            "status": event.status,
            "selected_tool": event.selected_tool,
        }
        for event in result.trace
    ]

    return data

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
