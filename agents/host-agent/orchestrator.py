import json
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
from shared.llm import async_call_llm, extract_json
from shared.config import AGENT_URLS

DECOMPOSE_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "orchestrator.txt")
SELECTION_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "selection.txt")

RESEARCH_DOMAINS = [
    "computer vision", "image classification", "object detection", "segmentation",
    "medical imaging", "video analytics", "vision-language", "nlp", "llm",
    "natural language", "rag", "retrieval augmented", "prompt engineering",
    "text classification", "summarization", "conversational ai", "information extraction",
    "machine learning", "deep learning", "neural network", "model selection",
    "feature engineering", "time series", "hyperparameter", "experiment design",
    "evaluation strategy", "research", "dataset", "benchmark", "architecture",
    "transformer", "cnn", "diffusion", "gan", "reinforcement learning",
    "paper", "arxiv", "论文", "research proposal", "proof of concept",
]

NOT_RESEARCH_RESPONSE = {
    "error": "not_research_query",
    "message": "This query does not appear to be related to AI/ML research. This system is a Research Assistant that helps with: Computer Vision, NLP, Machine Learning research — including literature review, dataset recommendation, model selection, experiment planning, and prototype guidance. Please ask a research-related question.",
    "supported_topics": [
        "Research paper discovery and summarization",
        "Dataset recommendation (CV, NLP, ML)",
        "Model/architecture recommendation",
        "Experiment design and planning",
        "Benchmark search and comparison",
        "Research gap analysis",
        "Prototype development guidance",
    ],
}


def load_prompt(path: str) -> str:
    with open(path) as f:
        return f.read()

def _load_prompt_safe(path: str) -> str:
    try:
        content = load_prompt(path)
        if not content.strip():
            raise ValueError(f"Prompt file is empty: {path}")
        return content
    except (FileNotFoundError, ValueError) as e:
        raise RuntimeError(f"Failed to load prompt from {path}: {e}")


async def _is_research_query(query: str) -> bool:
    query_lower = query.lower().strip()
    if len(query_lower) < 5:
        return False
    if any(domain in query_lower for domain in RESEARCH_DOMAINS):
        return True
    gate_prompt = f"""You are a research query classifier. Determine if the following query is related to AI, Machine Learning, Computer Vision, NLP, or academic/scientific research.

Respond ONLY with valid JSON:
{{"is_research": true, "reason": "brief reason"}} or {{"is_research": false, "reason": "brief reason"}}

Query: {query}"""
    try:
        raw = await async_call_llm(
            system_prompt="You are a strict classifier. Only classify queries clearly related to AI/ML/CV/NLP research as true.",
            user_prompt=gate_prompt,
        )
        result = extract_json(raw)
        return result.get("is_research", False)
    except Exception:
        return True


async def orchestrate(query: str, progress_callback=None) -> dict:
    if progress_callback is None:
        progress_callback = lambda step, status, detail: None

    # ── Step 0: Research-relevance gate ────────────────────────────────────────
    progress_callback("validating_query", "running", "Checking if query is research-related...")
    if not await _is_research_query(query):
        progress_callback("validating_query", "complete", "Query rejected: not research-related")
        return NOT_RESEARCH_RESPONSE
    progress_callback("validating_query", "complete", "Query is research-related")

    # ── Step 1: Select agents ──────────────────────────────────────────────────
    progress_callback("selecting_agents", "running", "Selecting relevant agents...")
    try:
        selection_prompt = _load_prompt_safe(SELECTION_PROMPT_PATH)
        selection_raw = await async_call_llm(
            system_prompt="You are a research orchestrator that selects relevant agents.",
            user_prompt=selection_prompt.format(query=query)
        )
        selection = extract_json(selection_raw)
        selected_agents = selection.get("selected_agents", ["research", "solution", "experiment"])
        # Validate agent names
        valid_agents = {"research", "solution", "experiment"}
        selected_agents = [a for a in selected_agents if a in valid_agents]
        if not selected_agents:
            progress_callback("selecting_agents", "complete", "No relevant agents found for this query")
            return NOT_RESEARCH_RESPONSE
        progress_callback("selecting_agents", "complete", f"Selected: {', '.join(selected_agents)}")
    except Exception as e:
        selected_agents = ["research", "solution", "experiment"]
        progress_callback("selecting_agents", "complete", f"Selection failed, using all agents: {e}")

    # ── Step 2: Decompose query ────────────────────────────────────────────────
    progress_callback("decomposing_task", "running", "Decomposing query into sub-tasks...")
    try:
        decompose_prompt = _load_prompt_safe(DECOMPOSE_PROMPT_PATH)
        decomposed_raw = await async_call_llm(
            system_prompt="You are a research orchestrator.",
            user_prompt=decompose_prompt.format(query=query)
        )
        tasks = extract_json(decomposed_raw)
        progress_callback("decomposing_task", "complete", "Query decomposed into sub-tasks")
    except Exception as e:
        tasks = {}
        progress_callback("decomposing_task", "complete", f"Decomposition failed, using original query: {e}")

    agent_endpoints = {
        "research": ("research_task", f"{AGENT_URLS['research']}/research"),
        "solution": ("solution_task", f"{AGENT_URLS['solution']}/solution"),
        "experiment": ("experiment_task", f"{AGENT_URLS['experiment']}/experiment"),
    }

    # ── Step 3: Dispatch to sub-agents concurrently ────────────────────────────
    async def _call_agent(client: httpx.AsyncClient, agent_name: str):
        task_key, url = agent_endpoints[agent_name]
        payload = {"query": tasks.get(task_key, query)}
        progress_callback(agent_name, "running", f"Calling {agent_name} agent...")
        try:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            result = r.json()
            progress_callback(agent_name, "complete", f"{agent_name} agent completed")
            return agent_name, result
        except Exception as e:
            progress_callback(agent_name, "error", f"{agent_name} agent failed: {str(e)}")
            return agent_name, {"error": str(e)}

    async with httpx.AsyncClient(timeout=120) as client:
        agent_tasks = [_call_agent(client, name) for name in selected_agents]
        agent_results = await asyncio.gather(*agent_tasks)
        responses = {name: result for name, result in agent_results}

    # ── Step 4: Aggregate results ──────────────────────────────────────────────
    progress_callback("aggregating", "running", "Aggregating results into final report...")
    try:
        agg_prompt = f"""
Combine these agent responses into a single research report.
Agents used: {json.dumps(selected_agents)}
Research: {json.dumps(responses.get('research', {'result': {}}))}
Solution: {json.dumps(responses.get('solution', {'result': {}}))}
Experiment: {json.dumps(responses.get('experiment', {'result': {}}))}
Return ONLY valid JSON with keys: literature_review, datasets, models, evaluation_plan, prototype_guidance
"""
        final_raw = await async_call_llm(
            system_prompt="You are a research report writer that synthesizes multi-agent outputs.",
            user_prompt=agg_prompt
        )
        progress_callback("aggregating", "complete", "Report finalized")
        return extract_json(final_raw)
    except Exception as e:
        progress_callback("aggregating", "error", f"Aggregation failed: {e}")
        # Return raw agent responses as fallback
        fallback = {
            "literature_review": str(responses.get("research", {}).get("result", {})),
            "datasets": str(responses.get("research", {}).get("result", {})),
            "models": str(responses.get("solution", {}).get("result", {})),
            "evaluation_plan": str(responses.get("experiment", {}).get("result", {})),
            "prototype_guidance": f"Aggregation failed: {e}",
        }
        return fallback
