"""Shared utility functions for TUI widgets."""


def format_hhmm(decimal_hours: float) -> str:
    """Convert decimal hours to H:MM clock string.

    Example: 7.4 → '7:24'.

    Converts a floating-point hour value to a base-60 clock format string,
    which is more natural for time registration than decimal hours and
    consistent with how promark entries are displayed.
    """
    total_minutes = round(decimal_hours * 60)
    h, m = divmod(total_minutes, 60)
    return f"{h}:{m:02d}"
