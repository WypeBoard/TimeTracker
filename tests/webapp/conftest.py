"""Shared fixtures for webapp/ tests.

`isolated_db` points db/repository.py at a throwaway SQLite file and creates
the minimal schema Phase 3 (Today page) needs: `sessions`, `epics`,
`task_catalog`, `settings`. No triggers/history tables are created — Phase 3
tests only exercise reads/writes against the base tables, mirroring what
app/Storage.create_schema() ships in production without importing it (see
features/standalone-web-app.md Non-Goals: webapp/ does not import app/*).
"""
import sqlite3

import pytest

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    date  TEXT NOT NULL,
    start TEXT NOT NULL,
    end   TEXT,
    task  TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS epics (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS task_catalog (
    task_id    TEXT PRIMARY KEY,
    epic_id    INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("db.repository.DB_FILE", db_path)
    conn = sqlite3.connect(db_path)
    conn.executescript(_SCHEMA)
    conn.commit()
    conn.close()
    return db_path
