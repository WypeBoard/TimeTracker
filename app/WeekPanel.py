"""WeekPanel — promark-style view of the current week.

Displays Mon–Fri with date, day name, promark start→end range, and total
hours for each day:

    2026-06-16  Mon  07:30 → 17:00  7:30
    2026-06-17  Tue  08:00 → 15:45  7:15
    2026-06-18  Wed  —
    2026-06-19  Thu  08:30 → now ▶  4:00

Today's row shows "now ▶" for the end time when a session is active, and the
hours cell includes a ▶ marker. Days with no sessions show "—" in the range.

Hours totals and the promark range for past days are computed from filtered
sessions (applying the lunch_excluded and excluded_tasks settings). Excluded
sessions are still stored and visible elsewhere; they are omitted only from
the hours calculation shown here.

The panel refreshes on demand when TuiAppContext.on_session_changed() is called
and every 60 seconds via a timer (so the running total stays current).
"""
from datetime import date, timedelta

from rich.table import Table
from rich.text import Text
from rich import box
from textual.widgets import Static


class WeekPanel(Static):
    """Current-week daily totals in promark-style (Date Day Start→End Hours)."""

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
        # Refresh every 60 seconds so the active-session running total stays current.
        self.set_interval(60, self.refresh_data)

    def refresh_data(self) -> None:
        """Re-query the current week's sessions and redraw the panel."""
        from Storage import read_log
        from Commands import _build_day_status
        from SettingsStorage import SettingsRepository

        today = date.today()
        today_iso = today.isocalendar()
        week_num = today_iso.week
        year = today_iso.year

        # read_log() returns only *closed* sessions; today's live status
        # supplements it with any active session.
        days = read_log()
        day_status = _build_day_status()  # already applies settings

        # Read settings for filtering past days.
        settings = SettingsRepository()
        lunch_excluded = settings.get_lunch_excluded()
        excluded_tasks = settings.get_excluded_tasks()
        lunch_offset = settings.get_lunch_promark_offset_minutes()

        table = _build_week_table(
            days, day_status, week_num, year, today,
            lunch_excluded, excluded_tasks, lunch_offset,
        )
        self.update(table)
        self.border_title = f"Week {week_num}"


def _build_week_table(
        days: dict,
        day_status,
        week_num: int,
        year: int,
        today: date,
        lunch_excluded: bool = True,
        excluded_tasks: list | None = None,
        lunch_offset: int = 0,
) -> Table:
    """Build a Rich Table with the promark-style week layout."""
    from Promark import promark_entry, session_hours
    from app.utils import format_hhmm

    if excluded_tasks is None:
        excluded_tasks = []

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
    table.add_column("Date",  style="dim",  no_wrap=True)
    table.add_column("Day",   style="dim",  no_wrap=True)
    table.add_column("Range", no_wrap=True)
    table.add_column("Hours", justify="right", no_wrap=True)

    for i in range(5):
        d = monday + timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        day_label = day_names[i]
        is_today = date_str == today_str

        if is_today:
            total = day_status.total_so_far
            if total > 0 or day_status.active_start:
                # Use promark_start if available (requires at least one closed
                # session); fall back to the active session's start time.
                pm_start = day_status.promark_start or day_status.active_start

                if day_status.active_start:
                    # Session is still running — show "now ▶" for the end time.
                    range_text = Text(f"{pm_start} → now ▶", style="bold green")
                    hours_text = Text(f"{format_hhmm(total)} ▶", style="bold green")
                else:
                    # Day is closed — show the computed promark end.
                    pm_end = day_status.promark_end or "?"
                    range_text = Text(f"{pm_start} → {pm_end}", style="bold")
                    hours_text = Text(format_hhmm(total), style="bold green")
            else:
                range_text = Text("—", style="dim")
                hours_text = Text("—", style="dim")

            date_text = Text(date_str, style="bold")
            day_text  = Text(day_label, style="bold")

        elif date_str in days:
            raw_sessions = days[date_str]["sessions"]  # (start, end, task)

            # Filter sessions for hours calculation (same rules as _build_day_status).
            filtered = [
                (s, e, t) for s, e, t in raw_sessions
                if not (lunch_excluded and t == "Lunch")
                and t not in excluded_tasks
            ]
            total = sum(session_hours(s, e) for s, e, _ in filtered)

            # Actual lunch minutes for the Promark offset (from all sessions).
            actual_lunch = sum(
                round(session_hours(s, e) * 60)
                for s, e, t in raw_sessions
                if t == "Lunch"
            )

            pm_start, pm_end = promark_entry(filtered, total, lunch_offset, actual_lunch)
            range_text = Text(f"{pm_start} → {pm_end}", style="")
            hours_text = Text(format_hhmm(total), style="bold")
            date_text  = Text(date_str, style="dim")
            day_text   = Text(day_label, style="dim")

        else:
            range_text = Text("—", style="dim")
            hours_text = Text("", style="")
            date_text  = Text(date_str, style="dim")
            day_text   = Text(day_label, style="dim")

        table.add_row(date_text, day_text, range_text, hours_text)

    return table