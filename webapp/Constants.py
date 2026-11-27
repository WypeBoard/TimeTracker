"""Generic, webapp-wide constants.

Mirrors the role of app/Constants.py for the TUI, but scoped to webapp/ only.
This module must not import anything from app/ — the only cross-package
dependency webapp/ is allowed is db/ (see webapp/__init__.py and
features/standalone-web-app.md).
"""

# Loopback-only; never bind to 0.0.0.0 or any externally reachable interface
# (see Requirements: "Access model" in features/standalone-web-app.md).
HOST = "127.0.0.1"

# Fixed, non-standard (non-well-known) port. The exact number is an
# implementation detail per the feature's Requirements — 8765 was chosen
# because it is unassigned and easy to remember.
PORT = 8765
