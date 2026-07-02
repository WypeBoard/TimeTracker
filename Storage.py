"""Session-domain layer.

This module is the only place that knows about the sessions table schema.
Commands.py calls these functions; it never imports from db/ directly.
"""
import os
from datetime import date, datetime

import db.repository as repo
from Constants import DB_FILE
from db.connection import Connection
from db.query_type import QueryType


def create_schema() -> None:
    """Create the database directory, tables, and triggers if they do not exist.

    Safe to call on every startup — all DDL uses CREATE TABLE IF NOT EXISTS
    and CREATE TRIGGER IF NOT EXISTS, so it is a no-op after the first run.
    """
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

    # A single WRITE connection is used so that all DDL is committed together.
    with Connection(QueryType.WRITE, DB_FILE) as cur:

        # --- Main table ---------------------------------------------------
        cur.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                date  TEXT NOT NULL,
                start TEXT NOT NULL,
                end   TEXT,
                task  TEXT DEFAULT ''
            )
        ''')

        # --- History / shadow table ---------------------------------------
        # Every INSERT, UPDATE, and DELETE on sessions is recorded here
        # automatically via triggers. Application code never writes to this
        # table directly.
        cur.execute('''
            CREATE TABLE IF NOT EXISTS sessions_h (
                h_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                h_operation TEXT NOT NULL,
                h_timestamp TEXT NOT NULL,
                id          INTEGER NOT NULL,
                date        TEXT    NOT NULL,
                start       TEXT    NOT NULL,
                end         TEXT,
                task        TEXT
            )
        ''')

        # --- Triggers -----------------------------------------------------
        # Triggers fire inside the same transaction as the originating
        # statement, so history rows are committed/rolled back atomically.
        # h_timestamp uses UTC (datetime('now')) — audit trail only.

        cur.execute('''
            CREATE TRIGGER IF NOT EXISTS sessions_after_insert
            AFTER INSERT ON sessions
            BEGIN
                INSERT INTO sessions_h (h_operation, h_timestamp, id, date, start, end, task)
                VALUES ('I', datetime('now'), NEW.id, NEW.date, NEW.start, NEW.end, NEW.task);
            END
        ''')
        cur.execute('''
            CREATE TRIGGER IF NOT EXISTS sessions_after_update
            AFTER UPDATE ON sessions
            BEGIN
                INSERT INTO sessions_h (h_operation, h_timestamp, id, date, start, end, task)
                VALUES ('U', datetime('now'), NEW.id, NEW.date, NEW.start, NEW.end, NEW.task);
            END
        ''')
        cur.execute('''
            CREATE TRIGGER IF NOT EXISTS sessions_after_delete
            AFTER DELETE ON sessions
            BEGIN
                INSERT INTO sessions_h (h_operation, h_timestamp, id, date, start, end, task)
                VALUES ('D', datetime('now'), OLD.id, OLD.date, OLD.start, OLD.end, OLD.task);
            END
        ''')

        # ── epics table ───────────────────────────────────────────────────
        cur.execute('''
            CREATE TABLE IF NOT EXISTS epics (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    NOT NULL UNIQUE,
                created_at TEXT    NOT NULL
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS epics_h (
                h_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                h_operation TEXT    NOT NULL,
                h_timestamp TEXT    NOT NULL,
                id          INTEGER NOT NULL,
                name        TEXT    NOT NULL,
                created_at  TEXT    NOT NULL
            )
        ''')

        cur.execute('''
            CREATE TRIGGER IF NOT EXISTS epics_after_insert
            AFTER INSERT ON epics
            BEGIN
                INSERT INTO epics_h (h_operation, h_timestamp, id, name, created_at)
                VALUES ('I', datetime('now'), NEW.id, NEW.name, NEW.created_at);
            END
        ''')
        cur.execute('''
            CREATE TRIGGER IF NOT EXISTS epics_after_update
            AFTER UPDATE ON epics
            BEGIN
                INSERT INTO epics_h (h_operation, h_timestamp, id, name, created_at)
                VALUES ('U', datetime('now'), NEW.id, NEW.name, NEW.created_at);
            END
        ''')
        cur.execute('''
            CREATE TRIGGER IF NOT EXISTS epics_after_delete
            AFTER DELETE ON epics
            BEGIN
                INSERT INTO epics_h (h_operation, h_timestamp, id, name, created_at)
                VALUES ('D', datetime('now'), OLD.id, OLD.name, OLD.created_at);
            END
        ''')

        # ── task_catalog table ────────────────────────────────────────────
        cur.execute('''
            CREATE TABLE IF NOT EXISTS task_catalog (
                task_id    TEXT    PRIMARY KEY,
                epic_id    INTEGER NOT NULL,
                created_at TEXT    NOT NULL,
                FOREIGN KEY (epic_id) REFERENCES epics(id)
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS task_catalog_h (
                h_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                h_operation TEXT    NOT NULL,
                h_timestamp TEXT    NOT NULL,
                task_id     TEXT    NOT NULL,
                epic_id     INTEGER NOT NULL,
                created_at  TEXT    NOT NULL
            )
        ''')

        cur.execute('''
            CREATE TRIGGER IF NOT EXISTS task_catalog_after_insert
            AFTER INSERT ON task_catalog
            BEGIN
                INSERT INTO task_catalog_h (h_operation, h_timestamp, task_id, epic_id, created_at)
                VALUES ('I', datetime('now'), NEW.task_id, NEW.epic_id, NEW.created_at);
            END
        ''')
        cur.execute('''
            CREATE TRIGGER IF NOT EXISTS task_catalog_after_update
            AFTER UPDATE ON task_catalog
            BEGIN
                INSERT INTO task_catalog_h (h_operation, h_timestamp, task_id, epic_id, created_at)
                VALUES ('U', datetime('now'), NEW.task_id, NEW.epic_id, NEW.created_at);
            END
        ''')
        cur.execute('''
            CREATE TRIGGER IF NOT EXISTS task_catalog_after_delete
            AFTER DELETE ON task_catalog
            BEGIN
                INSERT INTO task_catalog_h (h_operation, h_timestamp, task_id, epic_id, created_at)
                VALUES ('D', datetime('now'), OLD.task_id, OLD.epic_id, OLD.created_at);
            END
        ''')


def open_session(date_str: str, start: str, task: str) -> None:
    """Insert a new open session. `end` is NULL until the session is closed."""
    repo.execute(
        'INSERT INTO sessions (date, start, end, task) VALUES (?, ?, NULL, ?)',
        (date_str, start, task),
    )


def close_session(session_id: int, end: str) -> None:
    """Set the end time on the given session, closing it."""
    repo.execute(
        'UPDATE sessions SET end = ? WHERE id = ?',
        (end, session_id),
    )


def update_session_task(session_id: int, task: str) -> None:
    """Update the task/epic label on the given session."""
    repo.execute(
        'UPDATE sessions SET task = ? WHERE id = ?',
        (task, session_id),
    )


def get_open_session() -> tuple | None:
    """Return (id, date, start, task) for the most recent open session, or None."""
    return repo.fetch_one(
        'SELECT id, date, start, task FROM sessions WHERE end IS NULL ORDER BY id DESC LIMIT 1'
    )


def get_today_sessions() -> list[tuple]:
    """Return [(id, start, end, task)] for all of today's sessions, ordered by start time.

    `end` is None for the open session (if any).
    """
    today = date.today().strftime('%Y-%m-%d')
    return repo.fetch_many(
        'SELECT id, start, end, task FROM sessions WHERE date = ? ORDER BY start, id',
        (today,),
    )


def read_log() -> dict:
    """Return all closed sessions grouped by date.

    Shape matches the old Workbook.read_log() return value:
        {
            "2026-06-16": {
                "week": 25,
                "sessions": [("08:30", "12:00", "Epic-42"), ...],
                "total": 3.5,
            },
            ...
        }

    Open sessions (end IS NULL) are excluded — they have no end time yet.
    """
    rows = repo.fetch_many(
        'SELECT date, start, end, task FROM sessions '
        'WHERE end IS NOT NULL ORDER BY date, start, id'
    )

    days: dict = {}
    for date_str, start_val, end_val, task_val in rows:
        week = datetime.strptime(date_str, '%Y-%m-%d').isocalendar().week

        try:
            s = datetime.strptime(start_val, '%H:%M')
            e = datetime.strptime(end_val, '%H:%M')
            hours = (e.hour * 60 + e.minute - (s.hour * 60 + s.minute)) / 60
        except ValueError:
            hours = 0.0

        if date_str not in days:
            days[date_str] = {'week': week, 'sessions': [], 'total': 0.0}
        days[date_str]['sessions'].append((start_val, end_val, task_val or ''))
        days[date_str]['total'] += hours

    return days
