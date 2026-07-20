#!/usr/bin/env python3
"""
Time Tracker — logs work sessions to a SQLite database.

Launch: python TimeTracker.py
Opens the Textual TUI. All commands are entered from the TUI command bar.
"""
import sys

from logger import setup_logging, get_logger
from Storage import create_schema

_log = get_logger(__name__)


def _handle_unhandled_exception(exc_type, exc_val, exc_tb):
    """Log any unhandled exception at CRITICAL level before the process exits.

    Installed as sys.excepthook so crashes are always captured in the log
    even when no try/except block is present higher up in the call stack.

    KeyboardInterrupt (Ctrl+C) is passed through to the default handler so
    the user still gets a clean exit — it is not treated as a crash.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_val, exc_tb)
        return
    _log.critical("Unhandled exception — application will exit", exc_info=(exc_type, exc_val, exc_tb))


def main():
    # Logging must be configured before anything else so that all subsequent
    # module-level and runtime log calls are captured.
    setup_logging()

    # Install the crash hook after logging is ready.
    sys.excepthook = _handle_unhandled_exception

    _log.info("TimeTracker starting up")

    # Ensure the database directory, tables, and triggers exist before the TUI
    # starts. Safe to call on every startup — all DDL uses IF NOT EXISTS.
    create_schema()

    from app.TimeTrackerApp import TimeTrackerApp
    try:
        TimeTrackerApp().run()
    finally:
        _log.info("TimeTracker shut down")


if __name__ == "__main__":
    main()