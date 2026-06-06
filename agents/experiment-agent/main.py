import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI, Request
from shared.models import AgentRequest, AgentResponse
from shared.mcp import handle_mcp_request, MCP_TOOLS
from shared.a2a import handle_a2a_request, create_agent_card
from agent import run_agent

app = FastAPI(title="ML Experiment Agent")

AGENT_NAME = "ML Experiment Agent"
TASKS = [
    "paper_search", "experiment_planning", "metric_recommendation",
    "hyperparameter_advice", "model_recommendation",
    "benchmark_search", "feature_engineering_advisor",
    "model_explainability_advisor", "time_series_strategy",
    "research_gap_analysis", "paper_summarization",
    "solution_recommendation", "prototype_guidance",
]

CAPABILITIES = {
    "name": AGENT_NAME,
    "description": "Specializes in experiment design, metric recommendation, hyperparameter tuning, and model selection",
    "port": 8003,
    "tasks": TASKS,
}

@app.get("/capabilities")
def capabilities():
    return CAPABILITIES

@app.get("/.well-known/agent-card")
def agent_card():
    return create_agent_card(AGENT_NAME, CAPABILITIES["description"], "http://localhost:8003", TASKS).model_dump()

@app.post("/experiment", response_model=AgentResponse)
async def experiment(req: AgentRequest):
    result = await run_agent(req.query)
    return AgentResponse(agent=AGENT_NAME, result=result)

@app.post("/mcp")
async def mcp_endpoint(req: Request):
    body = await req.json()
    return handle_mcp_request(body)

@app.post("/a2a")
async def a2a_endpoint(req: Request):
    body = await req.json()
    return await handle_a2a_request(body, AGENT_NAME, TASKS, "http://localhost:8003", run_agent)

@app.get("/tools")
def list_tools():
    return {"tools": MCP_TOOLS}

@app.get("/health")
def health():
    return {"status": "ok", "agent": AGENT_NAME}
