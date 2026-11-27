"""Generic database helpers.

All direct use of Connection is centralised here so that the rest of the
codebase never needs to know about the db/ package directly.
app/Storage.py calls these helpers; app/Commands.py calls app/Storage.py.
webapp/services/*.py calls these helpers directly instead — see the db/
boundary discussion in features/completed/standalone-web-app.md for why
db/ does not import from app/.
"""
import logging
import sqlite3
from typing import Any

from db.config import DB_FILE
from db.connection import Connection
from db.query_type import QueryType

_log = logging.getLogger(__name__)


def execute(query: str, params: tuple[Any, ...] = ()) -> None:
    """Run a WRITE query (INSERT / UPDATE / DELETE) and commit."""
    try:
        with Connection(QueryType.WRITE, DB_FILE) as cur:
            cur.execute(query, params)
    except sqlite3.Error as exc:
        _log.error("execute failed — query=%r params=%r error=%s", query, params, exc)
        raise


def fetch_one(query: str, params: tuple[Any, ...] = ()) -> tuple | None:
    """Run a READ query and return the first matching row, or None."""
    try:
        with Connection(QueryType.READ, DB_FILE) as cur:
            return cur.execute(query, params).fetchone()
    except sqlite3.Error as exc:
        _log.error("fetch_one failed — query=%r params=%r error=%s", query, params, exc)
        raise


def fetch_many(query: str, params: tuple[Any, ...] = ()) -> list[tuple]:
    """Run a READ query and return all matching rows."""
    try:
        with Connection(QueryType.READ, DB_FILE) as cur:
            return cur.execute(query, params).fetchall()
    except sqlite3.Error as exc:
        _log.error("fetch_many failed — query=%r params=%r error=%s", query, params, exc)
        raise
