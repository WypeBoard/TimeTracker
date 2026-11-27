"""Tests for the Weekly page (features/standalone-web-app.md, Phase 4):
the independent day -> Epic -> task view, week navigation, and the
Promark-style consolidated day span.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

import db.repository as repo
from webapp.main import app


@pytest.fixture
def client(isolated_db):
    return TestClient(app)


def _target_week() -> tuple[int, int, date]:
    """A week guaranteed not to be the current ISO week, so "next" stays
    enabled and results are stable regardless of when the suite runs."""
    today_iso = date.today().isocalendar()
    year, week = today_iso.year, today_iso.week
    if week > 1:
        week -= 1
    else:
        year -= 1
        week = date(year, 12, 28).isocalendar().week
    monday = date.fromisocalendar(year, week, 1)
    return year, week, monday


def _insert_closed_session(d: date, start: str, end: str, task: str) -> None:
    repo.execute(
        "INSERT INTO sessions (date, start, end, task) VALUES (?, ?, ?, ?)",
        (d.strftime("%Y-%m-%d"), start, end, task),
    )


def _link_epic(task: str, epic_name: str) -> None:
    repo.execute("INSERT INTO epics (name, created_at) VALUES (?, datetime('now'))", (epic_name,))
    epic_id = repo.fetch_one("SELECT id FROM epics WHERE name = ?", (epic_name,))[0]
    repo.execute(
        "INSERT INTO task_catalog (task_id, epic_id, created_at) VALUES (?, ?, datetime('now'))",
        (task, epic_id),
    )


# ---------------------------------------------------------------------------
# GET /weekly
# ---------------------------------------------------------------------------

def test_weekly_page_shows_empty_state(client):
    year, week, _monday = _target_week()
    response = client.get(f"/weekly?year={year}&week={week}")
    assert response.status_code == 200
    assert "No tracked time this week." in response.text
    assert f"Week {week:02d}/{year}" in response.text


def test_weekly_page_defaults_to_current_week_when_omitted(client):
    today_iso = date.today().isocalendar()
    response = client.get("/weekly")
    assert response.status_code == 200
    assert f"Week {today_iso.week:02d}/{today_iso.year}" in response.text


def test_weekly_page_shows_day_epic_task_hierarchy_and_week_total(client):
    year, week, monday = _target_week()
    _insert_closed_session(monday, "09:00", "11:00", "TASK-1")
    _link_epic("TASK-1", "Platform")

    response = client.get(f"/weekly?year={year}&week={week}")
    assert response.status_code == 200
    assert "Platform" in response.text
    assert "TASK-1" in response.text
    assert "2:00" in response.text  # HH:MM column
    assert "2.00" in response.text  # decimal column
    assert "Week total" in response.text


def test_weekly_page_groups_untagged_task_as_misc(client):
    year, week, monday = _target_week()
    _insert_closed_session(monday, "09:00", "10:00", "TASK-UNLINKED")

    response = client.get(f"/weekly?year={year}&week={week}")
    assert response.status_code == 200
    assert "(Misc)" in response.text
    assert "TASK-UNLINKED" in response.text


def test_weekly_page_excludes_lunch_from_totals_by_default(client):
    year, week, monday = _target_week()
    _insert_closed_session(monday, "09:00", "10:00", "TASK-1")
    _insert_closed_session(monday, "12:00", "12:30", "Lunch")

    response = client.get(f"/weekly?year={year}&week={week}")
    assert response.status_code == 200
    assert "Lunch" not in response.text
    assert "1:00" in response.text  # only TASK-1's hour counted


def test_weekly_page_shows_promark_style_day_span(client):
    year, week, monday = _target_week()
    repo.execute(
        "INSERT INTO settings (key, value, updated_at) VALUES ('lunch_duration_minutes', '30', datetime('now'))"
    )
    _insert_closed_session(monday, "09:00", "11:00", "TASK-1")

    response = client.get(f"/weekly?year={year}&week={week}")
    assert response.status_code == 200
    # Consolidated span: start 09:00, 2 hours worked + 30 min default lunch
    # addition (lunch_excluded defaults to True) -> ends 11:30.
    assert "09:00" in response.text
    assert "11:30" in response.text


# ---------------------------------------------------------------------------
# Week navigation
# ---------------------------------------------------------------------------

def test_week_nav_next_is_disabled_on_current_week(client):
    today_iso = date.today().isocalendar()
    response = client.get(f"/weekly?year={today_iso.year}&week={today_iso.week}")
    assert response.status_code == 200
    assert "disabled" in response.text


def test_week_nav_links_point_to_prev_and_next_week(client):
    year, week, _monday = _target_week()
    response = client.get(f"/weekly?year={year}&week={week}")
    assert response.status_code == 200
    assert "/weekly?year=" in response.text


def test_week_nav_shows_current_week_link_when_not_on_current_week(client):
    year, week, _monday = _target_week()
    response = client.get(f"/weekly?year={year}&week={week}")
    assert response.status_code == 200
    assert 'hx-get="/weekly"' in response.text
    assert ">Current week</a>" in response.text


def test_week_nav_hides_current_week_link_on_current_week(client):
    today_iso = date.today().isocalendar()
    response = client.get(f"/weekly?year={today_iso.year}&week={today_iso.week}")
    assert response.status_code == 200
    assert "Current week</a>" not in response.text


def test_week_nav_links_carry_htmx_swap_attributes(client):
    year, week, _monday = _target_week()
    response = client.get(f"/weekly?year={year}&week={week}")
    assert response.status_code == 200
    assert 'hx-target="#weekly-dynamic"' in response.text
    assert 'hx-swap="innerHTML"' in response.text
    assert 'hx-push-url="true"' in response.text


# ---------------------------------------------------------------------------
# HTMX fragment responses (Manual Changes, 2026-11-27, "Weekly page: HTMX-based
# week navigation")
# ---------------------------------------------------------------------------

def test_weekly_plain_request_returns_full_page(client):
    year, week, _monday = _target_week()
    response = client.get(f"/weekly?year={year}&week={week}")
    assert response.status_code == 200
    assert "<html" in response.text
    assert 'id="weekly-dynamic"' in response.text


def test_weekly_htmx_request_returns_fragment_only(client):
    year, week, _monday = _target_week()
    response = client.get(f"/weekly?year={year}&week={week}", headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert "<html" not in response.text
    assert "navbar" not in response.text
    assert f"Week {week:02d}/{year}" in response.text
    assert "Week total" in response.text
