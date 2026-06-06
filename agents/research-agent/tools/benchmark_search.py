import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.llm import call_llm
import json

def benchmark_search_cv(query: str = "", task: str = "", **kwargs) -> dict:
    task_name = task or query
    prompt = f"""Search for state-of-the-art benchmarks for this CV task. Return ONLY valid JSON with:
- task (the specific task)
- benchmarks (list of 3-5 benchmarks, each with dataset name, metric, SOTA score, model name, and source)
Task: {task_name}"""
    raw = call_llm(system_prompt="You are a computer vision benchmark tracking expert.", user_prompt=prompt)
    return json.loads(raw)
