import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.crossref import get_work_by_doi, search_works
import re

def citation_generator(query: str = "", title: str = "", doi: str = "", authors: str = "", year: int = 2024, venue: str = "", url: str = "", **kwargs) -> dict:
    title_text = title or query
    author_text = authors or "Author et al."
    year_text = str(year)
    venue_text = venue or "arXiv preprint"
    url_text = url or ""
    if doi:
        try:
            data = get_work_by_doi(doi)
            item = data if isinstance(data, dict) and "title" in data else data.get("message", data)
            if isinstance(item, dict) and item.get("title"):
                title_text = item.get("title", [title_text])[0] if isinstance(item.get("title"), list) else item.get("title", title_text)
                authors_list = item.get("author", [])
                if authors_list:
                    author_text = ", ".join(
                        f"{a.get('given', '')} {a.get('family', '')}".strip()
                        for a in authors_list[:5]
                        if a.get("family")
                    ) or author_text
                date_parts = (item.get("published-print") or item.get("published-online") or item.get("issued") or {}).get("date-parts", [[year]])
                if date_parts and date_parts[0] and date_parts[0][0]:
                    year_text = str(date_parts[0][0])
                container = item.get("container-title", [venue_text])[0] if isinstance(item.get("container-title"), list) else item.get("container-title", venue_text)
                venue_text = container or venue_text
                doi_str = item.get("DOI", doi)
                url_text = f"https://doi.org/{doi_str}"
        except Exception:
            pass
    elif query and not doi:
        try:
            cr_data = search_works(query_bibliographic=query, rows=1, select="DOI,title,author,published-print,published-online,issued,container-title")
            items = cr_data.get("items", [])
            if items:
                item = items[0]
                title_text = item.get("title", [title_text])[0] if isinstance(item.get("title"), list) else item.get("title", title_text)
                authors_list = item.get("author", [])
                if authors_list:
                    author_text = ", ".join(
                        f"{a.get('given', '')} {a.get('family', '')}".strip()
                        for a in authors_list[:5]
                        if a.get("family")
                    ) or author_text
                date_parts = (item.get("published-print") or item.get("published-online") or item.get("issued") or {}).get("date-parts", [[year]])
                if date_parts and date_parts[0] and date_parts[0][0]:
                    year_text = str(date_parts[0][0])
                container = item.get("container-title", [venue_text])[0] if isinstance(item.get("container-title"), list) else item.get("container-title", venue_text)
                venue_text = container or venue_text
                doi_str = item.get("DOI", "")
                if doi_str:
                    url_text = f"https://doi.org/{doi_str}"
        except Exception:
            pass
    def clean(s):
        return re.sub(r'[{}]', '', s).strip() if s else ""
    t = clean(title_text)
    a = clean(author_text)
    v = clean(venue_text)
    return {
        "bibtex": f"@article{{unknown{year_text},\n  title={{{t}}},\n  author={{{a}}},\n  year={{{year_text}}},\n  journal={{{v}}},\n  url={{{url_text}}}\n}}",
        "apa": f"{a} ({year_text}). {t}. {v}. {url_text}",
        "mla": f"{a.split(',')[0] if ',' in a else a}. \"{t}.\" {v} ({year_text}). {url_text}",
        "ieee": f"\"{t},\" {v}, {year_text}.",
    }
