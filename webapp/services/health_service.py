"""Backend health check used by GET /health.

Per features/standalone-web-app.md Requirements: "A /health endpoint must
exist; the browser checks it on page load and shows whether the backend is
up or down." This module verifies the FastAPI process is alive and that the
shared SQLite database file is reachable — the two things that could make
the backend appear "down" from the browser's perspective.
"""
import sqlite3

import db.repository as repo


def check_database_reachable() -> bool:
    """Return True if a trivial read against the shared database succeeds.

    Uses db/repository.py directly (webapp/'s only shared dependency with
    app/) rather than any app.*Storage module — see webapp/services/__init__.py.
    """
    try:
        repo.fetch_one("SELECT 1")
        return True
    except sqlite3.Error:
        return False
