# webapp/schemas/ — Pydantic models for request/response validation.
#
# One module per route group, mirroring webapp/routes/ and
# webapp/services/ (e.g. schemas/health.py, schemas/today.py,
# schemas/settings.py).
#
# Two uses, both via FastAPI's standard Pydantic integration:
#
# 1. Outbound JSON responses — declared as a route's `response_model`, e.g.
#    HealthResponse in schemas/health.py. FastAPI validates/serializes the
#    return value against the model and documents the shape in /docs.
#
# 2. Inbound HTMX form POSTs — bound directly from form-encoded bodies
#    using `Annotated[SomeModel, Form()]` (supported natively by FastAPI
#    since 0.113; confirmed working against the fastapi>=0.115 pin in
#    requirements-webapp.txt). This validates an entire form submission
#    (e.g. the New Session modal's task/epic/start-time fields) as one
#    Pydantic model instead of declaring each field as a separate
#    `Form(...)` parameter — the same validation benefits FastAPI gives
#    JSON bodies, applied to the form-POST style this feature uses
#    throughout (see features/standalone-web-app.md Requirements: HTMX is
#    used for post-mutation fragment swaps, not a separate JSON API).
#
# Per docs/operations/software-standard.md's Dependency Policy, Pydantic is
# already a preferred library in this codebase (listed alongside
# Textual/Rich, SQLAlchemy, Click/Typer) — using it here is consistent with
# that existing policy, not a new dependency decision.
