import os
import sqlite3
import time
from pathlib import Path
from dotenv import load_dotenv

# ── Infra-only: HOST, PORT, Docker, CI/CD from .env ──────────────────────────
load_dotenv()

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
_VALID_ENVS = ("local", "production")
APP_ENV = os.getenv("APP_ENV", "local")  # "local" | "production"
if APP_ENV not in _VALID_ENVS:
    raise ValueError(f"APP_ENV must be one of {_VALID_ENVS}, got '{APP_ENV}'")

# ── API keys, provider, agent URLs → SQLite only ─────────────────────────────
_DB_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent / "data"
_DB_PATH = _DB_DIR / f"agent_black_{APP_ENV}.db"
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

SSE_TIMEOUT = int(get_setting("SSE_TIMEOUT", "900"))

KAGGLE_USERNAME = get_setting("KAGGLE_USERNAME")
KAGGLE_KEY = get_setting("KAGGLE_KEY")

# ── Agent URLs: env var > DB > env-default ─────────────────────────────────
# Defaults differ by environment: production uses Docker service names,
# local uses localhost.
_DEFAULT_AGENTS = {
    "local": {
        "RESEARCH_AGENT_URL": "http://localhost:8001",
        "SOLUTION_AGENT_URL": "http://localhost:8002",
        "EXPERIMENT_AGENT_URL": "http://localhost:8003",
        "HOST_AGENT_URL": "http://localhost:8000",
    },
    "production": {
        "RESEARCH_AGENT_URL": "http://research-agent:8001",
        "SOLUTION_AGENT_URL": "http://solution-agent:8002",
        "EXPERIMENT_AGENT_URL": "http://experiment-agent:8003",
        "HOST_AGENT_URL": "http://control-panel:8000",
    },
}

def _agent_url(key: str) -> str:
    """Env var > DB > environment-specific default."""
    env_val = os.getenv(key)
    if env_val:
        return env_val
    return get_setting(key, _DEFAULT_AGENTS[APP_ENV].get(key, ""))

# ── Per-agent mode: local | network | disabled ──────────────────────────────
# "local"    → agent runs on localhost, started by start.py
# "network"  → agent runs on remote PC, orchestrator uses configured host/port
# "disabled" → agent is not used at all, skipped in discovery and routing

_AGENT_KEY_MAP = {
    "research": "RESEARCH_AGENT",
    "solution": "SOLUTION_AGENT",
    "experiment": "EXPERIMENT_AGENT",
}

AGENT_PORTS = {
    "research": 8001,
    "solution": 8002,
    "experiment": 8003,
    "host": 8000,
}

_VALID_AGENT_MODES = ("local", "network", "disabled")


def get_agent_mode(agent_name: str) -> str:
    """Return the agent's mode: 'local', 'network', or 'disabled'."""
    prefix = _AGENT_KEY_MAP.get(agent_name, "")
    if not prefix:
        return "local"
    raw = get_setting(f"{prefix}_MODE", "local").lower()
    if raw not in _VALID_AGENT_MODES:
        return "local"
    return raw


def set_agent_mode(agent_name: str, mode: str):
    """Set the agent's mode: 'local', 'network', or 'disabled'."""
    if mode not in _VALID_AGENT_MODES:
        raise ValueError(f"Invalid mode '{mode}'. Must be one of {_VALID_AGENT_MODES}")
    prefix = _AGENT_KEY_MAP.get(agent_name)
    if not prefix:
        raise ValueError(f"Unknown agent: {agent_name}. Valid: {list(_AGENT_KEY_MAP.keys())}")
    set_setting(f"{prefix}_MODE", mode)


def get_agent_modes() -> dict[str, str]:
    """Return mode for all agents."""
    return {name: get_agent_mode(name) for name in _AGENT_KEY_MAP}


def is_agent_network_mode(agent_name: str) -> bool:
    """Check if an agent is in 'network' mode."""
    return get_agent_mode(agent_name) == "network"


def is_agent_disabled(agent_name: str) -> bool:
    """Check if an agent is disabled."""
    return get_agent_mode(agent_name) == "disabled"


def get_agent_network_host(agent_name: str) -> str:
    """Return the configured network host/IP for an agent (empty string if not set)."""
    prefix = _AGENT_KEY_MAP.get(agent_name, "")
    return get_setting(f"{prefix}_NETWORK_HOST", "") if prefix else ""


def set_agent_network_host(agent_name: str, host: str):
    """Set the network host/IP for a specific agent."""
    prefix = _AGENT_KEY_MAP.get(agent_name)
    if not prefix:
        raise ValueError(f"Unknown agent: {agent_name}")
    set_setting(f"{prefix}_NETWORK_HOST", host)


def get_agent_network_port(agent_name: str) -> int:
    """Return the configured network port for an agent (defaults to standard port)."""
    prefix = _AGENT_KEY_MAP.get(agent_name, "")
    default_port = AGENT_PORTS.get(agent_name, 0)
    if not prefix:
        return default_port
    return int(get_setting(f"{prefix}_NETWORK_PORT", str(default_port)))


def set_agent_network_port(agent_name: str, port: int):
    """Set the network port for a specific agent."""
    prefix = _AGENT_KEY_MAP.get(agent_name)
    if not prefix:
        raise ValueError(f"Unknown agent: {agent_name}")
    set_setting(f"{prefix}_NETWORK_PORT", str(port))



def get_agent_urls() -> dict[str, str]:
    """Read agent URLs fresh every call (avoids stale module-level cache).

    Priority per agent:
      1. Environment variable  (e.g. RESEARCH_AGENT_URL — for Docker/CI)
      2. Network-mode URL      (when mode is 'network' and a host is set)
      3. DB-stored URL          (manual override via settings API)
      4. Environment default   (localhost for local, service names for production)

    Disabled agents are excluded from the result entirely.
    """
    result = {}
    for name, prefix in _AGENT_KEY_MAP.items():
        mode = get_agent_mode(name)
        if mode == "disabled":
            continue
        url_key = f"{prefix}_URL"
        env_val = os.getenv(url_key)
        if env_val:
            result[name] = env_val
        elif mode == "network":
            host = get_agent_network_host(name)
            port = get_agent_network_port(name)
            if host:
                result[name] = f"http://{host}:{port}"
            else:
                result[name] = get_setting(url_key, _DEFAULT_AGENTS[APP_ENV].get(url_key, ""))
        else:
            result[name] = get_setting(url_key, _DEFAULT_AGENTS[APP_ENV].get(url_key, ""))
    result["host"] = _agent_url("HOST_AGENT_URL")
    return result
