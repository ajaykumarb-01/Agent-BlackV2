from pydantic import BaseModel
from typing import Any, Optional

class QueryRequest(BaseModel):
    query: str
    tech_stack: Optional[dict] = None

class QueryResponse(BaseModel):
    query: str
    report: dict[str, Any]
    diagram: Optional[str] = None

class SystemStatus(BaseModel):
    host_agent: str
    agents: dict[str, str]
    llm_provider: str
    uptime: float

class AgentStatus(BaseModel):
    name: str
    port: int
    status: str
    capabilities: list[str] = []

class LLMSettings(BaseModel):
    provider: str
    model: str
    api_key_set: bool
    base_url: Optional[str] = None

class SettingsUpdate(BaseModel):
    llm_provider: Optional[str] = None
    gemini_api_key: Optional[str] = None
    gemini_base_url: Optional[str] = None
    gemini_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_model: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    anthropic_base_url: Optional[str] = None
    anthropic_model: Optional[str] = None
    research_agent_url: Optional[str] = None
    solution_agent_url: Optional[str] = None
    experiment_agent_url: Optional[str] = None

class SettingsResponse(BaseModel):
    llm_provider: str
    providers: dict[str, LLMSettings]
    agent_urls: dict[str, str]

class TechStackItem(BaseModel):
    category: str
    name: str
    description: str
    version: Optional[str] = None

class TechStackResponse(BaseModel):
    recommended: list[TechStackItem]
    preferences: dict[str, Any]

class DiagramRequest(BaseModel):
    query: Optional[str] = None
    include_tech_stack: bool = True
    format: str = "mermaid"

class DiagramResponse(BaseModel):
    diagram: str
    description: str

class AgentCardResponse(BaseModel):
    card: dict
    health: str
