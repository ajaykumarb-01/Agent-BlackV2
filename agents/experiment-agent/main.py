import sys
import os
import logging
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.logging_setup import setup_service_logging, get_logger

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
setup_service_logging("experiment-agent", log_dir=LOG_DIR, console_level=logging.INFO)
logger = get_logger("experiment-agent")

from fastapi import FastAPI, Request
from shared.models import AgentRequest, AgentResponse
from shared.a2a_sdk import add_sdk_a2a_routes, agent_card_to_legacy_dict, build_agent_card
from shared.config import get_agent_urls
from tools import TASKS, build_mcp_server
from agent import run_agent

AGENT_NAME = "ML Experiment Agent"

CAPABILITIES = {
    "name": AGENT_NAME,
    "description": "Specializes in experiment design, metric recommendation, hyperparameter tuning, and model selection",
    "port": 8003,
    "tasks": TASKS,
}

AGENT_CARD = build_agent_card(
    name=AGENT_NAME,
    description=CAPABILITIES["description"],
    base_url=get_agent_urls()["experiment"],
    tasks=TASKS,
)

mcp = build_mcp_server(AGENT_NAME)
mcp_app = mcp.http_app(path="/")


@asynccontextmanager
async def lifespan(app):
    agent_url = get_agent_urls()["experiment"]
    logger.info("Experiment Agent started  url=%s  tools=%d", agent_url, len(TASKS))
    async with mcp_app.lifespan(app):
        yield


app = FastAPI(title="ML Experiment Agent", lifespan=lifespan)

add_sdk_a2a_routes(app, card=AGENT_CARD, run_fn=run_agent)

app.mount("/mcp", mcp_app)


@app.get("/capabilities")
def capabilities():
    return CAPABILITIES


@app.get("/.well-known/agent-card")
@app.get("/.well-known/agent-card.json")
def agent_card():
    return agent_card_to_legacy_dict(AGENT_CARD)


@app.post("/experiment", response_model=AgentResponse)
async def experiment(req: AgentRequest):
    logger.info("POST /experiment  query=%s", req.query[:120])
    result = await run_agent(req.query)
    return AgentResponse(agent=AGENT_NAME, result=result)


@app.get("/health")
def health():
    return {"status": "ok", "agent": AGENT_NAME}
