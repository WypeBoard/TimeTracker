"""Today-page view model, Quick Stats calculation, and mutating actions.

This module is the independent web-service-function layer for the Today
page (features/standalone-web-app.md, Implementation Plan Phase 3). It does
not import app.Commands/app.Storage/app.QuickStatsPanel/app.Printer — those
TUI modules are used only as the *reference spec* for the calculations
reproduced below (see Manual Changes, 2026-11-24, "Today page: Quick Stats
row added").
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from webapp.services import epics_service, sessions_service, settings_service

_RESERVED_LUNCH_TASK = "Lunch"


# ---------------------------------------------------------------------------
# View model
# ---------------------------------------------------------------------------

@dataclass
class QuickStats:
    today_logged: float
    today_target: float
    today_remaining: float
    week_remaining: float
    leave: str | None
    leave_with_lunch: str | None
    week_logged: float
    week_target: float
    sessions_count: int


@dataclass
class SessionRow:
    id: int
    start: str
    end: str | None
    task: str
    epic_name: str | None
    hours: float
    is_open: bool


@dataclass
class TodayViewModel:
    sessions: list[SessionRow]
    quick_stats: QuickStats
    known_tasks: list[str]
    today_tasks: list[str]
    resume_default_task: str | None
    epics: list[tuple]
    task_epic_id: dict = field(default_factory=dict)
    default_start_time: str = "00:00"
    error: str | None = None


def build_today_view_model(error: str | None = None) -> TodayViewModel:
    """Gather everything today.html needs from one consistent read.

    Per Manual Changes (2026-11-24, "Page load strategy"), this is a single
    synchronous pass — no per-section async fan-out.
    """
    now = datetime.now()
    today_sessions = sessions_service.get_today_sessions()  # [(id, start, end, task)]

    quick_stats = _compute_quick_stats(now, today_sessions)
    session_rows = _build_session_rows(today_sessions, now)

    known_tasks = epics_service.list_known_tasks()
    epics = epics_service.list_epics()
    # Maps each known task to its linked Epic's id, or None when unlinked —
    # lets the New Session modal both disable and pre-select the Epic field
    # for a task that already has one (see Manual Changes, 2026-11-26,
    # "New Session modal: show the linked Epic in the disabled select").
    task_epic_id: dict[str, int | None] = {}
    for t in known_tasks:
        epic_row = epics_service.get_task_epic(t)
        task_epic_id[t] = epic_row[0] if epic_row else None

    today_tasks: list[str] = []
    for _id, _start, _end, task in today_sessions:
        if task and task not in today_tasks:
            today_tasks.append(task)

    skip_tasks = _skip_tasks()
    resume_default_task = _resolve_carry_task(today_sessions, skip_tasks)

    return TodayViewModel(
        sessions=session_rows,
        quick_stats=quick_stats,
        known_tasks=known_tasks,
        today_tasks=today_tasks,
        resume_default_task=resume_default_task,
        epics=epics,
        task_epic_id=task_epic_id,
        default_start_time=_rounded_now_hhmm(now),
        error=error,
    )


# ---------------------------------------------------------------------------
# Mutating actions — return an error message string, or None on success.
# ---------------------------------------------------------------------------

def do_new_session(
    task: str,
    start_time: str,
    epic_id: str | None,
    new_epic_name: str | None,
) -> str | None:
    """Equivalent of cmd_start, plus the New Session modal's Epic step.

    Per the Today-page modal design, the Epic selection/creation step only
    matters when the task has no existing task_catalog entry yet. If the
    task is already linked, any submitted epic_id/new_epic_name is silently
    ignored rather than treated as an error — relinking an existing task is
    out of this phase's scope.

    If a session is already open, it is auto-closed at start_time first,
    the same auto-close-then-open behaviour as Resume/Lunch (see Manual
    Changes, "New Session: auto-close the running session instead of
    rejecting"). This matches the TUI's long-standing workflow pattern of
    never requiring a separate stop step before starting the next task.
    """
    task = (task or "").strip()
    if not task:
        return "Task is required."

    _close_open_session_if_any(start_time)

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    sessions_service.open_session(date_str, start_time, task)

    if epics_service.get_task_epic(task) is None:
        linked_epic_id = _resolve_epic_selection(epic_id, new_epic_name)
        if linked_epic_id is not None:
            epics_service.link_task_to_epic(task, linked_epic_id)

    return None


def do_resume(task: str, start_time: str) -> str | None:
    """Equivalent of cmd_resume, but with an explicit (visible) task choice
    instead of an implicit carry-forward lookup — see Manual Changes,
    2026-11-24, "Resume modal field design"."""
    today_sessions = sessions_service.get_today_sessions()
    if not today_sessions:
        return "No sessions today yet. Use New Session first."

    task = (task or "").strip()
    if not task:
        return "Task is required."

    _close_open_session_if_any(start_time)

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    sessions_service.open_session(date_str, start_time, task)
    return None


def do_resume_now() -> str | None:
    """The Resume split-button dropdown's "Now" bypass: carries the last
    work task forward automatically, same lookup as cmd_resume."""
    today_sessions = sessions_service.get_today_sessions()
    if not today_sessions:
        return "No sessions today yet. Use New Session first."
    task = _resolve_carry_task(today_sessions, _skip_tasks()) or ""
    time_str = datetime.now().strftime("%H:%M")
    return do_resume(task, time_str)


def do_lunch(start_time: str) -> str | None:
    """Equivalent of cmd_lunch."""
    _close_open_session_if_any(start_time)
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    sessions_service.open_session(date_str, start_time, _RESERVED_LUNCH_TASK)
    return None


def do_lunch_now() -> str | None:
    """The Lunch split-button dropdown's "Now" bypass."""
    return do_lunch(datetime.now().strftime("%H:%M"))


def do_stop(end_time: str) -> str | None:
    """Close the currently open session. Web equivalent of cmd_pause — there
    is no end-of-day summary dialog in the web UI to reproduce cmd_stop's
    extra step (see Manual Changes, 2026-11-26, "Stop button: closes the
    active session")."""
    open_sess = sessions_service.get_open_session()
    if not open_sess:
        return "No active session to stop."
    sessions_service.close_session(open_sess[0], end_time)
    return None


def do_stop_now() -> str | None:
    """The Stop split-button dropdown's "Now" bypass."""
    return do_stop(datetime.now().strftime("%H:%M"))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_epic_selection(epic_id: str | None, new_epic_name: str | None) -> int | None:
    if epic_id == "__new__":
        name = (new_epic_name or "").strip()
        if not name:
            return None
        created_id = epics_service.add_epic(name)
        if created_id is not None:
            return created_id
        # Name already exists — link to the existing Epic instead of failing.
        for existing_id, existing_name in epics_service.list_epics():
            if existing_name == name:
                return existing_id
        return None
    if epic_id:
        try:
            return int(epic_id)
        except ValueError:
            return None
    return None


def _close_open_session_if_any(time_str: str) -> None:
    open_sess = sessions_service.get_open_session()
    if open_sess:
        sessions_service.close_session(open_sess[0], time_str)


def _skip_tasks() -> set[str]:
    """Task names skipped by the resume carry-forward lookup.

    Mirrors app.Commands.cmd_resume's skip_tasks set — see
    features/standalone-web-app.md Requirements for why webapp/ cannot
    import that function directly.
    """
    return (
        {_RESERVED_LUNCH_TASK}
        | set(settings_service.get_excluded_tasks())
        | set(settings_service.get_always_separate_tasks())
    )


def _resolve_carry_task(today_sessions: list[tuple], skip_tasks: set[str]) -> str | None:
    if not today_sessions:
        return None
    work_sessions = [s for s in today_sessions if s[3] not in skip_tasks]
    source = work_sessions[-1] if work_sessions else today_sessions[-1]
    return source[3] or None


def _session_hours(start: str, end: str) -> float:
    try:
        s = datetime.strptime(start, "%H:%M")
        e = datetime.strptime(end, "%H:%M")
        return (e.hour * 60 + e.minute - (s.hour * 60 + s.minute)) / 60
    except ValueError:
        return 0.0


def _running_hours(start: str, now: datetime) -> float:
    try:
        s = datetime.strptime(start, "%H:%M")
        return (now.hour * 60 + now.minute - (s.hour * 60 + s.minute)) / 60
    except ValueError:
        return 0.0


def _build_session_rows(today_sessions: list[tuple], now: datetime) -> list[SessionRow]:
    rows = []
    for sid, start, end, task in today_sessions:
        epic_row = epics_service.get_task_epic(task) if task else None
        epic_name = epic_row[1] if epic_row else None
        is_open = end is None
        hours = _running_hours(start, now) if is_open else _session_hours(start, end)
        rows.append(SessionRow(
            id=sid, start=start, end=end, task=task or "",
            epic_name=epic_name, hours=hours, is_open=is_open,
        ))
    return rows


def _filter_for_hours(
    sessions: list[tuple], lunch_excluded: bool, excluded_tasks: list[str],
) -> list[tuple]:
    result = []
    for s, e, t in sessions:
        if lunch_excluded and t == _RESERVED_LUNCH_TASK:
            continue
        if t in excluded_tasks:
            continue
        result.append((s, e, t))
    return result


def _fmt_minutes(total_minutes: int) -> str:
    h, m = divmod(total_minutes, 60)
    return f"{h % 24:02d}:{m:02d}"


def _leave_projection(
    active_start: str | None,
    remaining_today: float,
    lunch_excluded: bool,
    lunch_logged: bool,
    lunch_duration: int,
    now: datetime,
) -> tuple[str | None, str | None]:
    if not active_start or remaining_today <= 0:
        return None, None
    leave_min = now.hour * 60 + now.minute + int(remaining_today * 60)
    leave = _fmt_minutes(leave_min)
    if lunch_excluded and not lunch_logged and lunch_duration:
        return leave, _fmt_minutes(leave_min + lunch_duration)
    return leave, None


def _week_monday(d: date) -> date:
    iso = d.isocalendar()
    jan4 = date(iso.year, 1, 4)
    week1_monday = jan4 - timedelta(days=jan4.weekday())
    return week1_monday + timedelta(weeks=iso.week - 1)


def _compute_quick_stats(now: datetime, today_sessions: list[tuple]) -> QuickStats:
    daily_target = settings_service.get_daily_work_target()
    lunch_excluded = settings_service.get_lunch_excluded()
    excluded_tasks = settings_service.get_excluded_tasks()
    lunch_duration = settings_service.get_lunch_duration_minutes()

    completed = [(s, e, t) for _id, s, e, t in today_sessions if e is not None]
    filtered = _filter_for_hours(completed, lunch_excluded, excluded_tasks)
    total_hours = sum(_session_hours(s, e) for s, e, _ in filtered)

    open_sess = sessions_service.get_open_session()
    active_start = None
    active_hours = 0.0
    if open_sess:
        _id, _date, active_start, _task = open_sess
        active_hours = _running_hours(active_start, now)

    total_so_far = total_hours + active_hours
    remaining_today = daily_target - total_so_far

    lunch_logged = any(task == _RESERVED_LUNCH_TASK for _id, _s, _e, task in today_sessions)

    leave, leave_with_lunch = _leave_projection(
        active_start, remaining_today, lunch_excluded, lunch_logged, lunch_duration, now,
    )

    week_total, week_days_count = _compute_week_total(
        now, total_so_far, today_sessions, lunch_excluded, excluded_tasks,
    )
    week_target = daily_target * week_days_count
    week_remaining = max(0.0, week_target - week_total)

    return QuickStats(
        today_logged=total_so_far,
        today_target=daily_target,
        today_remaining=max(0.0, remaining_today),
        week_remaining=week_remaining,
        leave=leave,
        leave_with_lunch=leave_with_lunch,
        week_logged=week_total,
        week_target=week_target,
        sessions_count=len(today_sessions),
    )


def _compute_week_total(
    now: datetime,
    today_total_so_far: float,
    today_sessions: list[tuple],
    lunch_excluded: bool,
    excluded_tasks: list[str],
) -> tuple[float, int]:
    """Sum logged hours for the current ISO week (Mon-Sun), with the number
    of days that have at least one qualifying registration — see
    app.QuickStatsPanel._compute_week_total (used here as the reference
    spec only, not imported)."""
    today = now.date()
    monday = _week_monday(today)
    sunday = monday + timedelta(days=6)
    today_str = today.strftime("%Y-%m-%d")

    rows = sessions_service.get_closed_sessions_in_range(
        monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d"),
    )

    total = 0.0
    days_seen: set[str] = set()
    for d_str, start, end, task in rows:
        if d_str == today_str:
            continue  # today is accounted for separately below
        if lunch_excluded and task == _RESERVED_LUNCH_TASK:
            continue
        if task in excluded_tasks:
            continue
        total += _session_hours(start, end)
        days_seen.add(d_str)

    total += today_total_so_far
    if today_sessions:
        days_seen.add(today_str)

    return total, len(days_seen)


def _rounded_now_hhmm(now: datetime) -> str:
    """Round `now` to the nearest 5 minutes, per the Start Time input default."""
    total_minutes = now.hour * 60 + now.minute
    rounded = int(round(total_minutes / 5.0)) * 5
    h, m = divmod(rounded % (24 * 60), 60)
    return f"{h:02d}:{m:02d}"
