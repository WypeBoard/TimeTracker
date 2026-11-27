# webapp/ — standalone browser application for TimeTracker.
#
# This package is an independent process from the TUI (app/, TimeTracker.py).
# It shares only db/ (generic SQLite infrastructure) with the TUI; it must
# never import from app/, and app/ must never import from webapp/.
#
# See features/standalone-web-app.md for the full design and
# features/standalone-web-app.md#implementation-plan for the phased build
# order this package follows (currently Phase 2 — webapp/ skeleton).
