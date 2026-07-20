"""Settings storage layer.

Manages the `settings` table in the SQLite database.
Commands.py calls SettingsRepository; it never imports from db/ directly.
Follows the same patterns established by EpicStorage.py.

The application works correctly with an empty `settings` table — all
getters return documented defaults when no row exists for a given key.
"""
import json
from datetime import datetime

import db.repository as repo


# ---------------------------------------------------------------------------
# Module-level utility (no DB access)
# ---------------------------------------------------------------------------

def filter_sessions_for_hours(
    sessions: list[tuple],
    lunch_excluded: bool,
    excluded_tasks: list[str],
) -> list[tuple]:
    """Return a filtered copy of sessions for working-hours calculation.

    Removes:
    - Lunch sessions when lunch_excluded is True.
    - Any session whose task is in excluded_tasks.

    This is a pure function — no database access. The full sessions list
    is still used for display; this filtered list is used only for totals
    and progress calculations.

    Args:
        sessions: List of (start, end, task) tuples.
        lunch_excluded: If True, sessions with task == 'Lunch' are excluded.
        excluded_tasks: Task identifiers that should not count toward hours.
    """
    result = []
    for s, e, t in sessions:
        if lunch_excluded and t == "Lunch":
            continue
        if t in excluded_tasks:
            continue
        result.append((s, e, t))
    return result


# ---------------------------------------------------------------------------
# SettingsRepository
# ---------------------------------------------------------------------------

class SettingsRepository:
    """Key-value settings repository backed by the `settings` SQLite table.

    Each getter returns a typed default when no row exists, so the
    application behaves correctly on a fresh database with no settings.

    Each setter writes a single key using INSERT OR REPLACE with the
    current local datetime as updated_at (for human-readable auditing).
    """

    # Key constants prevent typos when reading and writing.
    _KEY_DAILY_WORK_TARGET = "daily_work_target_hours"
    _KEY_LUNCH_EXCLUDED = "lunch_excluded"
    _KEY_LUNCH_PROMARK_OFFSET = "lunch_promark_offset_minutes"
    _KEY_EXCLUDED_TASKS = "excluded_tasks"
    _KEY_ALWAYS_SEPARATE = "always_separate_tasks"

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _get(self, key: str) -> str | None:
        """Fetch the raw string value for a key, or None if not set."""
        row = repo.fetch_one("SELECT value FROM settings WHERE key = ?", (key,))
        return row[0] if row else None

    def _set(self, key: str, value: str) -> None:
        """Write a key-value pair using INSERT OR REPLACE."""
        updated_at = datetime.now().isoformat(timespec="seconds")
        repo.execute(
            "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, updated_at),
        )

    # ------------------------------------------------------------------ #
    # Daily work target
    # ------------------------------------------------------------------ #

    def get_daily_work_target(self) -> float:
        """Return the daily work target in hours. Default: 7.4 (37-hour week)."""
        raw = self._get(self._KEY_DAILY_WORK_TARGET)
        if raw is None:
            return 7.4
        try:
            return float(raw)
        except ValueError:
            return 7.4

    def set_daily_work_target(self, hours: float) -> None:
        """Persist the daily work target in hours."""
        self._set(self._KEY_DAILY_WORK_TARGET, str(hours))

    # ------------------------------------------------------------------ #
    # Lunch exclusion
    # ------------------------------------------------------------------ #

    def get_lunch_excluded(self) -> bool:
        """Return whether Lunch sessions are excluded from hours total. Default: True."""
        raw = self._get(self._KEY_LUNCH_EXCLUDED)
        if raw is None:
            return True
        return raw.lower() == "true"

    def set_lunch_excluded(self, excluded: bool) -> None:
        """Persist the lunch exclusion toggle."""
        self._set(self._KEY_LUNCH_EXCLUDED, "true" if excluded else "false")

    # ------------------------------------------------------------------ #
    # Lunch Promark offset
    # ------------------------------------------------------------------ #

    def get_lunch_promark_offset_minutes(self) -> int:
        """Return the expected lunch duration for the Promark offset. Default: 0.

        When the actual Lunch session on a given day is shorter than this
        offset, the shortfall is added to the Promark consolidated end time.
        """
        raw = self._get(self._KEY_LUNCH_PROMARK_OFFSET)
        if raw is None:
            return 0
        try:
            return int(raw)
        except ValueError:
            return 0

    def set_lunch_promark_offset_minutes(self, minutes: int) -> None:
        """Persist the Promark lunch offset in minutes."""
        self._set(self._KEY_LUNCH_PROMARK_OFFSET, str(minutes))

    # ------------------------------------------------------------------ #
    # Excluded tasks
    # ------------------------------------------------------------------ #

    def get_excluded_tasks(self) -> list[str]:
        """Return task identifiers excluded from working-hours totals. Default: [].

        Excluded tasks are still recorded and visible in all panels —
        they are only omitted from hours calculations and the progress bar.
        """
        raw = self._get(self._KEY_EXCLUDED_TASKS)
        if raw is None:
            return []
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return []

    def set_excluded_tasks(self, tasks: list[str]) -> None:
        """Persist the list of excluded task identifiers as JSON."""
        self._set(self._KEY_EXCLUDED_TASKS, json.dumps(tasks))

    # ------------------------------------------------------------------ #
    # Always-separate tasks (Promark)
    # ------------------------------------------------------------------ #

    def get_always_separate_tasks(self) -> list[str]:
        """Return tasks that appear as standalone rows in Promark output. Default: [].

        Always-separate tasks DO count toward the working-hours total —
        the separation is exclusively a Promark representation concern.
        """
        raw = self._get(self._KEY_ALWAYS_SEPARATE)
        if raw is None:
            return []
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return []

    def set_always_separate_tasks(self, tasks: list[str]) -> None:
        """Persist the list of always-separate task identifiers as JSON."""
        self._set(self._KEY_ALWAYS_SEPARATE, json.dumps(tasks))
