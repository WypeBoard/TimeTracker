"""QuickStatsPanel — narrow sidebar of five at-a-glance metrics.

Displayed values (feature `ui-layout-redesign.md` §6):

- **Today** — logged hours / daily target (decimal, e.g. ``5.8h/7.4h``).
- **Rem.** — remaining hours today / remaining hours for the current ISO
  week (e.g. ``1.6h/2.8h``). The weekly remainder is the weekly target
  minus the week total so far — see the **Week** entry below for how the
  weekly target is derived.
- **Leave** — projected leave time (same calc as the CLI status panel).
- **Week** — total logged hours / weekly target for the current ISO week
  (Mon–Sun). The weekly target is ``daily_target × number_of_days_with_registration``
  — e.g. by Wednesday of a week with three registered days the target is
  ``3 × 7.4h = 22.2h``.
- **Sessions** — number of sessions recorded today.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from rich.console import Group
from rich.text import Text
from textual.widgets import Static


class QuickStatsPanel(Static):
    """Top-right cockpit panel — five compact stats."""

    DEFAULT_CSS = """
    QuickStatsPanel {
        border: solid $accent;
        padding: 0 1;
        width: 32;
        margin-left: 1;
    }
    """

    def on_mount(self) -> None:
        self.border_title = "Quick Stats"
        self.refresh_data()
        # 60 s cadence matches the other data panels; sub-minute precision
        # is not meaningful for aggregate totals.
        self.set_interval(60, self.refresh_data)

    def refresh_data(self) -> None:
        from Commands import _build_day_status

        now = datetime.now()
        status = _build_day_status(now)
        week_total, week_days = _compute_week_total(status)
        week_target = status.target_hours * week_days
        week_remaining = max(0.0, week_target - week_total)

        rows = [
            _row("Today", f"{status.total_so_far:.1f}h/{status.target_hours:.1f}h"),
            _row("Rem.", _remaining_str(status.remaining, week_remaining)),
            _row("Leave", _leave_str(status, now)),
            _row("Week", f"{week_total:.1f}h/{week_target:.1f}h"),
            _row("Sessions", str(len(status.sessions) + (1 if status.active_start else 0))),
        ]
        self.update(Group(*rows))


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _row(label: str, value: str) -> Text:
    return Text.from_markup(f"[dim]{label:<9}[/dim] [bold]{value}[/bold]")


def _remaining_str(remaining: float, week_remaining: float) -> str:
    """Format the daily / weekly remainder pair, clamping negatives to zero."""
    day = max(0.0, remaining)
    week = max(0.0, week_remaining)
    return f"{day:.1f}h/{week:.1f}h"


def _leave_str(status, now: datetime) -> str:
    """Same leave-time algorithm as ``Printer.build_status_group``.

    Only meaningful when a session is currently active — otherwise the
    projection would extrapolate the clock forward from a past moment.
    """
    if not status.active_start or status.remaining <= 0:
        return "—"
    leave_min = now.hour * 60 + now.minute + int(status.remaining * 60)
    h, m = divmod(leave_min, 60)
    return f"~{h:02d}:{m:02d}"


def _compute_week_total(day_status) -> tuple[float, int]:
    """Sum all logged hours for the current ISO week (Mon–Sun).

    Returns ``(total_hours, day_count)`` where ``day_count`` is the number of
    calendar days in the week that have at least one recorded session
    (including today if a session is running or has been closed). The count
    drives the weekly target displayed alongside the total — so on a
    Wednesday with three days of registrations the target is
    ``3 × daily_target``.

    Today's contribution uses the live ``day_status`` (so an active session
    is included); past days are filtered through the same lunch/excluded-task
    rules that ``_build_day_status`` applies.
    """
    from Storage import read_log
    from Promark import session_hours
    from SettingsStorage import SettingsRepository

    settings = SettingsRepository()
    lunch_excluded = settings.get_lunch_excluded()
    excluded_tasks = settings.get_excluded_tasks()

    days = read_log()
    today = date.today()
    iso = today.isocalendar()
    jan4 = date(iso.year, 1, 4)
    week1_monday = jan4 - timedelta(days=jan4.weekday())
    monday = week1_monday + timedelta(weeks=iso.week - 1)
    today_str = today.strftime("%Y-%m-%d")

    total = 0.0
    day_count = 0
    # Sunday inclusive: some users record weekend sessions.
    for i in range(7):
        d = monday + timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        if d_str == today_str:
            total += day_status.total_so_far
            if day_status.sessions or day_status.active_start:
                day_count += 1
        elif d_str in days:
            raw = days[d_str]["sessions"]
            filtered = [
                (s, e, t) for s, e, t in raw
                if not (lunch_excluded and t == "Lunch")
                and t not in excluded_tasks
            ]
            if filtered:
                total += sum(session_hours(s, e) for s, e, _ in filtered)
                day_count += 1
    return total, day_count
