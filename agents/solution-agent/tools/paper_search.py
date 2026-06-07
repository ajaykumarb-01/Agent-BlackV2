import arxiv
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.crossref import search_works, works_to_papers
from shared.semantic_scholar import search_papers as ss_search, results_to_papers as ss_to_papers

def search_papers(query: str, max_results: int = 10, **kwargs) -> list:
    results = []
    seen_dois = set()

    try:
        cr_data = search_works(query=query, rows=max_results, select="DOI,title,author,abstract,published-print,published-online,issued,type,publisher,container-title")
        for paper in works_to_papers(cr_data):
            doi = paper.get("doi", "")
            if doi:
                seen_dois.add(doi)
            results.append(paper)
    except Exception:
        pass

    try:
        ss_data = ss_search(query=query, limit=max_results)
        for paper in ss_to_papers(ss_data):
            doi = paper.get("doi", "")
            if doi and doi in seen_dois:
                continue
            if doi:
                seen_dois.add(doi)
            results.append(paper)
    except Exception:
        pass

    try:
        client = arxiv.Client()
        search = arxiv.Search(query=query, max_results=max_results,
                              sort_by=arxiv.SortCriterion.Relevance)
        for paper in client.results(search):
            doi = paper.doi or ""
            if doi and doi in seen_dois:
                continue
            if doi:
                seen_dois.add(doi)
            results.append({
                "title": paper.title,
                "authors": [str(a) for a in paper.authors],
                "year": paper.published.year,
                "abstract": paper.summary[:500],
                "doi": doi,
                "url": paper.entry_id,
                "type": "arxiv",
                "publisher": "arXiv",
                "container": "",
                "source": "arxiv",
            })
    except Exception:
        pass

    return results[:max_results]
