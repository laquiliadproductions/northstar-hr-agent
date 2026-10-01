"""MCP server exposing controlled Northstar HR tools."""

from __future__ import annotations
from typing import Any
from mcp.server.mcpserver import MCPServer
from src.retrieval.retriever import retrieve
from src.tools.hr_data import lookup_employee as lookup_employee_data
from src.tools.mock_actions import (
    mock_submit_pto_request as mock_submit_pto_request_action,
)

from src.tools.pto_data import get_pto_balance as get_pto_balance_data

server = MCPServer(
    name="northstar-hr-tools",
    title="Northstar Analytics HR Tools",
    description=(
        "Read-only employee and PTO tools plus confirmation-gated "
        "mock HR actions."
    ),

    instructions=(
        "Use employee data only for supported HR workflows. "
        "Never claim that a mock action changed an HR record."
    ),

    version="1.0.0",
)

@server.tool(
    name="search_policy_documents",
    description=(
        "Search Northstar Analytics policy documents for relevant "
        "evidence. Returns ranked policy chunks with source metadata "
        "and similarity scores."
    ),

    structured_output=True,
)

def search_policy_documents_tool(
    query: str,
    top_k: int = 5,
) -> dict[str, Any]:
    """Search the Northstar policy vector index."""

    normalized_query = query.strip()

    if not normalized_query:
        return {
            "status": "needs_clarification",
            "message": "Provide a policy question or search query.",
        }

    if top_k < 1 or top_k > 10:
        return {
            "status": "invalid_request",
            "message": "top_k must be between 1 and 10.",
        }

    try:
        results = retrieve(
            query=normalized_query,
            top_k=top_k,
        )

    except Exception as exc:
        return {
            "status": "unavailable",
            "message": "Policy search is currently unavailable.",
            "error_type": type(exc).__name__,
        }

    matches = [
        {
            "rank": result.rank,
            "chunk_id": result.chunk_id,
            "text": result.text,
            "title": result.metadata.get("title"),
            "source": result.metadata.get("source"),
            "section": result.metadata.get("section"),
            "page": result.metadata.get("page"),
            "row": result.metadata.get("row"),
            "similarity": round(result.similarity, 4),
        }

        for result in results
    ]

    return {
        "status": "ok",
        "query": normalized_query,
        "match_count": len(matches),
        "matches": matches,
    }

@server.tool(
    name="get_policy_section",
    description=(
        "Retrieve evidence from a specific Northstar Analytics policy "
        "section. Optionally narrow the lookup to a policy title."
    ),

    structured_output=True,
)

def get_policy_section_tool(
    section: str,
    policy_title: str | None = None,
    top_k: int = 5,
) -> dict[str, Any]:

    """Retrieve policy evidence filtered by section metadata."""

    normalized_section = section.strip()

    if not normalized_section:
        return {
            "status": "needs_clarification",
            "message": "Provide a policy section name.",
        }

    if top_k < 1 or top_k > 10:
        return {
            "status": "invalid_request",
            "message": "top_k must be between 1 and 10.",
        }

    where: dict[str, Any] = {
        "section": normalized_section,
    }

    normalized_title = (policy_title or "").strip()

    if normalized_title:
        where = {
            "$and": [
                {"section": normalized_section},
                {"title": normalized_title},
            ]
        }

    try:
        results = retrieve(
            query=normalized_section,
            top_k=top_k,
            where=where,
        )

    except Exception as exc:
        return {
            "status": "unavailable",
            "message": "Policy section retrieval is currently unavailable.",
            "error_type": type(exc).__name__,
        }

    if not results:
        return {
            "status": "not_found",
            "message": (
                f"No policy evidence matched section "
                f"{normalized_section!r}."
            ),
        }

    matches = [
        {
            "rank": result.rank,
            "chunk_id": result.chunk_id,
            "text": result.text,
            "title": result.metadata.get("title"),
            "source": result.metadata.get("source"),
            "section": result.metadata.get("section"),
            "page": result.metadata.get("page"),
            "row": result.metadata.get("row"),
            "similarity": round(result.similarity, 4),
        }
        for result in results
    ]

    return {
        "status": "ok",
        "section": normalized_section,
        "policy_title": normalized_title or None,
        "match_count": len(matches),
        "matches": matches,
    }

@server.tool(
    name="lookup_employee_profile",
    description=(
        "Find one employee by work email or exact full name. "
        "Returns only workflow-relevant employee fields."
    ),

    structured_output=True,
)

def lookup_employee_tool(
    work_email: str | None = None,
    full_name: str | None = None,
) -> dict[str, Any]:
    """Look up a Northstar employee."""

    return lookup_employee_data(
        work_email=work_email,
        full_name=full_name,
    )

@server.tool(
    name="check_pto_balance",
    description=(
        "Get one employee's PTO balance by employee ID or work email."
    ),

    structured_output=True,
)

def get_pto_balance_tool(
    employee_id: str | None = None,
    work_email: str | None = None,
) -> dict[str, Any]:
    """Get a Northstar employee's PTO balance."""

    return get_pto_balance_data(
        employee_id=employee_id,
        work_email=work_email,
    )

@server.tool(
    name="mock_submit_pto_request",
    description=(
        "Preview or simulate a PTO request. Explicit confirmation is "
        "required, and no real HR record is ever changed."
    ),

    structured_output=True,
)

def mock_submit_pto_request_tool(
    employee_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    requested_days: float | None = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Preview or simulate a PTO request."""

    return mock_submit_pto_request_action(
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        requested_days=requested_days,
        confirmed=confirmed,
    )

if __name__ == "__main__":
    server.run(transport="stdio")
