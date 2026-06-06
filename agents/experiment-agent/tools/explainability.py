import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.llm import call_llm
import json

def model_explainability_advisor(query: str = "", model_type: str = "", task: str = "", **kwargs) -> dict:
    mtype = model_type or task or query
    prompt = f"""Recommend model explainability methods for this model type. Return ONLY valid JSON with:
- model_category (the category of model)
- methods (list of 3-5 explainability methods, each with name, description, and when to use)
- limitations (string with caveats about the methods)
- recommendation (string with the best approach to start with)
Model type: {mtype}"""
    raw = call_llm(system_prompt="You are a model explainability and XAI expert.", user_prompt=prompt)
    return json.loads(raw)
