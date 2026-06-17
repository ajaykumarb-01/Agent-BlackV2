import sys
import os
import time
import uuid
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.logging_setup import (
    get_logger,
    setup_service_logging,
    set_correlation_id,
)

# ── Logging setup ──────────────────────────────────────────────
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
setup_service_logging("control-panel", log_dir=LOG_DIR, console_level=logging.INFO)

logger = get_logger("control-panel")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        cid = uuid.uuid4().hex[:12]
        set_correlation_id(cid)
        start = time.time()
        client_ip = request.client.host if request.client else "unknown"
        logger.info(
            ">>> %s %s  client_ip=%s",
            request.method,
            request.url.path,
            client_ip,
        )
        try:
            response = await call_next(request)
            elapsed = round((time.time() - start) * 1000, 1)
            logger.info(
                "<<< %s %s  status=%d  elapsed=%sms  client_ip=%s  cid=%s",
                request.method,
                request.url.path,
                response.status_code,
                elapsed,
                client_ip,
                cid,
            )
            return response
        except Exception as exc:
            elapsed = round((time.time() - start) * 1000, 1)
            logger.error(
                "!!! %s %s  ERROR  elapsed=%sms  client_ip=%s  error=%s  cid=%s",
                request.method,
                request.url.path,
                elapsed,
                client_ip,
                exc,
                cid,
            )
            raise


# ── App setup ──────────────────────────────────────────────────
from app.routes.control import router as control_router
from app.routes.query import router as query_router
from app.routes.settings import router as settings_router
from app.routes.diagram import router as diagram_router
from app.routes.discovery import router as discovery_router
from app.routes.setup import router as setup_router
from app.routes.logs import router as logs_router
from app.database import init_db

init_db()

app = FastAPI(title="Agent Black - Control Panel")

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(control_router, prefix="/api")
app.include_router(query_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(diagram_router, prefix="/api")
app.include_router(discovery_router, prefix="/api")
app.include_router(setup_router, prefix="/api")
app.include_router(logs_router, prefix="/api")


@app.on_event("startup")
def on_startup():
    logger.info("Agent Black Control Panel starting up")
    logger.info(
        "Routes: /api/status, /api/query, /api/settings, /api/setup/step, /api/diagram/*, /api/logs"
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "control-panel"}


@app.get("/")
def root():
    return {
        "name": "Agent Black Control Panel",
        "docs": "/docs",
        "endpoints": {
            "system": "GET /api/status, POST /api/agents/start, POST /api/agents/stop",
            "query": "POST /api/query, GET /api/query/history",
            "settings": "GET/PUT /api/settings",
            "diagram": "POST /api/diagram/agent-flow, POST /api/diagram/tech-stack",
        },
    }
