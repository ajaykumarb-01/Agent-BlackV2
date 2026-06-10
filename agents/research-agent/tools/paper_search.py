import arxiv
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.crossref import search_works, works_to_papers
from shared.semantic_scholar import search_papers as ss_search, results_to_papers as ss_to_papers


def _dedupe_papers(papers: list) -> list:
    seen = set()
    output = []
    for paper in papers:
        key = paper.get("doi") or paper.get("arxiv_id") or paper.get("url") or paper.get("title", "").lower()
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(paper)
    return output


def search_papers(query: str = "", max_results: int = 10, year: str = "", domain: str = "", source: str = "all") -> dict:
    max_results = max(1, min(int(max_results or 10), 50))
    selected_sources = source if isinstance(source, list) else [s.strip() for s in (source or "all").split(",") if s.strip()]
    if not selected_sources or "all" in selected_sources:
        selected_sources = ["crossref", "semantic_scholar", "arxiv"]
    results = []
    errors = []
    source_counts = {name: 0 for name in selected_sources}

    if "crossref" in selected_sources:
        try:
            cr_data = search_works(
                query=query,
                rows=max_results,
                select="DOI,title,author,abstract,published-print,published-online,issued,type,publisher,container-title",
            )
            papers = works_to_papers(cr_data)
            results.extend(papers)
            source_counts["crossref"] = len(papers)
        except Exception as exc:
            errors.append({"source": "crossref", "error": str(exc)})

    if "semantic_scholar" in selected_sources:
        try:
            ss_data = ss_search(query=query, limit=max_results, year=year or None)
            papers = ss_to_papers(ss_data)
            results.extend(papers)
            source_counts["semantic_scholar"] = len(papers)
        except Exception as exc:
            errors.append({"source": "semantic_scholar", "error": str(exc)})

    if "arxiv" in selected_sources:
        try:
            client = arxiv.Client()
            search_query = f"{query} {domain}".strip()
            search = arxiv.Search(query=search_query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance)
            papers = []
            for paper in client.results(search):
                arxiv_id = paper.get_short_id()
                papers.append({
                    "title": paper.title,
                    "authors": [str(a) for a in paper.authors],
                    "year": paper.published.year if getattr(paper, "published", None) else None,
                    "abstract": paper.summary[:500],
                    "doi": paper.doi or "",
                    "arxiv_id": arxiv_id,
                    "url": paper.entry_id,
                    "type": "arxiv",
                    "publisher": "arXiv",
                    "container": "",
                    "source": "arxiv",
                })
            results.extend(papers)
            source_counts["arxiv"] = len(papers)
        except Exception as exc:
            errors.append({"source": "arxiv", "error": str(exc)})

    deduped = _dedupe_papers(results)
    return {
        "query": query,
        "domain": domain,
        "year": year,
        "max_results": max_results,
        "sources": selected_sources,
        "source_counts": source_counts,
        "results": deduped[:max_results],
        "errors": errors,
    }
