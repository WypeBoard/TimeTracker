"""CommandInput — the command bar at the bottom of the TUI.

Accepts the same command syntax as the one-shot CLI:
  start [hhmm] [epic]
  pause [hhmm]
  stop  [hhmm]
  resume [hhmm]
  restart [hhmm]          (deprecated alias for resume)
  task <epic> [-s N]
  log [wNN]
  promark [wNN]
  status                  (refreshes TodayPanel instead of printing)

Supports:
  Enter    submit command and clear the field
  Up/Down  navigate command history within the session
  Esc      clear the current input
"""
from __future__ import annotations

import re

from textual.widgets import Input


class CommandInput(Input):
    """The command bar. Parses and dispatches commands to Commands.py."""

    DEFAULT_CSS = """
    CommandInput {
        border: solid $accent-darken-1;
        margin-top: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(placeholder="> type a command…", **kwargs)
        # _ctx is injected by TimeTrackerApp.on_mount after all widgets exist.
        self._ctx = None
        self._history: list[str] = []
        self._history_pos: int = -1   # -1 means "not browsing history"

    # ------------------------------------------------------------------ #
    # Textual event handlers
    # ------------------------------------------------------------------ #

    def on_input_submitted(self, event: Input.Submitted) -> None:
        raw = event.value.strip()
        if raw:
            self._history.append(raw)
            self._history_pos = -1
            self._dispatch(raw)
        self.value = ""

    def on_key(self, event) -> None:
        """Handle Up/Down for command history navigation."""
        if event.key == "up":
            if self._history:
                if self._history_pos == -1:
                    self._history_pos = len(self._history) - 1
                elif self._history_pos > 0:
                    self._history_pos -= 1
                self.value = self._history[self._history_pos]
                self.cursor_position = len(self.value)
            event.stop()
        elif event.key == "down":
            if self._history_pos != -1:
                if self._history_pos < len(self._history) - 1:
                    self._history_pos += 1
                    self.value = self._history[self._history_pos]
                else:
                    self._history_pos = -1
                    self.value = ""
                self.cursor_position = len(self.value)
            event.stop()
        elif event.key == "escape":
            self.value = ""
            self._history_pos = -1

    # ------------------------------------------------------------------ #
    # Command dispatch
    # ------------------------------------------------------------------ #

    def _dispatch(self, raw: str) -> None:
        """Parse a raw command string and call the appropriate cmd_* function."""
        if self._ctx is None:
            return

        tokens = raw.split()
        command = tokens[0].lower()
        args = tokens[1:]

        if command == "status":
            # status refreshes the Today panel directly — no cmd_status call.
            from app.TodayPanel import TodayPanel
            self.app.query_one(TodayPanel).refresh_data()
            return

        if command == "log":
            week_str = _parse_week_arg(args[0]) if args else None
            from Commands import cmd_log
            cmd_log(self._ctx, week_str)
            return

        if command == "start":
            time_override, epic = _parse_start_args(args)
            from Commands import cmd_start
            cmd_start(self._ctx, time_override, epic)
            return

        if command in ("pause", "stop", "resume", "restart"):
            time_override = _parse_hhmm(args[0]) if args else None
            from Commands import cmd_pause, cmd_stop, cmd_resume, cmd_restart
            if command == "pause":
                cmd_pause(self._ctx, time_override)
            elif command == "stop":
                cmd_stop(self._ctx, time_override)
            elif command == "resume":
                cmd_resume(self._ctx, time_override)
            elif command == "restart":
                cmd_restart(self._ctx, time_override)
            return

        if command == "task":
            if not args:
                self._ctx.error("⚠  Usage: task <epic> [-s N]")
                return
            epic = args[0]
            session_num = None
            if len(args) >= 3 and args[1] == "-s":
                try:
                    session_num = int(args[2])
                except ValueError:
                    self._ctx.error("⚠  -s requires an integer session number.")
                    return
            from Commands import cmd_task
            cmd_task(self._ctx, epic, session_num)
            return

        if command == "promark":
            week_str = _parse_week_arg(args[0]) if args else None
            from Commands import cmd_promark
            cmd_promark(self._ctx, week_str)
            return

        if command in ("quit", "exit", "q"):
            self.app.exit()
            return

        self._ctx.error(f"⚠  Unknown command: {command!r}")


# ---------------------------------------------------------------------------
# Parsing helpers (local copies — avoids importing from TimeTracker.py)
# ---------------------------------------------------------------------------

def _parse_hhmm(value: str) -> str | None:
    """Convert a 4-digit hhmm string to 'HH:MM', or return None if invalid."""
    if re.fullmatch(r"\d{4}", value):
        h, m = int(value[:2]), int(value[2:])
        if 0 <= h <= 23 and 0 <= m <= 59:
            return f"{h:02d}:{m:02d}"
    return None


def _parse_start_args(args: list[str]) -> tuple[str | None, str | None]:
    """Parse tokens for 'start': optional hhmm, then optional epic string."""
    time_override = None
    epic = None
    remaining = list(args)
    if remaining and re.fullmatch(r"\d{4}", remaining[0]):
        time_override = _parse_hhmm(remaining.pop(0))
    if remaining:
        epic = " ".join(remaining)
    return time_override, epic


def _parse_week_arg(value: str) -> str | None:
    """Validate and normalise a wNN week string, or return None if invalid."""
    if re.fullmatch(r"[wW]\d{1,2}", value):
        n = int(value[1:])
        if 1 <= n <= 53:
            return f"w{n:02d}"
    return None
