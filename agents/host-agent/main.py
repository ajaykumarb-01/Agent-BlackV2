import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI, Request
from shared.models import AgentRequest
from shared.a2a import handle_a2a_request, create_agent_card
from orchestrator import orchestrate

app = FastAPI(title="Host Agent / Orchestrator")

AGENT_NAME = "Host Orchestrator"
TASKS = [
    "research_orchestration", "agent_selection",
    "task_decomposition", "result_aggregation",
]

@app.get("/.well-known/agent-card")
def agent_card():
    return create_agent_card(AGENT_NAME, "Orchestrates CV, NLP, and ML agents for research queries", "http://localhost:8000", TASKS).model_dump()

@app.post("/research")
async def research(req: AgentRequest):
    result = await orchestrate(req.query)
    return {"query": req.query, "report": result}

@app.post("/a2a")
async def a2a_endpoint(req: Request):
    body = await req.json()
    return await handle_a2a_request(body, AGENT_NAME, TASKS, "http://localhost:8000", lambda q: orchestrate(q))

@app.get("/health")
def health():
    return {"status": "ok", "agent": "Host Orchestrator"}

@app.get("/")
def root():
    return {
        "name": "Agent Black",
        "agents": ["Computer Vision Research Agent", "NLP Solution Agent", "ML Experiment Agent"],
        "endpoints": {
            "POST /research": "Submit a research query to all agents",
            "POST /a2a": "A2A protocol endpoint",
            "GET /.well-known/agent-card": "Agent card for A2A discovery",
            "GET /health": "Health check",
        }
    }
