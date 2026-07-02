"""TuiAppContext — AppContext implementation for the Textual TUI.

Delivers command feedback to the OutputPanel widget and triggers panel
refreshes after mutating commands. The show_log method pushes the LogScreen
overlay; show_promark writes the Promark panel directly to OutputPanel.

The TYPE_CHECKING guard on the TimeTrackerApp import breaks the circular
import chain: TimeTrackerApp imports TuiAppContext, and TuiAppContext needs
to reference TimeTrackerApp only for type annotations — not at runtime.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.TimeTrackerApp import TimeTrackerApp
    from Printer import DayStatus


class TuiAppContext:
    """AppContext for the Textual TUI.

    Wired to the live app instance so it can post messages to OutputPanel
    and trigger widget refreshes.
    """

    def __init__(self, app: TimeTrackerApp) -> None:
        self._app = app

    def info(self, message: str) -> None:
        self._get_output().add_message(message, "info")

    def warning(self, message: str) -> None:
        self._get_output().add_message(message, "warning")

    def error(self, message: str) -> None:
        self._get_output().add_message(message, "error")

    def on_session_changed(self) -> None:
        # call_after_refresh schedules the callback to run after the current
        # render cycle, so the DB writes are committed before we re-query.
        self._app.call_after_refresh(self._app.refresh_session_panels)

    def on_day_stopped(self, status: DayStatus) -> None:
        # No-op: the Today panel already shows live data via on_session_changed.
        pass

    def show_log(self, week_days: dict, week_num: int, year: int) -> None:
        from app.LogScreen import LogScreen
        self._app.push_screen(LogScreen(week_num, year))

    def show_promark(self, week_days: dict, week_num: int, year: int) -> None:
        from Printer import build_promark_panel
        panel = build_promark_panel(week_days, week_num, year)
        self._get_output().write(panel)

    def on_new_task(self, task_id: str) -> None:
        """Push the EpicModal so the user can link the task to an Epic."""
        from app.EpicModal import EpicModal
        self._app.push_screen(EpicModal(task_id))

    def show_epic_summary(self, week_num: int, year: int) -> None:
        """Push the EpicSummaryScreen overlay."""
        from app.EpicSummaryScreen import EpicSummaryScreen
        self._app.push_screen(EpicSummaryScreen(week_num, year))

    # ------------------------------------------------------------------ #

    def _get_output(self):
        from app.OutputPanel import OutputPanel
        return self._app.query_one(OutputPanel)
