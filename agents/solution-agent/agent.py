import json
import asyncio
import sys
import os
_agent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_agent_dir, ".."))
sys.path.insert(0, _agent_dir)

from shared.llm import call_llm, async_call_llm, extract_json
from tools import TOOLS, execute_tool

SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "agent.txt")

def load_system_prompt() -> str:
    with open(SYSTEM_PROMPT_PATH) as f:
        return f.read()

async def run_agent(query: str) -> dict:
    from tools import TASKS as _TASKS
    tool_list = _TASKS
    system_prompt = load_system_prompt().format(tool_list=tool_list)
    decision_raw = await async_call_llm(system_prompt=system_prompt, user_prompt=query)
    decision = extract_json(decision_raw)

    selected_tools = decision.get("selected_tools", [])
    selected_tools = [t for t in selected_tools if t in TOOLS]
    if not selected_tools:
        selected_tools = ["search_papers", "analyze_gaps", "solution_recommendation"]

    async def _run_tool(tool_name: str):
        try:
            result = await asyncio.to_thread(execute_tool, tool_name, query=query)
            return tool_name, result
        except Exception as e:
            return tool_name, {"error": str(e)}

    tool_results = await asyncio.gather(*[_run_tool(t) for t in selected_tools])
    results = {name: result for name, result in tool_results}

    synthesis_prompt = f"""
Query: {query}
Tool Results: {json.dumps(results, indent=2)}

Synthesize a structured solution response with:
- papers, datasets, models, architecture, implementation_guidance
Return ONLY valid JSON.
"""
    final_raw = await async_call_llm(
        system_prompt="You are a solution architect specializing in NLP systems.",
        user_prompt=synthesis_prompt
    )
    return extract_json(final_raw)
