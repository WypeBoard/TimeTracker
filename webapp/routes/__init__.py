# webapp/routes/ — FastAPI routers, one module per route group.
#
# Each module exports an `APIRouter` named `router`, included from
# webapp/main.py. Full page logic (Quick Stats, session tables, weekly
# grouping, settings forms) is built out phase-by-phase per the
# Implementation Plan in features/standalone-web-app.md:
#   Phase 2 (this phase) — skeleton routers only, enough to prove routing
#     and template rendering work end to end.
#   Phase 3 — today.py gains real content.
#   Phase 4 — weekly.py gains real content.
#   Phase 5 — settings.py gains real content.
