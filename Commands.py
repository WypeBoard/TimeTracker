from datetime import datetime, date

from Constants import TARGET_HOURS
from Storage import (
    open_session, close_session, update_session_task,
    get_open_session, get_today_sessions, read_log,
)
from Promark import promark_entry
from Printer import DayStatus, print_status, print_day_summary, print_promark_week, print_log_week


def cmd_start(time_override=None, epic=None):
    open_sess = get_open_session()
    if open_sess:
        _id, _date, start, _task = open_sess
        print(f"⚠  Session already running since {start}. Use 'pause' or 'stop' first.")
        return

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = time_override or now.strftime("%H:%M")

    open_session(date_str, time_str, epic or "")

    epic_suffix = f" — {epic}" if epic else ""
    note = " (manually set)" if time_override else ""
    print(f"▶  Started at {time_str}{epic_suffix}{note}")


def cmd_restart(time_override=None):
    """Close the current session and open a new one, carrying the epic forward."""
    open_sess = get_open_session()
    if not open_sess:
        print("No open session found. Run 'start' first.")
        return

    sess_id, _date, start_val, task_val = open_sess

    # Find the position of this session in today's list (for the printout)
    today_sessions = get_today_sessions()  # [(id, start, end, task)]
    today_ids = [s[0] for s in today_sessions]
    session_num = today_ids.index(sess_id) + 1 if sess_id in today_ids else "?"

    time_str = time_override or datetime.now().strftime("%H:%M")
    close_session(sess_id, time_str)
    print(f"⏸  Closed #{session_num} — {start_val} → {time_str}")

    # Open a new session carrying the task forward
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    open_session(date_str, time_str, task_val)

    new_num = session_num + 1 if isinstance(session_num, int) else "?"
    carry_note = f"  {task_val}  (carried forward)" if task_val else ""
    print(f"▶  Started #{new_num} — {time_str}{carry_note}")


def cmd_pause(time_override=None):
    _close_session(time_override)


def cmd_stop(time_override=None):
    closed = _close_session(time_override)
    if not closed:
        return
    print_day_summary(_build_day_status())


def cmd_status():
    now = datetime.now()
    print_status(_build_day_status(now), now)


def cmd_task(epic, session_num=None):
    """Tag a session with a Task/Epic ID."""
    today_sessions = get_today_sessions()  # [(id, start, end, task)]
    if not today_sessions:
        print("No sessions found for today.")
        return

    if session_num is not None:
        idx = session_num - 1
        if idx < 0 or idx >= len(today_sessions):
            print(f"⚠  Session #{session_num} not found. Today has {len(today_sessions)} session(s).")
            return
        target = today_sessions[idx]
    else:
        # Default: open session if it belongs to today, otherwise last session
        open_sess = get_open_session()
        if open_sess:
            open_id = open_sess[0]
            today_ids = [s[0] for s in today_sessions]
            target = today_sessions[today_ids.index(open_id)] if open_id in today_ids else today_sessions[-1]
        else:
            target = today_sessions[-1]

    target_id = target[0]
    target_idx = today_sessions.index(target) + 1
    update_session_task(target_id, epic)
    print(f"📌  #{target_idx}  {epic}  saved.")


def cmd_log(week_str=None):
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

    print_log_week(week_days, target_week, target_year)


def cmd_promark(week_str=None):
    """Print a full week's Promark entries to the terminal."""
    days = read_log()

    today_iso = date.today().isocalendar()
    target_week = today_iso.week if week_str is None else int(week_str[1:])
    target_year = today_iso.year

    week_days = {
        d: info for d, info in days.items()
        if date.fromisoformat(d).isocalendar().week == target_week
        and date.fromisoformat(d).isocalendar().year == target_year
    }

    print_promark_week(week_days, target_week, target_year)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_day_status(now: datetime | None = None) -> DayStatus:
    """Gather today's log data into a DayStatus for the printers."""
    now = now or datetime.now()
    today_str = date.today().strftime("%Y-%m-%d")

    # All of today's sessions: [(id, start, end, task)]
    today_sessions = get_today_sessions()

    # Separate completed sessions (end is not None) from the open one
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


def _close_session(time_override=None) -> bool:
    """Close the open session. Returns True on success, False if none is open."""
    open_sess = get_open_session()
    if not open_sess:
        print("No open session found. Run 'start' first.")
        return False

    sess_id, date_val, start_val, _task = open_sess
    time_str = time_override or datetime.now().strftime("%H:%M")
    close_session(sess_id, time_str)

    note = " (manually set)" if time_override else ""
    print(f"⏸  Closed — {date_val}  {start_val} → {time_str}{note}")
    return True