"""TimeTrackerApp — root Textual application.

Layout:
  ┌─ Header ──────────────────────────────────────────────┐
  │  ┌─ Today ─────────────────┐  ┌─ Week ──────────────┐ │
  │  │  sessions + progress    │  │  Mon–Fri totals     │ │
  │  └─────────────────────────┘  └────────────────────┘ │
  │  ┌─ Output ───────────────────────────────────────────┐│
  │  │  command feedback (scrollable)                    ││
  │  └───────────────────────────────────────────────────┘│
  │  > command input                                       │
  └─ Footer ──────────────────────────────────────────────┘

Keybindings:
  ctrl+q   quit
  ?        show help (placeholder — not yet implemented)
  Tab      cycle focus
"""
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Footer, Header

from app.CommandInput import CommandInput
from app.OutputPanel import OutputPanel
from app.TodayPanel import TodayPanel
from app.TuiAppContext import TuiAppContext
from app.WeekPanel import WeekPanel


class TimeTrackerApp(App):
    """The persistent Textual TUI for TimeTracker."""

    TITLE = "TimeTracker"
    SUB_TITLE = "press ctrl+q to quit"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
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
        yield OutputPanel(id="output")
        yield CommandInput(id="cmd")
        yield Footer()

    def on_mount(self) -> None:
        # Wire up the TuiAppContext now that all widgets exist.
        ctx = TuiAppContext(self)
        self.query_one(CommandInput)._ctx = ctx

        # Initial data load.
        self.query_one(TodayPanel).refresh_data()
        self.query_one(WeekPanel).refresh_data()

        # Focus the command input on startup so the user can type immediately.
        self.query_one(CommandInput).focus()

    def refresh_session_panels(self) -> None:
        """Refresh both the Today and Week panels.

        Called by TuiAppContext.on_session_changed() after any mutating command.
        """
        self.query_one(TodayPanel).refresh_data()
        self.query_one(WeekPanel).refresh_data()
