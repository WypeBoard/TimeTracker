"""TimeTrackerApp — root Textual application.

Layout:
  ┌─ Header ──────────────────────────────────────────────┐
  │  ┌─ Today ─────────────────┐  ┌─ Week ──────────────┐ │
  │  │  sessions + leave time  │  │  promark-style rows │ │
  │  └─────────────────────────┘  └────────────────────┘ │
  │  ┌─ Task Summary ─────────────────────────────────────┐│
  │  │  Day × Task → Hours pivot for the current week    ││
  │  └───────────────────────────────────────────────────┘│
  │  ┌─ Progress ─────────────────────────────────────────┐│
  │  │  Today H:MM / H:MM [bar] ZZ%                      ││
  │  │  Week  H:MM / H:MM [bar] ZZ%                      ││
  │  └───────────────────────────────────────────────────┘│
  │  ┌─ Output ───────────────────────────────────────────┐│
  │  │  command feedback (scrollable)                    ││
  │  └───────────────────────────────────────────────────┘│
  │  > command input                                       │
  └─ Footer ──────────────────────────────────────────────┘

Keybindings:
  ctrl+q   quit
  l        open LogScreen overlay (week session detail)
  Tab      cycle focus
"""
from datetime import date

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Footer, Header

from app.CommandInput import CommandInput
from app.OutputPanel import OutputPanel
from app.ProgressStrip import ProgressStrip
from app.TaskSummaryPanel import TaskSummaryPanel
from app.TodayPanel import TodayPanel
from app.TuiAppContext import TuiAppContext
from app.WeekPanel import WeekPanel


class TimeTrackerApp(App):
    """The persistent Textual TUI for TimeTracker."""

    TITLE = "TimeTracker"
    SUB_TITLE = "press ctrl+q to quit"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("l", "show_log", "Log"),
    ]

    DEFAULT_CSS = """
    Screen {
        background: $surface;
        layout: vertical;
    }

    #panel-row {
        height: 1fr;
        width: 1fr;
    }

    TodayPanel {
        width: 3fr;
    }

    WeekPanel {
        width: 2fr;
        margin-left: 1;
    }

    TaskSummaryPanel {
        height: auto;
    }

    ProgressStrip {
        height: auto;
    }

    OutputPanel {
        height: 8;
        margin-top: 1;
    }

    CommandInput {
        height: 3;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="panel-row"):
            yield TodayPanel(id="today")
            yield WeekPanel(id="week")
        yield TaskSummaryPanel(id="task-summary")
        yield ProgressStrip(id="progress")
        yield OutputPanel(id="output")
        yield CommandInput(id="cmd")
        yield Footer()

    def on_mount(self) -> None:
        # Wire up the TuiAppContext now that all widgets exist.
        ctx = TuiAppContext(self)
        self.query_one(CommandInput)._ctx = ctx

        # Initial data load for all data-driven panels.
        self.query_one(TodayPanel).refresh_data()
        self.query_one(WeekPanel).refresh_data()
        self.query_one(TaskSummaryPanel).refresh_data()
        self.query_one(ProgressStrip).refresh_data()

        # Focus the command input on startup so the user can type immediately.
        self.query_one(CommandInput).focus()

    def refresh_session_panels(self) -> None:
        """Refresh all data-driven panels.

        Called by TuiAppContext.on_session_changed() after any mutating command.
        """
        self.query_one(TodayPanel).refresh_data()
        self.query_one(WeekPanel).refresh_data()
        self.query_one(TaskSummaryPanel).refresh_data()
        self.query_one(ProgressStrip).refresh_data()

    def action_show_log(self) -> None:
        """Open the week log overlay for full session-by-session detail."""
        from app.LogScreen import LogScreen
        today_iso = date.today().isocalendar()
        self.push_screen(LogScreen(today_iso.week, today_iso.year))