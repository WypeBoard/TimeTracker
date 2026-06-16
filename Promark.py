from datetime import datetime, timedelta

LUNCH_START = "11:45"
LUNCH_END = "12:15"
LUNCH_MINUTES = 30


def _parse_hhmm(s: str) -> datetime:
    return datetime.strptime(s, "%H:%M")


def _fmt_hhmm(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def promark_entry(sessions: list, total_hours: float) -> tuple[str | None, str | None]:
    """Return (first_start, promark_end) as HH:MM strings.

    Promark end = first_start + total_hours + 30 min lunch.
    Returns (None, None) if sessions is empty.
    """
    if not sessions:
        return None, None

    first_start = _parse_hhmm(sessions[0][0])  # sessions are (start, end, task)
    total_minutes = round(total_hours * 60)
    promark_end = first_start + timedelta(minutes=total_minutes + LUNCH_MINUTES)
    return _fmt_hhmm(first_start), _fmt_hhmm(promark_end)