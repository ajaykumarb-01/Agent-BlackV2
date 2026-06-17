import json
import asyncio
import logging
import sys
import os
import time
_agent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_agent_dir, ".."))
sys.path.insert(0, _agent_dir)

from shared.llm import call_llm, async_call_llm, extract_json
from tools import TOOLS, execute_tool

logger = logging.getLogger("research-agent")

SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "agent.txt")


def load_system_prompt() -> str:
    with open(SYSTEM_PROMPT_PATH) as f:
        return f.read()


def _parse_orchestrator_envelope(raw: str) -> dict:
    """Detect whether the incoming A2A message is an orchestrator envelope.

    Plain text queries (e.g. direct POST /research calls) pass through unchanged.
    JSON envelopes carry pre-selected tools and an optional sub_query.
    """
    stripped = raw.strip() if isinstance(raw, str) else ""
    if not stripped.startswith("{"):
        return {"query": raw, "sub_query": None, "pre_selected_tools": None}
    try:
        env = json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        return {"query": raw, "sub_query": None, "pre_selected_tools": None}
    if not isinstance(env, dict):
        return {"query": raw, "sub_query": None, "pre_selected_tools": None}

    sub_query = env.get("sub_query")
    sub_query = sub_query if isinstance(sub_query, str) and sub_query.strip() else None

    base_query = env.get("query")
    query = base_query if isinstance(base_query, str) and base_query.strip() else raw

    pre_tools = env.get("tools")
    if isinstance(pre_tools, list) and pre_tools:
        kept = [t for t in pre_tools if isinstance(t, str) and t in TOOLS]
        pre_tools = kept if kept else None
    else:
        pre_tools = None

    return {"query": query, "sub_query": sub_query, "pre_selected_tools": pre_tools}


async def run_agent(raw_input: str) -> dict:
    t_start = time.perf_counter()
    envelope = _parse_orchestrator_envelope(raw_input)
    query = envelope["sub_query"] or envelope["query"]
    pre_selected = envelope["pre_selected_tools"]
    query_preview = query[:100] + "..." if len(query) > 100 else query
    logger.info("Agent invoked  query=%r  has_envelope=%s", query_preview, pre_selected is not None)

    if pre_selected is not None:
        selected_tools = pre_selected
        tools_source = "orchestrator"
        logger.info("Tools from orchestrator  tools=%s", selected_tools)
    else:
        from tools import TASKS as _TASKS
        tool_list = _TASKS
        system_prompt = load_system_prompt().format(tool_list=tool_list)
        logger.info("Selecting tools via LLM  available=%d", len(tool_list))
        decision_raw = await async_call_llm(system_prompt=system_prompt, user_prompt=query)
        decision = extract_json(decision_raw)

        selected_tools = decision.get("selected_tools", [])
        selected_tools = [t for t in selected_tools if t in TOOLS]
        if not selected_tools:
            selected_tools = ["search_papers", "analyze_gaps", "solution_recommendation"]
            logger.warning("LLM returned no valid tools, using fallback: %s", selected_tools)
        tools_source = "agent_llm"
        logger.info("Tools from agent LLM  selected=%s", selected_tools)

    async def _run_tool(tool_name: str):
        t_tool = time.perf_counter()
        logger.info("Tool executing  tool=%s", tool_name)
        try:
            result = await asyncio.to_thread(execute_tool, tool_name, query=query)
            elapsed = round((time.perf_counter() - t_tool) * 1000, 1)
            logger.info("Tool done  tool=%s  elapsed=%sms", tool_name, elapsed)
            return tool_name, result
        except Exception as e:
            elapsed = round((time.perf_counter() - t_tool) * 1000, 1)
            logger.error("Tool failed  tool=%s  elapsed=%sms  error=%s", tool_name, elapsed, e)
            return tool_name, {"error": str(e)}

    tool_results = await asyncio.gather(*[_run_tool(t) for t in selected_tools])
    results = {name: result for name, result in tool_results}

    logger.info("Synthesizing results  tools_used=%s", selected_tools)
    synthesis_prompt = f"""
Query: {query}
Tool Results: {json.dumps(results, indent=2)}

Synthesize a structured research response with:
- papers, datasets, models, recommendations, evaluation_plan
Return ONLY valid JSON.
"""
    final_raw = await async_call_llm(
        system_prompt="You are a research synthesizer specializing in Computer Vision.",
        user_prompt=synthesis_prompt,
    )
    result = extract_json(final_raw)
    if isinstance(result, dict):
        result["tools_used"] = selected_tools
        result["tools_source"] = tools_source
    total_ms = round((time.perf_counter() - t_start) * 1000, 1)
    logger.info("Agent complete  tools=%s  source=%s  elapsed=%sms", selected_tools, tools_source, total_ms)
    return result
