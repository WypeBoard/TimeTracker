"""ProgressStrip — combined Today + Week progress bars.

Two stacked rows showing hours logged vs. target for today and this week:

    Today   6:00 / 7:24   ████████████████░░░░░░░░  81%
    Week   32:30 / 29:36  ██████████████████████    100%+

All times are in base-60 clock format (H:MM).

Week target is dynamic: TARGET_HOURS × (number of weekdays with at least one
session this week). This avoids the misleading "20%" on Monday that a fixed
5-day target would produce.

Edge case — zero sessions this week:
    Week   0:00 / —   (dim, no bar, no percentage)
The row remains visible so the layout does not shift when the first session
of the week is started.

The widget refreshes whenever TuiAppContext.on_session_changed() fires (via
TimeTrackerApp.refresh_session_panels) and every 60 seconds via an interval
timer so the live active-session counter stays current.
"""
from datetime import date, timedelta

from rich.console import Group
from rich.text import Text
from textual.widgets import Static


class ProgressStrip(Static):
    """Stacked Today and Week progress bar rows."""

    DEFAULT_CSS = """
    ProgressStrip {
        width: 1fr;
        border: solid $accent;
        padding: 0 1;
        height: auto;
        margin-top: 1;
    }
    """

    def on_mount(self) -> None:
        self.refresh_data()
        # Same 60-second cadence as TodayPanel so the active-session running
        # total is updated without user action.
        self.set_interval(60, self.refresh_data)

    def refresh_data(self) -> None:
        """Re-compute today's and this week's progress and redraw."""
        from datetime import datetime
        from Commands import _build_day_status
        from Storage import read_log
        from Constants import TARGET_HOURS

        now = datetime.now()
        day_status = _build_day_status(now)

        today_logged = day_status.total_so_far
        today_target = day_status.target_hours

        # --- Week totals -------------------------------------------------------
        # read_log() returns only closed sessions; today's live total from
        # day_status is used instead so the active session is included.
        days = read_log()
        today = date.today()
        today_iso = today.isocalendar()
        week_num = today_iso.week
        year = today_iso.year

        jan4 = date(year, 1, 4)
        week1_monday = jan4 - timedelta(days=jan4.weekday())
        monday = week1_monday + timedelta(weeks=week_num - 1)
        today_str = today.strftime("%Y-%m-%d")

        week_total = 0.0
        days_with_sessions = 0

        for i in range(5):
            d = monday + timedelta(days=i)
            d_str = d.strftime("%Y-%m-%d")
            if d_str == today_str:
                # Use the live total (includes any active session).
                if day_status.total_so_far > 0 or day_status.active_start:
                    week_total += day_status.total_so_far
                    days_with_sessions += 1
            elif d_str in days:
                week_total += days[d_str]["total"]
                days_with_sessions += 1

        # Dynamic target: only count days that actually have sessions.
        week_target = TARGET_HOURS * days_with_sessions if days_with_sessions > 0 else 0.0

        rows = [
            _progress_row("Today", today_logged, today_target),
            _progress_row("Week ", week_total, week_target),
        ]
        self.update(Group(*rows))
        self.border_title = "Progress"


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _hours_bar_markup(logged: float, target: float, width: int = 24) -> str:
    """Return a Rich markup string for a filled/unfilled bar with percentage."""
    ratio  = min(logged / target, 1.0) if target else 0.0
    filled = round(ratio * width)
    bar    = "█" * filled + "░" * (width - filled)
    pct    = ratio * 100
    color  = "green" if logged >= target else "yellow"
    return f"[{color}]{bar}[/{color}] [bold]{pct:.0f}%[/bold]"


def _progress_row(label: str, logged: float, target: float) -> Text:
    """Build one labelled progress row as a Rich Text object.

    If target is 0.0 (no sessions this week yet), the row shows a dim
    placeholder with no bar to avoid a division-by-zero.
    """
    from app.utils import format_hhmm

    if target == 0.0:
        # Zero-session edge case: render a dim placeholder, no bar.
        return Text.from_markup(
            f"  {label}   [dim]{format_hhmm(logged)} / —[/dim]"
        )

    logged_str = format_hhmm(logged)
    target_str = format_hhmm(target)
    bar = _hours_bar_markup(logged, target)

    return Text.from_markup(
        f"  {label}   [bold]{logged_str}[/bold] [dim]/[/dim] {target_str}   {bar}"
    )
