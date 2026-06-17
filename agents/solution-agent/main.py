import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.logging_setup import setup_service_logging, get_logger

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
setup_service_logging("solution-agent", log_dir=LOG_DIR, console_level=logging.INFO)
logger = get_logger("solution-agent")

from fastapi import FastAPI, Request
from shared.models import AgentRequest, AgentResponse
from shared.mcp import handle_mcp_request, MCP_TOOLS
from shared.a2a_sdk import add_sdk_a2a_routes, agent_card_to_legacy_dict, build_agent_card
from shared.config import get_agent_urls
from tools import TASKS
from agent import run_agent

app = FastAPI(title="NLP Solution Agent")

AGENT_NAME = "NLP Solution Agent"

CAPABILITIES = {
    "name": AGENT_NAME,
    "description": "Specializes in NLP solutions including dataset finding, RAG design, and LLM benchmarking",
    "port": 8002,
    "tasks": TASKS,
}

AGENT_CARD = build_agent_card(
    name=AGENT_NAME,
    description=CAPABILITIES["description"],
    base_url=get_agent_urls()["solution"],
    tasks=TASKS,
)

add_sdk_a2a_routes(app, card=AGENT_CARD, run_fn=run_agent)


@app.on_event("startup")
def on_startup():
    agent_url = get_agent_urls()["solution"]
    logger.info(
        "Solution Agent started  url=%s  tools=%d",
        agent_url,
        len(MCP_TOOLS),
    )


@app.get("/capabilities")
def capabilities():
    return CAPABILITIES


@app.get("/.well-known/agent-card")
@app.get("/.well-known/agent-card.json")
def agent_card():
    return agent_card_to_legacy_dict(AGENT_CARD)


@app.post("/solution", response_model=AgentResponse)
async def solution(req: AgentRequest):
    logger.info("POST /solution  query=%s", req.query[:120])
    result = await run_agent(req.query)
    return AgentResponse(agent=AGENT_NAME, result=result)


@app.post("/mcp")
async def mcp_endpoint(req: Request):
    body = await req.json()
    return handle_mcp_request(body, service_name="solution-agent")


@app.get("/tools")
def list_tools():
    return {"tools": MCP_TOOLS}


@app.get("/health")
def health():
    return {"status": "ok", "agent": AGENT_NAME}
