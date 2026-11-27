"""GET /weekly - Weekly overview page (day -> Epic -> task hours).

Phase 4 of the Implementation Plan in features/standalone-web-app.md: the
independent equivalent of the TUI's WeeklyOverviewScreen, consolidating
Weekly/Epic Summary/Promark into one page (see Manual Changes, 2026-11-24,
"Weekly page: consolidates Weekly/Epic Summary/Promark into one page").

Week navigation (prev/next/current-week) is an HTMX-swapped partial update
rather than a full page reload, per Manual Changes (2026-11-27, "Weekly page:
HTMX-based week navigation"). When the request carries the `HX-Request`
header, only the `_weekly_fragment.html` partial (nav header + table) is
returned; a normal navigation still gets the full page.
"""
from datetime import date

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from webapp.services import weekly_service
from webapp.templating import templates

router = APIRouter()


@router.get("/weekly", response_class=HTMLResponse)
def weekly_page(request: Request, year: int | None = None, week: int | None = None):
    # Query params default to the current ISO week when omitted (per the
    # Page/Route/Component Inventory).
    if year is None or week is None:
        today_iso = date.today().isocalendar()
        year = year if year is not None else today_iso.year
        week = week if week is not None else today_iso.week

    view = weekly_service.build_weekly_view_model(week, year)
    template_name = "_weekly_fragment.html" if request.headers.get("hx-request") == "true" else "weekly.html"
    return templates.TemplateResponse(
        request,
        template_name,
        {"active_nav": "weekly", "view": view},
    )
