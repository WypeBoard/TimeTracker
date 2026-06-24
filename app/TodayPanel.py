"""TodayPanel — live view of today's work sessions.

Displays the same information as the CLI's `status` command:
  - Session table with start/end times, hours, and task labels.
  - Active session row (if running) marked with "now ▶".
  - Progress bar showing logged hours vs. target.
  - Estimated leave time (when a session is active).

The panel refreshes automatically every 60 seconds while any session is
active so the active_hours and leave estimate stay current without user
action. It also refreshes on demand when TuiAppContext.on_session_changed()
is called (after start, stop, pause, resume, task).
"""
from datetime import datetime

from textual.widgets import Static


class TodayPanel(Static):
    """Today's sessions, progress bar, and leave time estimate."""

    DEFAULT_CSS = """
    TodayPanel {
        width: 3fr;
        border: solid $accent;
        padding: 0 1;
        height: auto;
        min-height: 10;
    }
    """

    def on_mount(self) -> None:
        self.refresh_data()
        # Refresh every 60 seconds so the active_hours counter stays current.
        self.set_interval(60, self.refresh_data)

    def refresh_data(self) -> None:
        """Re-query today's sessions and redraw the panel content.

        The progress bar is intentionally omitted here (show_progress=False)
        because ProgressStrip owns that responsibility on the TUI dashboard.
        The CLI path via print_status() is unaffected.
        """
        from Commands import _build_day_status
        from Printer import build_status_group

        now = datetime.now()
        status = _build_day_status(now)
        group = build_status_group(status, now, show_progress=False)

        self.update(group)
        self.border_title = f"Today: {status.today_str}"
