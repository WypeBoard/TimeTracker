"""Generic database helpers.

All direct use of Connection is centralised here so that the rest of the
codebase never needs to know about the db/ package directly.
Storage.py calls these helpers; Commands.py calls Storage.py.
"""
from typing import Any

from Constants import DB_FILE
from db.connection import Connection
from db.query_type import QueryType


def execute(query: str, params: tuple[Any, ...] = ()) -> None:
    """Run a WRITE query (INSERT / UPDATE / DELETE) and commit."""
    with Connection(QueryType.WRITE, DB_FILE) as cur:
        cur.execute(query, params)


def fetch_one(query: str, params: tuple[Any, ...] = ()) -> tuple | None:
    """Run a READ query and return the first matching row, or None."""
    with Connection(QueryType.READ, DB_FILE) as cur:
        return cur.execute(query, params).fetchone()


def fetch_many(query: str, params: tuple[Any, ...] = ()) -> list[tuple]:
    """Run a READ query and return all matching rows."""
    with Connection(QueryType.READ, DB_FILE) as cur:
        return cur.execute(query, params).fetchall()
