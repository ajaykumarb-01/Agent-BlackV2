import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.llm import call_llm
import json

def eval_metric_advisor(query: str = "", task: str = "", **kwargs) -> dict:
    task_name = task or query
    prompt = f"""Recommend evaluation metrics for this ML task. Return ONLY valid JSON with:
- task (the specific ML task)
- recommended (the most important metric with explanation)
- all_metrics (list of 5-7 relevant metrics)
- notes (string with usage guidance including class imbalance, multi-task, etc.)
Task: {task_name}"""
    raw = call_llm(system_prompt="You are an ML evaluation metrics expert.", user_prompt=prompt)
    return json.loads(raw)
