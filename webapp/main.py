"""FastAPI application factory and route wiring for the standalone web app.

Entry points:
    python -m webapp            (see webapp/__main__.py)
    uvicorn webapp.main:app     (direct uvicorn invocation)

Per features/standalone-web-app.md:
- This process is fully independent of the TUI (app/, TimeTracker.py). It
  must never import from app/ — only from db/ (generic SQLite
  infrastructure) and from webapp/ itself.
- The server binds to 127.0.0.1 on a fixed, non-standard port (see
  webapp/Constants.py). No authentication, no CORS handling — loopback-only.
- Schema creation is intentionally NOT performed here: per the Brainstorm
  Notes ("db/ boundary" discussion), the web app uses the TUI-created
  schema rather than creating a duplicate. Run the TUI (TimeTracker.py) at
  least once first so the database file and tables exist.
"""
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from webapp.routes import health, today, weekly, settings as settings_routes
import os

app = FastAPI(title="TimeTracker")

_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

app.include_router(health.router)
app.include_router(today.router)
app.include_router(weekly.router)
app.include_router(settings_routes.router)


@app.get("/")
def root():
    """Redirect the root URL to /today, the dashboard page."""
    return RedirectResponse(url="/today")
