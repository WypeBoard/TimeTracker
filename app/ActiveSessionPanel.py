"""ActiveSessionPanel — cockpit panel showing the currently running session.

Three display states are rendered by :meth:`refresh_data`:

- **Active** — task ID, optional Epic line, and a live running-time ticker
  next to the session start.
- **Idle with history** — "No active session" plus the end time and task ID
  of the most recently closed session today.
- **Idle, empty day** — "No active session" alone.

The panel ticks once per second so the running-time value stays current
without user interaction (per feature `ui-layout-redesign.md` §3).
"""
from __future__ import annotations

from datetime import datetime

from rich.console import Group
from rich.text import Text
from textual.widgets import Static


class ActiveSessionPanel(Static):
    """Top-left cockpit panel — active session context and running time."""

    DEFAULT_CSS = """
    ActiveSessionPanel {
        border: solid $accent;
        padding: 0 1;
    }
    """

    def on_mount(self) -> None:
        self.border_title = "Active Session"
        self.refresh_data()
        # 1 Hz ticker: the running-time counter needs sub-minute precision.
        # _build_day_status hits SQLite each tick — acceptable for a local
        # single-user file DB; profile before optimising.
        self.set_interval(1, self.refresh_data)

    def refresh_data(self) -> None:
        from Commands import _build_day_status
        from EpicStorage import get_task_epic

        now = datetime.now()
        status = _build_day_status(now)

        if status.active_start and status.active_task is not None:
            self.update(_render_active(status, now, get_task_epic))
        elif status.sessions:
            self.update(_render_idle_with_history(status.sessions))
        else:
            self.update(_render_idle_empty())


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------

def _render_active(status, now: datetime, get_task_epic) -> Group:
    """Build the active-state renderable.

    Sessions do not store a separate "task name" field — the ID doubles as
    the label. The feature spec's "task_id · task_name" line is therefore
    rendered as the task ID alone.
    """
    task_id = status.active_task or ""
    running = _running_time(status.active_start, now)

    rows: list = [
        Text(task_id, style="bold"),
    ]

    epic_row = get_task_epic(task_id) if task_id else None
    if epic_row is not None:
        _epic_id, epic_name = epic_row
        rows.append(Text.from_markup(f"[dim]Epic:[/dim] {epic_name}"))

    rows.append(Text(""))
    rows.append(Text.from_markup(
        f"[bold green]Running[/bold green]  {running}"
        f"    [dim]Started[/dim]  {status.active_start}"
    ))
    return Group(*rows)


def _render_idle_with_history(sessions: list[tuple[str, str, str]]) -> Group:
    last_start, last_end, last_task = sessions[-1]
    task_suffix = f"  ({last_task})" if last_task else ""
    return Group(
        Text("No active session", style="dim"),
        Text(""),
        Text.from_markup(f"[dim]Last ended[/dim]  {last_end}{task_suffix}"),
    )


def _render_idle_empty() -> Group:
    return Group(Text("No active session", style="dim"))


def _running_time(active_start: str, now: datetime) -> str:
    """Return the current running duration as ``HH:MM:SS``.

    Falls back to ``00:00:00`` if the stored start time cannot be parsed —
    same defensive posture as Commands._build_day_status.
    """
    try:
        start = datetime.strptime(active_start, "%H:%M")
    except ValueError:
        return "00:00:00"
    start_dt = now.replace(hour=start.hour, minute=start.minute,
                           second=0, microsecond=0)
    delta = now - start_dt
    total = max(int(delta.total_seconds()), 0)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"
