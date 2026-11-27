"""Pydantic request models for the Today page's mutating form POSTs.

Bound via `Annotated[Model, Form()]` per Manual Changes, 2026-11-26 ("Pydantic
models for endpoint request/response shapes") — see webapp/schemas/__init__.py
for the package convention.
"""
import re

from pydantic import BaseModel, field_validator

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _validate_time(value: str) -> str:
    if not _TIME_RE.match(value):
        raise ValueError("Start time must be in HH:MM (24-hour) format.")
    return value


class NewSessionForm(BaseModel):
    """POST /sessions/new — New Session modal submit.

    epic_id is "__new__" when the user chose the inline Epic-creation
    option, a numeric string when an existing Epic was picked, or blank/None
    when no Epic step was shown (task already has a task_catalog entry).
    """
    task: str
    start_time: str
    epic_id: str | None = None
    new_epic_name: str | None = None

    @field_validator("start_time")
    @classmethod
    def _check_start_time(cls, value: str) -> str:
        return _validate_time(value)


class ResumeForm(BaseModel):
    """POST /sessions/resume — Resume modal submit (main button path)."""
    task: str
    start_time: str

    @field_validator("start_time")
    @classmethod
    def _check_start_time(cls, value: str) -> str:
        return _validate_time(value)


class LunchForm(BaseModel):
    """POST /sessions/lunch — Lunch modal submit (main button path)."""
    start_time: str

    @field_validator("start_time")
    @classmethod
    def _check_start_time(cls, value: str) -> str:
        return _validate_time(value)


class StopForm(BaseModel):
    """POST /sessions/stop — Stop modal submit (main button path).

    See Manual Changes, 2026-11-26, "Stop button: closes the active
    session" — closes the open session, web equivalent of cmd_pause.
    """
    end_time: str

    @field_validator("end_time")
    @classmethod
    def _check_end_time(cls, value: str) -> str:
        return _validate_time(value)
