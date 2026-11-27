"""GET /health - backend availability check.

Polled by base.html's on-load script so the browser can show whether the
FastAPI backend is up or down, per features/standalone-web-app.md
Requirements.
"""
from fastapi import APIRouter

from webapp.schemas.health import HealthResponse
from webapp.services.health_service import check_database_reachable

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    db_ok = check_database_reachable()
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        database_reachable=db_ok,
    )
