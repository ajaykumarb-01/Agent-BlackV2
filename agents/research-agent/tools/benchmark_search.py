import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.benchmarks import search_benchmarks


def benchmark_search_cv(query: str = "", task: str = "", max_results: int = 10, sources: list | None = None) -> dict:
    return search_benchmarks(query=query, task=task, max_results=max_results)
