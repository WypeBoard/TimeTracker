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
        self.log_calls: list[tuple] = []      # (week_days, week_num, year)
        self.promark_calls: list[tuple] = []  # (week_days, week_num, year)
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
