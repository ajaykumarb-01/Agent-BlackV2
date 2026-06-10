import requests
from urllib.parse import quote

HF_DATASETS_URL = "https://huggingface.co/api/datasets"
KAGGLE_DATASETS_URL = "https://www.kaggle.com/api/v1/datasets/list"
PWC_DATASETS_URL = "https://paperswithcode.com/api/v1/datasets/"

HEADERS = {"User-Agent": "Agent-Black/1.0"}


def _safe_get_json(url: str, params: dict | None = None, timeout: int = 30) -> dict | list:
    resp = requests.get(url, headers=HEADERS, params=params or {}, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _as_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _search_terms(query: str = "", topic: str = "", domain: str = "", task: str = "") -> str:
    return " ".join(part for part in [query, topic, domain, task] if part and part.strip())


def _normalize_hf_dataset(item: dict) -> dict:
    dataset_id = item.get("id") or item.get("datasetId") or item.get("slug") or ""
    url = f"https://huggingface.co/datasets/{dataset_id}" if dataset_id else ""
    card_data = item.get("cardData") or {}
    tags = _as_list(item.get("tags"))
    papers_with_code = item.get("paperswithcode") or {}
    return {
        "id": dataset_id,
        "name": card_data.get("pretty_name") or item.get("title") or dataset_id,
        "description": item.get("description") or card_data.get("task_categories") or "",
        "domain": "",
        "task": ", ".join(_as_list(card_data.get("task_categories"))),
        "license": card_data.get("license") or "",
        "tags": tags,
        "downloads": item.get("downloads") or item.get("downloadsAllTime"),
        "likes": item.get("likes"),
        "papers_with_code_id": papers_with_code.get("id") or papers_with_code.get("slug") or "",
        "url": url,
        "source": "huggingface",
    }


def _normalize_kaggle_dataset(item: dict) -> dict:
    ref = item.get("ref") or item.get("url") or item.get("id") or ""
    title = item.get("title") or ref
    url = item.get("url") or f"https://www.kaggle.com/datasets/{ref}" if ref else ""
    return {
        "id": ref,
        "name": title,
        "description": item.get("subtitle") or item.get("description") or "",
        "domain": "",
        "task": "",
        "license": item.get("licenseName") or "",
        "tags": _as_list(item.get("tags")) or _as_list(item.get("topic")),
        "downloads": item.get("totalDownloads"),
        "likes": item.get("totalVotes"),
        "papers_with_code_id": "",
        "url": url,
        "source": "kaggle",
    }


def _normalize_pwc_dataset(item: dict) -> dict:
    slug = item.get("slug") or item.get("id") or ""
    name = item.get("name") or item.get("title") or slug
    return {
        "id": slug,
        "name": name,
        "description": item.get("description") or item.get("abstract") or "",
        "domain": "",
        "task": item.get("task") or "",
        "license": "",
        "tags": _as_list(item.get("tags")),
        "downloads": None,
        "likes": None,
        "papers_with_code_id": slug,
        "url": item.get("url") or f"https://paperswithcode.com/dataset/{quote(slug)}" if slug else "",
        "source": "paperswithcode",
    }


def search_huggingface_datasets(query: str = "", max_results: int = 10, domain: str = "", task: str = "") -> dict:
    search = _search_terms(query=query, domain=domain, task=task)
    params = {"search": search, "limit": max_results}
    filters = []
    if domain:
        filters.append(f"domain:{domain}")
    if task:
        filters.append(f"task_categories:{task}")
    if filters:
        params["filter"] = filters
    data = _safe_get_json(HF_DATASETS_URL, params=params)
    datasets = [_normalize_hf_dataset(item) for item in _as_list(data)[:max_results]]
    return {"source": "huggingface", "datasets": datasets, "count": len(datasets)}


def search_kaggle_datasets(query: str = "", max_results: int = 10) -> dict:
    search = _search_terms(query=query)
    data = _safe_get_json(
        KAGGLE_DATASETS_URL,
        params={"search": search, "sortBy": "relevance", "group": "public", "size": max_results, "page": 1},
    )
    datasets = [_normalize_kaggle_dataset(item) for item in _as_list(data)[:max_results]]
    return {"source": "kaggle", "datasets": datasets, "count": len(datasets)}


def search_paperswithcode_datasets(query: str = "", max_results: int = 10) -> dict:
    search = _search_terms(query=query)
    data = _safe_get_json(PWC_DATASETS_URL, params={"search": search, "page_size": max_results})
    results = data.get("results", _as_list(data)) if isinstance(data, dict) else _as_list(data)
    datasets = [_normalize_pwc_dataset(item) for item in results[:max_results]]
    return {"source": "paperswithcode", "datasets": datasets, "count": len(datasets)}


def _dedupe_datasets(datasets: list) -> list:
    seen = set()
    output = []
    for item in datasets:
        key = item.get("id") or item.get("url") or item.get("name") or ""
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def search_datasets(
    query: str = "",
    topic: str = "",
    domain: str = "",
    task: str = "",
    max_results: int = 10,
    sources: list | None = None,
) -> dict:
    max_results = max(1, min(int(max_results or 10), 50))
    selected_sources = sources or ["huggingface", "kaggle", "paperswithcode"]
    search = _search_terms(query=query, topic=topic, domain=domain, task=task)
    datasets = []
    errors = []
    source_counts = {}

    if "huggingface" in selected_sources:
        try:
            result = search_huggingface_datasets(query=search, max_results=max_results, domain=domain, task=task)
            datasets.extend(result["datasets"])
            source_counts["huggingface"] = result["count"]
        except Exception as exc:
            errors.append({"source": "huggingface", "error": str(exc)})

    if "kaggle" in selected_sources:
        try:
            result = search_kaggle_datasets(query=search, max_results=max_results)
            datasets.extend(result["datasets"])
            source_counts["kaggle"] = result["count"]
        except Exception as exc:
            errors.append({"source": "kaggle", "error": str(exc)})

    if "paperswithcode" in selected_sources:
        try:
            result = search_paperswithcode_datasets(query=search, max_results=max_results)
            datasets.extend(result["datasets"])
            source_counts["paperswithcode"] = result["count"]
        except Exception as exc:
            errors.append({"source": "paperswithcode", "error": str(exc)})

    deduped = _dedupe_datasets(datasets)
    return {
        "query": search,
        "domain": domain,
        "task": task,
        "max_results": max_results,
        "sources": selected_sources,
        "source_counts": source_counts,
        "datasets": deduped[:max_results],
        "errors": errors,
    }
