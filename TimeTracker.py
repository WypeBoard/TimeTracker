#!/usr/bin/env python3
"""
Time Tracker — logs work sessions to a SQLite database.

Launch: python TimeTracker.py
Opens the Textual TUI. All commands are entered from the TUI command bar.
"""

from Storage import create_schema


def main():
    # Ensure the database directory, tables, and triggers exist before the TUI
    # starts. Safe to call on every startup — all DDL uses IF NOT EXISTS.
    create_schema()

    from app.TimeTrackerApp import TimeTrackerApp
    TimeTrackerApp().run()


if __name__ == "__main__":
    main()