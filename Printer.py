from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()

# ── colour palette ──────────────────────────────────────────────────────────
_C_OK      = "bold green"
_C_WARN    = "bold yellow"
_C_ACTIVE  = "bold green"
_C_DIM     = "dim"
_C_LABEL   = "dim"
_C_VALUE   = "bold cyan"
_C_BORDER  = "steel_blue1"
_C_PROMARK = "medium_orchid"


@dataclass
class DayStatus:
    today_str: str
    sessions: list[tuple[str, str, str]]   # completed (start, end, task) triples
    total_hours: float                      # sum of completed sessions
    target_hours: float
    active_start: str | None = None
    active_hours: float = 0.0
    active_task: str | None = None
    promark_start: str | None = None
    promark_end: str | None = None

    @property
    def total_so_far(self) -> float:
        return self.total_hours + self.active_hours

    @property
    def remaining(self) -> float:
        return self.target_hours - self.total_so_far


# ── internal helpers ─────────────────────────────────────────────────────────

def _hours_bar(logged: float, target: float, width: int = 24) -> str:
    ratio  = min(logged / target, 1.0) if target else 0.0
    filled = round(ratio * width)
    bar    = "█" * filled + "░" * (width - filled)
    pct    = ratio * 100
    color  = "green" if logged >= target else "yellow"
    return f"[{color}]{bar}[/{color}] [bold]{pct:.0f}%[/bold]"


def _session_hours(start: str, end: str) -> float:
    try:
        s = datetime.strptime(start, "%H:%M")
        e = datetime.strptime(end,   "%H:%M")
        return (e.hour * 60 + e.minute - s.hour * 60 - s.minute) / 60
    except ValueError:
        return 0.0


def _sessions_table(
    sessions: list[tuple[str, str, str]],
    active_start: str | None = None,
    active_hours: float = 0.0,
    active_task: str | None = None,
    start_index: int = 1,
) -> Table:
    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold dim",
        padding=(0, 1),
        show_edge=False,
    )
    table.add_column("#",      style="dim",   no_wrap=True)
    table.add_column("Start",  style="cyan",  no_wrap=True)
    table.add_column("End",    style="cyan",  no_wrap=True)
    table.add_column("Hours",  justify="right", no_wrap=True)
    table.add_column("Task",   style="magenta", no_wrap=True)

    for i, (start, end, task) in enumerate(sessions, start=start_index):
        h = _session_hours(start, end)
        table.add_row(f"#{i}", start, end, f"{h:.2f}h", task or "")

    if active_start:
        n = start_index + len(sessions)
        table.add_row(
            f"[{_C_ACTIVE}]#{n}[/{_C_ACTIVE}]",
            f"[{_C_ACTIVE}]{active_start}[/{_C_ACTIVE}]",
            f"[{_C_ACTIVE}]now ▶[/{_C_ACTIVE}]",
            f"[{_C_ACTIVE}]{active_hours:.2f}h[/{_C_ACTIVE}]",
            f"[{_C_ACTIVE}]{active_task or ''}[/{_C_ACTIVE}]",
        )

    return table


# ── buildable renderables (used by both CLI printers and TUI widgets) ────────

def build_status_group(
    status: DayStatus,
    now: datetime,
    show_progress: bool = True,
) -> Group:
    """Build the Rich Group that represents the live status view.

    Extracted so both print_status() and the TUI TodayPanel can reuse the
    same rendering logic without going through console.print().

    Args:
        status: Today's session data.
        now: Current datetime (used to compute leave time).
        show_progress: When False, the progress bar line (Logged X / Y [bar])
            is omitted. The remaining-time and leave-time lines are always
            shown when relevant — ProgressStrip owns the bar in TUI mode, but
            the leave estimate still lives in TodayPanel.
    """
    rows: list = []

    if status.sessions or status.active_start:
        rows.append(_sessions_table(
            status.sessions,
            status.active_start,
            status.active_hours,
            status.active_task,
        ))
    else:
        rows.append(Text("No sessions today.", style=_C_DIM))

    if show_progress:
        rows.append(Text(""))
        rows.append(Text.from_markup(
            f"  Logged   [bold]{status.total_so_far:.2f}h[/bold]"
            f" [dim]/[/dim] {status.target_hours:.2f}h   "
            + _hours_bar(status.total_so_far, status.target_hours)
        ))

    # Always show the remaining / leave-time indicator when there is something
    # to show — this line belongs in TodayPanel regardless of whether the
    # progress bar is present.
    remaining = status.remaining
    if remaining <= 0 and (status.sessions or status.active_start):
        rows.append(Text.from_markup(
            f"\n  [{_C_OK}]✅  Target reached — {-remaining:.2f}h over[/{_C_OK}]"
        ))
    elif status.active_start:
        leave_min  = now.hour * 60 + now.minute + int(remaining * 60)
        leave_h, leave_m = divmod(leave_min, 60)
        leave_line = (
            f"\n  [{_C_WARN}]⏳  Remaining [bold]{remaining:.2f}h[/bold][/{_C_WARN}]"
            f"   [cyan]🚪  Leave at [bold]{leave_h:02d}:{leave_m:02d}[/bold][/cyan]"
        )
        if not status.sessions:  # only this one active session — show lunch variant
            lunch_min  = leave_min + 30
            lunch_h, lunch_m = divmod(lunch_min, 60)
            leave_line += (
                f"   [dim]([/dim][magenta]with lunch [bold]{lunch_h:02d}:{lunch_m:02d}[/bold][/magenta][dim])[/dim]"
            )
        rows.append(Text.from_markup(leave_line))
    elif not status.active_start and (status.sessions or show_progress):
        # Sessions exist but none is active — show the "still needed" reminder
        # only in the full CLI view (show_progress=True) to avoid noise in TUI.
        if show_progress and remaining > 0:
            rows.append(Text.from_markup(
                f"\n  [{_C_WARN}]⏳  Still needed [bold]{remaining:.2f}h[/bold]"
                f"  [dim](no active session)[/dim][/{_C_WARN}]"
            ))

    return Group(*rows)


def build_log_week_panel(week_days: dict, week_num: int, year: int) -> Panel:
    """Build the Rich Panel for a full week log view.

    Extracted so both print_log_week() and the TUI LogScreen can reuse the
    same rendering logic.
    """
    jan4 = date(year, 1, 4)
    week1_monday = jan4 - timedelta(days=jan4.weekday())
    monday = week1_monday + timedelta(weeks=week_num - 1)

    title = (
        f"📅  Week {week_num}, {year}"
        f"  [dim]({monday.strftime('%b %d')} – {(monday + timedelta(days=4)).strftime('%b %d')})[/dim]"
    )

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    today_str = date.today().strftime("%Y-%m-%d")
    week_total = 0.0
    rows: list = []

    for i in range(5):
        d = monday + timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        day_label = day_names[i]
        info = week_days.get(date_str)
        is_today = date_str == today_str

        day_style = "bold" if is_today else ""
        label_text = Text(f"  {day_label}  ", style=day_style or "dim")

        if info:
            sessions = info["sessions"]
            day_total = info["total"]
            week_total += day_total

            for j, (start, end, task) in enumerate(sessions):
                h = _session_hours(start, end)
                prefix = label_text if j == 0 else Text("         ")
                line = Text.assemble(
                    prefix,
                    (f"#{j+1} ", "dim"),
                    (f"{start}–{end}", "cyan"),
                    (f"  {h:.2f}h", "bold"),
                    (f"  {task}" if task else "", "magenta"),
                )
                rows.append(line)

            if len(sessions) > 1:
                rows.append(Text.from_markup(
                    f"           [dim]daily total[/dim]  [bold]{day_total:.2f}h[/bold]"
                ))
        else:
            rows.append(Text.assemble(label_text, ("—", "dim")))

    rows.append(Text(""))
    rows.append(Text.from_markup(
        f"  [bold]Week total:[/bold]  [bold cyan]{week_total:.2f}h[/bold cyan]"
    ))

    return Panel(Group(*rows), title=title, border_style=_C_PROMARK, padding=(0, 2))


def build_promark_panel(week_days: dict, week_num: int, year: int) -> Panel:
    """Build the Rich Panel for the Promark week table.

    Extracted so both print_promark_week() and the TUI OutputPanel can reuse
    the same rendering logic.
    """
    from Promark import promark_entry

    jan4 = date(year, 1, 4)
    week1_monday = jan4 - timedelta(days=jan4.weekday())
    monday = week1_monday + timedelta(weeks=week_num - 1)

    title = (
        f"📋  Promark  [dim]—[/dim]  "
        f"[bold]Week {week_num}, {year}[/bold]"
        f"  ({monday.strftime('%b %d')} – {(monday + timedelta(days=4)).strftime('%b %d')})"
    )

    t = Table(
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold dim",
        padding=(0, 1),
    )
    t.add_column("Date",   style="bold",    no_wrap=True)
    t.add_column("Day",    style="dim",     no_wrap=True)
    t.add_column("Start",  style=_C_VALUE,  no_wrap=True)
    t.add_column("End",    style=_C_VALUE,  no_wrap=True)
    t.add_column("Logged", justify="right", no_wrap=True)

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    today_str = date.today().strftime("%Y-%m-%d")

    for i in range(5):
        d = monday + timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        day_name = day_names[i]
        info = week_days.get(date_str)
        is_today = date_str == today_str
        alt_style = "on grey19" if i % 2 else ""
        row_style  = "bold" if is_today else alt_style

        if info:
            sessions = info["sessions"]
            total = info["total"]
            pm_start, pm_end = promark_entry(sessions, total)
            t.add_row(
                date_str, day_name,
                pm_start or "—", pm_end or "—",
                f"{total:.2f}h",
                style=row_style,
            )
        else:
            t.add_row(
                date_str, day_name, "—", "—", "—",
                style=row_style,
            )

    return Panel(t, title=title, border_style=_C_PROMARK, padding=(0, 2))


# ── public printers ──────────────────────────────────────────────────────────

def print_status(status: DayStatus, now: datetime) -> None:
    """Live status: sessions, active session, progress bar, leave time."""
    title = (
        f"📅  [bold]{status.today_str}[/bold]"
        f"  [dim]—[/dim]"
        f"  🕐 [bold]{now.strftime('%H:%M')}[/bold]"
    )
    console.print(Panel(
        build_status_group(status, now),
        title=title,
        border_style=_C_BORDER,
        padding=(0, 2),
    ))
    console.print()


def print_day_summary(status: DayStatus) -> None:
    """End-of-session summary: session list, total, delta vs target."""
    title = f"📅  [bold]{status.today_str}[/bold]"
    rows: list = []

    if not status.sessions:
        rows.append(Text("No completed sessions today.", style=_C_DIM))
    else:
        rows.append(_sessions_table(status.sessions))
        rows.append(Text(""))

        diff = status.total_hours - status.target_hours
        sign = "+" if diff >= 0 else ""
        delta_style = _C_OK if diff >= 0 else _C_WARN
        delta_icon  = "✅" if diff >= 0 else "⚠️ "

        rows.append(Text.from_markup(
            f"  Total    [bold]{status.total_hours:.2f}h[/bold]"
            f" [dim]/[/dim] {status.target_hours:.2f}h   "
            + _hours_bar(status.total_hours, status.target_hours)
        ))
        rows.append(Text.from_markup(
            f"  Delta    [{delta_style}]{delta_icon}  {sign}{diff:.2f}h[/{delta_style}]"
        ))

    console.print(Panel(Group(*rows), title=title, border_style=_C_BORDER, padding=(0, 2)))
    console.print()


def print_log_week(week_days: dict, week_num: int, year: int) -> None:
    """Print a full week's sessions (with task labels) and daily/weekly totals."""
    console.print(build_log_week_panel(week_days, week_num, year))
    console.print()


def print_promark_week(week_days: dict, week_num: int, year: int) -> None:
    """Print Mon–Fri Promark entries for the given ISO week as a rich table."""
    console.print(build_promark_panel(week_days, week_num, year))
    console.print()


# ---------------------------------------------------------------------------
# Epic summary
# ---------------------------------------------------------------------------

def _minutes_to_clock(minutes: int) -> str:
    """Convert total minutes to H:MM clock format (e.g. 90 → '1:30')."""
    h, m = divmod(max(minutes, 0), 60)
    return f"{h}:{m:02d}"


def build_epic_summary_panel(data: list[tuple], week_num: int, year: int) -> Panel:
    """Build the Rich Panel for the Epic summary overlay.

    The layout groups time by day first, then by Epic within each day:

        Monday Jun 16            12:30
          Platform Team          10:00
            TASK-123              7:30
          (Misc)                  2:30
            TASK-789              2:30

    Args:
        data: Rows returned by EpicStorage.get_epic_summary_data —
              each row is (date_str, epic_name_or_None, task_id, total_minutes).
              None means the task has no task_catalog entry and belongs
              to the virtual '(Misc)' group.
        week_num: ISO week number.
        year: ISO year.
    """
    jan4 = date(year, 1, 4)
    week1_monday = jan4 - timedelta(days=jan4.weekday())
    monday = week1_monday + timedelta(weeks=week_num - 1)

    title = (
        f"📊  Epic Summary — Week {week_num}"
        f"  [dim]({monday.strftime('%b %d')} – "
        f"{(monday + timedelta(days=4)).strftime('%b %d')})[/dim]"
    )

    # Build ordered structure preserving the SQL sort order (date → epic → task).
    # day_order: list of date strings in order of first appearance.
    # day_epic_order: per-date ordered list of epic display names.
    # epic_task_data: (date_str, epic_display) → [(task_id, minutes)].
    day_order: list[str] = []
    day_epic_order: dict[str, list[str]] = {}
    epic_task_data: dict[tuple, list[tuple[str, int]]] = {}

    for date_str, epic_name, task_id, total_minutes in data:
        display_name = epic_name if epic_name is not None else "(Misc)"
        if date_str not in day_epic_order:
            day_order.append(date_str)
            day_epic_order[date_str] = []
        key = (date_str, display_name)
        if display_name not in day_epic_order[date_str]:
            day_epic_order[date_str].append(display_name)
            epic_task_data[key] = []
        epic_task_data[key].append((task_id, total_minutes))

    _DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    week_total = 0

    # A borderless two-column table lets Rich expand the name column to fill
    # the panel width and right-align the time column, so all clock values
    # line up in one consistent right-hand column regardless of name length.
    t = Table(
        box=None,
        show_header=False,
        show_edge=False,
        padding=(0, 1),
        expand=True,
    )
    t.add_column("Name", ratio=1)          # expands to fill available width
    t.add_column("Time", justify="right", no_wrap=True)

    if not day_order:
        t.add_row(
            Text("No tracked time this week.", style=_C_DIM),
            Text(""),
        )
    else:
        for day_index, date_str in enumerate(day_order):
            day_total = sum(
                mins
                for epic_key in day_epic_order[date_str]
                for _, mins in epic_task_data[(date_str, epic_key)]
            )
            week_total += day_total

            d = date.fromisoformat(date_str)
            day_label = _DAY_NAMES[d.weekday()]
            display_date = d.strftime("%b %d")

            # Blank separator row between days (not before the first).
            if day_index > 0:
                t.add_row(Text(""), Text(""))

            # Day header — bold white.
            t.add_row(
                Text(f"  {day_label} {display_date}", style="bold white"),
                Text(_minutes_to_clock(day_total), style="bold white"),
            )

            for epic_display in day_epic_order[date_str]:
                key = (date_str, epic_display)
                epic_total = sum(mins for _, mins in epic_task_data[key])
                is_misc = epic_display == "(Misc)"

                # Epic row — indented; (Misc) is dim, named Epics are cyan.
                t.add_row(
                    Text(f"    {epic_display}", style="dim" if is_misc else "bold cyan"),
                    Text(_minutes_to_clock(epic_total), style="dim" if is_misc else "bold cyan"),
                )

                # Task rows — double-indented, magenta.
                for task_id, task_mins in sorted(epic_task_data[key]):
                    t.add_row(
                        Text(f"      {task_id}", style="magenta"),
                        Text(_minutes_to_clock(task_mins), style="magenta"),
                    )

    # Separator + week total at the bottom.
    t.add_row(Text(""), Text(""))
    t.add_row(
        Text("  Week total:", style="bold"),
        Text(_minutes_to_clock(week_total), style="bold cyan"),
    )

    return Panel(t, title=title, border_style=_C_PROMARK, padding=(0, 2))
