import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import APIRouter, HTTPException
import httpx
from app.models import AgentCardResponse
from shared.config import AGENT_URLS
from app.database import save_agent_discovery, get_agent_discovery

router = APIRouter(tags=["discovery"])

AGENT_NAMES = {
    "research": "Computer Vision Research Agent",
    "solution": "NLP Solution Agent",
    "experiment": "ML Experiment Agent",
}

AGENT_META = {
    "research": {"name": "Research Agent", "port": 8001, "url": AGENT_URLS.get("research", "http://localhost:8001")},
    "solution": {"name": "Solution Agent", "port": 8002, "url": AGENT_URLS.get("solution", "http://localhost:8002")},
    "experiment": {"name": "Experiment Agent", "port": 8003, "url": AGENT_URLS.get("experiment", "http://localhost:8003")},
}


@router.get("/agents/discover")
async def discover_agents():
    results = {}
    for key, url in AGENT_URLS.items():
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{url}/capabilities")
                if r.status_code == 200:
                    data = r.json()
                    results[key] = data
                    save_agent_discovery(key, url, data.get("port", 0), data.get("tasks", []), "running")
                else:
                    results[key] = {"error": f"HTTP {r.status_code}"}
        except Exception as e:
            results[key] = {"error": str(e)}
    return {"agents": results}


@router.get("/agents/{agent_name}/card", response_model=AgentCardResponse)
async def get_agent_card(agent_name: str):
    if agent_name not in AGENT_URLS:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_name}")
    url = AGENT_URLS[agent_name]
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{url}/.well-known/agent-card")
            r2 = await client.get(f"{url}/health")
            return AgentCardResponse(
                card=r.json() if r.status_code == 200 else {"error": f"HTTP {r.status_code}"},
                health=r2.json().get("status", "unknown") if r2.status_code == 200 else "stopped",
            )
    except Exception as e:
        return AgentCardResponse(card={"error": str(e)}, health="stopped")


@router.get("/agents/discovered")
def get_discovered_agents():
    from app.database import get_agent_discovery
    discovered = get_agent_discovery()
    if discovered:
        return {"agents": discovered}
    return {"agents": [
        {"name": "research-agent", "port": 8001, "url": AGENT_URLS.get("research", "http://localhost:8001")},
        {"name": "solution-agent", "port": 8002, "url": AGENT_URLS.get("solution", "http://localhost:8002")},
        {"name": "experiment-agent", "port": 8003, "url": AGENT_URLS.get("experiment", "http://localhost:8003")},
    ]}
