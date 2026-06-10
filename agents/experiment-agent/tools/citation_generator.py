import arxiv
import re
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.crossref import get_work_by_doi, search_works
from shared.semantic_scholar import search_papers as ss_search


def _clean(s):
    return re.sub(r"[{}]", "", str(s or "").strip())


def _normalize_title(value) -> str:
    if isinstance(value, list):
        return value[0] if value else ""
    return value or ""


def _normalize_authors(value) -> str:
    authors = []
    for item in value or []:
        if isinstance(item, dict):
            name = f"{item.get('given', '')} {item.get('family', '')}".strip() or item.get("name", "")
        else:
            name = str(item)
        if name:
            authors.append(name)
    return ", ".join(authors[:5])


def _year_from_parts(parts) -> str:
    try:
        date_parts = (parts or {}).get("date-parts", [[None]])
        if date_parts and date_parts[0] and date_parts[0][0]:
            return str(date_parts[0][0])
    except Exception:
        pass
    return ""


def _bibtex_key(title: str, authors: str, year: str) -> str:
    family = ""
    if authors:
        first = authors.split(",")[0].strip().split()
        family = first[-1] if first else ""
    title_word = re.sub(r"[^A-Za-z0-9]+", "", (title or "unknown").split()[0][:12])
    year_short = (year or "unknown")[:4]
    return f"{family.lower()}{year_short}{title_word.lower() or 'paper'}"


def _format_citations(title: str, authors: str, year: str, venue: str, url: str, doi: str = "") -> dict:
    t = _clean(title)
    a = _clean(authors) or "Unknown"
    y = _clean(year) or "unknown"
    v = _clean(venue) or "Unknown venue"
    u = _clean(url)
    doi_url = _clean(doi)
    key = _bibtex_key(t, a, y)
    return {
        "bibtex": f"@article{{{key},\n  title={{{t}}},\n  author={{{a}}},\n  year={{{y}}},\n  journal={{{v}}},\n  doi={{{doi_url}}},\n  url={{{u}}}\n}}",
        "apa": f"{a} ({y}). {t}. {v}. {doi_url or u}".strip(),
        "mla": f"{a.split(',')[0] if ',' in a else a}. \"{t}.\" {v}, {y}. {doi_url or u}".strip(),
        "ieee": f"\"{t},\" {v}, {y}. {doi_url or u}".strip(),
    }


def _crossref_item(doi: str = "", query: str = "", title: str = "") -> tuple:
    if doi:
        data = get_work_by_doi(doi)
        item = data if isinstance(data, dict) and "title" in data else data.get("message", data)
    else:
        cr_data = search_works(query_bibliographic=title or query, rows=1, select="DOI,title,author,published-print,published-online,issued,container-title,publisher")
        items = cr_data.get("items", [])
        item = items[0] if items else {}
    if not isinstance(item, dict):
        return {}, "crossref"
    title_text = _normalize_title(item.get("title"))
    authors = _normalize_authors(item.get("author"))
    year = _year_from_parts(item.get("published-print") or item.get("published-online") or item.get("issued") or {})
    venue = item.get("container-title") or item.get("publisher") or ""
    venue = _normalize_title(venue)
    doi_text = item.get("DOI") or doi or ""
    url = f"https://doi.org/{doi_text}" if doi_text else item.get("URL") or ""
    return {
        "title": title_text,
        "authors": authors,
        "year": year,
        "venue": venue,
        "url": url,
        "doi": doi_text,
        "source": "crossref",
    }, "crossref"


def _semantic_scholar_item(query: str = "", title: str = "", max_results: int = 5) -> tuple:
    data = ss_search(query=title or query, limit=max_results, fields="title,authors,year,venue,externalIds,url,publicationTypes")
    papers = data.get("data", [])
    for paper in papers:
        ext_ids = paper.get("externalIds") or {}
        return {
            "title": paper.get("title", ""),
            "authors": ", ".join(a.get("name", "Unknown") for a in paper.get("authors", [])[:5]),
            "year": str(paper.get("year") or ""),
            "venue": paper.get("venue", ""),
            "url": paper.get("url", ""),
            "doi": ext_ids.get("DOI", ""),
            "arxiv_id": ext_ids.get("ArXiv", ""),
            "source": "semantic_scholar",
        }, "semantic_scholar"
    return {}, "semantic_scholar"


def _arxiv_item(arxiv_id: str = "", query: str = "", title: str = "", max_results: int = 5) -> tuple:
    client = arxiv.Client()
    search_query = arxiv_id or title or query
    search = arxiv.Search(query=search_query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance)
    for paper in client.results(search):
        return {
            "title": paper.title,
            "authors": ", ".join(str(a) for a in paper.authors[:5]),
            "year": str(paper.published.year) if getattr(paper, "published", None) else "",
            "venue": "arXiv preprint",
            "url": paper.entry_id,
            "doi": paper.doi or "",
            "arxiv_id": paper.get_short_id(),
            "source": "arxiv",
        }, "arxiv"
    return {}, "arxiv"


def citation_generator(
    query: str = "",
    title: str = "",
    doi: str = "",
    authors: str = "",
    year: int | str | None = None,
    venue: str = "",
    url: str = "",
    arxiv_id: str = "",
    source: str = "auto",
    max_results: int = 5,
) -> dict:
    max_results = max(1, min(int(max_results or 5), 20))
    selected_source = source or "auto"
    errors = []
    matched = {}

    try:
        if selected_source in ("auto", "crossref") and (doi or title or query):
            matched, matched_source = _crossref_item(doi=doi, query=query, title=title)
            if matched:
                selected_source = matched_source
    except Exception as exc:
        errors.append({"source": "crossref", "error": str(exc)})

    if not matched and selected_source in ("auto", "semantic_scholar") and (title or query):
        try:
            matched, matched_source = _semantic_scholar_item(query=query, title=title, max_results=max_results)
            if matched:
                selected_source = matched_source
        except Exception as exc:
            errors.append({"source": "semantic_scholar", "error": str(exc)})

    if not matched and selected_source in ("auto", "arxiv") and (arxiv_id or title or query):
        try:
            matched, matched_source = _arxiv_item(arxiv_id=arxiv_id, query=query, title=title, max_results=max_results)
            if matched:
                selected_source = matched_source
        except Exception as exc:
            errors.append({"source": "arxiv", "error": str(exc)})

    title_text = title or matched.get("title") or query or "Unknown title"
    author_text = authors or matched.get("authors") or "Unknown"
    year_text = str(year or matched.get("year") or "")
    venue_text = venue or matched.get("venue") or "Unknown venue"
    url_text = url or matched.get("url") or ""
    doi_text = doi or matched.get("doi") or ""
    arxiv_text = arxiv_id or matched.get("arxiv_id") or ""
    if arxiv_text and not url_text:
        url_text = f"https://arxiv.org/abs/{arxiv_text}"
    if doi_text and not url_text:
        url_text = f"https://doi.org/{doi_text}"

    citations = _format_citations(title_text, author_text, year_text, venue_text, url_text, doi_text)
    return {
        "citation": citations,
        "matched": matched,
        "source": selected_source,
        "errors": errors,
    }
