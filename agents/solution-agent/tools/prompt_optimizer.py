import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.llm import call_llm
import json

def prompt_optimizer(query: str = "", task: str = "", prompt_text: str = "", **kwargs) -> dict:
    task_name = task or query
    current_prompt = prompt_text or query
    prompt = f"""Optimize this prompt for the NLP task. Return ONLY valid JSON with:
- original_prompt (the original prompt text)
- optimization_strategies (list of 3-5 specific optimization suggestions)
- optimized_example (string with an improved version of the prompt)
- reasoning (string explaining why each change helps)
Task: {task_name}
Current Prompt: {current_prompt}"""
    raw = call_llm(system_prompt="You are a prompt engineering and optimization expert.", user_prompt=prompt)
    return json.loads(raw)
