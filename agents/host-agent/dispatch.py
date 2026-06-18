"""Agent dispatch: sending tasks to specialist agents and collecting results."""

import json
import time
import logging

import httpx

from shared.a2a_sdk import send_text_task

logger = logging.getLogger("orchestrator.dispatch")


async def call_agent(
    client: httpx.AsyncClient,
    entry: dict,
    query: str,
    catalog_by_name: dict[str, dict],
    progress_callback,
) -> tuple[str, dict]:
    """Send a task to a single agent via A2A and return (name, result)."""
    name = entry["name"]
    agent_info = catalog_by_name[name]
    base_url = agent_info["url"]
    agent_port = agent_info.get("port", "N/A")
    sub_query = entry.get("sub_query") or query
    tools = entry.get("tools") or []
    envelope = json.dumps({
        "query": query,
        "sub_query": sub_query,
        "tools": tools,
    })

    logger.info(
        "[Step 3] Dispatching  agent=%s  url=%s  port=%s  mcp_tools=%s",
        name, base_url, agent_port, tools,
    )
    progress_callback(
        name, "running",
        json.dumps({"tools": tools, "message": f"Calling {name} with {len(tools)} pre-selected tool(s)..."}),
    )

    agent_start = time.perf_counter()
    try:
        result = await send_text_task(base_url, envelope)
        elapsed_ms = round((time.perf_counter() - agent_start) * 1000, 1)
        snippet = ""
        if isinstance(result, dict):
            snippet = json.dumps(result, indent=2)[:500]
        elif isinstance(result, str):
            snippet = result[:500]
        logger.info(
            "[Step 3] Agent response  agent=%s  url=%s  elapsed=%sms  tools=%s",
            name, base_url, elapsed_ms, tools,
        )
        progress_callback(name, "complete", json.dumps({"tools": tools, "snippet": snippet}))
        return name, result
    except Exception as e:
        elapsed_ms = round((time.perf_counter() - agent_start) * 1000, 1)
        msg = f"{name} A2A request failed: {e}"
        logger.error(
            "[Step 3] Agent FAILED  agent=%s  url=%s  elapsed=%sms  error=%s",
            name, base_url, elapsed_ms, e,
        )
        progress_callback(name, "error", msg)
        return name, {"error": msg}


async def dispatch_to_agents(
    selected: list[dict],
    query: str,
    catalog: list[dict],
    progress_callback,
) -> dict[str, dict]:
    """Dispatch to all selected agents concurrently and return responses dict."""
    catalog_by_name = {a["name"]: a for a in catalog}
    dispatch_start = time.perf_counter()

    async with httpx.AsyncClient(timeout=300) as client:
        tasks = [call_agent(client, entry, query, catalog_by_name, progress_callback) for entry in selected]
        results = await asyncio.gather(*tasks)
        responses = {name: result for name, result in results}

    elapsed_ms = round((time.perf_counter() - dispatch_start) * 1000, 1)
    logger.info(
        "[Step 3] Dispatch complete  agents=%s  total_elapsed=%sms",
        [s["name"] for s in selected], elapsed_ms,
    )
    progress_callback("dispatching", "complete", "All agent responses received")
    return responses


# Needed for asyncio.gather
import asyncio  # noqa: E402
