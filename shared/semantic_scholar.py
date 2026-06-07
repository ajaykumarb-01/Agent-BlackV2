import requests
from typing import Optional

BASE_URL = "https://api.semanticscholar.org/graph/v1"
HEADERS = {"User-Agent": "Agent-Black/1.0"}

def search_papers(
    query: str,
    limit: int = 10,
    offset: int = 0,
    year: Optional[str] = None,
    fields: str = "title,authors,year,abstract,externalIds,url,venue,publicationTypes",
) -> dict:
    params = {
        "query": query,
        "limit": limit,
        "offset": offset,
        "fields": fields,
    }
    if year:
        params["year"] = year
    resp = requests.get(
        f"{BASE_URL}/paper/search",
        headers=HEADERS,
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def get_paper(paper_id: str, fields: str = "title,authors,year,abstract,externalIds,url,venue") -> dict:
    resp = requests.get(
        f"{BASE_URL}/paper/{paper_id}",
        headers=HEADERS,
        params={"fields": fields},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def results_to_papers(data: dict) -> list:
    papers = data.get("data", [])
    results = []
    for paper in papers:
        authors = [a.get("name", "Unknown") for a in paper.get("authors", [])]
        ext_ids = paper.get("externalIds", {}) or {}
        doi = ext_ids.get("DOI", "")
        arxiv_id = ext_ids.get("ArXiv", "")
        url = paper.get("url", "")
        if not url and arxiv_id:
            url = f"https://arxiv.org/abs/{arxiv_id}"
        elif not url and doi:
            url = f"https://doi.org/{doi}"
        results.append({
            "title": paper.get("title", ""),
            "authors": authors[:5],
            "year": paper.get("year"),
            "abstract": (paper.get("abstract", "") or "")[:500],
            "doi": doi,
            "url": url,
            "type": paper.get("publicationTypes", [""])[0] if paper.get("publicationTypes") else "",
            "publisher": "",
            "container": paper.get("venue", ""),
            "source": "semantic_scholar",
        })
    return results
