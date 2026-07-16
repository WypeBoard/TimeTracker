"""Promark calculation helpers.

Computes synthetic time ranges and partitions sessions for Promark export.

All settings are passed as plain parameters — this module does not import
from SettingsStorage.py. Reading settings and deciding which values to pass
here is the responsibility of Commands.py.

How Promark works:
  Promark does not record actual session timestamps. It computes a single
  synthetic time range per day:
    start = first session start of the day
    end   = start + stacked_hours + lunch_offset_addition

  Sessions are treated as if back-to-back regardless of gaps. The lunch
  offset addition is max(0, expected_lunch_minutes - actual_lunch_minutes).
"""
from datetime import datetime, timedelta


def _parse_hhmm(s: str) -> datetime:
    return datetime.strptime(s, "%H:%M")


def _fmt_hhmm(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def session_hours(start: str, end: str) -> float:
    """Return decimal hours between two HH:MM strings. Returns 0.0 on error."""
    try:
        s = _parse_hhmm(start)
        e = _parse_hhmm(end)
        return (e.hour * 60 + e.minute - s.hour * 60 - s.minute) / 60
    except ValueError:
        return 0.0


def _session_minutes(start: str, end: str) -> int:
    """Return integer minutes between two HH:MM strings. Returns 0 on error."""
    try:
        s = _parse_hhmm(start)
        e = _parse_hhmm(end)
        return e.hour * 60 + e.minute - s.hour * 60 - s.minute
    except ValueError:
        return 0


def promark_entry(
    sessions: list,
    total_hours: float,
    lunch_promark_offset_minutes: int = 0,
    actual_lunch_minutes: int = 0,
) -> tuple[str | None, str | None]:
    """Return (first_start, promark_end) as HH:MM strings.

    Promark end = first_start + total_hours + lunch_offset_addition,
    where lunch_offset_addition = max(0, lunch_promark_offset_minutes
                                       - actual_lunch_minutes).

    This models the expectation that a lunch break of a fixed duration is
    invisible in Promark: if the user took less lunch than the configured
    offset, the shortfall is added to the synthetic end time.

    Returns (None, None) if sessions is empty.

    Args:
        sessions: Filtered sessions (start, end, task) used for start time.
                  The first session's start is the Promark start.
        total_hours: Pre-computed sum of hours from the filtered sessions.
        lunch_promark_offset_minutes: Expected lunch duration (from settings).
                                      Default 0 disables the offset.
        actual_lunch_minutes: Actual Lunch session duration on this day,
                              computed from ALL sessions regardless of the
                              lunch_excluded setting. Default 0.
    """
    if not sessions:
        return None, None

    promark_addition = max(0, lunch_promark_offset_minutes - actual_lunch_minutes)

    first_start = _parse_hhmm(sessions[0][0])   # sessions are (start, end, task)
    total_minutes = round(total_hours * 60)
    promark_end = first_start + timedelta(minutes=total_minutes + promark_addition)
    return _fmt_hhmm(first_start), _fmt_hhmm(promark_end)


def compute_day_promark(
    all_day_sessions: list,
    always_separate_tasks: list[str],
    lunch_excluded: bool,
    lunch_promark_offset_minutes: int,
) -> tuple[dict | None, list[dict]]:
    """Partition a day's sessions into consolidated and always-separate Promark rows.

    Returns:
        (consolidated, separate_rows)

        consolidated: {"start": str, "end": str, "hours": float} or None.
            None when no normal sessions remain after filtering.
        separate_rows: [{"task": str, "hours": float}, ...], one entry per
            distinct always-separate task name in order of first appearance.

    Processing order (per feature spec):
      1. Partition sessions into always-separate and normal pools.
      2. Compute actual_lunch_minutes from the normal pool (before filtering
         Lunch), regardless of the lunch_excluded setting.
      3. If lunch_excluded: remove Lunch sessions from the normal pool.
      4. Run the consolidated entry on remaining normal sessions.
         Apply promark_addition = max(0, offset - actual_lunch_minutes).
      5. For each distinct always-separate task: emit one standalone row.
      6. If no normal sessions remain, consolidated is None.

    Args:
        all_day_sessions: All closed sessions for the day as (start, end, task).
        always_separate_tasks: Task names that produce standalone Promark rows.
        lunch_excluded: If True, remove Lunch sessions from the normal pool.
        lunch_promark_offset_minutes: Expected lunch duration for offset calc.
    """
    # ── Step 1: partition into always-separate and normal ──────────────
    normal_sessions: list[tuple] = []
    separate_by_task: dict[str, float] = {}   # task_name → total hours
    separate_order: list[str] = []             # insertion-ordered unique names

    for start, end, task in all_day_sessions:
        if task in always_separate_tasks:
            hours = _session_minutes(start, end) / 60.0
            if task not in separate_by_task:
                separate_by_task[task] = 0.0
                separate_order.append(task)
            separate_by_task[task] += hours
        else:
            normal_sessions.append((start, end, task))

    # ── Step 2: compute actual_lunch_minutes from normal pool ───────────
    # "regardless of the lunch_excluded setting" — per feature spec.
    actual_lunch_minutes = sum(
        _session_minutes(s, e)
        for s, e, t in normal_sessions
        if t == "Lunch"
    )

    # ── Step 3: optionally remove Lunch from the normal pool ───────────
    if lunch_excluded:
        normal_sessions = [(s, e, t) for s, e, t in normal_sessions if t != "Lunch"]

    # ── Step 4: compute consolidated entry from remaining normal sessions
    if normal_sessions:
        normal_hours = sum(_session_minutes(s, e) / 60.0 for s, e, _ in normal_sessions)
        pm_start, pm_end = promark_entry(
            normal_sessions,
            normal_hours,
            lunch_promark_offset_minutes,
            actual_lunch_minutes,
        )
        consolidated: dict | None = {"start": pm_start, "end": pm_end, "hours": normal_hours}
    else:
        consolidated = None

    # ── Step 5: build separate rows list ────────────────────────────────
    separate_rows = [
        {"task": t, "hours": separate_by_task[t]}
        for t in separate_order
    ]

    return consolidated, separate_rows