"""TodaysTimelinePanel — full-width chronological list of today's sessions.

One row per session with columns: index, start, separator, end (or ``Now``),
task ID, right-aligned duration in decimal hours, and a ``▶`` marker on the
active session (feature `ui-layout-redesign.md` §8).

The panel is a Textual ``ScrollableContainer`` so that days with more than
5–6 sessions overflow gracefully instead of pushing lower panels off-screen.
"""
from __future__ import annotations

from datetime import datetime

from rich.table import Table
from rich.text import Text
from rich import box
from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Static


class TodaysTimelinePanel(ScrollableContainer):
    """Full-width panel listing today's sessions in chronological order."""

    DEFAULT_CSS = """
    TodaysTimelinePanel {
        border: solid $accent;
        padding: 0 1;
        height: 8;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(id="timeline-content")

    def on_mount(self) -> None:
        self.border_title = "Today's Timeline"
        self.refresh_data()
        self.set_interval(60, self.refresh_data)

    def refresh_data(self) -> None:
        from Commands import _build_day_status

        status = _build_day_status(datetime.now())
        content = self.query_one("#timeline-content", Static)

        if not status.sessions and not status.active_start:
            content.update(Text("No sessions recorded today.", style="dim"))
            return

        content.update(_build_timeline_table(status))
        # Keep the active session visible when the list overflows.
        self.scroll_end(animate=False)


def _build_timeline_table(status) -> Table:
    from Commands import _session_hours

    table = Table(
        box=box.SIMPLE,
        show_header=False,
        padding=(0, 1),
        show_edge=False,
        expand=True,
    )
    table.add_column("#",     style="dim",  no_wrap=True)
    table.add_column("Start", no_wrap=True)
    table.add_column("Sep",   no_wrap=True, style="dim")
    table.add_column("End",   no_wrap=True)
    table.add_column("Task",  style="magenta", no_wrap=True)
    table.add_column("Hours", justify="right", no_wrap=True)
    table.add_column("Act",   no_wrap=True)

    idx = 0
    for start, end, task in status.sessions:
        idx += 1
        hours = _session_hours(start, end)
        table.add_row(
            f"#{idx}", start, "–", end,
            task or "",
            f"{hours:.1f}h",
            "",
        )

    if status.active_start:
        idx += 1
        # Highlight every cell of the active row so the accent colour reads
        # consistently regardless of the surrounding row style.
        active_style = "bold green"
        table.add_row(
            Text(f"#{idx}", style=active_style),
            Text(status.active_start, style=active_style),
            Text("–", style=active_style),
            Text("Now", style=active_style),
            Text(status.active_task or "", style=active_style),
            Text(f"{status.active_hours:.1f}h", style=active_style),
            Text("▶", style=active_style),
        )

    return table
