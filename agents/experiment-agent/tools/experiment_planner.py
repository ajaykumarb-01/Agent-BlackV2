import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.llm import call_llm
import json

def plan_experiment(query: str = "", problem: str = "", **kwargs) -> dict:
    problem_name = problem or query
    prompt = f"""Design a comprehensive experiment plan for this ML problem. Return ONLY valid JSON with:
- problem (the problem description)
- datasets (list of 3-5 recommended datasets with split ratios)
- baselines (list of 2-4 baseline methods to compare against)
- ablation_studies (list of 3-5 ablation experiments to run)
- cross_validation (string with CV strategy)
- statistical_tests (string with recommended significance tests)
- budget_estimate (object with compute and time estimates)
Problem: {problem_name}"""
    raw = call_llm(system_prompt="You are an ML experiment design expert.", user_prompt=prompt)
    return json.loads(raw)
