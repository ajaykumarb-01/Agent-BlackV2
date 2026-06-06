import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.llm import call_llm
import json

def information_extraction(query: str = "", text: str = "", **kwargs) -> dict:
    content = text or query
    prompt = f"""Extract structured information from this text. Return ONLY valid JSON with:
- entities_detected (list of entities, each with type and value)
- key_concepts (list of 3-6 key concepts)
- relationships (list of entity-relation-entity triples)
- summary (string summarizing the extraction)
Text: {content[:3000]}"""
    raw = call_llm(system_prompt="You are an information extraction and NER expert.", user_prompt=prompt)
    return json.loads(raw)
