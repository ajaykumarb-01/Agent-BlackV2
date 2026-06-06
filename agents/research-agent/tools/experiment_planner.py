import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.llm import call_llm
import json

def experiment_planner(query: str = "", problem: str = "", **kwargs) -> dict:
    problem_name = problem or query
    prompt = f"""Design an experiment plan for this CV research problem. Return ONLY valid JSON with:
- problem (the problem description)
- datasets (list of 2-4 recommended datasets with split ratios)
- baselines (list of 2-4 baseline methods)
- ablation_studies (list of 3-5 ablation experiments)
- evaluation_strategy (string describing evaluation approach)
- compute_estimate (object with GPU needs and time estimate)
Problem: {problem_name}"""
    raw = call_llm(system_prompt="You are a computer vision experiment design expert.", user_prompt=prompt)
    return json.loads(raw)
