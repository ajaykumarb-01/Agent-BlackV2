import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.llm import call_llm
import json

def llm_benchmark(query: str = "", task: str = "", **kwargs) -> dict:
    task_name = task or query
    prompt = f"""Compare LLMs for this NLP task. Return ONLY valid JSON with:
- task (the specific task)
- top_models (list of 3-5 models, each with name, strength, cost_estimate, context_window)
- recommendation (string with the best model and why)
Task: {task_name}"""
    raw = call_llm(system_prompt="You are an LLM benchmarking and comparison expert.", user_prompt=prompt)
    return json.loads(raw)
