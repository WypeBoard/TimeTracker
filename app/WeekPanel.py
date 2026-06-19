"""WeekPanel — condensed view of the current week's daily totals.

Shows Mon–Fri with the promark-style start→end range and total hours for
each day. Today's row highlights the in-progress total if a session is
currently active.

This panel is not timer-driven. It refreshes only when a mutating command
(start/stop/pause/resume/task) fires TuiAppContext.on_session_changed().
"""
from datetime import date, timedelta

from rich.table import Table
from rich.text import Text
from rich import box
from textual.widgets import Static


class WeekPanel(Static):
    """Current-week daily totals (Mon–Fri)."""

    DEFAULT_CSS = """
    WeekPanel {
        width: 2fr;
        border: solid $accent;
        padding: 0 1;
        height: auto;
        min-height: 10;
    }
    """

    def on_mount(self) -> None:
        self.refresh_data()

    def refresh_data(self) -> None:
        """Re-query the current week's sessions and redraw the panel."""
        from Storage import read_log
        from Commands import _build_day_status

        today = date.today()
        today_iso = today.isocalendar()
        week_num = today_iso.week
        year = today_iso.year

        # read_log() returns only *closed* sessions, so we supplement with
        # today's live status for the current day.
        days = read_log()
        day_status = _build_day_status()

        table = _build_week_table(days, day_status, week_num, year, today)
        self.update(table)
        self.border_title = f"Week {week_num}"


def _build_week_table(
    days: dict,
    day_status,
    week_num: int,
    year: int,
    today: date,
) -> Table:
    """Build a Rich Table showing daily totals for Mon–Fri of the given week."""
    # Resolve the Monday of the target ISO week.
    jan4 = date(year, 1, 4)
    week1_monday = jan4 - timedelta(days=jan4.weekday())
    monday = week1_monday + timedelta(weeks=week_num - 1)

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    today_str = today.strftime("%Y-%m-%d")

    table = Table(
        box=box.SIMPLE,
        show_header=False,
        padding=(0, 1),
        show_edge=False,
    )
    table.add_column("Day",   style="dim",      no_wrap=True)
    table.add_column("Hours", justify="right",  no_wrap=True)

    for i in range(5):
        d = monday + timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        day_label = day_names[i]
        is_today = date_str == today_str

        if is_today:
            # Use live status which includes the active session's partial hours.
            total = day_status.total_so_far
            if total > 0:
                suffix = " ▶" if day_status.active_start else ""
                hours_text = Text(f"{total:.2f}h{suffix}", style="bold green")
            else:
                hours_text = Text("—", style="dim")
        elif date_str in days:
            total = days[date_str]["total"]
            hours_text = Text(f"{total:.2f}h", style="bold")
        else:
            hours_text = Text("—", style="dim")

        label_style = "bold" if is_today else "dim"
        table.add_row(
            Text(day_label, style=label_style),
            hours_text,
        )

    return table
