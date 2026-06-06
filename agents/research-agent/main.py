import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI, Request
from shared.models import AgentRequest, AgentResponse
from shared.mcp import handle_mcp_request, MCP_TOOLS
from shared.a2a import handle_a2a_request, create_agent_card
from agent import run_agent

app = FastAPI(title="Computer Vision Research Agent")

AGENT_NAME = "Computer Vision Research Agent"
TASKS = [
    "paper_search", "paper_summarization", "research_gap_analysis",
    "cv_dataset_recommendation", "cv_model_recommendation",
    "citation_generation", "benchmark_search", "eval_metric_advisor",
    "architecture_comparison", "synthetic_data_strategy",
    "solution_recommendation", "prototype_guidance", "experiment_planning",
]

CAPABILITIES = {
    "name": AGENT_NAME,
    "description": "Specializes in computer vision research including paper search, CV datasets, and CV model recommendations",
    "port": 8001,
    "tasks": TASKS,
}

@app.get("/capabilities")
def capabilities():
    return CAPABILITIES

@app.get("/.well-known/agent-card")
def agent_card():
    return create_agent_card(AGENT_NAME, CAPABILITIES["description"], "http://localhost:8001", TASKS).model_dump()

@app.post("/research", response_model=AgentResponse)
async def research(req: AgentRequest):
    result = await run_agent(req.query)
    return AgentResponse(agent=AGENT_NAME, result=result)

@app.post("/mcp")
async def mcp_endpoint(req: Request):
    body = await req.json()
    return handle_mcp_request(body)

@app.post("/a2a")
async def a2a_endpoint(req: Request):
    body = await req.json()
    return await handle_a2a_request(body, AGENT_NAME, TASKS, "http://localhost:8001", run_agent)

@app.get("/tools")
def list_tools():
    return {"tools": MCP_TOOLS}

@app.get("/health")
def health():
    return {"status": "ok", "agent": AGENT_NAME}
