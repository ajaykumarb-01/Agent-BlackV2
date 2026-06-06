import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.llm import call_llm
import json

def recommend_cv_models(query: str = "", problem: str = "", **kwargs) -> dict:
    problem_name = problem or query
    prompt = f"""Given the CV problem, recommend the best model architectures. Return ONLY valid JSON with:
- task (the specific task)
- models (list of 3-5 models, each with name, strengths, weaknesses, params_count)
- recommendation (string with the best starting point)
Problem: {problem_name}"""
    raw = call_llm(system_prompt="You are a computer vision model architecture expert.", user_prompt=prompt)
    return json.loads(raw)
