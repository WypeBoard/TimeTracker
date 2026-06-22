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
        show_progress: When False, the progress bar and leave-time lines are
            omitted. Set to False in the TUI path because ProgressStrip owns
            that responsibility; leave True for the CLI path.
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

        remaining = status.remaining
        if remaining <= 0:
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
        else:
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
