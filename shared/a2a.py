from pydantic import BaseModel
from typing import Any, Optional
import inspect


class AgentCard(BaseModel):
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    capabilities: list[str] = []
    authentication: Optional[dict] = None
    defaultInputModes: list[str] = ["text"]
    defaultOutputModes: list[str] = ["text"]
    skills: list[dict] = []


class A2ARequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: dict = {}
    id: str = "1"


class A2AResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[dict] = None
    id: str = "1"


def create_agent_card(name: str, description: str, url: str, tasks: list[str]) -> AgentCard:
    return AgentCard(
        name=name,
        description=description,
        url=url,
        capabilities=tasks,
        skills=[{"id": t, "name": t.replace("_", " ").title(), "description": f"Performs {t.replace('_', ' ')}"} for t in tasks],
    )


async def handle_a2a_request(body: dict, agent_name: str, tasks: list[str], agent_url: str, run_fn) -> dict:
    method = body.get("method", "")
    req_id = body.get("id", "1")

    if method == "a2a/agent-card":
        descriptions = {
            "Computer Vision Research Agent": "Specializes in computer vision research including paper search, CV datasets, and CV model recommendations",
            "NLP Solution Agent": "Specializes in NLP solutions including dataset finding, RAG design, and LLM benchmarking",
            "ML Experiment Agent": "Specializes in experiment design, metric recommendation, hyperparameter tuning, and model selection",
        }
        desc = descriptions.get(agent_name, f"Research agent: {agent_name}")
        card = create_agent_card(agent_name, desc, agent_url, tasks)
        return {"jsonrpc": "2.0", "result": card.model_dump(), "id": req_id}

    if method == "a2a/sendTask":
        task_params = body.get("params", {})
        query = task_params.get("query", task_params.get("message", ""))
        # Support both sync and async run_fn
        if inspect.iscoroutinefunction(run_fn):
            result = await run_fn(query)
        else:
            result = run_fn(query)
        return {
            "jsonrpc": "2.0",
            "result": {
                "id": req_id,
                "status": {"state": "completed"},
                "artifacts": [{"parts": [{"text": str(result)}]}],
            },
            "id": req_id,
        }

    return {"jsonrpc": "2.0", "error": {"code": -32601, "message": f"Method not found: {method}"}, "id": req_id}
