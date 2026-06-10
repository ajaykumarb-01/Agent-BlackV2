import requests
from urllib.parse import quote

PWC_BASE_URL = "https://paperswithcode.com/api/v1"

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


def _clean(value) -> str:
    return str(value or "").strip()


def _normalize_task(item: dict) -> dict:
    slug = item.get("slug") or item.get("id") or ""
    return {
        "id": slug,
        "name": item.get("name") or item.get("title") or slug,
        "description": item.get("description") or "",
        "url": item.get("url") or (f"https://paperswithcode.com/task/{quote(slug)}" if slug else ""),
        "source": "paperswithcode",
    }


def _extract_score(item: dict) -> tuple:
    for key in ("score", "metric_value", "value"):
        value = item.get(key)
        if isinstance(value, (int, float)):
            return value, key
    metric = item.get("metric") or {}
    if isinstance(metric, dict):
        for key in ("score", "value"):
            value = metric.get(key)
            if isinstance(value, (int, float)):
                return value, f"metric.{key}"
    return None, ""


def _normalize_benchmark(item: dict, task: str = "") -> dict:
    score, score_key = _extract_score(item)
    dataset = item.get("dataset") or item.get("dataset_name") or item.get("dataset_slug") or ""
    if isinstance(dataset, dict):
        dataset_name = dataset.get("name") or dataset.get("title") or dataset.get("slug") or ""
        dataset_url = dataset.get("url") or ""
        dataset_id = dataset.get("slug") or dataset.get("id") or ""
    else:
        dataset_name = _clean(dataset)
        dataset_id = dataset_name
        dataset_url = f"https://paperswithcode.com/dataset/{quote(dataset_id)}" if dataset_id else ""
    method = item.get("method") or item.get("model") or item.get("model_name") or item.get("paper") or ""
    if isinstance(method, dict):
        model_name = method.get("name") or method.get("title") or method.get("slug") or ""
        model_url = method.get("url") or ""
        method_id = method.get("slug") or method.get("id") or ""
    else:
        model_name = _clean(method)
        method_id = model_name
        model_url = ""
    metric = item.get("metric") or item.get("metric_name") or item.get("evaluation_metric") or ""
    if isinstance(metric, dict):
        metric_name = metric.get("name") or metric.get("title") or metric.get("slug") or ""
        metric_url = metric.get("url") or ""
        metric_id = metric.get("slug") or metric.get("id") or ""
    else:
        metric_name = _clean(metric)
        metric_id = metric_name
        metric_url = ""
    return {
        "id": item.get("id") or item.get("slug") or f"{task}:{dataset_id}:{metric_id}:{method_id}",
        "task": task or item.get("task") or "",
        "dataset": dataset_name,
        "dataset_id": dataset_id,
        "dataset_url": dataset_url,
        "metric": metric_name,
        "metric_id": metric_id,
        "metric_url": metric_url,
        "model_name": model_name,
        "model_id": method_id,
        "model_url": model_url,
        "sota_score": score,
        "score_key": score_key,
        "score_provided_by_api": score is not None,
        "url": item.get("url") or model_url or metric_url or "",
        "source": "paperswithcode",
        "raw": item,
    }


def search_tasks(query: str = "", max_results: int = 10) -> dict:
    data = _safe_get_json(f"{PWC_BASE_URL}/tasks/", params={"search": query, "page_size": max_results})
    results = data.get("results", _as_list(data)) if isinstance(data, dict) else _as_list(data)
    tasks = [_normalize_task(item) for item in results[:max_results]]
    return {"tasks": tasks, "count": len(tasks)}


def get_task(task_slug: str) -> dict:
    return _safe_get_json(f"{PWC_BASE_URL}/tasks/{quote(task_slug)}/")


def search_benchmarks(query: str = "", task: str = "", max_results: int = 10) -> dict:
    max_results = max(1, min(int(max_results or 10), 50))
    task_name = task or query
    benchmarks = []
    errors = []
    source_counts = {"tasks": 0, "task_details": 0, "state_of_the_art": 0}

    try:
        task_result = search_tasks(query=task_name, max_results=max_results)
        tasks = task_result["tasks"]
        source_counts["tasks"] = len(tasks)
        if tasks:
            task_slug = tasks[0]["id"]
            try:
                detail = get_task(task_slug)
                source_counts["task_details"] = 1
                for key in ("benchmarks", "leaderboards", "results", "papers"):
                    for item in _as_list(detail.get(key)):
                        benchmarks.append(_normalize_benchmark(item, task=task_slug))
            except Exception as exc:
                errors.append({"source": "paperswithcode.task_detail", "error": str(exc)})
    except Exception as exc:
        errors.append({"source": "paperswithcode.tasks", "error": str(exc)})

    try:
        data = _safe_get_json(
            f"{PWC_BASE_URL}/state-of-the-art/",
            params={"q": task_name, "page_size": max_results},
        )
        results = data.get("results", _as_list(data)) if isinstance(data, dict) else _as_list(data)
        for item in results[:max_results]:
            benchmarks.append(_normalize_benchmark(item, task=task_name))
        source_counts["state_of_the_art"] = len(results)
    except Exception as exc:
        errors.append({"source": "paperswithcode.state_of_the_art", "error": str(exc)})

    seen = set()
    deduped = []
    for item in benchmarks:
        key = item.get("id")
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return {
        "query": task_name,
        "max_results": max_results,
        "sources": ["paperswithcode"],
        "source_counts": source_counts,
        "benchmarks": deduped[:max_results],
        "errors": errors,
        "score_policy": "Scores are included only when returned by Papers With Code APIs; otherwise sota_score is null.",
    }
