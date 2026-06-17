import json
import asyncio
import logging
import sys
import os

_agent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_agent_dir, ".."))
sys.path.insert(0, _agent_dir)

from shared.llm import call_llm, async_call_llm, extract_json
from shared.logging_setup import LogTimer
from tools import TOOLS, execute_tool

logger = logging.getLogger("experiment-agent.agent")

SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "agent.txt")


def load_system_prompt() -> str:
    with open(SYSTEM_PROMPT_PATH) as f:
        return f.read()


def _parse_orchestrator_envelope(raw: str) -> dict:
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
    envelope = _parse_orchestrator_envelope(raw_input)
    query = envelope["sub_query"] or envelope["query"]
    pre_selected = envelope["pre_selected_tools"]

    if pre_selected is not None:
        selected_tools = pre_selected
        tools_source = "orchestrator"
        logger.info(
            "Tool selection: source=%s  tools=%s  query=%s",
            tools_source,
            selected_tools,
            query[:120],
        )
    else:
        from tools import TASKS as _TASKS
        tool_list = _TASKS
        system_prompt = load_system_prompt().format(tool_list=tool_list)
        logger.info(
            "Tool selection: source=agent_llm  requesting LLM decision  available_tools=%s",
            list(TOOLS.keys()),
        )
        with LogTimer(logger, "agent_llm_tool_selection"):
            decision_raw = await async_call_llm(system_prompt=system_prompt, user_prompt=query)
            decision = extract_json(decision_raw)

        selected_tools = decision.get("selected_tools", [])
        selected_tools = [t for t in selected_tools if t in TOOLS]
        if not selected_tools:
            selected_tools = ["search_papers", "analyze_gaps", "experiment_planner"]
        tools_source = "agent_llm"
        logger.info(
            "Tool selection: source=%s  tools=%s  query=%s",
            tools_source,
            selected_tools,
            query[:120],
        )

    logger.info("Executing %d tool(s): %s", len(selected_tools), selected_tools)

    async def _run_tool(tool_name: str):
        try:
            result = await asyncio.to_thread(execute_tool, tool_name, query=query)
            return tool_name, result
        except Exception as e:
            logger.error("Tool execution failed  tool=%s  error=%s", tool_name, e)
            return tool_name, {"error": str(e)}

    with LogTimer(logger, "tool_execution", tools=selected_tools):
        tool_results = await asyncio.gather(*[_run_tool(t) for t in selected_tools])
    results = {name: result for name, result in tool_results}

    synthesis_prompt = f"""
Query: {query}
Tool Results: {json.dumps(results, indent=2)}

Synthesize a structured experiment design response with:
- experiment_plan, metrics, hyperparameters, models, implementation_steps
Return ONLY valid JSON.
"""
    logger.info("Synthesizing response from %d tool results...", len(results))
    with LogTimer(logger, "ml_synthesis"):
        final_raw = await async_call_llm(
            system_prompt="You are an ML experiment design expert.",
            user_prompt=synthesis_prompt,
        )
    result = extract_json(final_raw)
    if isinstance(result, dict):
        result["tools_used"] = selected_tools
        result["tools_source"] = tools_source
    logger.info("Agent response complete  tools_used=%s", selected_tools)
    return result
