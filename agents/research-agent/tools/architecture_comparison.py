import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.llm import call_llm
import json

def architecture_comparison(query: str = "", task: str = "", architectures: list = None, **kwargs) -> dict:
    task_name = task or query
    arch_context = f"Compare these architectures: {json.dumps(architectures)}" if architectures else ""
    prompt = f"""Compare CV architectures for this task. Return ONLY valid JSON with:
- comparison (list of 3-5 architectures, each with name, params, speed, accuracy, use_case)
- recommendation (string with recommended architecture and why)
Task: {task_name}
{arch_context}"""
    raw = call_llm(system_prompt="You are a computer vision architecture comparison expert.", user_prompt=prompt)
    return json.loads(raw)
