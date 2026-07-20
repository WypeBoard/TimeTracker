"""Central logging configuration for TimeTracker.

Call `setup_logging()` once at application startup (in TimeTracker.py main()).
All other modules obtain their logger with:

    from logger import get_logger
    _log = get_logger(__name__)

Design notes:
- A single TimedRotatingFileHandler writes to logs/app.log.
- The file rotates weekly at midnight on Monday (when='W0'), keeping 8 weeks
  of history (~2 months).
- Log level defaults to INFO; set the TT_LOG_LEVEL environment variable to
  override (e.g. TT_LOG_LEVEL=DEBUG).
- No console (StreamHandler) output — the Textual TUI owns the terminal and a
  second stream to stdout/stderr would corrupt the display.
"""
import logging
import logging.handlers
import os
import datetime

# Resolve the logs/ directory relative to this file so the path is stable
# regardless of which directory the application is launched from.
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_LOG_DIR = os.path.join(_PROJECT_ROOT, "logs")
_LOG_FILE = os.path.join(_LOG_DIR, "app.log")

_VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

# Tracks whether setup_logging() has already been called so it is safe to
# call multiple times (e.g. in tests) without adding duplicate handlers.
_configured = False


def setup_logging() -> None:
    """Configure the root logger with a weekly-rotating file handler.

    Must be called once before any logging occurs — typically as the very
    first statement in TimeTracker.py main().
    """
    global _configured
    if _configured:
        return
    _configured = True

    # Create the logs/ directory if it does not exist.
    os.makedirs(_LOG_DIR, exist_ok=True)

    # Determine the log level from the environment variable, falling back to INFO.
    level_name = os.environ.get("TT_LOG_LEVEL", "INFO").upper()
    if level_name not in _VALID_LEVELS:
        level_name = "INFO"
    level = getattr(logging, level_name)

    # TimedRotatingFileHandler rotates at midnight on Monday (when='W0').
    # backupCount=8 retains roughly 2 months of weekly files.
    # Rotated files are named  logs/app.log.YYYY-MM-DD  (default suffix).
    handler = logging.handlers.TimedRotatingFileHandler(
        filename=_LOG_FILE,
        when="W0",                        # W0 = Monday
        atTime=datetime.time(0, 0),       # rotate at midnight
        backupCount=8,
        encoding="utf-8",
    )

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a standard library Logger for the given name.

    Modules should call this at module level:

        _log = get_logger(__name__)

    Using __name__ as the logger name means log lines automatically
    identify which module produced them.
    """
    return logging.getLogger(name)
