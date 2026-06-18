"""Routing: parsing LLM routing decisions and filtering against catalog."""

import logging

from shared.llm import extract_json

logger = logging.getLogger("orchestrator.routing")


def parse_routing_decision(raw: str) -> dict:
    """Parse the LLM routing JSON response into a normalized structure."""
    try:
        parsed = extract_json(raw)
    except Exception as e:
        logger.warning("Routing JSON parse failed: %s", e)
        return {"selected_agents": [], "reasoning": f"Parse failed: {e}"}

    if not isinstance(parsed, dict):
        return {"selected_agents": [], "reasoning": "Routing response was not a JSON object."}

    raw_list = parsed.get("selected_agents")
    if not isinstance(raw_list, list):
        return {"selected_agents": [], "reasoning": "No selected_agents list in response."}

    normalized: list[dict] = []
    for entry in raw_list:
        if isinstance(entry, str):
            normalized.append({"name": entry, "tools": [], "sub_query": ""})
        elif isinstance(entry, dict):
            name = entry.get("name")
            if isinstance(name, str) and name.strip():
                tools = entry.get("tools") or []
                tools = [t for t in tools if isinstance(t, str) and t.strip()]
                sub_query = entry.get("sub_query") or entry.get("query") or ""
                if not isinstance(sub_query, str):
                    sub_query = ""
                normalized.append({
                    "name": name.strip(),
                    "tools": tools,
                    "sub_query": sub_query.strip(),
                })

    return {
        "selected_agents": normalized,
        "reasoning": str(parsed.get("reasoning", "")),
    }


def filter_routing_against_catalog(
    routing: dict, catalog: list[dict]
) -> tuple[list[dict], list[str], list[str]]:
    """Validate LLM-selected agents against the live discovery catalog.

    Returns (valid_entries, drop_reasons, offline_agent_names).
    """
    catalog_by_name = {a["name"]: a for a in catalog}
    valid: list[dict] = []
    drops: list[str] = []
    offline_agents: list[str] = []

    for entry in routing.get("selected_agents", []):
        name = entry["name"]
        if name not in catalog_by_name:
            drops.append(f"unknown agent '{name}'")
            continue
        agent = catalog_by_name[name]
        if not agent.get("online", True):
            drops.append(f"agent '{name}' is offline")
            offline_agents.append(name)
            continue
        available_tools = {t["name"] for t in agent.get("tools", [])}
        requested_tools = entry.get("tools") or []
        kept_tools = [t for t in requested_tools if t in available_tools]
        dropped_tools = [t for t in requested_tools if t not in available_tools]
        for t in dropped_tools:
            drops.append(f"tool '{t}' not on agent '{name}'")
        valid.append({**entry, "name": name, "tools": kept_tools})

    return valid, drops, offline_agents


def build_routing_prompt(catalog_text: str, query: str, prompt_path: str) -> str:
    """Build the LLM routing prompt from template, catalog, and query."""
    with open(prompt_path) as f:
        template = f.read()
    return template.replace("{{CATALOG}}", catalog_text).replace("{{QUERY}}", query)
