"""Weekly page view model: day -> Epic -> task hours, Promark-style day spans.

Phase 4 of the Implementation Plan in features/standalone-web-app.md. This is
an independent re-implementation of app.EpicStorage.get_epic_summary_data and
app.Promark.compute_day_promark's consolidated-span calculation against the
shared database. Per this feature's Non-Goals, webapp/ does not import
app.EpicStorage/app.Promark directly — those modules are used only as the
reference spec for the SQL/logic below (see Manual Changes, 2026-11-24,
"Weekly page: consolidates Weekly/Epic Summary/Promark into one page").
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

import db.repository as repo

from webapp.services import sessions_service, settings_service

_RESERVED_LUNCH_TASK = "Lunch"
_MISC_LABEL = "(Misc)"
_DAY_NAMES = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
]


# ---------------------------------------------------------------------------
# View model
# ---------------------------------------------------------------------------

@dataclass
class TaskRow:
    task: str
    minutes: int

    @property
    def display_task(self) -> str:
        return self.task if self.task else "(no task)"

    @property
    def hhmm(self) -> str:
        return _minutes_to_clock(self.minutes)

    @property
    def decimal(self) -> str:
        return _minutes_to_decimal(self.minutes)


@dataclass
class EpicGroup:
    name: str
    is_misc: bool
    minutes: int
    tasks: list[TaskRow] = field(default_factory=list)

    @property
    def hhmm(self) -> str:
        return _minutes_to_clock(self.minutes)

    @property
    def decimal(self) -> str:
        return _minutes_to_decimal(self.minutes)


@dataclass
class DayRow:
    date_str: str
    label: str
    minutes: int
    span: tuple[str, str] | None
    epics: list[EpicGroup] = field(default_factory=list)

    @property
    def hhmm(self) -> str:
        return _minutes_to_clock(self.minutes)

    @property
    def decimal(self) -> str:
        return _minutes_to_decimal(self.minutes)


@dataclass
class WeeklyViewModel:
    week_num: int
    year: int
    week_label: str
    date_range_label: str
    days: list[DayRow]
    week_total_minutes: int
    can_go_next: bool
    is_current_week: bool
    prev_week: tuple[int, int]
    next_week: tuple[int, int]

    @property
    def week_total_hhmm(self) -> str:
        return _minutes_to_clock(self.week_total_minutes)

    @property
    def week_total_decimal(self) -> str:
        return _minutes_to_decimal(self.week_total_minutes)


def build_weekly_view_model(week_num: int, year: int) -> WeeklyViewModel:
    """Gather everything weekly.html needs from one consistent read.

    Per Manual Changes (2026-11-24, "Page load strategy"), this is a single
    synchronous pass — no per-section async fan-out.
    """
    lunch_excluded = settings_service.get_lunch_excluded()
    excluded_tasks = settings_service.get_excluded_tasks()
    always_separate = settings_service.get_always_separate_tasks()
    lunch_duration = settings_service.get_lunch_duration_minutes()

    monday = _week_monday(week_num, year)
    sunday = monday + timedelta(days=6)

    summary_rows = _get_epic_summary_data(
        monday, sunday, lunch_excluded=lunch_excluded, excluded_tasks=excluded_tasks,
    )
    daily_promark = _compute_daily_promark(
        monday, sunday, always_separate, lunch_excluded, lunch_duration,
    )

    days, week_total = _build_days(summary_rows, daily_promark)

    today_iso = date.today().isocalendar()
    can_go_next = (year, week_num) < (today_iso.year, today_iso.week)
    is_current_week = (year, week_num) == (today_iso.year, today_iso.week)
    prev_week = _shift_week(week_num, year, -1)
    next_week = _shift_week(week_num, year, 1) if can_go_next else (week_num, year)

    return WeeklyViewModel(
        week_num=week_num,
        year=year,
        week_label=f"Week {week_num:02d}/{year}",
        date_range_label=f"{monday.strftime('%b %d')} \u2013 {sunday.strftime('%b %d')}",
        days=days,
        week_total_minutes=week_total,
        can_go_next=can_go_next,
        is_current_week=is_current_week,
        prev_week=prev_week,
        next_week=next_week,
    )


# ---------------------------------------------------------------------------
# Data assembly
# ---------------------------------------------------------------------------

def _build_days(
    summary_rows: list[tuple], daily_promark: dict[str, tuple[str, str]],
) -> tuple[list[DayRow], int]:
    """Group (date_str, epic_name, task_id, minutes) rows into day -> Epic ->
    task rows, same ordering rules as app.Printer.build_weekly_overview_panel:
    days in date order, named Epics alphabetically then (Misc) last within
    each day (already guaranteed by the SQL ORDER BY), tasks alphabetically.
    """
    day_order: list[str] = []
    day_epic_order: dict[str, list[str]] = {}
    epic_task_data: dict[tuple, list[tuple[str, int]]] = {}

    for date_str, epic_name, task_id, total_minutes in summary_rows:
        display_name = epic_name if epic_name is not None else _MISC_LABEL
        if date_str not in day_epic_order:
            day_order.append(date_str)
            day_epic_order[date_str] = []
        key = (date_str, display_name)
        if display_name not in day_epic_order[date_str]:
            day_epic_order[date_str].append(display_name)
            epic_task_data[key] = []
        epic_task_data[key].append((task_id, total_minutes))

    days: list[DayRow] = []
    week_total = 0
    for date_str in day_order:
        day_total = sum(
            mins
            for epic_key in day_epic_order[date_str]
            for _, mins in epic_task_data[(date_str, epic_key)]
        )
        week_total += day_total

        d = date.fromisoformat(date_str)
        label = f"{_DAY_NAMES[d.weekday()]} {d.strftime('%b %d')}"

        epics: list[EpicGroup] = []
        for epic_display in day_epic_order[date_str]:
            key = (date_str, epic_display)
            epic_total = sum(mins for _, mins in epic_task_data[key])
            tasks = [
                TaskRow(task=task_id, minutes=mins)
                for task_id, mins in sorted(epic_task_data[key])
            ]
            epics.append(EpicGroup(
                name=epic_display,
                is_misc=(epic_display == _MISC_LABEL),
                minutes=epic_total,
                tasks=tasks,
            ))

        days.append(DayRow(
            date_str=date_str,
            label=label,
            minutes=day_total,
            span=daily_promark.get(date_str),
            epics=epics,
        ))

    return days, week_total


# ---------------------------------------------------------------------------
# Independent queries (reference spec: app.EpicStorage.get_epic_summary_data)
# ---------------------------------------------------------------------------

def _get_epic_summary_data(
    monday: date, sunday: date, lunch_excluded: bool, excluded_tasks: list[str],
) -> list[tuple]:
    """Return [(date_str, epic_name_or_None, task_id, total_minutes)] for the
    Monday-Sunday range, grouped the same way as the TUI's weekly overview.
    """
    monday_str = monday.strftime("%Y-%m-%d")
    sunday_str = sunday.strftime("%Y-%m-%d")

    exclusions: list[str] = list(excluded_tasks)
    if lunch_excluded and _RESERVED_LUNCH_TASK not in exclusions:
        exclusions.append(_RESERVED_LUNCH_TASK)

    exclude_clause = ""
    params: list = [monday_str, sunday_str]
    if exclusions:
        placeholders = ", ".join("?" for _ in exclusions)
        exclude_clause = f" AND s.task NOT IN ({placeholders})"
        params.extend(exclusions)

    return repo.fetch_many(
        f"""
        SELECT
            s.date AS date_str,
            e.name AS epic_name,
            s.task AS task_id,
            SUM(
                (CAST(substr(s.end,   1, 2) AS INTEGER) * 60
                 + CAST(substr(s.end,   4, 2) AS INTEGER))
                - (CAST(substr(s.start, 1, 2) AS INTEGER) * 60
                 + CAST(substr(s.start, 4, 2) AS INTEGER))
            ) AS total_minutes
        FROM sessions s
        LEFT JOIN task_catalog tc ON tc.task_id = s.task
        LEFT JOIN epics e ON e.id = tc.epic_id
        WHERE s.end IS NOT NULL
          AND s.date >= ?
          AND s.date <= ?
          {exclude_clause}
        GROUP BY s.date, e.name, s.task
        ORDER BY
            s.date,
            CASE WHEN e.name IS NULL THEN 1 ELSE 0 END,
            e.name,
            s.task
        """,
        tuple(params),
    )


# ---------------------------------------------------------------------------
# Independent Promark-style day span (reference spec: app.Promark.compute_day_promark)
# ---------------------------------------------------------------------------

def _compute_daily_promark(
    monday: date, sunday: date, always_separate_tasks: list[str],
    lunch_excluded: bool, lunch_duration_minutes: int,
) -> dict[str, tuple[str, str]]:
    """Return {date_str: (start_hhmm, end_hhmm)} consolidated Promark-style
    spans for each day in range that has a normal (non-always-separate,
    non-excluded-lunch) session. Only the consolidated span is needed here —
    the day's always-separate tasks are already visible as their own Epic
    rows in the day -> Epic -> task table, unlike the TUI's Promark output.
    """
    rows = sessions_service.get_closed_sessions_in_range(
        monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d"),
    )
    by_day: dict[str, list[tuple[str, str, str]]] = {}
    for d_str, start, end, task in rows:
        by_day.setdefault(d_str, []).append((start, end, task or ""))

    result: dict[str, tuple[str, str]] = {}
    for d_str, day_sessions in by_day.items():
        span = _consolidated_span(
            day_sessions, always_separate_tasks, lunch_excluded, lunch_duration_minutes,
        )
        if span is not None:
            result[d_str] = span
    return result


def _consolidated_span(
    day_sessions: list[tuple[str, str, str]],
    always_separate_tasks: list[str],
    lunch_excluded: bool,
    lunch_duration_minutes: int,
) -> tuple[str, str] | None:
    normal_sessions = [
        (s, e, t) for s, e, t in day_sessions if t not in always_separate_tasks
    ]
    if lunch_excluded:
        normal_sessions = [
            (s, e, t) for s, e, t in normal_sessions if t != _RESERVED_LUNCH_TASK
        ]
        lunch_addition = lunch_duration_minutes
    else:
        lunch_addition = 0

    if not normal_sessions:
        return None

    total_minutes = sum(_session_minutes(s, e) for s, e, _ in normal_sessions)
    first_start = _parse_hhmm(normal_sessions[0][0])
    end_dt = first_start + timedelta(minutes=total_minutes + lunch_addition)
    return _fmt_hhmm(first_start), _fmt_hhmm(end_dt)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _week_monday(week_num: int, year: int) -> date:
    jan4 = date(year, 1, 4)
    week1_monday = jan4 - timedelta(days=jan4.weekday())
    return week1_monday + timedelta(weeks=week_num - 1)


def _max_week_of_year(year: int) -> int:
    """Return the number of ISO weeks in the given year (52 or 53)."""
    return date(year, 12, 28).isocalendar().week


def _shift_week(week_num: int, year: int, delta: int) -> tuple[int, int]:
    if delta < 0:
        if week_num > 1:
            return week_num - 1, year
        prev_year = year - 1
        return _max_week_of_year(prev_year), prev_year
    max_week = _max_week_of_year(year)
    if week_num < max_week:
        return week_num + 1, year
    return 1, year + 1


def _parse_hhmm(s: str) -> datetime:
    return datetime.strptime(s, "%H:%M")


def _fmt_hhmm(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def _session_minutes(start: str, end: str) -> int:
    try:
        s = _parse_hhmm(start)
        e = _parse_hhmm(end)
        return e.hour * 60 + e.minute - s.hour * 60 - s.minute
    except ValueError:
        return 0


def _minutes_to_clock(minutes: int) -> str:
    """Convert total minutes to H:MM clock format (e.g. 90 -> '1:30')."""
    h, m = divmod(max(minutes, 0), 60)
    return f"{h}:{m:02d}"


def _minutes_to_decimal(minutes: int) -> str:
    """Convert total minutes to decimal-hour format (e.g. 90 -> '1.50')."""
    return f"{max(minutes, 0) / 60:.2f}"
