"""Pydantic response model for GET /health.

See webapp/schemas/__init__.py for the schemas/ package convention.
"""
from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Shape returned by GET /health; polled by base.html on page load."""

    status: Literal["ok", "degraded"]
    database_reachable: bool
