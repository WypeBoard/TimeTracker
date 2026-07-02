"""Smoke tests for TimeTracker command layer.

These are integration tests that exercise the full command → storage →
read-back cycle against a real (file-backed) SQLite database. They do NOT
test the Textual TUI widgets.

Each test uses pytest's tmp_path fixture for an isolated database, so tests
are independent and leave no side-effects on the production database.

RecordingContext
---------------
A test double for AppContext that records every message delivered via
info/warning/error, and also records show_log / show_promark call arguments.
This lets tests assert on which methods were called without needing stdout
capture.
"""
from __future__ import annotations

import sys
import os
from datetime import date, datetime, timedelta

import pytest

# ---------------------------------------------------------------------------
# sys.path: allow importing from the project root even when pytest is run
# from a subdirectory.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from Storage import create_schema, get_today_sessions, get_open_session
from Commands import (
    cmd_start, cmd_pause, cmd_stop, cmd_resume, cmd_restart,
    cmd_task, cmd_log, _build_day_status, _session_hours,
    cmd_epic_add, cmd_epic_list, cmd_epic_summary,
)
import db.repository as repo


# ---------------------------------------------------------------------------
# Test double
# ---------------------------------------------------------------------------

class RecordingContext:
    """Minimal AppContext implementation that records calls for assertions."""

    def __init__(self) -> None:
        self.infos: list[str] = []
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.log_calls: list[tuple] = []           # (week_days, week_num, year)
        self.promark_calls: list[tuple] = []       # (week_days, week_num, year)
        self.new_task_calls: list[str] = []        # task_ids passed to on_new_task
        self.epic_summary_calls: list[tuple] = []  # (week_num, year)
        self.session_changed_count: int = 0

    def info(self, message: str) -> None:
        self.infos.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def on_session_changed(self) -> None:
        self.session_changed_count += 1

    def on_day_stopped(self, status) -> None:
        pass  # not relevant for smoke tests

    def show_log(self, week_days: dict, week_num: int, year: int) -> None:
        self.log_calls.append((week_days, week_num, year))

    def show_promark(self, week_days: dict, week_num: int, year: int) -> None:
        self.promark_calls.append((week_days, week_num, year))

    def on_new_task(self, task_id: str) -> None:
        self.new_task_calls.append(task_id)

    def show_epic_summary(self, week_num: int, year: int) -> None:
        self.epic_summary_calls.append((week_num, year))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db(tmp_path, monkeypatch):
    """Provide an isolated SQLite database for each test.

    monkeypatch replaces the DB_FILE module-level variable in every module
    that imported it from Constants. This is the standard approach for
    redirecting file-based singletons in tests.
    """
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("db.repository.DB_FILE", db_path)
    monkeypatch.setattr("Storage.DB_FILE", db_path)
    create_schema()
    return db_path


# ---------------------------------------------------------------------------
# Normal day scenario
# ---------------------------------------------------------------------------

def test_normal_day_sequence(db):
    """Full working day: start → pause → resume → stop → start → stop."""
    ctx = RecordingContext()

    # Session 1: 07:00 – 11:20
    cmd_start(ctx, "07:00", "TASK-1234")
    assert not ctx.errors, f"Unexpected errors: {ctx.errors}"
    assert any("07:00" in m for m in ctx.infos)

    cmd_pause(ctx, "11:20")
    assert not ctx.errors

    # Session 2: 11:50 – 14:45  (epic carried from session 1)
    cmd_resume(ctx, "11:50")
    assert not ctx.errors
    assert any("TASK-1234" in m for m in ctx.infos), (
        "resume should confirm the carried epic in its output"
    )

    # ── mid-sequence status check (simulating ≈ 14:00) ──────────────────
    mid_status = _build_day_status(datetime.now().replace(hour=14, minute=0))
    assert mid_status.active_start == "11:50", (
        f"Expected active session at 11:50, got {mid_status.active_start!r}"
    )
    assert mid_status.remaining > 0, "Should still have hours remaining at 14:00"
    # leave time must be computable (remaining > 0 and session is active)
    assert mid_status.active_hours > 0

    cmd_stop(ctx, "14:45")
    assert not ctx.errors

    # Session 3: 21:00 – 21:30  (no epic)
    cmd_start(ctx, "21:00")
    cmd_stop(ctx, "21:30")

    # ── final assertions ─────────────────────────────────────────────────
    sessions = get_today_sessions()
    assert len(sessions) == 3, f"Expected 3 sessions, got {len(sessions)}"
    assert all(s[2] is not None for s in sessions), "All sessions should be closed"

    # sessions = [(id, start, end, task), ...]
    _, s1_start, s1_end, s1_task = sessions[0]
    _, s2_start, s2_end, s2_task = sessions[1]
    _, s3_start, s3_end, s3_task = sessions[2]

    assert (s1_start, s1_end, s1_task) == ("07:00", "11:20", "TASK-1234")
    assert (s2_start, s2_end, s2_task) == ("11:50", "14:45", "TASK-1234")
    assert (s3_start, s3_end) == ("21:00", "21:30")
    assert s3_task == "", f"Session 3 should have no task, got {s3_task!r}"

    total = sum(_session_hours(s[1], s[2]) for s in sessions)
    assert abs(total - 7.75) < 0.01, f"Expected total 7.75h, got {total:.4f}h"


# ---------------------------------------------------------------------------
# resume carries epic
# ---------------------------------------------------------------------------

def test_resume_carries_epic(db):
    """resume opens a new session with the last session's epic."""
    ctx = RecordingContext()

    cmd_start(ctx, "09:00", "Epic-99")
    cmd_pause(ctx, "12:00")
    cmd_resume(ctx, "13:00")

    sessions = get_today_sessions()
    assert len(sessions) == 2

    open_sess = get_open_session()
    assert open_sess is not None, "Should have an open session after resume"
    _id, _date, start, task = open_sess
    assert start == "13:00"
    assert task == "Epic-99", f"Epic should be carried forward, got {task!r}"


def test_resume_with_open_session(db):
    """resume on an open session closes it first, then opens a new one."""
    ctx = RecordingContext()

    cmd_start(ctx, "08:00", "Epic-55")
    # Session is still open — resume should close + reopen
    cmd_resume(ctx, "10:00")

    sessions = get_today_sessions()
    # Should now have session 1 (closed 08:00–10:00) + session 2 (open from 10:00)
    assert len(sessions) == 2

    closed = [s for s in sessions if s[2] is not None]
    open_list = [s for s in sessions if s[2] is None]
    assert len(closed) == 1
    assert len(open_list) == 1
    assert closed[0][1] == "08:00" and closed[0][2] == "10:00"
    assert open_list[0][1] == "10:00" and open_list[0][3] == "Epic-55"


def test_resume_no_sessions_today(db):
    """resume with no sessions today prints an error and does nothing."""
    ctx = RecordingContext()
    cmd_resume(ctx, "09:00")

    assert ctx.errors, "Should have received an error message"
    assert get_today_sessions() == []


# ---------------------------------------------------------------------------
# task -s N
# ---------------------------------------------------------------------------

def test_task_targets_specific_session(db):
    """task -s N updates only the specified session."""
    ctx = RecordingContext()

    # Create 3 closed sessions manually via repo to keep test simple.
    today = date.today().strftime("%Y-%m-%d")
    repo.execute(
        "INSERT INTO sessions (date, start, end, task) VALUES (?, '08:00', '09:00', 'OldTask')",
        (today,),
    )
    repo.execute(
        "INSERT INTO sessions (date, start, end, task) VALUES (?, '09:30', '10:30', 'OldTask')",
        (today,),
    )
    repo.execute(
        "INSERT INTO sessions (date, start, end, task) VALUES (?, '11:00', '12:00', 'OldTask')",
        (today,),
    )

    cmd_task(ctx, "Epic-99", session_num=2)
    assert not ctx.errors

    sessions = get_today_sessions()
    assert sessions[0][3] == "OldTask", "Session 1 should be unchanged"
    assert sessions[1][3] == "Epic-99", "Session 2 should be updated"
    assert sessions[2][3] == "OldTask", "Session 3 should be unchanged"


# ---------------------------------------------------------------------------
# Double-start guard
# ---------------------------------------------------------------------------

def test_double_start_is_rejected(db):
    """A second start before stop/pause prints a warning; session count unchanged."""
    ctx = RecordingContext()

    cmd_start(ctx, "08:00")
    initial_count = len(get_today_sessions())

    cmd_start(ctx, "09:00")  # should be rejected

    assert ctx.warnings, "Should have received a warning about the running session"
    assert len(get_today_sessions()) == initial_count, (
        "Session count must not increase after a rejected start"
    )


# ---------------------------------------------------------------------------
# stop with no open session
# ---------------------------------------------------------------------------

def test_stop_with_no_session(db):
    """stop with no open session prints an error; database is unchanged."""
    ctx = RecordingContext()

    cmd_stop(ctx)

    assert ctx.errors, "Should have received an error message"
    assert get_today_sessions() == [], "Database should remain empty"


# ---------------------------------------------------------------------------
# log week filter
# ---------------------------------------------------------------------------

def test_log_week_filter(db):
    """cmd_log returns only sessions from the requested ISO week."""
    ctx = RecordingContext()
    today = date.today()
    this_week = today.isocalendar().week
    this_year = today.isocalendar().year

    # Insert a session for today (current week).
    repo.execute(
        "INSERT INTO sessions (date, start, end, task) VALUES (?, '09:00', '17:00', 'THIS-WEEK')",
        (today.strftime("%Y-%m-%d"),),
    )

    # Insert a session exactly 7 days ago (previous week in most cases; may
    # land in the same week near year boundaries — acceptable for this test).
    prev_date = today - timedelta(days=7)
    prev_week = prev_date.isocalendar().week
    prev_year = prev_date.isocalendar().year
    repo.execute(
        "INSERT INTO sessions (date, start, end, task) VALUES (?, '09:00', '17:00', 'LAST-WEEK')",
        (prev_date.strftime("%Y-%m-%d"),),
    )

    # Query the current week only.
    cmd_log(ctx, f"w{this_week:02d}")

    assert len(ctx.log_calls) == 1
    week_days, week_num, year = ctx.log_calls[0]

    assert week_num == this_week
    assert year == this_year
    assert today.strftime("%Y-%m-%d") in week_days, (
        "Today's session should appear in the current week log"
    )

    # If prev_date is in a different week (the normal case), it should be absent.
    if prev_week != this_week or prev_year != this_year:
        assert prev_date.strftime("%Y-%m-%d") not in week_days, (
            "Previous week's session must not appear in the current week log"
        )


# ---------------------------------------------------------------------------
# restart deprecation alias
# ---------------------------------------------------------------------------

def test_restart_is_deprecated_alias(db):
    """restart prints a deprecation warning and behaves like resume."""
    ctx = RecordingContext()

    cmd_start(ctx, "08:00", "Epic-42")
    cmd_restart(ctx, "10:00")

    assert any("deprecated" in w.lower() for w in ctx.warnings), (
        "restart should print a deprecation warning"
    )
    # Should still have created a new session with the carried epic.
    open_sess = get_open_session()
    assert open_sess is not None
    assert open_sess[3] == "Epic-42"


# ---------------------------------------------------------------------------
# Epic commands
# ---------------------------------------------------------------------------

def test_epic_add_and_list(db):
    """epic add creates Epics; epic list returns them alphabetically."""
    ctx = RecordingContext()

    cmd_epic_add(ctx, "Platform Team")
    cmd_epic_add(ctx, "Mobile App")

    assert not ctx.errors, f"Unexpected errors: {ctx.errors}"
    assert any("Platform Team" in m for m in ctx.infos)
    assert any("Mobile App" in m for m in ctx.infos)

    ctx2 = RecordingContext()
    cmd_epic_list(ctx2)

    assert len(ctx2.infos) == 1
    listing = ctx2.infos[0]
    # "Mobile App" comes before "Platform Team" alphabetically.
    assert listing.index("Mobile App") < listing.index("Platform Team"), (
        "epic list should be sorted alphabetically"
    )


def test_epic_add_duplicate(db):
    """epic add with a duplicate name prints a warning and writes nothing."""
    ctx = RecordingContext()

    cmd_epic_add(ctx, "Platform Team")
    cmd_epic_add(ctx, "Platform Team")

    assert ctx.warnings, "Should have warned about duplicate name"
    assert "already exists" in ctx.warnings[-1]

    from EpicStorage import list_epics
    assert len(list_epics()) == 1, "Only one Epic should exist after the duplicate attempt"


def test_epic_list_empty(db):
    """epic list with no Epics prints an informational message."""
    ctx = RecordingContext()
    cmd_epic_list(ctx)

    assert not ctx.errors
    assert ctx.infos, "epic list should output something even when empty"


def test_on_new_task_triggered_for_unknown_task(db):
    """start with an unknown task calls on_new_task."""
    ctx = RecordingContext()
    cmd_start(ctx, "08:00", "TASK-999")

    assert "TASK-999" in ctx.new_task_calls, (
        "on_new_task should be called when the task has no task_catalog entry"
    )


def test_on_new_task_not_triggered_for_known_task(db):
    """start with a task already in task_catalog does not call on_new_task."""
    from EpicStorage import add_epic, link_task_to_epic

    epic_id = add_epic("Platform")
    link_task_to_epic("TASK-123", epic_id)

    ctx = RecordingContext()
    cmd_start(ctx, "08:00", "TASK-123")

    assert ctx.new_task_calls == [], (
        "on_new_task should not be called when the task is already linked"
    )


def test_on_new_task_triggered_for_task_command(db):
    """cmd_task with an unknown task calls on_new_task."""
    ctx = RecordingContext()
    today = date.today().strftime("%Y-%m-%d")
    repo.execute(
        "INSERT INTO sessions (date, start, end, task) VALUES (?, '09:00', '10:00', '')",
        (today,),
    )

    cmd_task(ctx, "TASK-789")
    assert "TASK-789" in ctx.new_task_calls


def test_epic_summary_data_groups_correctly(db):
    """get_epic_summary_data groups known tasks under Epic and unknowns under None."""
    from EpicStorage import add_epic, link_task_to_epic, get_epic_summary_data

    today = date.today()
    week_num = today.isocalendar().week
    year = today.isocalendar().year
    today_str = today.strftime("%Y-%m-%d")

    # Two sessions: TASK-1 linked, TASK-2 unlinked.
    repo.execute(
        "INSERT INTO sessions (date, start, end, task) VALUES (?, '08:00', '10:00', 'TASK-1')",
        (today_str,),
    )
    repo.execute(
        "INSERT INTO sessions (date, start, end, task) VALUES (?, '10:00', '12:00', 'TASK-2')",
        (today_str,),
    )

    epic_id = add_epic("Platform")
    link_task_to_epic("TASK-1", epic_id)

    data = get_epic_summary_data(week_num, year)

    # Should have two rows: one for Platform/TASK-1 and one for None/(Misc)/TASK-2.
    # Each row is (date_str, epic_name_or_None, task_id, total_minutes).
    assert len(data) == 2, f"Expected 2 rows, got {len(data)}: {data}"

    epic_names = [row[1] for row in data]
    task_ids = [row[2] for row in data]

    assert "Platform" in epic_names, "TASK-1 should be under Platform"
    assert None in epic_names, "TASK-2 should be under (Misc) — i.e. None"
    assert "TASK-1" in task_ids
    assert "TASK-2" in task_ids

    # Verify minutes: TASK-1 is 2h = 120 min, TASK-2 is 2h = 120 min.
    minutes_by_task = {row[2]: row[3] for row in data}
    assert minutes_by_task["TASK-1"] == 120
    assert minutes_by_task["TASK-2"] == 120


def test_epic_summary_named_before_misc(db):
    """get_epic_summary_data returns named Epics before (Misc)."""
    from EpicStorage import add_epic, link_task_to_epic, get_epic_summary_data

    today = date.today()
    week_num = today.isocalendar().week
    year = today.isocalendar().year
    today_str = today.strftime("%Y-%m-%d")

    repo.execute(
        "INSERT INTO sessions (date, start, end, task) VALUES (?, '08:00', '09:00', 'TASK-X')",
        (today_str,),
    )
    repo.execute(
        "INSERT INTO sessions (date, start, end, task) VALUES (?, '09:00', '10:00', 'TASK-MISC')",
        (today_str,),
    )

    epic_id = add_epic("Zebra Epic")
    link_task_to_epic("TASK-X", epic_id)

    data = get_epic_summary_data(week_num, year)
    # Each row is (date_str, epic_name_or_None, task_id, total_minutes).
    epic_names = [row[1] for row in data]

    assert epic_names[0] == "Zebra Epic", "Named Epic should come first"
    assert epic_names[-1] is None, "(Misc) should be last"


def test_epic_summary_empty_week(db):
    """cmd_epic_summary delegates to show_epic_summary with no error."""
    ctx = RecordingContext()
    cmd_epic_summary(ctx)

    assert not ctx.errors
    assert len(ctx.epic_summary_calls) == 1

    week_num, year = ctx.epic_summary_calls[0]
    today_iso = date.today().isocalendar()
    assert week_num == today_iso.week
    assert year == today_iso.year


def test_epic_summary_excludes_sessions_without_task(db):
    """Sessions with no task label are not included in the epic summary."""
    from EpicStorage import get_epic_summary_data

    today = date.today()
    week_num = today.isocalendar().week
    year = today.isocalendar().year
    today_str = today.strftime("%Y-%m-%d")

    # Session with empty task.
    repo.execute(
        "INSERT INTO sessions (date, start, end, task) VALUES (?, '08:00', '10:00', '')",
        (today_str,),
    )

    data = get_epic_summary_data(week_num, year)
    assert data == [], "Sessions with no task should not appear in epic summary data"
