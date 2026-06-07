import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import subprocess
import time
import asyncio
from fastapi import APIRouter, HTTPException
from app.models import SystemStatus
from shared.config import get_setting

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PYTHON = sys.executable
LOGS_DIR = os.path.join(ROOT, "logs")

agent_processes = {}
agent_start_time = time.time()

AGENTS = [
    {"name": "research-agent", "port": 8001, "dir": os.path.join("agents", "research-agent")},
    {"name": "solution-agent", "port": 8002, "dir": os.path.join("agents", "solution-agent")},
    {"name": "experiment-agent", "port": 8003, "dir": os.path.join("agents", "experiment-agent")},
]

router = APIRouter(tags=["control"])

_agent_status_cache: dict[int, tuple[str, float]] = {}
_CACHE_TTL = 5.0


async def _check_agent(port: int) -> str:
    now = time.time()
    cached = _agent_status_cache.get(port)
    if cached and (now - cached[1]) < _CACHE_TTL:
        return cached[0]
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            r = await client.get(f"http://localhost:{port}/health", timeout=1)
            status = "running" if r.status_code == 200 else "error"
    except Exception:
        status = "stopped"
    _agent_status_cache[port] = (status, now)
    return status


async def _check_all_agents() -> dict[str, str]:
    results = await asyncio.gather(
        *[_check_agent(a["port"]) for a in AGENTS],
        return_exceptions=True,
    )
    return {
        a["name"]: (r if isinstance(r, str) else "stopped")
        for a, r in zip(AGENTS, results)
    }


@router.get("/status", response_model=SystemStatus)
async def get_status():
    os.makedirs(LOGS_DIR, exist_ok=True)
    agents = await _check_all_agents()
    return SystemStatus(
        host_agent="running",
        agents=agents,
        llm_provider=get_setting("LLM_PROVIDER", "gemini"),
        uptime=time.time() - agent_start_time,
    )


@router.post("/agents/start")
def start_agents():
    os.makedirs(LOGS_DIR, exist_ok=True)
    started = []
    for agent in AGENTS:
        name = agent["name"]
        if name in agent_processes and agent_processes[name].poll() is None:
            started.append({"name": name, "status": "already_running"})
            continue
        log_out = open(os.path.join(LOGS_DIR, f"{name}.log"), "w")
        log_err = open(os.path.join(LOGS_DIR, f"{name}-err.log"), "w")
        proc = subprocess.Popen(
            [PYTHON, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(agent["port"])],
            cwd=os.path.join(ROOT, agent["dir"]),
            stdout=log_out,
            stderr=log_err,
        )
        agent_processes[name] = proc
        started.append({"name": name, "status": "started", "pid": proc.pid})
    time.sleep(2)
    return {"message": "Agents starting", "agents": started}


@router.post("/agents/stop")
def stop_agents():
    stopped = []
    for name, proc in list(agent_processes.items()):
        if proc.poll() is None:
            proc.terminate()
            proc.wait()
        stopped.append({"name": name, "status": "stopped"})
    agent_processes.clear()
    return {"message": "Agents stopped", "agents": stopped}


@router.get("/agents/{name}/logs")
def get_agent_logs(name: str):
    if name not in [a["name"] for a in AGENTS]:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {name}")
    log_path = os.path.join(LOGS_DIR, f"{name}.log")
    err_path = os.path.join(LOGS_DIR, f"{name}-err.log")
    stdout = ""
    stderr = ""
    if os.path.exists(log_path):
        with open(log_path) as f:
            stdout = f.read()[-5000:]
    if os.path.exists(err_path):
        with open(err_path) as f:
            stderr = f.read()[-5000:]
    return {"name": name, "stdout": stdout, "stderr": stderr}


@router.get("/agents/stats")
async def get_agent_stats():
    from app.database import get_query_count, get_avg_response_time
    agents = await _check_all_agents()
    return {
        "total_queries": get_query_count(),
        "active_agents": sum(1 for s in agents.values() if s == "running"),
        "total_agents": len(AGENTS),
        "uptime": time.time() - agent_start_time,
        "avg_response_time": get_avg_response_time(),
    }
