"""AppContext — output and refresh abstraction layer.

Commands.py dispatches feedback through an AppContext instead of calling
print() directly. This allows the same command logic to work in both the
one-shot CLI (CliAppContext) and the Textual TUI (TuiAppContext).

Why a Protocol?
---------------
Protocol (from typing) describes a structural interface: any class that
implements the required methods satisfies it, without needing to inherit from
it. This is Python's equivalent of a Go interface or a TypeScript interface.

Two things differ between CLI and TUI mode:
  1. How feedback messages are delivered (stdout vs. Output panel widget).
  2. Which UI state needs refreshing after a command (nothing in CLI; panels
     in TUI).

A Protocol targeting exactly these two concerns avoids duplicating the command
routing logic that is otherwise identical in both modes.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from Printer import DayStatus


class AppContext(Protocol):
    """Structural interface for delivering command feedback and refresh signals.

    Any class that provides these methods is a valid AppContext — no
    inheritance required.
    """

    def info(self, message: str) -> None:
        """Deliver an informational message to the user."""
        ...

    def warning(self, message: str) -> None:
        """Deliver a warning message to the user."""
        ...

    def error(self, message: str) -> None:
        """Deliver an error message to the user."""
        ...

    def on_session_changed(self) -> None:
        """Signal that session data has changed.

        CLI: no-op (the process exits after each command).
        TUI: triggers a refresh of the Today and Week panels.
        """
        ...

    def on_day_stopped(self, status: DayStatus) -> None:
        """Signal that the last session of the day has been closed.

        CLI: prints the end-of-day summary panel.
        TUI: no-op (the Today panel already shows live data).
        """
        ...

    def show_log(self, week_days: dict, week_num: int, year: int) -> None:
        """Display a full week log.

        CLI: prints the log panel to stdout.
        TUI: pushes the LogScreen overlay.
        """
        ...

    def show_promark(self, week_days: dict, week_num: int, year: int) -> None:
        """Display the Promark table for a week.

        CLI: prints the Promark panel to stdout.
        TUI: writes the Promark panel to the Output panel.
        """
        ...


class CliAppContext:
    """AppContext for one-shot CLI mode.

    Delivers messages via print() and renders panels to stdout through the
    Printer module. All signals (on_session_changed, on_day_stopped) are
    no-ops because the process exits after each command anyway.
    """

    def info(self, message: str) -> None:
        print(message)

    def warning(self, message: str) -> None:
        print(message)

    def error(self, message: str) -> None:
        print(message)

    def on_session_changed(self) -> None:
        pass  # CLI exits after each command — no live panels to refresh.

    def on_day_stopped(self, status: DayStatus) -> None:
        from Printer import print_day_summary
        print_day_summary(status)

    def show_log(self, week_days: dict, week_num: int, year: int) -> None:
        from Printer import print_log_week
        print_log_week(week_days, week_num, year)

    def show_promark(self, week_days: dict, week_num: int, year: int) -> None:
        from Printer import print_promark_week
        print_promark_week(week_days, week_num, year)
