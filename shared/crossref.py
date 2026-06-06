import requests
from typing import Optional

BASE_URL = "https://api.crossref.org"
HEADERS = {"User-Agent": "Agent-Black/1.0 (mailto:example@example.com)"}


def _get(path: str, params: Optional[dict] = None) -> dict:
    url = f"{BASE_URL}{path}"
    resp = requests.get(url, headers=HEADERS, params=params or {}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("message", data)


def search_works(
    query: str = "",
    query_bibliographic: str = "",
    filter: Optional[dict] = None,
    rows: int = 10,
    offset: Optional[int] = None,
    cursor: Optional[str] = None,
    sort: str = "relevance",
    order: str = "desc",
    select: Optional[str] = None,
    facet: Optional[str] = None,
) -> dict:
    params = {"rows": rows, "sort": sort, "order": order}
    if query:
        params["query"] = query
    if query_bibliographic:
        params["query.bibliographic"] = query_bibliographic
    if filter:
        params["filter"] = ",".join(f"{k}:{v}" for k, v in filter.items())
    if offset is not None:
        params["offset"] = offset
    if cursor:
        params["cursor"] = cursor
    if select:
        params["select"] = select
    if facet:
        params["facet"] = facet
    return _get("/works", params)


def get_work_by_doi(doi: str) -> dict:
    return _get(f"/works/{doi}")


def search_journals(
    query: str = "",
    rows: int = 10,
    cursor: Optional[str] = None,
) -> dict:
    params = {"rows": rows}
    if query:
        params["query"] = query
    if cursor:
        params["cursor"] = cursor
    return _get("/journals", params)


def get_journal_by_issn(issn: str) -> dict:
    return _get(f"/journals/{issn}")


def get_journal_works(
    issn: str,
    query: str = "",
    rows: int = 10,
    cursor: Optional[str] = None,
) -> dict:
    params = {"rows": rows}
    if query:
        params["query"] = query
    if cursor:
        params["cursor"] = cursor
    return _get(f"/journals/{issn}/works", params)


def search_funders(
    query: str = "",
    rows: int = 10,
    cursor: Optional[str] = None,
) -> dict:
    params = {"rows": rows}
    if query:
        params["query"] = query
    if cursor:
        params["cursor"] = cursor
    return _get("/funders", params)


def get_funder_by_id(funder_id: str) -> dict:
    return _get(f"/funders/{funder_id}")


def get_funder_works(
    funder_id: str,
    query: str = "",
    rows: int = 10,
    cursor: Optional[str] = None,
) -> dict:
    params = {"rows": rows}
    if query:
        params["query"] = query
    if cursor:
        params["cursor"] = cursor
    return _get(f"/funders/{funder_id}/works", params)


def search_members(
    query: str = "",
    rows: int = 10,
    cursor: Optional[str] = None,
) -> dict:
    params = {"rows": rows}
    if query:
        params["query"] = query
    if cursor:
        params["cursor"] = cursor
    return _get("/members", params)


def get_member_by_id(member_id: str) -> dict:
    return _get(f"/members/{member_id}")


def get_member_works(
    member_id: str,
    query: str = "",
    rows: int = 10,
    cursor: Optional[str] = None,
) -> dict:
    params = {"rows": rows}
    if query:
        params["query"] = query
    if cursor:
        params["cursor"] = cursor
    return _get(f"/members/{member_id}/works", params)


def search_prefixes(
    prefix: str = "",
    query: str = "",
    rows: int = 10,
) -> dict:
    params = {"rows": rows}
    if query:
        params["query"] = query
    return _get(f"/prefixes/{prefix}", params)


def get_prefix_works(
    prefix: str,
    query: str = "",
    rows: int = 10,
    cursor: Optional[str] = None,
) -> dict:
    params = {"rows": rows}
    if query:
        params["query"] = query
    if cursor:
        params["cursor"] = cursor
    return _get(f"/prefixes/{prefix}/works", params)


def list_types(rows: int = 20) -> dict:
    return _get("/types", {"rows": rows})


def get_type_by_id(type_id: str) -> dict:
    return _get(f"/types/{type_id}")


def get_type_works(
    type_id: str,
    query: str = "",
    rows: int = 10,
    cursor: Optional[str] = None,
) -> dict:
    params = {"rows": rows}
    if query:
        params["query"] = query
    if cursor:
        params["cursor"] = cursor
    return _get(f"/types/{type_id}/works", params)


def list_licenses(rows: int = 20) -> dict:
    return _get("/licenses", {"rows": rows})


def get_work_agency(doi: str) -> dict:
    return _get(f"/works/{doi}/agency")


def works_to_papers(data: dict) -> list:
    items = data.get("items", [])
    results = []
    for item in items:
        authors = []
        for a in item.get("author", []):
            given = a.get("given", "")
            family = a.get("family", "")
            name = f"{given} {family}".strip() or a.get("name", "Unknown")
            authors.append(name)
        results.append({
            "title": item.get("title", [""])[0] if item.get("title") else "",
            "authors": authors[:5],
            "year": (item.get("published-print", {}) or item.get("published-online", {}) or item.get("issued", {}) or {}).get("date-parts", [[None]])[0][0],
            "abstract": (item.get("abstract", "") or "")[:500],
            "doi": item.get("DOI", ""),
            "url": f"https://doi.org/{item['DOI']}" if item.get("DOI") else "",
            "type": item.get("type", ""),
            "publisher": item.get("publisher", ""),
            "container": (item.get("container-title", [""])[0] if item.get("container-title") else ""),
            "source": "crossref",
        })
    return results
