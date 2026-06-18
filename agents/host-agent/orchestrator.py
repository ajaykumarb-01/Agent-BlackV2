"""Orchestrator: the main pipeline that validates, routes, dispatches, and aggregates."""

import json
import asyncio
import logging
import os
import sys
import time

# Ensure host-agent submodules are importable (needed when loaded via importlib)
_HOST_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
if _HOST_AGENT_DIR not in sys.path:
    sys.path.insert(0, _HOST_AGENT_DIR)

from shared.discovery import discover_agents, render_catalog
from shared.llm import async_call_llm
from shared.logging_setup import LogTimer

from constants import AGENT_DOMAINS, AGENT_DISPLAY_NAMES, NOT_RESEARCH_RESPONSE
from validation import (
    build_not_research_response,
    validate_research_query,
    classify_query_domains,
    filter_by_domain,
)
from offline_check import check_offline_target
from routing import parse_routing_decision, filter_routing_against_catalog, build_routing_prompt
from dispatch import dispatch_to_agents
from aggregation import aggregate_results

logger = logging.getLogger("orchestrator")

SELECTION_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "selection.txt")


async def orchestrate(query: str, progress_callback=None) -> dict:
    """Public entry point. Wraps the inner pipeline with error handling."""
    if progress_callback is None:
        progress_callback = lambda step, status, detail: None
    try:
        return await _orchestrate_inner(query, progress_callback)
    except Exception as e:
        progress_callback("orchestrator", "error", f"Orchestration failed: {e}")
        logger.exception("Orchestration failed: %s", e)
        return {
            "error": str(e),
            "tech_stack": [],
            "literature_review": "",
            "datasets": "",
            "models": "",
            "evaluation_plan": "",
            "prototype_guidance": "",
        }


async def _orchestrate_inner(query: str, progress_callback) -> dict:
    logger.info("=" * 60)
    logger.info("ORCHESTRATION START  query=%s", query[:200])

    # ── Step 0: Research-relevance gate ────────────────────────────────────────
    logger.info("[Step 0] Validating research relevance...")
    with LogTimer(logger, "validation"):
        progress_callback("validating_query", "running", "Checking if query is research-related...")
        validation = await validate_research_query(query)

    if not validation.get("is_research"):
        reason = str(validation.get("reason") or NOT_RESEARCH_RESPONSE["message"])
        logger.info("[Step 0] Query REJECTED  method=%s  reason=%s", validation.get("method"), reason[:200])
        progress_callback("validating_query", "complete", f"Query rejected: {reason}")
        return build_not_research_response(reason, validation)

    logger.info("[Step 0] Query ACCEPTED  method=%s  reason=%s", validation.get("method"), validation.get("reason", "")[:200])
    progress_callback("validating_query", "complete", "Query is research-related")

    # ── Step 1: Live agent + tool discovery ───────────────────────────────────
    logger.info("[Step 1] Discovering live agents and their tools...")
    progress_callback("discovering_agents", "running", "Discovering live agents and their tools...")
    with LogTimer(logger, "agent_discovery"):
        catalog = await discover_agents()

    if not catalog:
        logger.warning("[Step 1] No agents are reachable")
        progress_callback("discovering_agents", "error", "No agents are reachable")
        return {
            "error": "no_agents_available",
            "message": "No specialist agents responded to discovery. Check that the 3 agent services are running on :8001/:8002/:8003.",
        }

    _log_discovered_agents(catalog)
    progress_callback(
        "discovering_agents", "complete",
        f"Found {len(catalog)} agents: {', '.join(a['name'] for a in catalog)}",
    )

    # ── Step 1.5: Deterministic offline-agent guard ────────────────────────
    offline_error = check_offline_target(query, catalog)
    if offline_error:
        progress_callback("routing", "complete", f"The {offline_error['offline_agent']} agent is offline — refusing to reroute.")
        return offline_error

    # ── Step 2: LLM picks agents + tools from the live catalog ────────────────
    logger.info("[Step 2] LLM routing — selecting agents and tools...")
    progress_callback("routing", "running", "LLM is selecting agents and tools...")
    with LogTimer(logger, "llm_routing"):
        routing = await _run_llm_routing(catalog, query, progress_callback)
        if routing is None:
            return {"error": "routing_failed", "message": "The orchestrator's routing LLM call failed."}

    logger.info("[Step 2] LLM raw decision  agents_requested=%s  reasoning=%s",
                [a["name"] for a in routing.get("selected_agents", [])], routing.get("reasoning", "")[:300])

    # Filter against live catalog
    selected, drop_reasons, offline_agents = filter_routing_against_catalog(routing, catalog)
    for drop in drop_reasons:
        logger.warning("[Step 2] Routing drop: %s", drop)

    # Filter against query domain
    if selected:
        selected, domain_drops = filter_by_domain(selected, query)
        for drop in domain_drops:
            logger.warning("[Step 2] Domain filter drop: %s", drop)

    if not selected:
        return _handle_no_agents(offline_agents, query, routing, progress_callback)

    _log_selected_agents(selected, catalog)
    selected_names = [s["name"] for s in selected]
    reasoning = routing.get("reasoning", "")
    progress_callback("routing", "complete", json.dumps({"agents": selected_names, "reasoning": reasoning}))

    # ── Step 3: Dispatch to sub-agents concurrently ────────────────────────
    logger.info("[Step 3] Dispatching to %d agent(s): %s", len(selected), selected_names)
    progress_callback("dispatching", "running", f"Dispatching to {len(selected)} agent(s)...")
    responses = await dispatch_to_agents(selected, query, catalog, progress_callback)

    # ── Step 4: Aggregate results ──────────────────────────────────────────
    logger.info("[Step 4] Aggregating results from %d agent(s)...", len(selected))
    progress_callback("aggregating", "running", "Aggregating results into final report...")
    with LogTimer(logger, "aggregation"):
        result = await aggregate_results(selected_names, responses, SELECTION_PROMPT_PATH)

    progress_callback("aggregating", "complete", "Report finalized")
    result["selected_agents"] = selected_names
    result["routing_reasoning"] = routing.get("reasoning", "")

    logger.info("ORCHESTRATION COMPLETE  agents=%s", selected_names)
    logger.info("=" * 60)
    return result


# ── Internal helpers ─────────────────────────────────────────────────────────


def _log_discovered_agents(catalog: list[dict]) -> None:
    online_count = sum(1 for a in catalog if a.get("online", True))
    for agent in catalog:
        status = "ONLINE" if agent.get("online", True) else "OFFLINE"
        tool_names = [t["name"] for t in agent.get("tools", [])]
        logger.info(
            "[Step 1] Agent discovered  name=%s  status=%s  url=%s  port=%s  tools=%d  tool_list=%s",
            agent["name"], status, agent.get("url", "N/A"), agent.get("port", "N/A"), len(tool_names), tool_names,
        )
    logger.info("[Step 1] Discovery complete  total=%d  online=%d  agents=%s",
                len(catalog), online_count, [a["name"] for a in catalog])


async def _run_llm_routing(catalog: list[dict], query: str, progress_callback) -> dict | None:
    """Call the LLM to select agents and tools. Returns None on failure."""
    try:
        catalog_text = render_catalog(catalog)
        routing_prompt = build_routing_prompt(catalog_text, query, SELECTION_PROMPT_PATH)
        routing_raw = await async_call_llm(
            system_prompt="You are a research routing orchestrator. Output ONLY valid JSON. No prose, no markdown.",
            user_prompt=routing_prompt,
            json_mode=True,
        )
        return parse_routing_decision(routing_raw)
    except Exception as e:
        logger.error("[Step 2] Routing LLM call failed: %s", e)
        progress_callback("routing", "error", f"Routing LLM call failed: {e}")
        return None


def _log_selected_agents(selected: list[dict], catalog: list[dict]) -> None:
    catalog_by_name = {a["name"]: a for a in catalog}
    for s in selected:
        agent_info = catalog_by_name.get(s["name"], {})
        logger.info(
            "[Step 2] Agent SELECTED  name=%s  url=%s  port=%s  mcp_tools=%s  sub_query=%s",
            s["name"], agent_info.get("url", "N/A"), agent_info.get("port", "N/A"),
            s.get("tools", []), (s.get("sub_query") or "N/A")[:150],
        )


def _handle_no_agents(offline_agents, query, routing, progress_callback) -> dict:
    """Return appropriate error when no agents are selected."""
    if offline_agents:
        names = ", ".join(offline_agents)
        logger.warning("[Step 2] Required agents OFFLINE: %s", names)
        msg = f"No suitable agent available. The required agent(s) ({names}) are offline."
        progress_callback("routing", "complete", msg)
        return {"error": "no_suitable_agent", "message": f"{msg} Start the agent service(s) and try again.", "routing": routing}

    query_domains = classify_query_domains(query)
    if query_domains:
        domain_names = ", ".join(AGENT_DOMAINS[d]["description"] for d in query_domains)
        msg = f"No suitable agent available for this query. Required domain: {domain_names}."
    else:
        msg = "No suitable agent available for this query."
    logger.info("[Step 2] No matching agent for query domains=%s", query_domains)
    progress_callback("routing", "complete", msg)
    return {"error": "no_suitable_agent", "message": msg, "routing": routing}
