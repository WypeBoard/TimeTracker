"""TimeTrackerApp — root Textual application.

Cockpit layout (see feature `ui-layout-redesign.md`):

  ┌─ Header ────────────────────────────────────────────────────┐
  │  ┌─ Active Session ───────────────┐  ┌─ Quick Stats ─────┐ │
  │  │  task id / epic / running time │  │  today / rem /    │ │
  │  │                                │  │  leave / week /   │ │
  │  │                                │  │  sessions         │ │
  │  └────────────────────────────────┘  └───────────────────┘ │
  │  ┌─ Today's Timeline ────────────────────────────────────┐ │
  │  │  #N  HH:MM – HH:MM  TASK  N.Nh  ▶                     │ │
  │  └───────────────────────────────────────────────────────┘ │
  │  ┌─ Task Notes ──────────────────────────────────────────┐ │
  │  │  Obsidian integration placeholder                     │ │
  │  └───────────────────────────────────────────────────────┘ │
  │  ┌─ Output ──────────────────────────────────────────────┐ │
  │  │  last 3 command results                               │ │
  │  └───────────────────────────────────────────────────────┘ │
  │  > command input                                             │
  └─ Footer ─────────────────────────────────────────────────────┘

Keybindings:
  ctrl+q   quit
  w        open WeeklyOverviewScreen overlay
  Tab      cycle focus
"""
from datetime import date

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Footer, Header

from app.ActiveSessionPanel import ActiveSessionPanel
from app.CommandInput import CommandInput
from app.OutputPanel import OutputPanel
from app.QuickStatsPanel import QuickStatsPanel
from app.TaskNotesPanel import TaskNotesPanel
from app.TodaysTimelinePanel import TodaysTimelinePanel
from app.TuiAppContext import TuiAppContext


class TimeTrackerApp(App):
    """The persistent Textual TUI for TimeTracker."""

    TITLE = "TimeTracker"
    SUB_TITLE = "press ctrl+q to quit"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("w", "show_weekly", "Weekly Overview"),
    ]

    DEFAULT_CSS = """
    Screen {
        background: $surface;
        layout: vertical;
    }

    /* Fixed top-row height so both panels align to the same bottom edge
       regardless of how many content lines each one renders (Active Session
       renders 3–4 lines depending on Epic assignment; Quick Stats always
       renders 5). Height = 5 content lines + 2 border lines = 7. */
    #top-row {
        height: 7;
        width: 1fr;
    }

    ActiveSessionPanel {
        width: 3fr;
        height: 100%;
    }

    QuickStatsPanel {
        width: 1fr;
        height: 100%;
    }

    TodaysTimelinePanel {
        height: 8;
    }

    TaskNotesPanel {
        height: 1fr;
    }

    OutputPanel {
        height: 5;
        margin-top: 1;
    }

    CommandInput {
        height: 3;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="top-row"):
            yield ActiveSessionPanel(id="active-session")
            yield QuickStatsPanel(id="quick-stats")
        yield TodaysTimelinePanel(id="timeline")
        yield TaskNotesPanel(id="notes")
        yield OutputPanel(id="output")
        yield CommandInput(id="cmd")
        yield Footer()

    def on_mount(self) -> None:
        # Wire up the TuiAppContext now that all widgets exist.
        ctx = TuiAppContext(self)
        self.query_one(CommandInput)._ctx = ctx

        # Initial data load for all data-driven panels.
        self.query_one(ActiveSessionPanel).refresh_data()
        self.query_one(QuickStatsPanel).refresh_data()
        self.query_one(TodaysTimelinePanel).refresh_data()

        # Focus the command input on startup so the user can type immediately.
        self.query_one(CommandInput).focus()

    def refresh_session_panels(self) -> None:
        """Refresh all data-driven cockpit panels.

        Called by TuiAppContext.on_session_changed() after any mutating command.
        TaskNotesPanel is static — no data source, no refresh.
        """
        self.query_one(ActiveSessionPanel).refresh_data()
        self.query_one(QuickStatsPanel).refresh_data()
        self.query_one(TodaysTimelinePanel).refresh_data()

    def action_show_weekly(self) -> None:
        """Open the Weekly Overview overlay for the current ISO week."""
        from app.WeeklyOverviewScreen import WeeklyOverviewScreen
        today_iso = date.today().isocalendar()
        self.push_screen(WeeklyOverviewScreen(today_iso.week, today_iso.year))

    def action_show_config(self) -> None:
        """Open the configuration screen."""
        from app.ConfigScreen import ConfigScreen
        self.push_screen(ConfigScreen())
