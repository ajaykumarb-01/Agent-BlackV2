import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.llm import call_llm
import json

def eval_metric_advisor_nlp(query: str = "", task: str = "", **kwargs) -> dict:
    task_name = task or query
    prompt = f"""Recommend evaluation metrics for this NLP task. Return ONLY valid JSON with:
- task (the specific NLP task)
- primary (the most important metric)
- secondary (list of 2-4 supporting metrics)
- notes (string with usage guidance and caveats)
Task: {task_name}"""
    raw = call_llm(system_prompt="You are an NLP evaluation metrics expert.", user_prompt=prompt)
    return json.loads(raw)
