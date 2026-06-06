import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from shared.config import set_setting

router = APIRouter(tags=["setup"])


class SetupConfig(BaseModel):
    llm_provider: str = "gemini"
    api_key: str = ""
    model: str = ""
    base_url: Optional[str] = ""
    research_agent_url: Optional[str] = "http://localhost:8001"
    solution_agent_url: Optional[str] = "http://localhost:8002"
    experiment_agent_url: Optional[str] = "http://localhost:8003"


@router.get("/setup/status")
def get_setup_status():
    from app.database import is_setup_complete, get_setup_progress
    return {
        "complete": is_setup_complete(),
        "steps": get_setup_progress(),
    }


@router.post("/setup/step")
def complete_step(data: dict):
    from app.database import complete_setup_step
    step = data.get("step", "")
    if step:
        complete_setup_step(step)
    from app.database import get_setup_progress
    return {"steps": get_setup_progress()}


@router.post("/setup/complete")
def complete_setup(config: SetupConfig):
    from app.database import complete_setup_step

    updates = {"LLM_PROVIDER": config.llm_provider}
    provider_upper = config.llm_provider.upper()

    if provider_upper == "GEMINI":
        updates["GEMINI_API_KEY"] = config.api_key
        updates["GEMINI_MODEL"] = config.model or "gemini-1.5-flash"
        if config.base_url:
            updates["GEMINI_BASE_URL"] = config.base_url
    elif provider_upper == "OPENAI":
        updates["OPENAI_API_KEY"] = config.api_key
        updates["OPENAI_MODEL"] = config.model or "gpt-4o"
        if config.base_url:
            updates["OPENAI_BASE_URL"] = config.base_url
    elif provider_upper == "ANTHROPIC":
        updates["ANTHROPIC_API_KEY"] = config.api_key
        updates["ANTHROPIC_MODEL"] = config.model or "claude-3-5-sonnet-20241022"
        if config.base_url:
            updates["ANTHROPIC_BASE_URL"] = config.base_url

    if config.research_agent_url:
        updates["RESEARCH_AGENT_URL"] = config.research_agent_url
    if config.solution_agent_url:
        updates["SOLUTION_AGENT_URL"] = config.solution_agent_url
    if config.experiment_agent_url:
        updates["EXPERIMENT_AGENT_URL"] = config.experiment_agent_url

    for k, v in updates.items():
        if v is not None:
            set_setting(k, v)

    import importlib
    import shared.config
    importlib.reload(shared.config)

    for step in ["welcome", "llm_provider", "agent_urls", "complete"]:
        complete_setup_step(step)

    return {"message": "Setup complete", "provider": config.llm_provider}
