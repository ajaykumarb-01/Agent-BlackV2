import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.datasets import search_datasets


def find_nlp_datasets(
    query: str = "",
    topic: str = "",
    domain: str = "nlp",
    task: str = "",
    max_results: int = 10,
    sources: list | None = None,
) -> dict:
    return search_datasets(query=query, topic=topic, domain=domain, task=task, max_results=max_results, sources=sources)
