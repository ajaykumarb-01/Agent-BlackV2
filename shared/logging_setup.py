"""
Production-grade logging setup for Agent Black services.

Usage:
    from shared.logging_setup import get_logger, setup_service_logging

    # In service startup (app/main.py or agent main.py):
    logger = setup_service_logging("control-panel", log_dir="logs")

    # In other modules:
    logger = get_logger(__name__)
"""

import glob
import json
import logging
import logging.handlers
import os
import re
import sys
import time
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional

from shared.config import APP_ENV

# ── Correlation ID (per-request tracing) ───────────────────────────────────
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="-")


def get_correlation_id() -> str:
    return _correlation_id.get()


def set_correlation_id(cid: str) -> None:
    _correlation_id.set(cid)


# ── Sensitive-key redaction filter ──────────────────────────────────────────
_SENSITIVE_KEYS = re.compile(
    r"(api[_-]?key|password|secret|token|kaggle[_-]?key|authorization)",
    re.IGNORECASE,
)

_REDACT_PLACEHOLDER = "***REDACTED***"


class SensitiveDataFilter(logging.Filter):
    """Redact values that look like API keys, passwords, or tokens."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self._redact(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: (_REDACT_PLACEHOLDER if _SENSITIVE_KEYS.search(k) else v)
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    _REDACT_PLACEHOLDER
                    if isinstance(a, str) and len(a) > 40 and _looks_like_secret(a)
                    else a
                    for a in record.args
                )
        return True

    @staticmethod
    def _redact(text: str) -> str:
        text = re.sub(
            r'((?:api[_-]?key|password|secret|token|kaggle[_-]?key|authorization)'
            r'["\s:=]+)["\']?[\w\-\.]{8,}["\']?',
            rf'\g<1>{_REDACT_PLACEHOLDER}',
            text,
            flags=re.IGNORECASE,
        )
        return text


def _looks_like_secret(value: str) -> bool:
    if not value or len(value) < 20:
        return False
    non_space = value.replace(" ", "")
    return len(non_space) == len(value) and re.match(r"^[\w\-\.]+$", value)


# ── JSON structured formatter (production) ──────────────────────────────────
class JSONFormatter(logging.Formatter):
    """Emit each log line as a single JSON object for machine parsing."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "correlation_id": get_correlation_id(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False, default=str)


# ── Human-readable formatter (local) ───────────────────────────────────────
class HumanFormatter(logging.Formatter):
    """Concise format for local development."""

    _FMT = "%(asctime)s.%(msecs)03d  %(levelname)-8s  [%(name)s]  %(message)s"
    _DATE = "%Y-%m-%d %H:%M:%S"

    def __init__(self) -> None:
        super().__init__(self._FMT, datefmt=self._DATE)


# ── Helpers ────────────────────────────────────────────────────────────────
_configured_services: set[str] = set()


def get_logger(name: str) -> logging.Logger:
    """Get a named logger. Child loggers inherit service handlers/filters."""
    return logging.getLogger(name)


def clear_logs(log_dir: str, pattern: str = "*.log") -> int:
    """Truncate (clear) all log files matching pattern in log_dir.

    Returns the number of files cleared.
    """
    count = 0
    log_path = os.path.join(log_dir, pattern)
    for filepath in glob.glob(log_path):
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.truncate(0)
            count += 1
        except OSError:
            pass
    return count


def get_log_info(log_dir: str) -> list[dict]:
    """Return metadata for every log file in log_dir."""
    info = []
    for filepath in sorted(glob.glob(os.path.join(log_dir, "*.log"))):
        name = os.path.basename(filepath)
        try:
            stat = os.stat(filepath)
            info.append({
                "file": name,
                "size_bytes": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        except OSError:
            info.append({"file": name, "size_bytes": 0, "modified": None})
    return info


def setup_service_logging(
    service_name: str,
    *,
    log_dir: Optional[str] = None,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> logging.Logger:
    """Configure logging for a service (control-panel, research-agent, etc.).

    Call this ONCE at service startup before creating any child loggers.

    Args:
        service_name: Short identifier like "control-panel" or "research-agent".
        log_dir: Directory for log files. If None, only console output is used.
        console_level: Minimum level for console (stderr) output.
        file_level: Minimum level for file output.
        max_bytes: Max size per rotating log file before rotation.
        backup_count: Number of rotated backup files to keep.

    Returns:
        The root logger for this service.
    """
    if service_name in _configured_services:
        return logging.getLogger(service_name)

    _configured_services.add(service_name)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Remove pre-existing handlers to avoid duplicates
    root.handlers.clear()

    redact_filter = SensitiveDataFilter()

    # Choose formatter: JSON for production, human-readable for local
    if APP_ENV == "production":
        formatter: logging.Formatter = JSONFormatter()
    else:
        formatter = HumanFormatter()

    # ── Console handler ──────────────────────────────────────────────────
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(console_level)
    console.setFormatter(formatter)
    console.addFilter(redact_filter)
    root.addHandler(console)

    # ── File handlers (rotating) ─────────────────────────────────────────
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

        # Main log file (all levels)
        main_path = os.path.join(log_dir, f"{service_name}.log")
        main_fh = logging.handlers.RotatingFileHandler(
            main_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        main_fh.setLevel(file_level)
        main_fh.setFormatter(formatter)
        main_fh.addFilter(redact_filter)
        root.addHandler(main_fh)

        # Error-only log file
        err_path = os.path.join(log_dir, f"{service_name}-err.log")
        err_fh = logging.handlers.RotatingFileHandler(
            err_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        err_fh.setLevel(logging.WARNING)
        err_fh.setFormatter(formatter)
        err_fh.addFilter(redact_filter)
        root.addHandler(err_fh)

    logger = logging.getLogger(service_name)
    logger.info(
        "Logging initialized  service=%s  console_level=%s  log_dir=%s  env=%s",
        service_name,
        logging.getLevelName(console_level),
        log_dir or "(console-only)",
        APP_ENV,
    )
    return logger


# ── Convenience: timing context manager ─────────────────────────────────────

class LogTimer:
    """Context manager that logs elapsed time on exit.

    Usage:
        with LogTimer(logger, "agent dispatch", agent="research"):
            await call_agent(...)
    """

    def __init__(self, logger: logging.Logger, operation: str, **extra):
        self.logger = logger
        self.operation = operation
        self.extra = extra
        self._start = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        extra_str = "  ".join(f"{k}={v}" for k, v in self.extra.items())
        self.logger.info(">> %s  %s", self.operation, extra_str or "")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_ms = round((time.perf_counter() - self._start) * 1000, 1)
        if exc_type:
            self.logger.error(
                "<< %s  FAILED  elapsed=%sms  error=%s",
                self.operation,
                elapsed_ms,
                exc_val,
            )
        else:
            self.logger.info(
                "<< %s  OK  elapsed=%sms",
                self.operation,
                elapsed_ms,
            )
        return False
