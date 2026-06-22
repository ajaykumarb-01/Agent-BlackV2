from __future__ import annotations

import logging
from typing import Any, Callable

from fastmcp import FastMCP

logger = logging.getLogger("mcp")


def create_mcp_server(
    name: str,
    tools: dict[str, Callable],
    tool_schemas: dict[str, dict[str, Any]],
) -> FastMCP:
    """Create a FastMCP server with the given tools registered.

    Parameters
    ----------
    name:
        Human-readable server name shown to MCP clients.
    tools:
        ``{tool_name: handler_function}`` mapping.
    tool_schemas:
        ``{tool_name: schema_dict}`` mapping where each value must contain
        a ``"description"`` key.
    """
    mcp = FastMCP(name)

    for tool_name, handler in tools.items():
        description = tool_schemas.get(tool_name, {}).get("description", "")
        mcp.add_tool(handler, name=tool_name, description=description)
        logger.debug("FastMCP tool registered: %s", tool_name)

    logger.info("FastMCP server created  name=%s  tools=%d", name, len(tools))
    return mcp
