from typing import Any, Callable
import json

MCP_TOOLS: dict[str, dict] = {}
MCP_HANDLERS: dict[str, Callable] = {}


def register_tool(name: str, description: str, input_schema: dict, handler: Callable):
    MCP_TOOLS[name] = {
        "name": name,
        "description": description,
        "inputSchema": input_schema,
    }
    MCP_HANDLERS[name] = handler


def handle_mcp_request(body: dict) -> dict:
    method = body.get("method")
    params = body.get("params", {})
    request_id = body.get("id", 1)

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": list(MCP_TOOLS.values())},
        }

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        if tool_name not in MCP_HANDLERS:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
            }
        try:
            result = MCP_HANDLERS[tool_name](**arguments)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]},
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32000, "message": str(e)},
            }

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }
