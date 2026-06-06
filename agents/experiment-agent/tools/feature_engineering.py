import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.llm import call_llm
import json

def feature_engineering_advisor(query: str = "", data_type: str = "", **kwargs) -> dict:
    dtype = data_type or query
    prompt = f"""Recommend feature engineering techniques for this data type. Return ONLY valid JSON with:
- data_type (the type of data)
- suggestions (object with categories as keys, each containing a list of techniques with explanations)
- priority_order (list of top 3 techniques to try first)
- notes (string with domain-specific guidance)
Data type: {dtype}"""
    raw = call_llm(system_prompt="You are a feature engineering expert.", user_prompt=prompt)
    return json.loads(raw)
