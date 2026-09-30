"""MCP server exposing controlled Northstar HR tools."""

from __future__ import annotations
from typing import Any
from mcp.server.mcpserver import MCPServer
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
    name="lookup_employee",
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
    name="get_pto_balance",
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
