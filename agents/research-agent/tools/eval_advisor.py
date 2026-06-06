import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.llm import call_llm
import json

def eval_metric_advisor_cv(query: str = "", task: str = "", **kwargs) -> dict:
    task_name = task or query
    prompt = f"""Recommend evaluation metrics for this CV task. Return ONLY valid JSON with:
- task (the specific task)
- primary (the most important metric)
- secondary (list of 2-4 supporting metrics)
- notes (string with usage guidance)
Task: {task_name}"""
    raw = call_llm(system_prompt="You are a computer vision evaluation metrics expert.", user_prompt=prompt)
    return json.loads(raw)
