"""Command implementations for TimeTracker.

Each public cmd_* function accepts an AppContext as its first argument.
AppContext abstracts the two things that differ between CLI and TUI mode:
  1. How feedback messages are delivered.
  2. Which UI elements need refreshing after a mutation.

The TYPE_CHECKING guard on the AppContext import means the type annotation is
only evaluated by type-checkers (e.g. mypy, Pyright), not at runtime. This
avoids importing app_context at startup time in all code paths.
"""
from __future__ import annotations

from datetime import datetime, date
from typing import TYPE_CHECKING

from Constants import TARGET_HOURS
from Storage import (
    open_session, close_session, update_session_task,
    get_open_session, get_today_sessions, read_log,
)
from EpicStorage import (
    add_epic, list_epics, get_task_epic,
    get_epic_summary_data,
)
from Promark import promark_entry
from Printer import DayStatus, print_status

if TYPE_CHECKING:
    # AppContext is imported only for type checking; at runtime the parameter
    # is duck-typed — any object with the required methods will work.
    from app_context import AppContext


def cmd_start(ctx: AppContext, time_override: str | None = None, epic: str | None = None) -> None:
    """Open a new work session."""
    open_sess = get_open_session()
    if open_sess:
        _id, _date, start, _task = open_sess
        ctx.warning(f"⚠  Session already running since {start}. Use 'pause' or 'stop' first.")
        return

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = time_override or now.strftime("%H:%M")

    open_session(date_str, time_str, epic or "")

    epic_suffix = f" — {epic}" if epic else ""
    note = " (manually set)" if time_override else ""
    ctx.info(f"▶  Started at {time_str}{epic_suffix}{note}")
    ctx.on_session_changed()

    # Notify if the task has no Epic link yet so the TUI can show the modal.
    _notify_if_new_task(ctx, epic)


def cmd_pause(ctx: AppContext, time_override: str | None = None) -> None:
    """Close the current session without printing a day summary."""
    closed = _close_session(ctx, time_override)
    if closed:
        ctx.on_session_changed()


def cmd_stop(ctx: AppContext, time_override: str | None = None) -> None:
    """Close the current session and trigger the end-of-day summary."""
    closed = _close_session(ctx, time_override)
    if not closed:
        return
    status = _build_day_status()
    ctx.on_day_stopped(status)
    ctx.on_session_changed()


def cmd_resume(ctx: AppContext, time_override: str | None = None) -> None:
    """Open a new session, carrying the epic from the most recent session forward.

    Handles three cases:
      - An open session exists: close it at time_str, then open a new one with
        the same epic (so 'resume' = 'pause' + 'start <same_epic>').
      - No open session but closed sessions exist today: open a new session
        carrying the last session's epic.
      - No sessions at all today: error.

    'resume' is the natural inverse of 'pause': clock out -> break -> clock back
    in. The epic is visible in the confirmation line so the user can verify.
    """
    today_sessions = get_today_sessions()  # [(id, start, end, task)]

    if not today_sessions:
        ctx.error("⚠  No sessions today. Run 'start' first.")
        return

    # Carry the epic from the last session (open or closed).
    last_id, last_start, last_end, last_task = today_sessions[-1]

    time_str = time_override or datetime.now().strftime("%H:%M")

    open_sess = get_open_session()
    if open_sess:
        # Close the open session first, then reopen with the carried epic.
        open_id, _date, open_start, _ = open_sess
        today_ids = [s[0] for s in today_sessions]
        session_num = today_ids.index(open_id) + 1 if open_id in today_ids else "?"
        close_session(open_id, time_str)
        ctx.info(f"⏸  Closed #{session_num} — {open_start} → {time_str}")

    # Open the new session carrying the epic forward.
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    open_session(date_str, time_str, last_task or "")

    # Determine the new session number by re-querying.
    new_sessions = get_today_sessions()
    new_num = len(new_sessions)
    carry_note = f"  {last_task}  (carried forward)" if last_task else ""
    ctx.info(f"▶  Started #{new_num} — {time_str}{carry_note}")
    ctx.on_session_changed()

    # Notify if the carried task has no Epic link yet.
    _notify_if_new_task(ctx, last_task)


def cmd_restart(ctx: AppContext, time_override: str | None = None) -> None:
    """Deprecated alias for cmd_resume.

    'restart' has been renamed to 'resume'. This alias prints a deprecation
    notice and then delegates to cmd_resume. It will be removed in a future
    cleanup.
    """
    ctx.warning("⚠  'restart' is deprecated — use 'resume' instead.")
    cmd_resume(ctx, time_override)


def cmd_status() -> None:
    """Print the live status panel to stdout.

    Does not accept AppContext: in TUI mode cmd_status is bypassed entirely
    by CommandInput, which refreshes the TodayPanel directly instead.
    """
    now = datetime.now()
    print_status(_build_day_status(now), now)


def cmd_task(ctx: AppContext, epic: str, session_num: int | None = None) -> None:
    """Tag a session with a Task/Epic ID."""
    today_sessions = get_today_sessions()  # [(id, start, end, task)]
    if not today_sessions:
        ctx.error("⚠  No sessions found for today.")
        return

    if session_num is not None:
        idx = session_num - 1
        if idx < 0 or idx >= len(today_sessions):
            ctx.warning(
                f"⚠  Session #{session_num} not found. "
                f"Today has {len(today_sessions)} session(s)."
            )
            return
        target = today_sessions[idx]
    else:
        # Default: open session if it belongs to today, otherwise last session.
        open_sess = get_open_session()
        if open_sess:
            open_id = open_sess[0]
            today_ids = [s[0] for s in today_sessions]
            target = (
                today_sessions[today_ids.index(open_id)]
                if open_id in today_ids
                else today_sessions[-1]
            )
        else:
            target = today_sessions[-1]

    target_id = target[0]
    target_idx = today_sessions.index(target) + 1
    update_session_task(target_id, epic)
    ctx.info(f"📌  #{target_idx}  {epic}  saved.")
    ctx.on_session_changed()

    # Notify if the task has no Epic link yet so the TUI can show the modal.
    _notify_if_new_task(ctx, epic)


def cmd_log(ctx: AppContext, week_str: str | None = None) -> None:
    """Show a full week's sessions with task labels."""
    days = read_log()

    today_iso = date.today().isocalendar()
    target_week = today_iso.week if week_str is None else int(week_str[1:])
    target_year = today_iso.year

    week_days = {
        d: info for d, info in days.items()
        if date.fromisoformat(d).isocalendar().week == target_week
        and date.fromisoformat(d).isocalendar().year == target_year
    }

    ctx.show_log(week_days, target_week, target_year)


def cmd_promark(ctx: AppContext, week_str: str | None = None) -> None:
    """Print a full week's Promark entries."""
    days = read_log()

    today_iso = date.today().isocalendar()
    target_week = today_iso.week if week_str is None else int(week_str[1:])
    target_year = today_iso.year

    week_days = {
        d: info for d, info in days.items()
        if date.fromisoformat(d).isocalendar().week == target_week
        and date.fromisoformat(d).isocalendar().year == target_year
    }

    ctx.show_promark(week_days, target_week, target_year)


def cmd_epic_add(ctx: AppContext, name: str) -> None:
    """Create a new Epic with the given free-text name."""
    result = add_epic(name)
    if result is None:
        ctx.warning("⚠  An Epic with that name already exists.")
    else:
        ctx.info(f"✅  Epic '{name}' created.")


def cmd_epic_list(ctx: AppContext) -> None:
    """List all defined Epics, sorted alphabetically by name."""
    epics = list_epics()
    if not epics:
        ctx.info("No Epics defined yet. Use 'epic add <name>' to create one.")
        return
    lines = [f"  {epic_id}  {name}" for epic_id, name in epics]
    ctx.info("\n".join(lines))


def cmd_epic_summary(ctx: AppContext, week_str: str | None = None) -> None:
    """Open the Epic summary overlay for the target week."""
    today_iso = date.today().isocalendar()
    target_week = today_iso.week if week_str is None else int(week_str[1:])
    target_year = today_iso.year
    ctx.show_epic_summary(target_week, target_year)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_day_status(now: datetime | None = None) -> DayStatus:
    """Gather today's log data into a DayStatus for the printers."""
    now = now or datetime.now()
    today_str = date.today().strftime("%Y-%m-%d")

    today_sessions = get_today_sessions()

    completed = [
        (start, end, task)
        for _id, start, end, task in today_sessions
        if end is not None
    ]
    total_hours = sum(_session_hours(s, e) for s, e, _ in completed)

    active_start = None
    active_hours = 0.0
    active_task = None

    open_sess = get_open_session()
    if open_sess:
        _id, _date, active_start, active_task = open_sess
        active_task = active_task or None
        try:
            s = datetime.strptime(active_start, "%H:%M")
            active_hours = (now.hour * 60 + now.minute - (s.hour * 60 + s.minute)) / 60
        except ValueError:
            active_hours = 0.0

    pm_start, pm_end = promark_entry(completed, total_hours) if completed else (None, None)

    return DayStatus(
        today_str=today_str,
        sessions=completed,
        total_hours=total_hours,
        target_hours=TARGET_HOURS,
        active_start=active_start,
        active_hours=active_hours,
        active_task=active_task,
        promark_start=pm_start,
        promark_end=pm_end,
    )


def _session_hours(start: str, end: str) -> float:
    """Calculate decimal hours between two HH:MM strings."""
    try:
        s = datetime.strptime(start, "%H:%M")
        e = datetime.strptime(end, "%H:%M")
        return (e.hour * 60 + e.minute - (s.hour * 60 + s.minute)) / 60
    except ValueError:
        return 0.0


def _close_session(ctx: AppContext, time_override: str | None = None) -> bool:
    """Close the open session. Returns True on success, False if none is open."""
    open_sess = get_open_session()
    if not open_sess:
        ctx.error("⚠  No open session found. Run 'start' first.")
        return False

    sess_id, date_val, start_val, _task = open_sess
    time_str = time_override or datetime.now().strftime("%H:%M")
    close_session(sess_id, time_str)

    note = " (manually set)" if time_override else ""
    ctx.info(f"⏸  Closed — {date_val}  {start_val} → {time_str}{note}")
    return True


def _notify_if_new_task(ctx: AppContext, task: str | None) -> None:
    """Notify the context if task is non-empty and has no Epic link.

    Called after saving a session so the TUI can show the EpicModal.
    In test mode (RecordingContext), on_new_task simply records the call.
    """
    if not task:
        return
    if get_task_epic(task) is None:
        ctx.on_new_task(task)
