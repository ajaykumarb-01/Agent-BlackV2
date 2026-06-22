import sys
import os
import logging
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.logging_setup import setup_service_logging, get_logger

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
setup_service_logging("research-agent", log_dir=LOG_DIR, console_level=logging.INFO)
logger = get_logger("research-agent")

from fastapi import FastAPI, Request
from shared.models import AgentRequest, AgentResponse
from shared.a2a_sdk import add_sdk_a2a_routes, agent_card_to_legacy_dict, build_agent_card
from shared.config import get_agent_urls
from tools import TASKS, build_mcp_server
from agent import run_agent

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
    base_url=get_agent_urls()["research"],
    tasks=TASKS,
)

mcp = build_mcp_server(AGENT_NAME)
mcp_app = mcp.http_app(path="/")


@asynccontextmanager
async def lifespan(app):
    agent_url = get_agent_urls()["research"]
    logger.info("Research Agent started  url=%s  tools=%d", agent_url, len(TASKS))
    async with mcp_app.lifespan(app):
        yield


app = FastAPI(title="Computer Vision Research Agent", lifespan=lifespan)

add_sdk_a2a_routes(app, card=AGENT_CARD, run_fn=run_agent)

app.mount("/mcp", mcp_app)


@app.get("/capabilities")
def capabilities():
    return CAPABILITIES


@app.get("/.well-known/agent-card")
@app.get("/.well-known/agent-card.json")
def agent_card():
    return agent_card_to_legacy_dict(AGENT_CARD)


@app.post("/research", response_model=AgentResponse)
async def research(req: AgentRequest):
    logger.info("POST /research  query=%s", req.query[:120])
    result = await run_agent(req.query)
    return AgentResponse(agent=AGENT_NAME, result=result)


@app.get("/health")
def health():
    return {"status": "ok", "agent": AGENT_NAME}
