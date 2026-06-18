import asyncio
import logging
import os
import sys
from typing import Any

import httpx

if __name__ != "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import get_agent_urls

logger = logging.getLogger("discovery")

DISCOVERY_TIMEOUT = 3.0


async def _fetch_agent(client: httpx.AsyncClient, name: str, url: str) -> dict[str, Any] | None:
    try:
        logger.debug("Probing agent %s at %s", name, url)
        cap_task = client.get(f"{url.rstrip('/')}/capabilities", timeout=DISCOVERY_TIMEOUT)
        tools_task = client.get(f"{url.rstrip('/')}/tools", timeout=DISCOVERY_TIMEOUT)
        health_task = client.get(f"{url.rstrip('/')}/health", timeout=DISCOVERY_TIMEOUT)
        cap_resp, tools_resp, health_resp = await asyncio.gather(
            cap_task, tools_task, health_task, return_exceptions=True
        )
    except Exception as e:
        logger.warning("Discovery request failed for %s at %s: %s", name, url, e)
        return None

    if isinstance(cap_resp, Exception) or cap_resp.status_code != 200:
        logger.warning("Capabilities unreachable for %s at %s", name, url)
        return None

    if isinstance(health_resp, Exception) or health_resp.status_code != 200:
        logger.warning("Health check failed for %s at %s", name, url)
        return None

    try:
        capabilities = cap_resp.json()
    except Exception:
        capabilities = {}

    tools: list[dict[str, str]] = []
    if not isinstance(tools_resp, Exception) and tools_resp.status_code == 200:
        try:
            raw_tools = tools_resp.json().get("tools", [])
        except Exception:
            raw_tools = []

        # Endpoint can return either a list of tool objects or a dict keyed by tool name.
        if isinstance(raw_tools, dict):
            raw_tools = [
                {"name": k, **(v if isinstance(v, dict) else {})}
                for k, v in raw_tools.items()
            ]
        elif not isinstance(raw_tools, list):
            raw_tools = []

        for t in raw_tools:
            if isinstance(t, dict) and t.get("name"):
                tools.append(
                    {
                        "name": str(t["name"]),
                        "description": str(t.get("description", "")).strip(),
                    }
                )

    logger.info(
        "Agent discovered  name=%s  url=%s  port=%s  tools=%d  tool_names=%s",
        name,
        url,
        capabilities.get("port"),
        len(tools),
        [t["name"] for t in tools],
    )

    return {
        "name": name,
        "url": url,
        "description": str(capabilities.get("description", "")).strip(),
        "port": capabilities.get("port"),
        "tools": tools,
    }


async def discover_agents(include_offline: bool = True) -> list[dict[str, Any]]:
    """Discover all configured agents and their available tools at runtime.

    Returns a list of:
        {
            "name": "research",
            "url": "http://localhost:8001",
            "description": "Computer Vision ...",
            "port": 8001,
            "online": true,
            "tools": [{"name": "search_papers", "description": "..."}, ...]
        }

    If include_offline is True (default), offline agents are included with
    online=False and empty tools so the LLM knows they exist but are unreachable.
    """
    all_urls = get_agent_urls()
    logger.info("Discovery starting  agents=%s", list(all_urls.keys()))

    async with httpx.AsyncClient(timeout=DISCOVERY_TIMEOUT) as client:
        tasks = [_fetch_agent(client, name, url) for name, url in all_urls.items()]
        results = await asyncio.gather(*tasks)

    online_agents: dict[str, dict[str, Any]] = {}
    for r in results:
        if r is not None:
            r["online"] = True
            online_agents[r["name"]] = r

    if not include_offline:
        logger.info(
            "Discovery complete  online=%d  agents=%s",
            len(online_agents),
            list(online_agents.keys()),
        )
        return list(online_agents.values())

    # Include offline agents with empty tools so the LLM knows they exist
    all_agents: list[dict[str, Any]] = []
    for name, url in all_urls.items():
        if name in online_agents:
            all_agents.append(online_agents[name])
        else:
            logger.warning("Agent OFFLINE  name=%s  url=%s", name, url)
            all_agents.append({
                "name": name,
                "url": url,
                "description": "",
                "port": None,
                "online": False,
                "tools": [],
            })

    online_count = sum(1 for a in all_agents if a.get("online", True))
    logger.info(
        "Discovery complete  total=%d  online=%d  offline=%d  agents=%s",
        len(all_agents),
        online_count,
        len(all_agents) - online_count,
        [(a["name"], "ONLINE" if a.get("online") else "OFFLINE") for a in all_agents],
    )
    return all_agents


def render_catalog(catalog: list[dict[str, Any]]) -> str:
    """Render the catalog as a human-readable text block for LLM prompts.

    Offline agents are shown with a status marker so the LLM knows they exist
    but cannot be used.
    """
    if not catalog:
        return "(no agents are currently online)"

    blocks: list[str] = []
    for agent in catalog:
        online = agent.get("online", True)
        status = "ONLINE" if online else "OFFLINE — agent is unreachable but still select it if it is the best fit; the system will notify the user"
        lines = [
            f"[Agent: {agent['name']}]  ({status})",
            f"  URL: {agent['url']}",
            f"  Description: {agent['description'] or '(none)'}",
            "  Tools:",
        ]
        if agent["tools"]:
            for tool in agent["tools"]:
                desc = tool["description"][:160].replace("\n", " ")
                lines.append(f"    - {tool['name']}: {desc}")
        else:
            lines.append("    (no tools discovered)")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


if __name__ == "__main__":
    import json
    print(json.dumps(asyncio.run(discover_agents()), indent=2))
