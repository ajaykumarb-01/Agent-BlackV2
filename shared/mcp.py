from __future__ import annotations

import inspect
import logging
from typing import Any, Callable

from fastmcp import FastMCP

logger = logging.getLogger("mcp")


def _wrap_handler(handler: Callable) -> Callable:
    sig = inspect.signature(handler)
    has_var_keyword = any(
        p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
    )
    if not has_var_keyword:
        return handler

    params = [
        p.replace(kind=inspect.Parameter.POSITIONAL_OR_KEYWORD)
        for p in sig.parameters.values()
        if p.kind != inspect.Parameter.VAR_KEYWORD
    ]

    def wrapper(**kwargs):
        bound = {k: v for k, v in kwargs.items() if k in sig.parameters}
        return handler(**bound)

    wrapper.__name__ = handler.__name__
    wrapper.__doc__ = handler.__doc__
    wrapper.__annotations__ = {
        k: v for k, v in handler.__annotations__.items()
        if k in sig.parameters and sig.parameters[k].kind != inspect.Parameter.VAR_KEYWORD
    }
    wrapper.__signature__ = sig.replace(parameters=params)
    return wrapper


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
        wrapped = _wrap_handler(handler)
        wrapped.__name__ = tool_name
        wrapped.__doc__ = description or None
        mcp.add_tool(wrapped)
        logger.debug("FastMCP tool registered: %s", tool_name)

    logger.info("FastMCP server created  name=%s  tools=%d", name, len(tools))
    return mcp
