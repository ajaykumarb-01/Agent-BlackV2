import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.llm import call_llm
import json

def recommend_models(query: str = "", problem: str = "", **kwargs) -> dict:
    problem_name = problem or query
    prompt = f"""Recommend ML models for this problem. Return ONLY valid JSON with:
- task (the specific ML task)
- models (list of 3-5 models, each with name, pros, cons, use_case)
- recommendation (string with the best model to start with and why)
Problem: {problem_name}"""
    raw = call_llm(system_prompt="You are an ML model selection expert.", user_prompt=prompt)
    return json.loads(raw)
