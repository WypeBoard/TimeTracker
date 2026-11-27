"""Smoke tests for the webapp/ FastAPI skeleton (Phase 2) plus basic
cross-page routing checks.

These are intentionally thin: they confirm routing, template rendering, and
the /health check work end to end. Business-logic tests for Today/Weekly/
Settings live in their own test modules (tests/webapp/test_today.py from
Phase 3 onward) once those pages have real content. The `isolated_db`
fixture (see conftest.py) now creates the minimal schema, since GET /today
queries real tables as of Phase 3.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from webapp.main import app


@pytest.fixture
def client(isolated_db):
    return TestClient(app)


def test_root_redirects_to_today(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/today"


@pytest.mark.parametrize("path, expected_active_nav_text", [
    ("/today", "Today"),
    ("/weekly", "Weekly"),
    ("/settings", "Settings"),
])
def test_pages_render_html(client, path, expected_active_nav_text):
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert expected_active_nav_text in response.text


def test_health_reports_database_reachable(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body == {"status": "ok", "database_reachable": True}


def test_health_reports_degraded_when_database_unreachable(client, monkeypatch):
    """An invalid DB_FILE path (e.g. parent directory missing) should make
    /health report degraded rather than raising a 500."""
    monkeypatch.setattr("db.repository.DB_FILE", "Z:\\does-not-exist\\nope.db")
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body == {"status": "degraded", "database_reachable": False}
