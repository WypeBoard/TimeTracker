"""GET /today - Today dashboard page, plus its mutating HTMX endpoints.

Phase 3 of the Implementation Plan in features/standalone-web-app.md:
quick-action buttons (New Session, Resume, Lunch), the Quick Stats row, and
today's session table, all from one synchronous render (see Manual Changes,
2026-11-24, "Page load strategy"). Each POST re-renders the
`_today_fragment.html` partial (Quick Stats + session table) as an HTMX
swap, per the Page/Route/Component Inventory.
"""
from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from webapp.schemas.today import LunchForm, NewSessionForm, ResumeForm, StopForm
from webapp.services import today_service
from webapp.templating import templates

router = APIRouter()


@router.get("/today", response_class=HTMLResponse)
def today_page(request: Request):
    view = today_service.build_today_view_model()
    return templates.TemplateResponse(
        request,
        "today.html",
        {"active_nav": "today", "view": view},
    )


def _fragment_response(request: Request, error: str | None) -> HTMLResponse:
    """Re-render the Quick Stats + session table fragment after a mutation."""
    view = today_service.build_today_view_model(error=error)
    return templates.TemplateResponse(
        request,
        "_today_fragment.html",
        {"view": view},
    )


@router.post("/sessions/new", response_class=HTMLResponse)
def new_session(request: Request, form: Annotated[NewSessionForm, Form()]):
    error = today_service.do_new_session(
        form.task, form.start_time, form.epic_id, form.new_epic_name,
    )
    return _fragment_response(request, error)


@router.post("/sessions/resume", response_class=HTMLResponse)
def resume(request: Request, form: Annotated[ResumeForm, Form()]):
    error = today_service.do_resume(form.task, form.start_time)
    return _fragment_response(request, error)


@router.post("/sessions/resume/now", response_class=HTMLResponse)
def resume_now(request: Request):
    error = today_service.do_resume_now()
    return _fragment_response(request, error)


@router.post("/sessions/lunch", response_class=HTMLResponse)
def lunch(request: Request, form: Annotated[LunchForm, Form()]):
    error = today_service.do_lunch(form.start_time)
    return _fragment_response(request, error)


@router.post("/sessions/lunch/now", response_class=HTMLResponse)
def lunch_now(request: Request):
    error = today_service.do_lunch_now()
    return _fragment_response(request, error)


@router.post("/sessions/stop", response_class=HTMLResponse)
def stop(request: Request, form: Annotated[StopForm, Form()]):
    error = today_service.do_stop(form.end_time)
    return _fragment_response(request, error)


@router.post("/sessions/stop/now", response_class=HTMLResponse)
def stop_now(request: Request):
    error = today_service.do_stop_now()
    return _fragment_response(request, error)
