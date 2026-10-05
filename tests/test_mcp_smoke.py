"""Smoke tests for the Northstar MCP server and client."""

import asyncio

from src.mcp_server.client import call_hr_tool, check_mcp_health


def test_mcp_tool_discovery() -> None:
    """The MCP server should start and expose its registered tools."""

    result = asyncio.run(check_mcp_health())

    assert result["status"] == "ok"
    assert result["tool_count"] == 5


def test_mcp_simple_tool_call() -> None:
    """A tool call should return structured output through MCP."""

    result = asyncio.run(
        call_hr_tool(
            "lookup_employee_profile",
            arguments={},
        )
    )

    assert result["status"] == "needs_clarification"

    message = result["message"].lower()
    assert "work email" in message
    assert "full name" in message
