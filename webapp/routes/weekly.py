"""GET /weekly - Weekly overview page.

Phase 2 (this phase): skeleton stub only. Real content (week-navigation
header, day -> Epic -> task table, Week total row) is added in Phase 4 of
the Implementation Plan in features/standalone-web-app.md.
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from webapp.templating import templates

router = APIRouter()


@router.get("/weekly", response_class=HTMLResponse)
def weekly_page(request: Request):
    return templates.TemplateResponse(
        request,
        "weekly.html",
        {"active_nav": "weekly"},
    )
