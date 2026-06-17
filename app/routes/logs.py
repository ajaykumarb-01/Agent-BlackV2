import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import re
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOGS_DIR = os.path.join(ROOT, "logs")

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
    files = []
    for svc in SERVICES:
        log_file = os.path.join(LOGS_DIR, f"{svc}.log")
        size = 0
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
        files.append({"service": svc, "size_bytes": size})
    return {"files": files}
