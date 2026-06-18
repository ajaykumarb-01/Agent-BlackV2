"""Result aggregation: combining agent responses into a final report."""

import json
import logging

from shared.llm import async_call_llm, extract_json
from shared.logging_setup import LogTimer

logger = logging.getLogger("orchestrator.aggregation")

AGGREGATOR_PROMPT_PATH = None  # Set by orchestrator on import


def _extract_section(responses: dict, agent_key: str, section_keys: list[str] | None = None) -> str:
    """Extract a section from an agent's response for fallback aggregation."""
    agent_resp = responses.get(agent_key)
    if isinstance(agent_resp, dict):
        if section_keys:
            for sk in section_keys:
                if sk in agent_resp:
                    val = agent_resp[sk]
                    return val if isinstance(val, str) else json.dumps(val, indent=2)
        return json.dumps(agent_resp, indent=2)
    if agent_resp is not None:
        return json.dumps(agent_resp, indent=2) if not isinstance(agent_resp, str) else agent_resp
    return ""


def parse_aggregator_output(raw: str) -> dict:
    """Parse the LLM aggregator JSON response into a structured report."""
    parsed = extract_json(raw)
    if not isinstance(parsed, dict):
        raise ValueError("aggregator did not return a JSON object")

    tech_stack = parsed.get("tech_stack") or []
    if not isinstance(tech_stack, list):
        tech_stack = []
    tech_stack = [str(t).strip() for t in tech_stack if t is not None and str(t).strip()]
    seen: set[str] = set()
    deduped: list[str] = []
    for t in tech_stack:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(t)

    section_keys = ("literature_review", "datasets", "models", "evaluation_plan", "prototype_guidance")
    result: dict = {"tech_stack": deduped}
    for key in section_keys:
        value = parsed.get(key)
        if isinstance(value, str):
            result[key] = value
        elif isinstance(value, dict):
            obj = dict(value)
            obj.setdefault("text", "")
            result[key] = obj
        elif value is None:
            result[key] = ""
        else:
            result[key] = str(value)
    return result


async def aggregate_results(
    selected_names: list[str],
    responses: dict[str, dict],
    prompt_path: str,
) -> dict:
    """Run the LLM aggregator to combine agent responses into a final report.

    Falls back to raw section extraction if the LLM call fails.
    """
    import os
    agg_template_path = os.path.join(os.path.dirname(__file__), "prompts", "aggregator.txt")
    with open(agg_template_path) as f:
        agg_template = f.read()

    agg_user = agg_template.format(
        agents=json.dumps(selected_names),
        research=json.dumps(responses.get("research", {"result": {}}))[:6000],
        solution=json.dumps(responses.get("solution", {"result": {}}))[:6000],
        experiment=json.dumps(responses.get("experiment", {"result": {}}))[:6000],
    )

    try:
        try:
            final_raw = await async_call_llm(
                system_prompt="You are a senior research synthesiser. Output ONLY valid JSON.",
                user_prompt=agg_user,
                json_mode=True,
            )
        except Exception as e:
            logger.warning("[Step 4] Aggregator json_mode failed, retrying without it: %s", e)
            final_raw = await async_call_llm(
                system_prompt="You are a senior research synthesiser. Output ONLY valid JSON.",
                user_prompt=agg_user,
            )
        return parse_aggregator_output(final_raw)
    except Exception as e:
        logger.error("[Step 4] Aggregation FAILED: %s", e)
        return _build_fallback_response(selected_names, responses, e)


def _build_fallback_response(
    selected_names: list[str],
    responses: dict[str, dict],
    error: Exception,
) -> dict:
    """Build a fallback response by extracting raw sections from agent responses."""
    fallback = {
        "tech_stack": [],
        "literature_review": _extract_section(responses, "research", ["literature_review", "papers", "text"]),
        "datasets": _extract_section(responses, "research", ["datasets", "datasets_found", "data"]),
        "models": _extract_section(responses, "research", ["models", "model_recommendations", "architecture"]),
        "evaluation_plan": _extract_section(responses, "experiment", ["evaluation_plan", "experiments", "metrics"]),
        "prototype_guidance": _extract_section(responses, "solution", ["prototype_guidance", "guidance", "recommendations"]),
        "selected_agents": selected_names,
        "parse_warning": "aggregator_failed",
    }
    if not any(v for k, v in fallback.items() if k not in ("selected_agents", "parse_warning", "tech_stack")):
        fallback["prototype_guidance"] = (
            f"Aggregation failed: {error}. "
            f"Agent responses: {json.dumps({k: str(v)[:200] for k, v in responses.items()})}"
        )
    return fallback
