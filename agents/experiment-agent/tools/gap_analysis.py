import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.llm import call_llm
import json

def analyze_gaps(query: str = "", papers: list = None, **kwargs) -> dict:
    prompt = f"""Analyze the ML research query and identify research gaps. Return ONLY valid JSON with:
- existing_approaches (list of 3-5 current approaches)
- gaps (list of 3-5 specific gaps/limitations)
- recommended_focus (string with future direction)
Query: {query}
Papers context: {json.dumps(papers) if papers else 'None provided'}"""
    raw = call_llm(system_prompt="You are an ML research gap analysis expert.", user_prompt=prompt)
    return json.loads(raw)
