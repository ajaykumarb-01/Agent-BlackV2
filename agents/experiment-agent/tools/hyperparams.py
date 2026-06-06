import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.llm import call_llm
import json

def hyperparameter_advice(query: str = "", model_type: str = "", **kwargs) -> dict:
    model_name = model_type or query
    prompt = f"""Recommend hyperparameter tuning strategies for this model type. Return ONLY valid JSON with:
- model_type (the model type)
- learning_rate (string with range and schedule recommendation)
- batch_size (string with recommended range)
- optimizer (string with optimizer name and key params)
- scheduler (string with learning rate scheduler recommendation)
- regularization (string with dropout, weight decay, etc.)
- epochs (string with training duration guidance)
Model type: {model_name}"""
    raw = call_llm(system_prompt="You are a hyperparameter optimization expert.", user_prompt=prompt)
    return json.loads(raw)
