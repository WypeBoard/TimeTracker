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

from datetime import datetime, date, timedelta
from typing import TYPE_CHECKING

from Storage import (
    open_session, close_session, update_session_task,
    get_open_session, get_today_sessions, read_log,
)
from EpicStorage import (
    add_epic, list_epics, get_task_epic,
)
from Promark import promark_entry, compute_day_promark
from Printer import DayStatus, print_status
from logger import get_logger

if TYPE_CHECKING:
    # AppContext is imported only for type checking; at runtime the parameter
    # is duck-typed — any object with the required methods will work.
    from app_context import AppContext

_log = get_logger(__name__)


def cmd_start(ctx: AppContext, time_override: str | None = None, epic: str | None = None) -> None:
    """Open a new work session."""
    _log.info("cmd_start: time_override=%r epic=%r", time_override, epic)
    open_sess = get_open_session()
    if open_sess:
        _id, _date, start, _task = open_sess
        _log.warning("cmd_start: session already running since %s", start)
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


def cmd_lunch(ctx: AppContext, time_override: str | None = None) -> None:
    """Open a new Lunch session.

    Creates a session with task = 'Lunch'. If a session is currently open,
    it is closed at time_str first — the same auto-close behaviour as
    'resume'. This mirrors the natural workflow: 'lunch 1200' closes
    whatever is running at 12:00 and immediately starts the lunch break.

    Intentionally does NOT call _notify_if_new_task — Lunch is never
    linked to an Epic.
    """
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = time_override or now.strftime("%H:%M")
    note = " (manually set)" if time_override else ""

    open_sess = get_open_session()
    if open_sess:
        # Auto-close the running session before starting Lunch, just like
        # 'resume' does. The user should not need a separate 'pause' call.
        open_id, _date, open_start, _ = open_sess
        today_sessions = get_today_sessions()
        today_ids = [s[0] for s in today_sessions]
        session_num = today_ids.index(open_id) + 1 if open_id in today_ids else "?"
        close_session(open_id, time_str)
        ctx.info(f"⏸  Closed #{session_num} — {open_start} → {time_str}{note}")

    open_session(date_str, time_str, "Lunch")
    ctx.info(f"▶  Started Lunch at {time_str}{note}")
    ctx.on_session_changed()


def cmd_config(ctx: AppContext) -> None:
    """Open the configuration screen."""
    ctx.show_config()


def cmd_pause(ctx: AppContext, time_override: str | None = None) -> None:
    """Close the current session without printing a day summary."""
    _log.info("cmd_pause: time_override=%r", time_override)
    closed = _close_session(ctx, time_override)
    if closed:
        ctx.on_session_changed()


def cmd_stop(ctx: AppContext, time_override: str | None = None) -> None:
    """Close the current session and trigger the end-of-day summary."""
    _log.info("cmd_stop: time_override=%r", time_override)
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

    The task-carry lookup skips any session whose task is a non-work marker:
    Lunch, anything in excluded_tasks, and anything in always_separate_tasks.
    This means that after lunch, a sick morning, or a bank-meeting session,
    resume restores the last real work task rather than carrying the break
    task forward.
    """
    _log.info("cmd_resume: time_override=%r", time_override)
    from SettingsStorage import SettingsRepository

    today_sessions = get_today_sessions()  # [(id, start, end, task)]

    if not today_sessions:
        _log.warning("cmd_resume: no sessions today")
        ctx.error("⚠  No sessions today. Run 'start' first.")
        return

    # Build the set of task names that should be skipped during the carry-
    # forward lookup. These are all "non-work" markers:
    #   - "Lunch" is always skipped (handled by its own dedicated command).
    #   - excluded_tasks: tasks that don't count toward the daily target
    #     (e.g. "commute", "coffee walk").
    #   - always_separate_tasks: tasks that appear as standalone Promark rows
    #     (e.g. "Sick", "Doctor", "Bank meeting").
    settings = SettingsRepository()
    skip_tasks = (
        {"Lunch"}
        | set(settings.get_excluded_tasks())
        | set(settings.get_always_separate_tasks())
    )

    # Find the last session whose task is not in skip_tasks. Fall back to
    # today_sessions[-1] if every session today is a non-work marker.
    work_sessions = [s for s in today_sessions if s[3] not in skip_tasks]
    source = work_sessions[-1] if work_sessions else today_sessions[-1]
    last_id, last_start, last_end, last_task = source

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
    by CommandInput, which refreshes the cockpit panels directly instead.
    """
    now = datetime.now()
    print_status(_build_day_status(now), now)


def cmd_task(ctx: AppContext, epic: str, session_num: int | None = None) -> None:
    """Tag a session with a Task/Epic ID."""
    _log.info("cmd_task: epic=%r session_num=%r", epic, session_num)
    today_sessions = get_today_sessions()  # [(id, start, end, task)]
    if not today_sessions:
        _log.warning("cmd_task: no sessions found for today")
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
    """Print a full week's Promark entries, applying configured settings.

    Reads always_separate_tasks, lunch_excluded, and lunch_promark_offset_minutes
    from SettingsRepository and passes them as plain arguments to Promark.py.
    Builds a list of processed day entries (one per weekday, Mon–Fri) and
    passes the result to ctx.show_promark().
    """
    from SettingsStorage import SettingsRepository

    days = read_log()

    today_iso = date.today().isocalendar()
    target_week = today_iso.week if week_str is None else int(week_str[1:])
    target_year = today_iso.year

    # Read settings once for the whole week.
    settings = SettingsRepository()
    always_separate = settings.get_always_separate_tasks()
    lunch_excluded = settings.get_lunch_excluded()
    lunch_offset = settings.get_lunch_promark_offset_minutes()

    # Resolve Monday of the target ISO week.
    jan4 = date(target_year, 1, 4)
    week1_monday = jan4 - timedelta(days=jan4.weekday())
    monday = week1_monday + timedelta(weeks=target_week - 1)

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    promark_entries = []

    for i in range(5):
        d = monday + timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")

        if date_str in days:
            all_sessions = days[date_str]["sessions"]  # (start, end, task)
            consolidated, separate = compute_day_promark(
                all_sessions, always_separate, lunch_excluded, lunch_offset
            )
        else:
            consolidated, separate = None, []

        promark_entries.append({
            "date_str": date_str,
            "day_name": day_names[i],
            "consolidated": consolidated,
            "separate": separate,
        })

    ctx.show_promark(promark_entries, target_week, target_year)


def cmd_epic_add(ctx: AppContext, name: str) -> None:
    """Create a new Epic with the given free-text name."""
    _log.info("cmd_epic_add: name=%r", name)
    result = add_epic(name)
    if result is None:
        ctx.warning("⚠  An Epic with that name already exists.")
    else:
        ctx.info(f"✅  Epic '{name}' created.")


def cmd_epic_list(ctx: AppContext) -> None:
    """List all defined Epics, sorted alphabetically by name."""
    _log.debug("cmd_epic_list")
    epics = list_epics()
    if not epics:
        ctx.info("No Epics defined yet. Use 'epic add <name>' to create one.")
        return
    lines = [f"  {epic_id}  {name}" for epic_id, name in epics]
    ctx.info("\n".join(lines))


def cmd_epic_summary(ctx: AppContext, week_str: str | None = None) -> None:
    """Open the Epic summary overlay for the target week."""
    _log.info("cmd_epic_summary: week_str=%r", week_str)
    today_iso = date.today().isocalendar()
    target_week = today_iso.week if week_str is None else int(week_str[1:])
    target_year = today_iso.year
    ctx.show_epic_summary(target_week, target_year)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_day_status(now: datetime | None = None) -> DayStatus:
    """Gather today's log data into a DayStatus for the printers.

    Reads settings (daily target, lunch exclusion, excluded tasks, lunch
    Promark offset) at call time. No settings state is cached.
    """
    from SettingsStorage import SettingsRepository

    now = now or datetime.now()
    today_str = date.today().strftime("%Y-%m-%d")

    settings = SettingsRepository()
    target_hours = settings.get_daily_work_target()
    lunch_excluded = settings.get_lunch_excluded()
    excluded_tasks = settings.get_excluded_tasks()
    lunch_offset = settings.get_lunch_promark_offset_minutes()

    today_sessions = get_today_sessions()

    # ALL completed sessions — used for display (sessions table in TUI/CLI).
    # Per spec: "Time logged against excluded tasks is still visible in all panels."
    completed = [
        (start, end, task)
        for _id, start, end, task in today_sessions
        if end is not None
    ]

    # Filtered sessions — used for hours totals and Promark range only.
    filtered = _filter_for_hours(completed, lunch_excluded, excluded_tasks)
    total_hours = sum(_session_hours(s, e) for s, e, _ in filtered)

    # actual_lunch_minutes: sum of Lunch session durations from ALL completed
    # sessions, regardless of lunch_excluded (per spec: the offset calculation
    # is independent of the exclusion toggle).
    actual_lunch_minutes = sum(
        round(_session_hours(s, e) * 60)
        for s, e, t in completed
        if t == "Lunch"
    )

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

    # Promark range computed from filtered sessions + lunch offset.
    pm_start, pm_end = promark_entry(
        filtered, total_hours, lunch_offset, actual_lunch_minutes
    ) if filtered else (None, None)

    return DayStatus(
        today_str=today_str,
        sessions=completed,       # all sessions for display
        total_hours=total_hours,  # filtered total for hours calculations
        target_hours=target_hours,
        active_start=active_start,
        active_hours=active_hours,
        active_task=active_task,
        promark_start=pm_start,
        promark_end=pm_end,
    )


def _filter_for_hours(
    sessions: list[tuple],
    lunch_excluded: bool,
    excluded_tasks: list[str],
) -> list[tuple]:
    """Return sessions filtered for hours calculation.

    Removes Lunch sessions when lunch_excluded is True, and any sessions
    whose task appears in excluded_tasks.

    The returned list is used only for totals and Promark range calculations.
    The full unfiltered list is still shown in all display panels.
    """
    result = []
    for s, e, t in sessions:
        if lunch_excluded and t == "Lunch":
            continue
        if t in excluded_tasks:
            continue
        result.append((s, e, t))
    return result


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
