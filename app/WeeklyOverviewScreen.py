"""WeeklyOverviewScreen — modal overlay showing day → Epic → task totals.

Replaces the previous separate ``LogScreen`` and ``EpicSummaryScreen`` (see
feature `ui-layout-redesign.md` §16). One screen, one key binding (``w``),
one navigation model (``←`` / ``→`` by ISO week), and one panel renderer
(``Printer.build_weekly_overview_panel``) that shows both duration formats
side by side.
"""
from __future__ import annotations

from datetime import date

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Static


class WeeklyOverviewScreen(ModalScreen):
    """Full-screen modal — one ISO week of hours grouped by day/Epic/task."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("left",   "prev_week", "Prev week"),
        Binding("right",  "next_week", "Next week"),
    ]

    DEFAULT_CSS = """
    WeeklyOverviewScreen { align: center middle; }
    #weekly-container {
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
        with ScrollableContainer(id="weekly-container"):
            yield Static(id="weekly-content")

    def on_mount(self) -> None:
        self._render_week()

    def _render_week(self) -> None:
        from datetime import timedelta

        from EpicStorage import get_epic_summary_data
        from Printer import build_weekly_overview_panel
        from Promark import compute_day_promark
        from SettingsStorage import SettingsRepository
        from Storage import read_log

        settings = SettingsRepository()
        lunch_excluded = settings.get_lunch_excluded()
        excluded_tasks = settings.get_excluded_tasks()
        always_separate = settings.get_always_separate_tasks()
        lunch_offset = settings.get_lunch_promark_offset_minutes()

        data = get_epic_summary_data(
            self._week_num, self._year,
            lunch_excluded=lunch_excluded,
            excluded_tasks=excluded_tasks,
        )

        # Per-day consolidated span (Promark-style: first_start → first_start
        # + worked_minutes) so the day header can show the equivalent of the
        # retired "single loggable session" line, e.g. "07:00 → 15:45".
        # We reuse compute_day_promark to keep the rules identical to the
        # `promark` command (always-separate tasks excluded, optional Lunch
        # exclusion, optional Promark offset).
        daily_promark: dict[str, tuple[str, str]] = {}
        days = read_log()
        jan4 = date(self._year, 1, 4)
        week1_monday = jan4 - timedelta(days=jan4.weekday())
        monday = week1_monday + timedelta(weeks=self._week_num - 1)
        for i in range(7):
            d = monday + timedelta(days=i)
            date_str = d.strftime("%Y-%m-%d")
            if date_str not in days:
                continue
            consolidated, _ = compute_day_promark(
                days[date_str]["sessions"],
                always_separate,
                lunch_excluded,
                lunch_offset,
            )
            if consolidated and consolidated["start"] and consolidated["end"]:
                daily_promark[date_str] = (consolidated["start"], consolidated["end"])

        panel = build_weekly_overview_panel(
            data, self._week_num, self._year,
            daily_promark=daily_promark,
        )
        self.query_one("#weekly-content", Static).update(panel)

    # ------------------------------------------------------------------ #
    # Navigation
    # ------------------------------------------------------------------ #

    def action_prev_week(self) -> None:
        if self._week_num > 1:
            self._week_num -= 1
        else:
            self._year -= 1
            self._week_num = _max_week_of_year(self._year)
        self._render_week()

    def action_next_week(self) -> None:
        # Forward navigation is capped at the current ISO week per feature
        # spec §22 — the overlay never shows a future week.
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _max_week_of_year(year: int) -> int:
    """Return the number of ISO weeks in the given year (52 or 53).

    Dec 28 is always in the last ISO week of its calendar year, so its
    ``isocalendar().week`` reliably gives that count.
    """
    return date(year, 12, 28).isocalendar().week
