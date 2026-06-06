import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.llm import call_llm
import json

def prototype_guidance(query: str = "", problem: str = "", **kwargs) -> dict:
    problem_name = problem or query
    prompt = f"""Provide prototype development guidance for this NLP use case. Return ONLY valid JSON with:
- problem (the use case)
- quick_start_code (string with pseudo-code or key code snippets)
- minimal_viable_pipeline (list of 5-8 steps to build an MVP)
- common_pitfalls (list of 3-5 pitfalls to avoid)
- next_steps (list of 3-5 improvements after MVP)
Use case: {problem_name}"""
    raw = call_llm(system_prompt="You are an NLP prototype development expert.", user_prompt=prompt)
    return json.loads(raw)
