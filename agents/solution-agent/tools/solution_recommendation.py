import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.llm import call_llm
import json

def solution_recommendation(query: str = "", problem: str = "", **kwargs) -> dict:
    problem_name = problem or query
    prompt = f"""Given this NLP research problem, recommend practical solutions. Return ONLY valid JSON with:
- problem (the problem statement)
- recommended_approaches (list of 2-4 solution approaches with methodology)
- implementation_roadmap (list of 3-5 steps to implement)
- tools_and_libraries (list of recommended frameworks with versions)
- expected_outcomes (string describing expected results)
Problem: {problem_name}"""
    raw = call_llm(system_prompt="You are an NLP solution architect.", user_prompt=prompt)
    return json.loads(raw)
