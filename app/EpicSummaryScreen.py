"""EpicSummaryScreen — full-screen overlay for the Epic summary view.

Shows time grouped by Epic for a target ISO week. Navigation matches
the LogScreen pattern: ← / → to move between weeks, Esc to close.
"""
from __future__ import annotations

from datetime import date

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Static


class EpicSummaryScreen(ModalScreen):
    """Full-screen overlay showing hours grouped by Epic for one ISO week."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("left",   "prev_week", "Prev week"),
        Binding("right",  "next_week", "Next week"),
    ]

    DEFAULT_CSS = """
    EpicSummaryScreen { align: center middle; }
    #summary-container {
        width: 90%; height: 90%;
        background: $surface;
        border: double $accent;
        overflow-y: auto;
        padding: 1 2;
    }
    """

    def __init__(self, week_num: int, year: int) -> None:
        super().__init__()
        self._week_num = week_num
        self._year = year

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="summary-container"):
            yield Static(id="summary-content")

    def on_mount(self) -> None:
        self._render_week()

    def _render_week(self) -> None:
        from EpicStorage import get_epic_summary_data
        from Printer import build_epic_summary_panel

        data = get_epic_summary_data(self._week_num, self._year)
        panel = build_epic_summary_panel(data, self._week_num, self._year)
        self.query_one("#summary-content", Static).update(panel)

    def action_prev_week(self) -> None:
        if self._week_num > 1:
            self._week_num -= 1
        else:
            self._year -= 1
            self._week_num = _max_week_of_year(self._year)
        self._render_week()

    def action_next_week(self) -> None:
        today_iso = date.today().isocalendar()
        if (self._year, self._week_num) >= (today_iso.year, today_iso.week):
            return
        max_week = _max_week_of_year(self._year)
        if self._week_num < max_week:
            self._week_num += 1
        else:
            self._week_num = 1
            self._year += 1
        self._render_week()


def _max_week_of_year(year: int) -> int:
    """Return the number of ISO weeks in the given year (52 or 53)."""
    return date(year, 12, 28).isocalendar().week
