"""Tests for the Today page (features/standalone-web-app.md, Phase 3):
quick-action buttons, Quick Stats, the session table, and the five
mutating endpoints (New Session/Resume/Lunch, each with its "now" bypass
where applicable).
"""
from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

import db.repository as repo
from webapp.main import app


@pytest.fixture
def client(isolated_db):
    return TestClient(app)


def _insert_session(start: str, end: str | None, task: str, d: str | None = None) -> None:
    repo.execute(
        "INSERT INTO sessions (date, start, end, task) VALUES (?, ?, ?, ?)",
        (d or date.today().strftime("%Y-%m-%d"), start, end, task),
    )


def _get_task_epic_name(task: str) -> str | None:
    row = repo.fetch_one(
        "SELECT e.name FROM task_catalog tc JOIN epics e ON e.id = tc.epic_id WHERE tc.task_id = ?",
        (task,),
    )
    return row[0] if row else None


# ---------------------------------------------------------------------------
# GET /today
# ---------------------------------------------------------------------------

def test_today_page_shows_empty_state(client):
    response = client.get("/today")
    assert response.status_code == 200
    assert "No sessions today." in response.text
    assert "New Session" in response.text
    assert "Resume" in response.text
    assert "Lunch" in response.text


def test_today_page_lists_sessions_with_epic_name(client):
    _insert_session("09:00", "10:00", "TASK-1")
    repo.execute("INSERT INTO epics (name, created_at) VALUES (?, datetime('now'))", ("Platform",))
    epic_id = repo.fetch_one("SELECT id FROM epics WHERE name = 'Platform'")[0]
    repo.execute(
        "INSERT INTO task_catalog (task_id, epic_id, created_at) VALUES (?, ?, datetime('now'))",
        ("TASK-1", epic_id),
    )

    response = client.get("/today")
    assert response.status_code == 200
    assert "TASK-1" in response.text
    assert "Platform" in response.text
    assert "1.00h" in response.text


# ---------------------------------------------------------------------------
# POST /sessions/new
# ---------------------------------------------------------------------------

def test_new_session_opens_a_session(client):
    response = client.post("/sessions/new", data={"task": "TASK-9", "start_time": "09:00"})
    assert response.status_code == 200
    assert "TASK-9" in response.text

    row = repo.fetch_one("SELECT date, start, end, task FROM sessions WHERE task = 'TASK-9'")
    assert row[1] == "09:00"
    assert row[2] is None


def test_new_session_auto_closes_open_session_then_starts_new_one(client):
    """Starting a New Session while one is already running auto-closes the
    old one at the given start time instead of rejecting — matches the
    TUI's long-standing Resume/Lunch auto-close workflow (see Manual
    Changes, "New Session: auto-close the running session instead of
    rejecting")."""
    _insert_session("08:00", None, "TASK-1")
    response = client.post("/sessions/new", data={"task": "TASK-9", "start_time": "09:00"})
    assert response.status_code == 200
    assert "already running" not in response.text

    closed = repo.fetch_one("SELECT end FROM sessions WHERE task = 'TASK-1'")
    assert closed[0] == "09:00"
    opened = repo.fetch_one("SELECT start, end FROM sessions WHERE task = 'TASK-9'")
    assert opened == ("09:00", None)
    count = repo.fetch_one("SELECT COUNT(*) FROM sessions")[0]
    assert count == 2


def test_new_session_links_a_new_epic(client):
    response = client.post(
        "/sessions/new",
        data={
            "task": "TASK-9",
            "start_time": "09:00",
            "epic_id": "__new__",
            "new_epic_name": "Platform Ops",
        },
    )
    assert response.status_code == 200
    assert _get_task_epic_name("TASK-9") == "Platform Ops"


def test_new_session_ignores_epic_fields_when_task_already_linked(client):
    repo.execute("INSERT INTO epics (name, created_at) VALUES (?, datetime('now'))", ("Existing",))
    epic_id = repo.fetch_one("SELECT id FROM epics WHERE name = 'Existing'")[0]
    repo.execute(
        "INSERT INTO task_catalog (task_id, epic_id, created_at) VALUES (?, ?, datetime('now'))",
        ("TASK-1", epic_id),
    )

    response = client.post(
        "/sessions/new",
        data={
            "task": "TASK-1",
            "start_time": "09:00",
            "epic_id": "__new__",
            "new_epic_name": "Should Not Apply",
        },
    )
    assert response.status_code == 200
    assert _get_task_epic_name("TASK-1") == "Existing"


# ---------------------------------------------------------------------------
# POST /sessions/resume + /sessions/resume/now
# ---------------------------------------------------------------------------

def test_resume_closes_open_session_and_opens_new_one(client):
    _insert_session("08:00", None, "TASK-1")
    response = client.post("/sessions/resume", data={"task": "TASK-2", "start_time": "10:00"})
    assert response.status_code == 200

    closed = repo.fetch_one("SELECT end FROM sessions WHERE task = 'TASK-1'")
    assert closed[0] == "10:00"
    opened = repo.fetch_one("SELECT start, end FROM sessions WHERE task = 'TASK-2'")
    assert opened == ("10:00", None)


def test_resume_rejects_when_no_sessions_today(client):
    response = client.post("/sessions/resume", data={"task": "TASK-2", "start_time": "10:00"})
    assert response.status_code == 200
    assert "No sessions today" in response.text


def test_resume_now_carries_last_work_task_skipping_lunch(client):
    _insert_session("08:00", "09:00", "TASK-1")
    _insert_session("09:00", None, "Lunch")
    response = client.post("/sessions/resume/now")
    assert response.status_code == 200

    rows = repo.fetch_many("SELECT task, end FROM sessions ORDER BY id")
    # Lunch was closed, and a new session carrying TASK-1 forward was opened.
    assert rows[1][1] is not None  # Lunch closed
    assert rows[2][0] == "TASK-1"
    assert rows[2][1] is None


# ---------------------------------------------------------------------------
# POST /sessions/lunch + /sessions/lunch/now
# ---------------------------------------------------------------------------

def test_lunch_closes_open_session_and_starts_lunch(client):
    _insert_session("08:00", None, "TASK-1")
    response = client.post("/sessions/lunch", data={"start_time": "12:00"})
    assert response.status_code == 200

    closed = repo.fetch_one("SELECT end FROM sessions WHERE task = 'TASK-1'")
    assert closed[0] == "12:00"
    lunch = repo.fetch_one("SELECT start, end FROM sessions WHERE task = 'Lunch'")
    assert lunch == ("12:00", None)


def test_lunch_now_uses_current_time(client):
    response = client.post("/sessions/lunch/now")
    assert response.status_code == 200
    lunch = repo.fetch_one("SELECT task, end FROM sessions WHERE task = 'Lunch'")
    assert lunch is not None
    assert lunch[1] is None


# ---------------------------------------------------------------------------
# POST /sessions/stop + /sessions/stop/now
# ---------------------------------------------------------------------------

def test_stop_closes_open_session(client):
    _insert_session("08:00", None, "TASK-1")
    response = client.post("/sessions/stop", data={"end_time": "12:00"})
    assert response.status_code == 200

    closed = repo.fetch_one("SELECT end FROM sessions WHERE task = 'TASK-1'")
    assert closed[0] == "12:00"


def test_stop_rejects_when_no_session_open(client):
    response = client.post("/sessions/stop", data={"end_time": "12:00"})
    assert response.status_code == 200
    assert "No active session to stop" in response.text


def test_stop_now_uses_current_time(client):
    _insert_session("08:00", None, "TASK-1")
    response = client.post("/sessions/stop/now")
    assert response.status_code == 200
    closed = repo.fetch_one("SELECT end FROM sessions WHERE task = 'TASK-1'")
    assert closed[0] is not None


# ---------------------------------------------------------------------------
# Quick Stats
# ---------------------------------------------------------------------------

def test_quick_stats_sessions_count_and_target(client):
    repo.execute(
        "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES "
        "('daily_work_target_hours', '7.4', datetime('now'))"
    )
    _insert_session("08:00", "09:30", "TASK-1")
    _insert_session("09:30", "10:00", "TASK-2")

    response = client.get("/today")
    assert response.status_code == 200
    assert "7.4h" in response.text
    # Two closed sessions today => Sessions count of 2.
    assert ">2<" in response.text


# ---------------------------------------------------------------------------
# Quick Stats client-side ticker (Manual Changes, 2026-11-27, "Quick Stats
# client-side ticker"): the baseline data embedded for
# webapp/static/js/quick-stats-ticker.js to recompute Today/Rem./Leave/Week
# every minute without a network round-trip.
# ---------------------------------------------------------------------------

def test_quick_stats_ticker_data_absent_when_no_open_session(client):
    _insert_session("08:00", "09:00", "TASK-1")
    response = client.get("/today")
    assert response.status_code == 200
    assert 'id="quick-stats-row"' in response.text
    assert '"active_start": null' in response.text


def test_quick_stats_ticker_data_present_when_session_open(client):
    _insert_session("08:00", None, "TASK-1")
    response = client.get("/today")
    assert response.status_code == 200
    assert '"active_start": "08:00"' in response.text
    assert '"baseline_today": 0.0' in response.text
    assert "initQuickStatsTicker();" in response.text


def test_quick_stats_ticker_baseline_excludes_active_session_hours(client):
    """baseline_today_logged must be the *completed*-session total only, so
    the client can add its own freshly-computed active-session hours on
    top without double counting."""
    _insert_session("08:00", "09:00", "TASK-1")  # 1h completed
    _insert_session("09:00", None, "TASK-2")  # open
    response = client.get("/today")
    assert response.status_code == 200
    assert '"baseline_today": 1.0' in response.text
