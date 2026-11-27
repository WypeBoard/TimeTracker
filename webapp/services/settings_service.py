"""Read-only access to the shared `settings` table for webapp/ services.

Per features/standalone-web-app.md Non-Goals, webapp/ does not import or
call app/SettingsStorage.py's SettingsRepository directly. This module is
an independent re-implementation of the *getters* that today_service.py
needs (daily target, lunch handling, excluded/always-separate task lists),
using docs/detailed-design/configuration.md's documented key names and
defaults as the authoritative schema reference — the same reference
SettingsRepository itself follows, so both apps keep reading settings the
same way without either one importing the other.

Phase 3 only needs reads (Quick Stats, the resume carry-forward skip-list).
Phase 5 (Settings page) is expected to extend this module with the
corresponding setters and the corrupt-list guard, rather than creating a
second settings module.
"""
import json

import db.repository as repo

_KEY_DAILY_WORK_TARGET = "daily_work_target_hours"
_KEY_LUNCH_EXCLUDED = "lunch_excluded"
_KEY_LUNCH_DURATION = "lunch_duration_minutes"
_KEY_EXCLUDED_TASKS = "excluded_tasks"
_KEY_ALWAYS_SEPARATE = "always_separate_tasks"

DEFAULT_DAILY_WORK_TARGET_HOURS = 7.4
DEFAULT_LUNCH_EXCLUDED = True
DEFAULT_LUNCH_DURATION_MINUTES = 30


def _get(key: str) -> str | None:
    row = repo.fetch_one("SELECT value FROM settings WHERE key = ?", (key,))
    return row[0] if row else None


def get_daily_work_target() -> float:
    """Return the daily work target in hours. Default: 7.4 (37-hour week)."""
    raw = _get(_KEY_DAILY_WORK_TARGET)
    if raw is None:
        return DEFAULT_DAILY_WORK_TARGET_HOURS
    try:
        return float(raw)
    except ValueError:
        return DEFAULT_DAILY_WORK_TARGET_HOURS


def get_lunch_excluded() -> bool:
    """Return whether Lunch sessions are excluded from hours totals. Default: True."""
    raw = _get(_KEY_LUNCH_EXCLUDED)
    if raw is None:
        return DEFAULT_LUNCH_EXCLUDED
    return raw.lower() == "true"


def get_lunch_duration_minutes() -> int:
    """Return the configured lunch duration in minutes. Default: 30.

    Does not implement the retired-key migration read that
    app/SettingsStorage.py performs for `lunch_promark_offset_minutes` —
    that is a one-time legacy-data concern owned by the TUI's settings
    writer; webapp/ only needs the current, documented key.
    """
    raw = _get(_KEY_LUNCH_DURATION)
    if raw is None:
        return DEFAULT_LUNCH_DURATION_MINUTES
    try:
        return int(raw)
    except ValueError:
        return DEFAULT_LUNCH_DURATION_MINUTES


def get_excluded_tasks() -> list[str]:
    """Return task identifiers excluded from working-hours totals. Default: []."""
    return _get_json_list(_KEY_EXCLUDED_TASKS)


def get_always_separate_tasks() -> list[str]:
    """Return tasks that appear as standalone Promark-style rows. Default: []."""
    return _get_json_list(_KEY_ALWAYS_SEPARATE)


def _get_json_list(key: str) -> list[str]:
    raw = _get(key)
    if raw is None:
        return []
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return []
    if not isinstance(value, list) or not all(isinstance(i, str) for i in value):
        return []
    return value
