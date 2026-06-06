import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.llm import call_llm
import json

def rag_design(query: str = "", problem: str = "", **kwargs) -> dict:
    problem_name = problem or query
    prompt = f"""Design a RAG architecture for this problem. Return ONLY valid JSON with:
- problem (the problem description)
- chunking_strategy (string with recommended chunking approach)
- embedding_model (string with recommended embedding model)
- vector_database (string with recommended vector DB)
- retrieval_strategy (string with retrieval approach)
- generation_pipeline (string describing the full pipeline)
- recommended_architecture (string with architecture overview)
Problem: {problem_name}"""
    raw = call_llm(system_prompt="You are a RAG architecture design expert.", user_prompt=prompt)
    return json.loads(raw)
