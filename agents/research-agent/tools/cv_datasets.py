import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.llm import call_llm
import json

def find_cv_datasets(query: str = "", topic: str = "", **kwargs) -> dict:
    topic_name = topic or query
    prompt = f"""Given the computer vision research topic, recommend relevant datasets. Return ONLY valid JSON with:
- domain (the CV subdomain)
- datasets (list of 3-6 dataset names with brief descriptions)
- suggested_use (string explaining which dataset fits which use case)
Topic: {topic_name}"""
    raw = call_llm(system_prompt="You are a computer vision datasets expert.", user_prompt=prompt)
    return json.loads(raw)
