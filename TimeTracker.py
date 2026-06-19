#!/usr/bin/env python3
"""
Time Tracker — logs work sessions to a SQLite database.

Usage:
  python TimeTracker.py [start|pause|stop|resume|restart|status|task|log|promark] [args]
  python TimeTracker.py          (launches the Textual TUI)
"""

import argparse
import re
from app_context import CliAppContext
from Commands import (
    cmd_start, cmd_pause, cmd_stop, cmd_resume, cmd_restart,
    cmd_status, cmd_task, cmd_log, cmd_promark,
)
from Storage import create_schema


def hhmm(value):
    """Argparse type: validates and converts '0830' -> '08:30'."""
    if len(value) == 4 and value.isdigit():
        h, m = int(value[:2]), int(value[2:])
        if 0 <= h <= 23 and 0 <= m <= 59:
            return f"{h:02d}:{m:02d}"
    raise argparse.ArgumentTypeError(
        f"Invalid time '{value}'. Use 4-digit hhmm, e.g. 0830 for 08:30."
    )


def week_arg(value):
    """Argparse type: validates 'w21' style week arguments."""
    if re.fullmatch(r'[wW]\d{1,2}', value):
        n = int(value[1:])
        if 1 <= n <= 53:
            return f"w{n:02d}"
    raise argparse.ArgumentTypeError(
        f"Invalid week '{value}'. Use format wNN, e.g. w21 for week 21."
    )


def _parse_start_args(raw_args):
    """Parse the variadic args for 'start': optional hhmm + optional epic."""
    time_override = None
    epic = None
    args = list(raw_args)
    if args and re.fullmatch(r'\d{4}', args[0]):
        val = args.pop(0)
        h, m = int(val[:2]), int(val[2:])
        if 0 <= h <= 23 and 0 <= m <= 59:
            time_override = f"{h:02d}:{m:02d}"
        else:
            print(f"⚠  Invalid time '{val}' — ignoring.")
    if args:
        epic = " ".join(args)
    return time_override, epic


def main():
    # Ensure the database directory, tables, and triggers exist before any
    # command runs. Safe to call on every startup — all DDL uses IF NOT EXISTS.
    create_schema()

    parser = argparse.ArgumentParser(
        description="Time tracker — logs work sessions to a SQLite database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python TimeTracker.py start\n"
            "  python TimeTracker.py start 0830\n"
            "  python TimeTracker.py start Epic-42\n"
            "  python TimeTracker.py start 0830 Epic-42\n"
            "  python TimeTracker.py resume\n"
            "  python TimeTracker.py resume 1150\n"
            "  python TimeTracker.py pause\n"
            "  python TimeTracker.py stop 1715\n"
            "  python TimeTracker.py status\n"
            "  python TimeTracker.py task Epic-42\n"
            "  python TimeTracker.py task Epic-42 -s 2\n"
            "  python TimeTracker.py log\n"
            "  python TimeTracker.py log w23\n"
            "  python TimeTracker.py promark\n"
            "  python TimeTracker.py promark w23\n"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=False)

    # start — variadic to handle optional hhmm + optional epic
    p_start = sub.add_parser("start", help="Clock in — begin a new session")
    p_start.add_argument("args", nargs="*", metavar="[hhmm] [epic]",
                         help="Optional time (4-digit hhmm) and/or task/epic ID")

    # pause / stop — optional time override
    for cmd, help_text in [
        ("pause", "Clock out temporarily — resume later with start"),
        ("stop",  "Clock out for the day and show a day summary"),
    ]:
        p = sub.add_parser(cmd, help=help_text)
        p.add_argument("time", nargs="?", type=hhmm, metavar="hhmm",
                       help="Optional time override, e.g. 0830")

    # resume — close current session (if any) and reopen, carrying epic forward
    p_resume = sub.add_parser(
        "resume",
        help="Resume after a break, carrying the epic forward",
    )
    p_resume.add_argument("time", nargs="?", type=hhmm, metavar="hhmm",
                          help="Optional time override, e.g. 1150")

    # restart — deprecated alias for resume
    p_restart = sub.add_parser(
        "restart",
        help="Deprecated — use 'resume' instead",
    )
    p_restart.add_argument("time", nargs="?", type=hhmm, metavar="hhmm",
                           help="Optional time override, e.g. 1015")

    sub.add_parser("status", help="Show today's sessions and estimated leave time")

    # task — required epic, optional -s N
    p_task = sub.add_parser("task", help="Tag current or specified session with a task/epic ID")
    p_task.add_argument("epic", metavar="epic", help="Task/epic ID, e.g. Epic-42")
    p_task.add_argument("-s", dest="session_num", type=int, metavar="N",
                        help="Target session number for today (default: current/last)")

    # log — optional week
    p_log = sub.add_parser("log", help="Show full week log with task labels (default: current week)")
    p_log.add_argument("week", nargs="?", type=week_arg, metavar="wNN",
                       help="Week to display, e.g. w23. Defaults to the current week.")

    # promark — optional week
    p_pm = sub.add_parser("promark", help="Show Promark entries (defaults to current week)")
    p_pm.add_argument("week", nargs="?", type=week_arg, metavar="wNN",
                      help="Week to display, e.g. w21. Defaults to the current week.")

    args = parser.parse_args()

    if not args.command:
        # No subcommand — launch the Textual TUI.
        from app.TimeTrackerApp import TimeTrackerApp
        TimeTrackerApp().run()
        return

    # One-shot CLI mode: instantiate a CliAppContext and dispatch.
    ctx = CliAppContext()
    command = args.command

    if command == "start":
        time_override, epic = _parse_start_args(getattr(args, "args", []))
        cmd_start(ctx, time_override, epic)
    elif command == "pause":
        cmd_pause(ctx, getattr(args, "time", None))
    elif command == "stop":
        cmd_stop(ctx, getattr(args, "time", None))
    elif command == "resume":
        cmd_resume(ctx, getattr(args, "time", None))
    elif command == "restart":
        cmd_restart(ctx, getattr(args, "time", None))
    elif command == "status":
        cmd_status()
    elif command == "task":
        cmd_task(ctx, args.epic, args.session_num)
    elif command == "log":
        cmd_log(ctx, getattr(args, "week", None))
    elif command == "promark":
        cmd_promark(ctx, getattr(args, "week", None))


if __name__ == "__main__":
    main()