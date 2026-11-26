"""Promark calculation helpers.

Computes synthetic time ranges and partitions sessions for Promark export.

All settings are passed as plain parameters — this module does not import
from SettingsStorage.py. Reading settings and deciding which values to pass
here is the responsibility of Commands.py.

How Promark works:
  Promark does not record actual session timestamps. It computes a single
  synthetic time range per day:
    start = first session start of the day
    end   = start + stacked_hours + lunch_addition

  Sessions are treated as if back-to-back regardless of gaps. When lunch is
  excluded from working hours, lunch_addition is a flat
  lunch_duration_minutes — the day is always registered as containing exactly
  the configured lunch break, no matter how long the actual Lunch session was
  (or whether one was logged at all). See
  features/completed/lunch-configuration.md.
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
    lunch_addition_minutes: int = 0,
) -> tuple[str | None, str | None]:
    """Return (first_start, promark_end) as HH:MM strings.

    Promark end = first_start + total_hours + lunch_addition_minutes.

    The addition is applied verbatim — the caller decides whether a lunch
    break should be baked into the day span. This models the registration
    requirement that a day always contains the contractual lunch break of a
    fixed length, independent of the actual break taken.

    Returns (None, None) if sessions is empty.

    Args:
        sessions: Filtered sessions (start, end, task) used for start time.
                  The first session's start is the Promark start.
        total_hours: Pre-computed sum of hours from the filtered sessions.
        lunch_addition_minutes: Minutes added to the synthetic end time.
                                0 disables the addition.
    """
    if not sessions:
        return None, None

    first_start = _parse_hhmm(sessions[0][0])   # sessions are (start, end, task)
    total_minutes = round(total_hours * 60)
    promark_end = first_start + timedelta(minutes=total_minutes + lunch_addition_minutes)
    return _fmt_hhmm(first_start), _fmt_hhmm(promark_end)


def compute_day_promark(
    all_day_sessions: list,
    always_separate_tasks: list[str],
    lunch_excluded: bool,
    lunch_duration_minutes: int,
) -> tuple[dict | None, list[dict]]:
    """Partition a day's sessions into consolidated and always-separate Promark rows.

    Returns:
        (consolidated, separate_rows)

        consolidated: {"start": str, "end": str, "hours": float} or None.
            None when no normal sessions remain after filtering.
        separate_rows: [{"task": str, "hours": float}, ...], one entry per
            distinct always-separate task name in order of first appearance.

    Processing order:
      1. Partition sessions into always-separate and normal pools.
      2. If lunch_excluded: remove Lunch sessions from the normal pool, and
         add a flat lunch_duration_minutes to the consolidated day span.
         If lunch is included in working hours, Lunch sessions are counted
         like any other session and no addition is made.
      3. Run the consolidated entry on the remaining normal sessions.
      4. For each distinct always-separate task: emit one standalone row.
      5. If no normal sessions remain, consolidated is None.

    Args:
        all_day_sessions: All closed sessions for the day as (start, end, task).
        always_separate_tasks: Task names that produce standalone Promark rows.
        lunch_excluded: If True, remove Lunch sessions from the normal pool
                        and bake the configured lunch break into the span.
        lunch_duration_minutes: Contractual lunch length, added flat when
                                lunch_excluded is True.
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

    # ── Step 2: lunch handling ─────────────────────────────────────────
    # The addition is flat and unconditional: a 20-minute lunch is still
    # registered as the configured duration, and a day with no logged Lunch
    # session still reserves it. Per features/completed/lunch-configuration.md.
    if lunch_excluded:
        normal_sessions = [(s, e, t) for s, e, t in normal_sessions if t != "Lunch"]
        lunch_addition = lunch_duration_minutes
    else:
        lunch_addition = 0

    # ── Step 3: compute consolidated entry from remaining normal sessions
    if normal_sessions:
        normal_hours = sum(_session_minutes(s, e) / 60.0 for s, e, _ in normal_sessions)
        pm_start, pm_end = promark_entry(
            normal_sessions,
            normal_hours,
            lunch_addition,
        )
        consolidated: dict | None = {"start": pm_start, "end": pm_end, "hours": normal_hours}
    else:
        consolidated = None

    # ── Step 4: build separate rows list ────────────────────────────────
    separate_rows = [
        {"task": t, "hours": separate_by_task[t]}
        for t in separate_order
    ]

    return consolidated, separate_rows