"""Generic SQLite file-path configuration for the shared db/ package.

This is infrastructure, not domain knowledge: it is just the on-disk
location of the SQLite file, with no table/column/schema awareness. Per the
`db/` boundary discussion in features/completed/standalone-web-app.md
("database path configuration or path resolution, if it contains no
TimeTracker domain rules" is an acceptable db/ concern), this constant lives
here so both `app/` (the TUI) and `webapp/` (the standalone browser app) can
resolve the same database file without either one importing the other.

`app/Constants.py` re-exports this value for backward compatibility with
existing TUI code/tests that import `DB_FILE` from `app.Constants`.
"""
import os

DB_FILE = os.path.join(os.environ["APPDATA"], "TimeTracker", "timetracker.db")
