import json
import logging
import time
from typing import Any, Callable

logger = logging.getLogger("mcp")

MCP_TOOLS: dict[str, dict] = {}
MCP_HANDLERS: dict[str, Callable] = {}


def register_tool(name: str, description: str, input_schema: dict, handler: Callable):
    MCP_TOOLS[name] = {
        "name": name,
        "description": description,
        "inputSchema": input_schema,
    }
    MCP_HANDLERS[name] = handler
    logger.debug("MCP tool registered: %s", name)


def handle_mcp_request(body: dict, service_name: str = "unknown") -> dict:
    method = body.get("method")
    params = body.get("params", {})
    request_id = body.get("id", 1)

    if method == "tools/list":
        tool_names = list(MCP_TOOLS.keys())
        logger.info(
            "MCP tools/list  service=%s  tool_count=%d  tools=%s",
            service_name,
            len(tool_names),
            tool_names,
        )
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": list(MCP_TOOLS.values())},
        }

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        logger.info(
            "MCP tools/call  service=%s  tool=%s  args=%s",
            service_name,
            tool_name,
            json.dumps(arguments, default=str)[:300],
        )

        if tool_name not in MCP_HANDLERS:
            logger.warning(
                "MCP tool not found  service=%s  tool=%s  available=%s",
                service_name,
                tool_name,
                list(MCP_HANDLERS.keys()),
            )
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
            }

        start = time.perf_counter()
        try:
            result = MCP_HANDLERS[tool_name](**arguments)
            elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
            result_size = len(json.dumps(result, default=str))
            logger.info(
                "MCP tool OK  service=%s  tool=%s  elapsed=%sms  result_size=%dbytes",
                service_name,
                tool_name,
                elapsed_ms,
                result_size,
            )
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]},
            }
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
            logger.error(
                "MCP tool FAILED  service=%s  tool=%s  elapsed=%sms  error=%s",
                service_name,
                tool_name,
                elapsed_ms,
                e,
            )
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32000, "message": str(e)},
            }

    logger.warning("MCP unknown method  service=%s  method=%s", service_name, method)
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }
