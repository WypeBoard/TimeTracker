"""Independent access to the shared `epics` / `task_catalog` tables.

Per features/standalone-web-app.md Non-Goals, webapp/ does not import
app/EpicStorage.py. This module re-implements the handful of operations
the Today page needs (New Session's task + conditional Epic step), against
the same schema app/Storage.py already created.
"""
import db.repository as repo


def list_epics() -> list[tuple]:
    """Return [(id, name)] for all Epics, sorted alphabetically by name."""
    return repo.fetch_many("SELECT id, name FROM epics ORDER BY name")


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


def get_task_epic(task_id: str) -> tuple | None:
    """Return (epic_id, epic_name) for the given task identifier, or None."""
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


def list_known_tasks() -> list[str]:
    """Return every distinct task identifier ever logged or cataloged.

    Union of `sessions.task` (excluding blanks and the reserved "Lunch"
    marker) and `task_catalog.task_id`, sorted alphabetically. Populates
    the New Session modal's task field — see Manual Changes, 2026-11-24,
    "Today page: quick-action buttons and modal design" ("Task selection
    from the full task catalog").
    """
    rows = repo.fetch_many(
        "SELECT task FROM sessions WHERE task != '' AND task != 'Lunch' "
        "UNION "
        "SELECT task_id FROM task_catalog "
        "ORDER BY 1"
    )
    return [r[0] for r in rows]
