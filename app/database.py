import sqlite3
import os
import json
import time
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "local")  # "local" | "production"
if APP_ENV not in ("local", "production"):
    raise ValueError(f"APP_ENV must be 'local' or 'production', got '{APP_ENV}'")

DB_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent / "data"
DB_PATH = DB_DIR / f"agent_black_{APP_ENV}.db"


def get_db():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            report TEXT NOT NULL DEFAULT '{}',
            diagram TEXT,
            agents_used TEXT DEFAULT '[]',
            created_at REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS system_setup (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            step TEXT NOT NULL UNIQUE,
            completed INTEGER NOT NULL DEFAULT 0,
            completed_at REAL
        );

        CREATE TABLE IF NOT EXISTS agent_discovery (
            name TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            port INTEGER NOT NULL,
            capabilities TEXT DEFAULT '[]',
            status TEXT DEFAULT 'stopped',
            last_seen REAL
        );

        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            query TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'running',
            report TEXT,
            diagram TEXT,
            agents_used TEXT DEFAULT '[]',
            error TEXT,
            created_at REAL NOT NULL,
            completed_at REAL
        );

        CREATE TABLE IF NOT EXISTS task_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            step TEXT NOT NULL,
            status TEXT NOT NULL,
            detail TEXT,
            timestamp REAL NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def create_task(task_id: str, query: str):
    conn = get_db()
    conn.execute(
        "INSERT INTO tasks (task_id, query, status, created_at) VALUES (?, ?, 'running', ?)",
        (task_id, query, time.time()),
    )
    conn.commit()
    conn.close()


def update_task_result(task_id: str, report: dict, diagram: str = None, agents_used: list = None):
    conn = get_db()
    conn.execute(
        "UPDATE tasks SET status='complete', report=?, diagram=?, agents_used=?, completed_at=? WHERE task_id=?",
        (json.dumps(report), diagram, json.dumps(agents_used or []), time.time(), task_id),
    )
    conn.commit()
    conn.close()


def update_task_error(task_id: str, error: str):
    conn = get_db()
    conn.execute(
        "UPDATE tasks SET status='error', error=?, completed_at=? WHERE task_id=?",
        (error, time.time(), task_id),
    )
    conn.commit()
    conn.close()


def get_task(task_id: str):
    conn = get_db()
    r = conn.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
    conn.close()
    if not r:
        return None
    return {
        "task_id": r["task_id"],
        "query": r["query"],
        "status": r["status"],
        "report": json.loads(r["report"]) if r["report"] else None,
        "diagram": r["diagram"],
        "agents_used": json.loads(r["agents_used"]) if r["agents_used"] else [],
        "error": r["error"],
        "created_at": r["created_at"],
        "completed_at": r["completed_at"],
    }


def save_task_event(task_id: str, step: str, status: str, detail: str = ""):
    conn = get_db()
    conn.execute(
        "INSERT INTO task_events (task_id, step, status, detail, timestamp) VALUES (?, ?, ?, ?, ?)",
        (task_id, step, status, detail, time.time()),
    )
    conn.commit()
    conn.close()


def get_task_events(task_id: str):
    conn = get_db()
    rows = conn.execute(
        "SELECT step, status, detail, timestamp FROM task_events WHERE task_id=? ORDER BY id",
        (task_id,),
    ).fetchall()
    conn.close()
    return [{"step": r["step"], "status": r["status"], "detail": r["detail"], "timestamp": r["timestamp"]} for r in rows]


def save_query(query: str, report: dict, diagram: str = None, agents_used: list = None):
    conn = get_db()
    conn.execute(
        "INSERT INTO queries (query, report, diagram, agents_used, created_at) VALUES (?, ?, ?, ?, ?)",
        (query, json.dumps(report), diagram, json.dumps(agents_used or []), time.time()),
    )
    conn.commit()
    conn.close()


def get_query_history(limit: int = 20):
    conn = get_db()
    rows = conn.execute(
        "SELECT id, query, report, diagram, agents_used, created_at FROM queries ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "query": r["query"],
            "report": json.loads(r["report"]),
            "diagram": r["diagram"],
            "agents_used": json.loads(r["agents_used"]),
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def get_query_count():
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM queries").fetchone()[0]
    conn.close()
    return count


def get_setting(key: str, default: str = None):
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    conn = get_db()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = ?",
        (key, value, value),
    )
    conn.commit()
    conn.close()


def get_all_settings():
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}


def is_setup_complete():
    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) FROM system_setup WHERE completed = 1"
    ).fetchone()[0]
    conn.close()
    return count > 0


def complete_setup_step(step: str):
    conn = get_db()
    conn.execute(
        "INSERT INTO system_setup (step, completed, completed_at) VALUES (?, 1, ?) ON CONFLICT(step) DO UPDATE SET completed = 1, completed_at = ?",
        (step, time.time(), time.time()),
    )
    conn.commit()
    conn.close()


def get_setup_progress():
    conn = get_db()
    rows = conn.execute("SELECT step, completed, completed_at FROM system_setup ORDER BY id").fetchall()
    conn.close()
    return [{"step": r["step"], "completed": bool(r["completed"]), "completed_at": r["completed_at"]} for r in rows]


def save_agent_discovery(name: str, url: str, port: int, capabilities: list, status: str):
    conn = get_db()
    conn.execute(
        "INSERT INTO agent_discovery (name, url, port, capabilities, status, last_seen) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(name) DO UPDATE SET url=?, port=?, capabilities=?, status=?, last_seen=?",
        (name, url, port, json.dumps(capabilities), status, time.time(), url, port, json.dumps(capabilities), status, time.time()),
    )
    conn.commit()
    conn.close()


def get_agent_discovery():
    conn = get_db()
    rows = conn.execute("SELECT name, url, port, capabilities, status, last_seen FROM agent_discovery").fetchall()
    conn.close()
    return [
        {
            "name": r["name"],
            "url": r["url"],
            "port": r["port"],
            "capabilities": json.loads(r["capabilities"]),
            "status": r["status"],
            "last_seen": r["last_seen"],
        }
        for r in rows
    ]


def get_avg_response_time():
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key = 'avg_response_time'").fetchone()
    conn.close()
    return float(row["value"]) if row else 0.0


def set_avg_response_time(val: float):
    set_setting("avg_response_time", str(val))


# ── Async wrappers (run blocking sqlite calls in threads) ─────────────────────

async def async_create_task(task_id: str, query: str):
    await asyncio.to_thread(create_task, task_id, query)

async def async_update_task_result(task_id: str, report: dict, diagram: str = None, agents_used: list = None):
    await asyncio.to_thread(update_task_result, task_id, report, diagram, agents_used)

async def async_update_task_error(task_id: str, error: str):
    await asyncio.to_thread(update_task_error, task_id, error)

async def async_get_task(task_id: str):
    return await asyncio.to_thread(get_task, task_id)

async def async_save_task_event(task_id: str, step: str, status: str, detail: str = ""):
    await asyncio.to_thread(save_task_event, task_id, step, status, detail)

async def async_get_task_events(task_id: str):
    return await asyncio.to_thread(get_task_events, task_id)

async def async_save_query(query: str, report: dict, diagram: str = None, agents_used: list = None):
    await asyncio.to_thread(save_query, query, report, diagram, agents_used)
