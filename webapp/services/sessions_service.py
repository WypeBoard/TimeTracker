"""Independent CRUD against the shared `sessions` table for webapp/ services.

Per features/standalone-web-app.md Non-Goals, webapp/ does not import
app/Storage.py. This module re-implements only the raw read/write
operations today_service.py needs, against the same `sessions` schema
app/Storage.py already created (webapp/ does not create or alter that
schema — see the Manual Changes "db/ boundary" discussion).
"""
from datetime import date

import db.repository as repo


def get_open_session() -> tuple | None:
    """Return (id, date, start, task) for the most recent open session, or None."""
    return repo.fetch_one(
        "SELECT id, date, start, task FROM sessions WHERE end IS NULL ORDER BY id DESC LIMIT 1"
    )


def get_today_sessions() -> list[tuple]:
    """Return [(id, start, end, task)] for today's sessions, ordered by start time.

    `end` is None for the open session (if any).
    """
    today = date.today().strftime("%Y-%m-%d")
    return repo.fetch_many(
        "SELECT id, start, end, task FROM sessions WHERE date = ? ORDER BY start, id",
        (today,),
    )


def get_closed_sessions_in_range(start_date: str, end_date: str) -> list[tuple]:
    """Return [(date, start, end, task)] for closed sessions within [start_date, end_date].

    Used by Quick Stats' week-total calculation. Dates are inclusive,
    formatted as YYYY-MM-DD.
    """
    return repo.fetch_many(
        "SELECT date, start, end, task FROM sessions "
        "WHERE end IS NOT NULL AND date >= ? AND date <= ? "
        "ORDER BY date, start, id",
        (start_date, end_date),
    )


def open_session(date_str: str, start: str, task: str) -> None:
    """Insert a new open session. `end` is NULL until the session is closed."""
    repo.execute(
        "INSERT INTO sessions (date, start, end, task) VALUES (?, ?, NULL, ?)",
        (date_str, start, task),
    )


def close_session(session_id: int, end: str) -> None:
    """Set the end time on the given session, closing it."""
    repo.execute(
        "UPDATE sessions SET end = ? WHERE id = ?",
        (end, session_id),
    )
