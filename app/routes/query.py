import sys
import os
import json
import asyncio
import uuid
import re
from datetime import datetime, timezone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse
from app.models import QueryRequest, ReportPdfRequest
from app.routes.diagram import generate_agent_flow_diagram
from app.database import (
    get_query_history, get_db,
    async_create_task, async_update_task_result, async_update_task_error,
    async_save_task_event, async_get_task, async_get_task_events, async_save_query,
)

router = APIRouter(tags=["query"])

REPORT_SECTION_TITLES = {
    "literature_review": "Literature Review",
    "datasets": "Datasets",
    "models": "Models",
    "evaluation_plan": "Evaluation Plan",
    "prototype_guidance": "Prototype Guidance",
}


def _format_label(value: str) -> str:
    return value.replace("_", " ").strip().title()


def _stringify_value(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    try:
        return json.dumps(value, indent=2, ensure_ascii=True)
    except Exception:
        return str(value)


def _append_report_lines(lines: list[str], value, indent: int = 0, label: str | None = None):
    prefix = "  " * indent

    if label:
        heading = f"{prefix}{label}:"
        if isinstance(value, (dict, list)):
            lines.append(heading)
        else:
            text = _stringify_value(value)
            if text:
                for idx, part in enumerate(text.splitlines() or [text]):
                    if idx == 0:
                        lines.append(f"{heading} {part}".rstrip())
                    else:
                        lines.append(f"{prefix}  {part}".rstrip())
            else:
                lines.append(heading)
            return

    if isinstance(value, dict):
        for key, nested in value.items():
            _append_report_lines(lines, nested, indent + (1 if label else 0), _format_label(str(key)))
        return

    if isinstance(value, list):
        if not value:
            lines.append(f"{prefix}- None")
            return
        child_indent = indent + (1 if label else 0)
        child_prefix = "  " * child_indent
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{child_prefix}-")
                _append_report_lines(lines, item, child_indent + 1)
            else:
                text = _stringify_value(item)
                item_lines = text.splitlines() or [text]
                for idx, part in enumerate(item_lines):
                    bullet = "- " if idx == 0 else "  "
                    lines.append(f"{child_prefix}{bullet}{part}".rstrip())
        return

    text = _stringify_value(value)
    for part in text.splitlines() or [text]:
        if part:
            lines.append(f"{prefix}{part}".rstrip())


def _wrap_pdf_line(text: str, max_chars: int = 92) -> list[str]:
    stripped = text.rstrip()
    if not stripped:
        return [""]

    indent = len(stripped) - len(stripped.lstrip(" "))
    words = stripped.strip().split()
    if not words:
        return [""]

    wrapped: list[str] = []
    current = " " * indent
    for word in words:
        candidate = f"{current} {word}".rstrip() if current.strip() else f"{' ' * indent}{word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            wrapped.append(current.rstrip())
            current = f"{' ' * indent}{word}"
    if current:
        wrapped.append(current.rstrip())
    return wrapped


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_pdf(report_title: str, lines: list[str]) -> bytes:
    page_width = 612
    page_height = 792
    left_margin = 54
    top_margin = 64
    bottom_margin = 54
    line_height = 15
    title_font_size = 18
    body_font_size = 10

    pages: list[list[str]] = []
    current_page: list[str] = []
    y = page_height - top_margin

    def start_page():
        nonlocal current_page, y
        current_page = []
        y = page_height - top_margin

    def flush_page():
        if current_page:
            pages.append(current_page.copy())

    start_page()
    current_page.append(f"BT /F1 {title_font_size} Tf 1 0 0 1 {left_margin} {y} Tm ({_escape_pdf_text(report_title)}) Tj ET")
    y -= 28

    for line in lines:
        for wrapped in _wrap_pdf_line(line):
            if y <= bottom_margin:
                flush_page()
                start_page()
            safe = _escape_pdf_text(wrapped)
            current_page.append(f"BT /F1 {body_font_size} Tf 1 0 0 1 {left_margin} {y} Tm ({safe}) Tj ET")
            y -= line_height

    flush_page()

    objects: list[bytes] = []

    def add_object(data: str | bytes) -> int:
        payload = data.encode("latin-1") if isinstance(data, str) else data
        objects.append(payload)
        return len(objects)

    font_obj = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_obj_ids: list[int] = []
    content_obj_ids: list[int] = []

    for commands in pages:
        stream = "\n".join(commands).encode("latin-1", errors="replace")
        content_obj_ids.append(add_object(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream"))
        page_obj_ids.append(0)

    pages_obj = len(objects) + 1
    for index, content_id in enumerate(content_obj_ids):
        page_obj_ids[index] = add_object(
            f"<< /Type /Page /Parent {pages_obj} 0 R /MediaBox [0 0 {page_width} {page_height}] /Resources << /Font << /F1 {font_obj} 0 R >> >> /Contents {content_id} 0 R >>"
        )

    kids = " ".join(f"{page_id} 0 R" for page_id in page_obj_ids)
    add_object(f"<< /Type /Pages /Count {len(page_obj_ids)} /Kids [{kids}] >>")
    catalog_obj = add_object(f"<< /Type /Catalog /Pages {pages_obj} 0 R >>")

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_obj} 0 R >>\nstartxref\n{xref_start}\n%%EOF".encode("ascii")
    )
    return bytes(pdf)


def _build_report_pdf_bytes(query: str, report: dict, agents_used: list[str]) -> tuple[bytes, str]:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"Generated: {timestamp}",
        "",
        "Query:",
        query.strip() or "N/A",
        "",
        f"Agents Used: {', '.join(agents_used) if agents_used else 'N/A'}",
        "",
    ]

    if isinstance(report, dict) and report.get("error") == "not_research_query":
        lines.append("Validation Result")
        lines.append("")
        _append_report_lines(lines, report)
    else:
        for key, title in REPORT_SECTION_TITLES.items():
            lines.append(title)
            lines.append("")
            value = report.get(key) if isinstance(report, dict) else None
            if value in (None, "", [], {}):
                lines.append("Not applicable for this query")
            else:
                _append_report_lines(lines, value)
            lines.append("")

    safe_slug = re.sub(r"[^a-z0-9]+", "-", (query or "report").lower()).strip("-") or "report"
    filename = f"{safe_slug[:60]}-report.pdf"
    return _build_pdf("Agent Black Research Report", lines), filename


async def run_orchestration(task_id: str, query: str):
    """
    Background task that runs the full orchestration pipeline.
    Progress events are written to the DB asynchronously for SSE streaming.
    """
    try:
        import importlib.util
        orch_path = os.path.join(os.path.dirname(__file__), "..", "..", "agents", "host-agent", "orchestrator.py")
        spec = importlib.util.spec_from_file_location("orchestrator", orch_path)
        orch = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(orch)

        # progress_callback is called synchronously from the async orchestrator
        # on the event loop thread — fire-and-forget an async DB write via create_task
        def progress(step: str, status: str, detail: str = ""):
            asyncio.create_task(async_save_task_event(task_id, step, status, detail))

        report = await orch.orchestrate(query, progress_callback=progress)

        # Generate diagram in a thread (it's a synchronous CPU-bound function)
        diagram = await asyncio.to_thread(generate_agent_flow_diagram, query, report)
        agents_used = report.get("selected_agents", []) if isinstance(report, dict) else []

        await async_update_task_result(task_id, report, diagram, agents_used)
        await async_save_query(query, report, diagram, agents_used)
    except Exception as e:
        await async_update_task_error(task_id, str(e))
        await async_save_task_event(task_id, "error", "error", str(e))


@router.post("/query")
async def submit_query(req: QueryRequest):
    task_id = str(uuid.uuid4())
    await async_create_task(task_id, req.query)
    await async_save_task_event(task_id, "submitted", "running", "Query submitted")
    # Fire-and-forget the orchestration background task
    asyncio.create_task(run_orchestration(task_id, req.query))
    return {"task_id": task_id, "status": "running"}


@router.get("/query/stream/{task_id}")
async def stream_task_events(task_id: str):
    task = await async_get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    sent_events = set()
    SSE_TIMEOUT = 300

    async def event_generator():
        nonlocal sent_events
        start = asyncio.get_event_loop().time()
        while True:
            elapsed = asyncio.get_event_loop().time() - start
            if elapsed > SSE_TIMEOUT:
                err_task = await async_get_task(task_id)
                if err_task and err_task["status"] == "running":
                    await async_update_task_error(task_id, "Stream timed out after 300s")
                    err_task = await async_get_task(task_id)
                yield f"event: done\ndata: {json.dumps(err_task or {})}\n\n"
                return
            task = await async_get_task(task_id)
            events = await async_get_task_events(task_id)
            for ev in events:
                key = (ev["step"], ev["status"], ev["timestamp"])
                if key not in sent_events:
                    sent_events.add(key)
                    yield f"data: {json.dumps(ev)}\n\n"
            if task and task["status"] in ("complete", "error"):
                yield f"event: done\ndata: {json.dumps(task)}\n\n"
                return
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/query/task/{task_id}")
async def get_task_status(task_id: str):
    task = await async_get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    events = await async_get_task_events(task_id)
    return {**task, "events": events}


@router.get("/query/history")
async def get_history():
    return await asyncio.to_thread(get_query_history, 20)


@router.post("/query/report/pdf")
async def download_report_pdf(req: ReportPdfRequest):
    pdf_bytes, filename = await asyncio.to_thread(
        _build_report_pdf_bytes,
        req.query,
        req.report,
        req.agents_used,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/query/history")
async def clear_history():
    def _clear():
        conn = get_db()
        conn.execute("DELETE FROM queries")
        conn.execute("DELETE FROM tasks")
        conn.execute("DELETE FROM task_events")
        conn.commit()
        conn.close()
    await asyncio.to_thread(_clear)
    return {"message": "History cleared"}
