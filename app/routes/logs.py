import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import re
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query
from shared.logging_setup import clear_logs, get_log_info

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOGS_DIR = os.path.join(ROOT, "logs")

logger = logging.getLogger("control-panel.logs")

router = APIRouter(tags=["logs"])

LOG_PATTERN = re.compile(
    r"^(\d{2}:\d{2}:\d{2})\s+(INFO|DEBUG|WARNING|ERROR|CRITICAL)\s+(.*)"
)

SERVICES = [
    "control-panel",
    "control-panel-err",
    "research-agent",
    "research-agent-err",
    "solution-agent",
    "solution-agent-err",
    "experiment-agent",
    "experiment-agent-err",
    "control-panel-app",
]


def _parse_log_file(filepath: str, service: str) -> list[dict]:
    entries = []
    if not os.path.exists(filepath):
        return entries
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.rstrip("\n")
                m = LOG_PATTERN.match(line)
                if m:
                    entries.append({
                        "time": m.group(1),
                        "level": m.group(2),
                        "message": m.group(3),
                        "service": service,
                    })
                elif line.strip():
                    entries.append({
                        "time": "",
                        "level": "INFO",
                        "message": line,
                        "service": service,
                    })
    except Exception:
        pass
    return entries


@router.get("/logs")
def get_logs(
    level: Optional[str] = Query(None, description="Filter by level: INFO,DEBUG,WARNING,ERROR,CRITICAL"),
    service: Optional[str] = Query(None, description="Filter by service name"),
    search: Optional[str] = Query(None, description="Search in message text"),
    limit: int = Query(500, ge=1, le=2000),
    offset: int = Query(0, ge=0),
):
    logger.info("GET /logs  level=%s  service=%s  search=%s  limit=%d  offset=%d", level, service, search, limit, offset)
    all_entries = []

    for svc in SERVICES:
        log_file = os.path.join(LOGS_DIR, f"{svc}.log")
        all_entries.extend(_parse_log_file(log_file, svc))

    if level:
        level_upper = level.upper()
        all_entries = [e for e in all_entries if e["level"] == level_upper]

    if service:
        svc_lower = service.lower()
        all_entries = [e for e in all_entries if svc_lower in e["service"].lower()]

    if search:
        search_lower = search.lower()
        all_entries = [e for e in all_entries if search_lower in e["message"].lower()]

    total = len(all_entries)
    all_entries = all_entries[offset : offset + limit]

    return {
        "entries": all_entries,
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.get("/logs/files")
def list_log_files():
    files = get_log_info(LOGS_DIR)
    return {"files": files}


@router.post("/logs/clear")
def clear_log_files(
    service: Optional[str] = Query(None, description="Clear only logs for this service (e.g. 'research-agent'). Clears all if omitted."),
):
    """Truncate log files to free disk space.

    Pass ?service=research-agent to clear only that service's logs,
    or omit to clear all log files.
    """
    if service:
        # Clear specific service logs
        cleared = 0
        for suffix in ["", "-err"]:
            path = os.path.join(LOGS_DIR, f"{service}{suffix}.log")
            if os.path.exists(path):
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.truncate(0)
                    cleared += 1
                    logger.info("Cleared log file: %s", path)
                except OSError as e:
                    logger.error("Failed to clear %s: %s", path, e)
        return {"cleared": cleared, "service": service}
    else:
        # Clear all log files
        count = clear_logs(LOGS_DIR, "*.log")
        logger.info("Cleared %d log file(s)", count)
        return {"cleared": count, "service": "all"}
