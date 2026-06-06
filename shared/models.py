from pydantic import BaseModel
from typing import Any


class AgentRequest(BaseModel):
    query: str
    context: dict = {}


class AgentResponse(BaseModel):
    agent: str
    result: dict[str, Any]
    status: str = "success"


class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: dict = {}
    id: int = 1


class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Any = None
    error: dict = None
    id: int = 0
