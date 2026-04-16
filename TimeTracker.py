#!/usr/bin/env python3
"""
Time Tracker — logs work sessions to an Excel file.

Usage:
  python timetracker.py [start|pause|stop|status] [hhmm]
  python timetracker.py          (interactive prompt)
"""

import argparse
from Commands import cmd_start, cmd_pause, cmd_stop, cmd_status


def hhmm(value):
    """Argparse type: validates and converts '0830' -> '08:30'."""
    if len(value) == 4 and value.isdigit():
        h, m = int(value[:2]), int(value[2:])
        if 0 <= h <= 23 and 0 <= m <= 59:
            return f"{h:02d}:{m:02d}"
    raise argparse.ArgumentTypeError(
        f"Invalid time '{value}'. Use 4-digit hhmm, e.g. 0830 for 08:30."
    )


def prompt_command():
    print("What do you want to do?")
    print("  1) start")
    print("  2) pause")
    print("  3) stop")
    print("  4) status")
    choice = input("Enter 1, 2, 3 or 4: ").strip()
    command = {"1": "start", "2": "pause", "3": "stop", "4": "status"}.get(choice)
    if not command:
        print(f"Invalid choice '{choice}'.")
        return None, None
    return command, None


def main():
    parser = argparse.ArgumentParser(
        description="Time tracker — logs work sessions to an Excel file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python timetracker.py start\n"
            "  python timetracker.py start 0830\n"
            "  python timetracker.py pause\n"
            "  python timetracker.py stop 1715\n"
            "  python timetracker.py status\n"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=False)

    for cmd, help_text in [
        ("start",  "Clock in — begin a new session"),
        ("pause",  "Clock out temporarily — resume later with start"),
        ("stop",   "Clock out for the day and update the Summary sheet"),
    ]:
        p = sub.add_parser(cmd, help=help_text)
        p.add_argument("time", nargs="?", type=hhmm, metavar="hhmm",
                       help="Optional time override, e.g. 0830")

    sub.add_parser("status", help="Show today's sessions and estimated leave time")

    args = parser.parse_args()

    if not args.command:
        command, time = prompt_command()
        if not command:
            return
    else:
        command = args.command
        time = getattr(args, "time", None)

    if command == "status":
        cmd_status()
    else:
        {"start": cmd_start, "pause": cmd_pause, "stop": cmd_stop}[command](time)


if __name__ == "__main__":
    main()