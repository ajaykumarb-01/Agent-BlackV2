import sys
import os
import json
import asyncio
import uuid
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models import QueryRequest
from app.routes.diagram import generate_agent_flow_diagram
from app.database import (
    get_query_history, get_db,
    async_create_task, async_update_task_result, async_update_task_error,
    async_save_task_event, async_get_task, async_get_task_events, async_save_query,
)

router = APIRouter(tags=["query"])


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
        agents_used = list(report.keys()) if isinstance(report, dict) else []

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
