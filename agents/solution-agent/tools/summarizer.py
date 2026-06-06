import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.llm import call_llm
from shared.crossref import search_works, works_to_papers
import json, arxiv

def summarize_paper(query: str = "", text: str = "", **kwargs) -> dict:
    content = text or query
    if not text:
        papers = []
        try:
            cr_data = search_works(query=query, rows=3, select="DOI,title,author,abstract,published-print,published-online,issued,type,publisher,container-title")
            for p in works_to_papers(cr_data):
                papers.append({"title": p["title"], "abstract": p["abstract"][:500], "authors": p["authors"][:3], "doi": p["doi"], "source": "crossref"})
        except Exception:
            pass
        try:
            client = arxiv.Client()
            search = arxiv.Search(query=query, max_results=3, sort_by=arxiv.SortCriterion.Relevance)
            for p in client.results(search):
                papers.append({"title": p.title, "abstract": p.summary[:500], "authors": [str(a) for a in p.authors[:3]], "doi": p.doi or "", "source": "arxiv"})
        except Exception:
            pass
        if papers:
            content = json.dumps(papers)
        else:
            content = query
    prompt = f"""Summarize the following NLP research content. Return ONLY valid JSON with keys:
- summary (2-3 sentence overview)
- key_contributions (list of 3-5 specific contributions)
- limitations (list of 2-4 limitations)
Content: {content[:3000]}"""
    raw = call_llm(system_prompt="You are an NLP research paper summarization expert.", user_prompt=prompt)
    return json.loads(raw)
