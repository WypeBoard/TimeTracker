"""GET /settings - Settings page.

Phase 2 (this phase): skeleton stub only. Real content (daily work target,
lunch, excluded tasks, always-separate tasks, save/validation) is added in
Phase 5 of the Implementation Plan in features/standalone-web-app.md.
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from webapp.templating import templates

router = APIRouter()


@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    return templates.TemplateResponse(
        request,
        "settings.html",
        {"active_nav": "settings"},
    )
