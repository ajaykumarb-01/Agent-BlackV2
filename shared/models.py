from pydantic import BaseModel
from typing import Any


class AgentRequest(BaseModel):
    query: str
    context: dict = {}


class AgentResponse(BaseModel):
    agent: str
    result: dict[str, Any]
    status: str = "success"

