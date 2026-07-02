"""AppContext — output and refresh abstraction layer.

Commands.py dispatches feedback through an AppContext instead of calling
print() directly. This allows the same command logic to be used both in
the Textual TUI (TuiAppContext) and in tests (RecordingContext in test_smoke.py).

Why a Protocol?
---------------
Protocol (from typing) describes a structural interface: any class that
implements the required methods satisfies it, without needing to inherit from
it. This is Python's equivalent of a Go interface or a TypeScript interface.

Two concerns are abstracted:
  1. How feedback messages are delivered (Output panel widget in TUI, captured
     list in tests).
  2. Which UI state needs refreshing after a command (panels in TUI; no-op in
     tests).

A Protocol targeting exactly these two concerns avoids duplicating the command
routing logic that is otherwise identical across contexts.
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

        TUI: triggers a refresh of the Today and Week panels.
        Tests: increments a counter for assertion.
        """
        ...

    def on_day_stopped(self, status: DayStatus) -> None:
        """Signal that the last session of the day has been closed.

        TUI: no-op (the Today panel already shows live data).
        Tests: no-op (not relevant for smoke tests).
        """
        ...

    def show_log(self, week_days: dict, week_num: int, year: int) -> None:
        """Display a full week log.

        TUI: pushes the LogScreen overlay.
        Tests: records the call arguments for assertion.
        """
        ...

    def show_promark(self, week_days: dict, week_num: int, year: int) -> None:
        """Display the Promark table for a week.

        TUI: writes the Promark panel to the Output panel.
        Tests: records the call arguments for assertion.
        """
        ...

    def on_new_task(self, task_id: str) -> None:
        """Signal that a task with no Epic link was used.

        Called after a session is saved when the task identifier has no entry
        in task_catalog.

        TUI: pushes the EpicModal so the user can link the task to an Epic.
        Tests: records the task_id for assertion.
        """
        ...

    def show_epic_summary(self, week_num: int, year: int) -> None:
        """Display the Epic summary overlay for the given ISO week.

        TUI: pushes the EpicSummaryScreen overlay.
        Tests: records the call arguments for assertion.
        """
        ...
