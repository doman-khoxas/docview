"""Centralized logging configuration for DocView.

Provides structured logging with:
- File output (rotating logs in user's .pdf_editor directory)
- Console output (stderr) for development
- Module-level loggers for each component
- Operation tracking for crash diagnostics
"""
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime


# ---------------------------------------------------------------------------
# Log directory & file
# ---------------------------------------------------------------------------

def _get_log_dir() -> Path:
    """Return the log directory, creating it if needed."""
    log_dir = Path.home() / ".pdf_editor" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def _get_log_path() -> Path:
    """Return path for the main application log file."""
    return _get_log_dir() / "docview.log"


# ---------------------------------------------------------------------------
# Formatter
# ---------------------------------------------------------------------------

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-28s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

_initialized = False


def setup_logging(level: int = logging.DEBUG, console: bool = True):
    """Initialize the logging system. Call once at startup.

    Args:
        level: Minimum log level for file output (default DEBUG).
        console: If True, also log WARNING+ to stderr.
    """
    global _initialized
    if _initialized:
        return
    _initialized = True

    root = logging.getLogger("docview")
    root.setLevel(level)

    # --- Rotating file handler (5 MB x 3 backups) ---
    log_path = _get_log_path()
    file_handler = logging.handlers.RotatingFileHandler(
        str(log_path),
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    root.addHandler(file_handler)

    # --- Console handler (WARNING+ only to avoid noise) ---
    if console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        root.addHandler(console_handler)

    # --- Startup banner ---
    root.info("=" * 72)
    root.info("DocView session started")
    root.info("  Python: %s", sys.version)
    root.info("  Platform: %s", sys.platform)
    root.info("  PID: %d", os.getpid())
    root.info("  Log file: %s", log_path)
    root.info("=" * 72)


def get_logger(module_name: str) -> logging.Logger:
    """Get a logger for a specific module.

    Usage:
        from app.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Document opened: %s", path)
    """
    return logging.getLogger(f"docview.{module_name}")


def log_exception(logger: logging.Logger, msg: str, exc: Exception):
    """Log an exception with full traceback at ERROR level."""
    logger.error("%s: %s", msg, exc, exc_info=True)
