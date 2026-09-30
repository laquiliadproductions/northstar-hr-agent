"""Client adapter for calling Northstar MCP tools."""

from __future__ import annotations
import json
import sys
from typing import Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_PARAMETERS = StdioServerParameters(
    command=sys.executable,
    args=["-m", "src.mcp_server.server"],
)

def _content_text(content: list[Any]) -> str:
    """Collect textual MCP content blocks into one string."""

    parts = [
        item.text
        for item in content
        if isinstance(getattr(item, "text", None), str)
    ]
    return "\n".join(parts).strip()

async def call_hr_tool(
    tool_name: str,
    arguments: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Call one HR tool and return a controlled structured result."""

    try:
        async with stdio_client(SERVER_PARAMETERS) as streams:
            read_stream, write_stream = streams

            async with ClientSession(
                read_stream,
                write_stream,
            ) as session:
                await session.initialize()

                result = await session.call_tool(
                    tool_name,
                    arguments=arguments or {},
                )

        if result.is_error:
            return {
                "status": "tool_error",
                "tool": tool_name,
                "message": _content_text(result.content)
                or "The MCP tool returned an error.",
            }

        if result.structured_content is not None:
            return dict(result.structured_content)

        text = _content_text(result.content)

        if text:
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                return {
                    "status": "ok",
                    "tool": tool_name,
                    "content": text,
                }

            if isinstance(parsed, dict):
                return parsed

        return {
            "status": "tool_error",
            "tool": tool_name,
            "message": "The MCP tool returned no usable output.",
        }

    except Exception as exc:
        return {
            "status": "tool_unavailable",
            "tool": tool_name,
            "message": "The HR tool service is currently unavailable.",
            "error_type": type(exc).__name__,
        }
