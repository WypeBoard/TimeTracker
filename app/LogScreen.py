"""LogScreen — full-screen overlay for the week log detail view."""
from __future__ import annotations
from datetime import date
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Static
class LogScreen(ModalScreen):
    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("left",   "prev_week", "Prev week"),
        Binding("right",  "next_week", "Next week"),
    ]
    DEFAULT_CSS = """
    LogScreen { align: center middle; }
    #log-container {
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
        with ScrollableContainer(id="log-container"):
            yield Static(id="log-content")
    def on_mount(self) -> None:
        self._render_week()
    def _render_week(self) -> None:
        from Storage import read_log
        from Printer import build_log_week_panel
        days = read_log()
        week_days = {
            d: info for d, info in days.items()
            if date.fromisoformat(d).isocalendar().week == self._week_num
            and date.fromisoformat(d).isocalendar().year == self._year
        }
        panel = build_log_week_panel(week_days, self._week_num, self._year)
        self.query_one("#log-content", Static).update(panel)
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
    return date(year, 12, 28).isocalendar().week
