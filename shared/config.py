import os
import sqlite3
import time
import atexit
from pathlib import Path
from dotenv import load_dotenv

# ── Infra-only: HOST, PORT, Docker, CI/CD from .env ──────────────────────────
load_dotenv()

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# ── API keys, provider, agent URLs → SQLite only ─────────────────────────────
_DB_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent / "data"
_DB_PATH = _DB_DIR / "agent_black.db"
_LOCK = _DB_DIR / ".config_init.lock"


def _with_lock_init():
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    for attempt in range(30):
        try:
            fd = os.open(str(_LOCK), os.O_CREAT | os.O_EXCL | os.O_RDWR)
            os.close(fd)
            break
        except FileExistsError:
            time.sleep(0.1)
    else:
        return
    try:
        conn = sqlite3.connect(str(_DB_PATH), timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        conn.commit()
        conn.close()
    finally:
        try:
            os.remove(str(_LOCK))
        except FileNotFoundError:
            pass


def _get_db():
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def get_setting(key: str, default: str = "") -> str:
    conn = _get_db()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    conn = _get_db()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=?",
        (key, value, value),
    )
    conn.commit()
    conn.close()


def get_all_settings() -> dict:
    conn = _get_db()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}


_with_lock_init()

LLM_PROVIDER = get_setting("LLM_PROVIDER", "gemini")

GEMINI_API_KEY = get_setting("GEMINI_API_KEY")
GEMINI_BASE_URL = get_setting("GEMINI_BASE_URL")
GEMINI_MODEL = get_setting("GEMINI_MODEL", "gemini-1.5-flash")

OPENAI_API_KEY = get_setting("OPENAI_API_KEY")
OPENAI_BASE_URL = get_setting("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = get_setting("OPENAI_MODEL", "gpt-4o")

ANTHROPIC_API_KEY = get_setting("ANTHROPIC_API_KEY")
ANTHROPIC_BASE_URL = get_setting("ANTHROPIC_BASE_URL")
ANTHROPIC_MODEL = get_setting("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

# ── Agent URLs: env vars take priority over DB (Docker service names) ───────
def _agent_url(key: str, default: str) -> str:
    """Env var > DB > default. Env vars win so Docker service names work."""
    env_val = os.getenv(key)
    if env_val:
        return env_val
    return get_setting(key, default)

AGENT_URLS = {
    "research": _agent_url("RESEARCH_AGENT_URL", "http://localhost:8001"),
    "solution": _agent_url("SOLUTION_AGENT_URL", "http://localhost:8002"),
    "experiment": _agent_url("EXPERIMENT_AGENT_URL", "http://localhost:8003"),
}

HOST_AGENT_URL = _agent_url("HOST_AGENT_URL", "http://localhost:8000")
RESEARCH_AGENT_URL = AGENT_URLS["research"]
SOLUTION_AGENT_URL = AGENT_URLS["solution"]
EXPERIMENT_AGENT_URL = AGENT_URLS["experiment"]
