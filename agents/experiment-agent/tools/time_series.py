import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.llm import call_llm
import json

def time_series_strategy(query: str = "", problem: str = "", **kwargs) -> dict:
    problem_name = problem or query
    prompt = f"""Recommend time series analysis strategy for this problem. Return ONLY valid JSON with:
- task (the time series task type: forecasting, anomaly, or classification)
- classical (list of 2-3 classical methods with brief description)
- ml (list of 2-3 ML-based methods with brief description)
- dl (list of 2-3 deep learning methods with brief description)
- decision_guide (string with how to choose based on data size and characteristics)
- evaluation (list of recommended evaluation metrics)
Problem: {problem_name}"""
    raw = call_llm(system_prompt="You are a time series analysis and forecasting expert.", user_prompt=prompt)
    return json.loads(raw)
