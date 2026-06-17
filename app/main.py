import sys
import os
import time
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# ── Logging setup ──────────────────────────────────────────────
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

_fmt = logging.Formatter("%(asctime)s  %(levelname)-7s  %(message)s", datefmt="%H:%M:%S")

# Root logger: DEBUG level, writes all levels to file
_root = logging.getLogger()
_root.setLevel(logging.DEBUG)

_fh = logging.FileHandler(os.path.join(LOG_DIR, "control-panel-app.log"), encoding="utf-8")
_fh.setLevel(logging.DEBUG)
_fh.setFormatter(_fmt)
_root.addHandler(_fh)

# Console: INFO and above only
_sh = logging.StreamHandler(sys.stderr)
_sh.setLevel(logging.INFO)
_sh.setFormatter(_fmt)
_root.addHandler(_sh)

logger = logging.getLogger("agent-black")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        logger.info(f">>> {request.method} {request.url.path}")
        try:
            response = await call_next(request)
            elapsed = round((time.time() - start) * 1000, 1)
            logger.info(f"<<< {request.method} {request.url.path}  {response.status_code}  {elapsed}ms")
            return response
        except Exception as exc:
            elapsed = round((time.time() - start) * 1000, 1)
            logger.error(f"!!! {request.method} {request.url.path}  ERROR  {elapsed}ms  {exc}")
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
    logger.info(f"Routes: /api/status, /api/query, /api/settings, /api/setup/step, /api/diagram/*, /api/logs")


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
        }
    }
