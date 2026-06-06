import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.llm import call_llm
import json

def synthetic_data_strategy(query: str = "", domain: str = "", **kwargs) -> dict:
    domain_name = domain or query
    prompt = f"""Recommend synthetic data and augmentation strategies for this CV domain. Return ONLY valid JSON with:
- domain (the CV subdomain)
- techniques (list of 3-5 specific augmentation/synthetic data techniques)
- tools (list of 2-4 recommended libraries)
- recommendation (string with the best starting strategy)
Domain: {domain_name}"""
    raw = call_llm(system_prompt="You are a computer vision data augmentation and synthetic data expert.", user_prompt=prompt)
    return json.loads(raw)
