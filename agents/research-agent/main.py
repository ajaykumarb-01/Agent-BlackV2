import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI, Request
from shared.models import AgentRequest, AgentResponse
from shared.mcp import handle_mcp_request, MCP_TOOLS
from shared.a2a_sdk import add_sdk_a2a_routes, agent_card_to_legacy_dict, build_agent_card
from shared.config import RESEARCH_AGENT_URL
from tools import TASKS
from agent import run_agent

app = FastAPI(title="Computer Vision Research Agent")

AGENT_NAME = "Computer Vision Research Agent"

CAPABILITIES = {
    "name": AGENT_NAME,
    "description": "Specializes in computer vision research including paper search, CV datasets, and CV model recommendations",
    "port": 8001,
    "tasks": TASKS,
}

AGENT_CARD = build_agent_card(
    name=AGENT_NAME,
    description=CAPABILITIES["description"],
    base_url=RESEARCH_AGENT_URL,
    tasks=TASKS,
)

add_sdk_a2a_routes(app, card=AGENT_CARD, run_fn=run_agent)

@app.get("/capabilities")
def capabilities():
    return CAPABILITIES

@app.get("/.well-known/agent-card")
def agent_card():
    return agent_card_to_legacy_dict(AGENT_CARD)

@app.post("/research", response_model=AgentResponse)
async def research(req: AgentRequest):
    result = await run_agent(req.query)
    return AgentResponse(agent=AGENT_NAME, result=result)

@app.post("/mcp")
async def mcp_endpoint(req: Request):
    body = await req.json()
    return handle_mcp_request(body)

@app.get("/tools")
def list_tools():
    return {"tools": MCP_TOOLS}

@app.get("/health")
def health():
    return {"status": "ok", "agent": AGENT_NAME}
