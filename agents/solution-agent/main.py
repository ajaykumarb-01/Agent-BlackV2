import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI, Request
from shared.models import AgentRequest, AgentResponse
from shared.mcp import handle_mcp_request, MCP_TOOLS
from shared.a2a import handle_a2a_request, create_agent_card
from agent import run_agent

app = FastAPI(title="NLP Solution Agent")

AGENT_NAME = "NLP Solution Agent"
TASKS = [
    "paper_search", "paper_summarization", "nlp_dataset_recommendation",
    "rag_architecture_design", "llm_benchmarking",
    "citation_generation", "prompt_optimization", "information_extraction",
    "eval_metric_advisor", "research_gap_analysis",
    "solution_recommendation", "prototype_guidance", "experiment_planning",
]

CAPABILITIES = {
    "name": AGENT_NAME,
    "description": "Specializes in NLP solutions including dataset finding, RAG design, and LLM benchmarking",
    "port": 8002,
    "tasks": TASKS,
}

@app.get("/capabilities")
def capabilities():
    return CAPABILITIES

@app.get("/.well-known/agent-card")
def agent_card():
    return create_agent_card(AGENT_NAME, CAPABILITIES["description"], "http://localhost:8002", TASKS).model_dump()

@app.post("/solution", response_model=AgentResponse)
async def solution(req: AgentRequest):
    result = await run_agent(req.query)
    return AgentResponse(agent=AGENT_NAME, result=result)

@app.post("/mcp")
async def mcp_endpoint(req: Request):
    body = await req.json()
    return handle_mcp_request(body)

@app.post("/a2a")
async def a2a_endpoint(req: Request):
    body = await req.json()
    return await handle_a2a_request(body, AGENT_NAME, TASKS, "http://localhost:8002", run_agent)

@app.get("/tools")
def list_tools():
    return {"tools": MCP_TOOLS}

@app.get("/health")
def health():
    return {"status": "ok", "agent": AGENT_NAME}
