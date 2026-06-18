"""Offline target detection: refuse to reroute when the correct agent is offline."""

import logging

from constants import AGENT_DISPLAY_NAMES
from validation import classify_query_domains

logger = logging.getLogger("orchestrator")


def check_offline_target(query: str, catalog: list[dict]) -> dict | None:
    """Return an error response if the query targets an offline agent.

    Uses domain keyword classification to determine the target agent.
    Runs *before* the LLM routing step so that we never silently re-route a
    domain-specific query to the wrong agent when the correct one is offline.
    """
    domains = classify_query_domains(query)
    if not domains or len(domains) > 1:
        return None  # ambiguous or cross-domain — let the LLM decide

    target = next(iter(domains))
    catalog_by_name = {a["name"]: a for a in catalog}
    agent_info = catalog_by_name.get(target)
    if agent_info is None:
        return None  # agent not in catalog at all
    if agent_info.get("online", True):
        return None  # agent is online — proceed normally

    display = AGENT_DISPLAY_NAMES.get(target, target)
    logger.warning(
        "[Step 1.5] Query targets OFFLINE agent '%s' (%s) — refusing to reroute",
        target, display,
    )
    return {
        "error": "no_suitable_agent",
        "message": (
            f"No suitable agent is available for this query. "
            f"The {display} is the best fit but is offline. "
            f"Start the agent service and try again."
        ),
        "offline_agent": target,
    }
