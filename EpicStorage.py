"""Epic-domain storage layer.

Manages the `epics` and `task_catalog` tables.
Commands.py calls these functions; it never imports from db/ directly.
Following the same patterns established by Storage.py.
"""
from datetime import date, timedelta

import db.repository as repo


# ---------------------------------------------------------------------------
# Epic management
# ---------------------------------------------------------------------------

def add_epic(name: str) -> int | None:
    """Create a new Epic with the given name.

    Returns the new row ID on success, or None if an Epic with that name
    already exists.
    """
    existing = repo.fetch_one("SELECT id FROM epics WHERE name = ?", (name,))
    if existing:
        return None
    repo.execute(
        "INSERT INTO epics (name, created_at) VALUES (?, datetime('now'))",
        (name,),
    )
    row = repo.fetch_one("SELECT id FROM epics WHERE name = ?", (name,))
    return row[0] if row else None


def list_epics() -> list[tuple]:
    """Return [(id, name)] for all Epics, sorted alphabetically by name."""
    return repo.fetch_many("SELECT id, name FROM epics ORDER BY name")


def get_epic_by_id(epic_id: int) -> tuple | None:
    """Return (id, name) for the given Epic ID, or None if not found."""
    return repo.fetch_one("SELECT id, name FROM epics WHERE id = ?", (epic_id,))


# ---------------------------------------------------------------------------
# Task catalog
# ---------------------------------------------------------------------------

def get_task_epic(task_id: str) -> tuple | None:
    """Return (epic_id, epic_name) for the given task identifier, or None.

    Returns None when the task has no entry in task_catalog — meaning
    it either predates this feature or the user pressed Esc in the modal.
    """
    return repo.fetch_one(
        "SELECT tc.epic_id, e.name "
        "FROM task_catalog tc "
        "JOIN epics e ON e.id = tc.epic_id "
        "WHERE tc.task_id = ?",
        (task_id,),
    )


def link_task_to_epic(task_id: str, epic_id: int) -> None:
    """Write a task_catalog entry linking task_id to epic_id."""
    repo.execute(
        "INSERT INTO task_catalog (task_id, epic_id, created_at) VALUES (?, ?, datetime('now'))",
        (task_id, epic_id),
    )


# ---------------------------------------------------------------------------
# Epic summary query
# ---------------------------------------------------------------------------

def get_epic_summary_data(week_num: int, year: int) -> list[tuple]:
    """Return session data grouped by day, then Epic, for the target ISO week.

    Returns a list of (date_str, epic_name_or_None, task_id, total_minutes) rows.
    - date_str is the session date (YYYY-MM-DD).
    - epic_name_or_None is None for tasks with no task_catalog entry (Misc).
    - Rows are sorted: by date, then named Epics alphabetically within each day,
      then None (Misc) last within each day, then tasks alphabetically.

    Open sessions (end IS NULL) and sessions with no task are excluded.
    """
    # Compute the Monday–Sunday date range for the ISO week.
    # This matches the same week-boundary logic used across the rest of the app.
    jan4 = date(year, 1, 4)
    week1_monday = jan4 - timedelta(days=jan4.weekday())
    monday = week1_monday + timedelta(weeks=week_num - 1)
    sunday = monday + timedelta(days=6)
    monday_str = monday.strftime("%Y-%m-%d")
    sunday_str = sunday.strftime("%Y-%m-%d")

    return repo.fetch_many(
        """
        SELECT
            s.date AS date_str,
            e.name AS epic_name,
            s.task AS task_id,
            SUM(
                (CAST(substr(s.end,   1, 2) AS INTEGER) * 60
                 + CAST(substr(s.end,   4, 2) AS INTEGER))
                - (CAST(substr(s.start, 1, 2) AS INTEGER) * 60
                 + CAST(substr(s.start, 4, 2) AS INTEGER))
            ) AS total_minutes
        FROM sessions s
        LEFT JOIN task_catalog tc ON tc.task_id = s.task
        LEFT JOIN epics e ON e.id = tc.epic_id
        WHERE s.end IS NOT NULL
          AND s.date >= ?
          AND s.date <= ?
          AND COALESCE(s.task, '') != ''
        GROUP BY s.date, e.name, s.task
        ORDER BY
            s.date,
            CASE WHEN e.name IS NULL THEN 1 ELSE 0 END,
            e.name,
            s.task
        """,
        (monday_str, sunday_str),
    )
