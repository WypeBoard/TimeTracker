"""TaskSummaryPanel — week pivot view: Day × Task → Hours.

Shows which tasks were worked on each weekday and the aggregated hours:

    Mon   Epic-42   7:30
    Tue   Epic-42   4:00
          Epic-55   3:15
    Wed   —
    Thu   Epic-42   3:30 ▶
          Epic-55   0:30

The day name appears only on the first task row per day; continuation rows
have a blank day cell.  Days with no sessions show "Day  —".  Sessions with
no task label are grouped under "(no task)".

If the active session shares a task label with a completed session, their
hours are merged and the combined row carries the ▶ marker.

All hours are displayed in base-60 clock format (H:MM) for consistency with
ProgressStrip and WeekPanel.

The panel refreshes whenever TuiAppContext.on_session_changed() fires (via
TimeTrackerApp.refresh_session_panels) and every 60 seconds via a timer.
"""
from datetime import date, datetime, timedelta

from rich.table import Table
from rich.text import Text
from rich import box
from textual.widgets import Static


class TaskSummaryPanel(Static):
    """Week pivot: Day × Task → Hours."""

    DEFAULT_CSS = """
    TaskSummaryPanel {
        width: 1fr;
        border: solid $accent;
        padding: 0 1;
        height: auto;
        margin-top: 1;
    }
    """

    def on_mount(self) -> None:
        self.refresh_data()
        # Same 60-second cadence as TodayPanel so the ▶ row stays current.
        self.set_interval(60, self.refresh_data)

    def refresh_data(self) -> None:
        """Re-query sessions and rebuild the task pivot table."""
        from Commands import _build_day_status
        from Storage import read_log

        today = date.today()
        today_iso = today.isocalendar()
        week_num = today_iso.week
        year = today_iso.year

        days = read_log()
        day_status = _build_day_status()

        table = _build_task_summary_table(days, day_status, week_num, year, today)
        self.update(table)
        self.border_title = f"Task Summary — Week {week_num}"


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _session_hours(start: str, end: str) -> float:
    """Calculate decimal hours between two HH:MM strings."""
    try:
        s = datetime.strptime(start, "%H:%M")
        e = datetime.strptime(end,   "%H:%M")
        return (e.hour * 60 + e.minute - s.hour * 60 - s.minute) / 60
    except ValueError:
        return 0.0


def _aggregate_tasks(
    sessions: list,
    active_start: str | None = None,
    active_hours: float = 0.0,
    active_task: str | None = None,
) -> list[tuple[str, float, bool]]:
    """Aggregate session hours by task label.

    Returns a list of (task_label, total_hours, is_active) tuples in
    insertion order.  Sessions with no task are grouped under '(no task)'.

    The is_active flag is set on the task row that includes the currently
    active session.  If the active session shares a task with completed
    sessions, their hours are merged and the combined row carries is_active.

    Python dicts preserve insertion order (guaranteed since 3.7), so the
    order of tasks matches the order they first appeared in the session list.
    """
    # Plain dict accumulating hours per task label in insertion order.
    task_hours: dict[str, float] = {}

    for start, end, task in sessions:
        label = task or "(no task)"
        task_hours[label] = task_hours.get(label, 0.0) + _session_hours(start, end)

    active_label: str | None = None
    if active_start:
        active_label = active_task or "(no task)"
        task_hours[active_label] = task_hours.get(active_label, 0.0) + active_hours

    return [
        (label, hours, label == active_label)
        for label, hours in task_hours.items()
    ]


def _build_task_summary_table(
    days: dict,
    day_status,
    week_num: int,
    year: int,
    today: date,
) -> Table:
    """Build the Rich Table for the week task pivot."""
    from app.utils import format_hhmm

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
    table.add_column("Day",   style="dim",     no_wrap=True)
    table.add_column("Task",  style="magenta", no_wrap=True)
    table.add_column("Hours", justify="right", no_wrap=True)

    for i in range(5):
        d = monday + timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        day_label = day_names[i]
        is_today = date_str == today_str

        if is_today:
            task_rows = _aggregate_tasks(
                day_status.sessions,
                day_status.active_start,
                day_status.active_hours,
                day_status.active_task,
            )
        elif date_str in days:
            task_rows = _aggregate_tasks(days[date_str]["sessions"])
        else:
            task_rows = []

        if not task_rows:
            # No sessions for this day — single placeholder row.
            table.add_row(
                Text(day_label, style="dim"),
                Text("—", style="dim"),
                Text("", style=""),
            )
            continue

        for j, (task_label, hours, is_active) in enumerate(task_rows):
            # The day name appears only on the first task row for each day.
            if j == 0:
                day_cell = Text(day_label, style="bold" if is_today else "dim")
            else:
                day_cell = Text("")

            hours_str = format_hhmm(hours)

            if is_active:
                task_cell  = Text(task_label, style="bold green")
                hours_cell = Text(f"{hours_str} ▶", style="bold green")
            elif is_today:
                task_cell  = Text(task_label, style="bold")
                hours_cell = Text(hours_str, style="bold")
            else:
                task_cell  = Text(task_label, style="")
                hours_cell = Text(hours_str, style="")

            table.add_row(day_cell, task_cell, hours_cell)

    return table
