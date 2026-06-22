# Feature: TUI Dashboard Enhancements

Status: Completed

## Purpose

The current TUI dashboard shows Today sessions and Week totals side by side. There is
untapped vertical and horizontal space, even after zooming in 2–3 times. Three areas
have been identified where the dashboard can surface more value without adding clutter:

1. **Combined progress bar widget** — a full-width strip that shows both Today's and
   the Week's progress bars simultaneously, currently only Today has one.
2. **WeekPanel redesigned as a promark view** — replace the current sparse `Day  Xh`
   table with the promark-style `Date  HH:MM → HH:MM  Xh` layout that also appears
   in the `promark` command output.
3. **Task Summary panel** — a new always-visible dashboard panel showing a pivot view
   of the current week: for each day, which task(s) were worked on and how many hours,
   so the user can see at a glance what was billed to what across the week.

---

## Requirements

### A — Combined Progress Bar (`ProgressStrip`)

- A new full-width widget positioned **below `TaskSummaryPanel` and above the `Output`
  panel** (between task summary and command feedback).
- Two **stacked** rows (not side-by-side):
  - Row 1: `Today   H:MM / H:MM  [bar]  ZZ%`
  - Row 2: `Week    H:MM / H:MM  [bar]  ZZ%`
- All times displayed in **base-60 clock format** (`H:MM`), not decimal hours.
  - Example: 7.4 decimal hours → `7:24`.
- **Week target is dynamic**: `TARGET_HOURS × (number of weekdays that have at least
  one session this week)`, not a fixed `× 5`.
  - On the first day with sessions: target = `TARGET_HOURS × 1` (e.g. `7:24`).
  - On the second day with sessions: target = `TARGET_HOURS × 2` (e.g. `14:48`).
  - This gives a meaningful progress signal each day rather than always showing a low
    percentage on Monday and an impossible-looking target before week's end.
- Both bars are green when their target is met; yellow otherwise.
- The widget refreshes whenever `TuiAppContext.on_session_changed()` fires and on the
  same 60-second timer as `TodayPanel`.
- Once this widget is in place, the progress bar currently rendered inside `TodayPanel`
  (via `build_status_group`) is removed from the TUI path. The CLI path (`print_status`)
  is unaffected — implement this via a `show_progress: bool = True` parameter on
  `build_status_group`.

### B — WeekPanel Redesigned as Promark View

- Replace the current sparse `Day  Xh` table with the promark-style layout.
- Each row: `Date  Day  HH:MM → HH:MM  Xh` (date, day name, promark start → promark end, total hours).
- Days with no sessions: `Date  Day  —`.
- Today's partial row uses live `promark_start` / `promark_end` from `DayStatus`
  (same data as `cmd_promark`); the hours cell shows the running total with a `▶` marker.
- The data is already available via `Promark.promark_entry()` — this is purely a
  display change to `WeekPanel.py`.
- The panel title remains `Week N`.

### C — Task Summary Panel (`TaskSummaryPanel`)

- A new always-visible dashboard panel spanning the full width, positioned **directly
  below the main panel row** (Today + Week) and above the `ProgressStrip`.
- Shows a **pivot view** of the current week: for each weekday, which task(s) were
  worked on and the total hours per task.
- Layout: `Day  Task  Hours` — one row per (day, task) combination.
  - If a day has multiple tasks, each gets its own row; the day name appears only on
    the first row (the day column is blank on continuation rows).
  - Days with no sessions show `Day  —`.
  - Today's active session is included live (task + running hours with `▶`).
- This is a summary view — tasks are **aggregated** within each day (e.g. three
  sessions on Epic-42 = one row: `Mon  Epic-42  X:XX`).
- Sessions with no task label are shown as `(no task)` so hours are never invisible.
- Hours in this panel also use **base-60 clock format** (`H:MM`) for consistency with
  the ProgressStrip and WeekPanel.
- The panel has a fixed height (scrollable if the week has many task/day combinations).
- Refreshes whenever `TuiAppContext.on_session_changed()` fires and on the 60-second timer.
- The `l` keyboard binding (and footer hint) opens the existing `LogScreen` overlay for
  full session-by-session detail when needed.

---

## Non-Goals

- Does not replace the existing `LogScreen` overlay — the overlay remains accessible
  via the `log` command and the new `l` binding for full session-by-session detail.
- Does not change the `log`, `promark`, `status`, or any other command behaviour.
- Does not add new commands.
- Does not change `Commands.py`, `Storage.py`, or `Promark.py` business logic.
- `build_status_group` in `Printer.py` is modified only by adding an optional
  `show_progress` parameter — no logic changes.

---

## Manual Changes

2026-06-22 (initial)
- Progress bar confirmed as **stacked rows** (not side-by-side). Initial design choice
  stands.
- WeekPanel redesigned to show promark-style `Date  Day  HH:MM → HH:MM  Xh` layout
  rather than a simple `Day  Xh` table. Previous B (embed times as extra columns)
  superseded by this fuller redesign.
- Log view changed from "keyboard shortcut only" to a new **always-visible
  `TaskSummaryPanel`** showing a Day × Task → Hours pivot. The `LogScreen` overlay is
  retained for full detail; `l` binding added to open it quickly.

2026-06-22 (approved)
- Zero-session week edge case resolved: Week row renders `0:00 / —` (dim, no bar, no
  percentage) until the first session of the week exists. Row remains visible to avoid
  layout shift.
- Status set to Approved. Implementation not yet started.
- `ProgressStrip` placement corrected: sits **between `TaskSummaryPanel` and the
  `Output` panel**. Final vertical order: Today+Week → TaskSummary → Progress → Output
  → Command input → Footer. Previous note placing it below the command input is
  superseded.
- Week target in `ProgressStrip` is now **dynamic**: `TARGET_HOURS × (days with
  sessions this week)`, not a fixed `× 5`. Rationale: a fixed target makes Monday's
  bar always show ~20%, which is misleading. A dynamic target based on worked days
  gives a meaningful daily signal.
- All time values in `ProgressStrip` and `TaskSummaryPanel` use **base-60 clock
  format** (`H:MM`) rather than decimal hours (`X.XXh`). Rationale: consistency with
  the promark view and how the user naturally thinks about time registration.

---

## Brainstorm Notes

### Final Layout Sketch

```
┌─ Header ──────────────────────────────────────────────────────────────────────┐
│  ┌─ Today: 2026-06-22 ─────────────────────┐  ┌─ Week 26 ──────────────────────┐ │
│  │  #  Start   End     Hours  Task         │  │  2026-06-16  Mon  07:30→17:00  7:30 │ │
│  │  1  07:30   11:20   3:50   Epic-42      │  │  2026-06-17  Tue  08:00→15:45  7:15 │ │
│  │  2  11:50   now ▶   2:10   Epic-42      │  │  2026-06-18  Wed  —                 │ │
│  │                                         │  │  2026-06-19  Thu  08:30→now ▶  4:00 │ │
│  │  ⏳ Remaining 1:30   🚪 Leave ~16:15    │  │  2026-06-20  Fri  —                 │ │
│  └─────────────────────────────────────────┘  └────────────────────────────────────┘ │
│  ┌─ Task Summary — Week 26 ──────────────────────────────────────────────────────────┐ │
│  │  Mon   Epic-42   7:30                                                            │ │
│  │  Tue   Epic-42   4:00                                                            │ │
│  │        Epic-55   3:15                                                            │ │
│  │  Wed   —                                                                        │ │
│  │  Thu   Epic-42   3:30 ▶                                                         │ │
│  │        Epic-55   0:30 ▶                                                         │ │
│  │  Fri   —                                                                        │ │
│  └───────────────────────────────────────────────────────────────────────────────────┘ │
│  ┌─ Progress ────────────────────────────────────────────────────────────────────────┐ │
│  │  Today   6:00 / 7:24   ████████████████░░░░░░░░  81%                            │ │
│  │  Week   32:30 / 29:36  ██████████████████████    100%+                          │ │
│  └───────────────────────────────────────────────────────────────────────────────────┘ │
│  ┌─ Output ──────────────────────────────────────────────────────────────────────────┐ │
│  │  ▶  Started at 11:50 — Epic-42 (carried forward)                               │ │
│  └───────────────────────────────────────────────────────────────────────────────────┘ │
│  > _                                                                                  │
└─ Footer: [Tab] focus  [↑↓] history  [l] log  [ctrl+q] quit ──────────────────────────┘
```

Vertical order: Today+Week → TaskSummary → Progress → Output → Command input → Footer.

### Multi-task day example (TaskSummaryPanel)

A typical day with two different tasks:
```
Tue   Epic-42   4:00
      Epic-55   3:15
```

A day where one session has no task assigned:
```
Wed   Epic-42   5:30
      (no task) 1:00
```

A day with three tasks, one session active:
```
Thu   Epic-42   3:30 ▶
      Epic-55   0:30
      TASK-99   1:00
```

The `▶` marker appears only on the task row that includes the currently active session.
If the active session shares a task with a completed session, their hours are merged and
the combined row carries the `▶` marker.

### Dynamic week target calculation

```python
# Pseudocode — not final code
days_with_sessions = count of Mon–Fri dates in this ISO week
                     that have at least one session (closed or active)
week_target = TARGET_HOURS * days_with_sessions
```

Edge case: if `days_with_sessions == 0` (no work yet this week), the week bar renders
as `0:00 / —` with a dim style and no percentage. The bar itself is omitted to avoid
a division-by-zero. The row remains visible so the layout does not shift when the first
session of the week is started.

### Base-60 helper

A small utility `format_hhmm(decimal_hours: float) -> str` converts decimal hours to
`H:MM` string. This lives in a shared utility module or inline in the widget files.

```python
def format_hhmm(decimal_hours: float) -> str:
    """Convert decimal hours to H:MM clock string. E.g. 7.4 → '7:24'."""
    total_minutes = round(decimal_hours * 60)
    h, m = divmod(total_minutes, 60)
    return f"{h}:{m:02d}"
```

### Progress bar duplication resolution

`build_status_group` in `Printer.py` gains `show_progress: bool = True`.
- CLI path: `print_status()` calls it with the default `True` — no change.
- TUI path: `TodayPanel.refresh_data()` calls it with `show_progress=False` — the bar
  is omitted from the panel; `ProgressStrip` owns that responsibility.

### Implementation Scope Summary

| Change | New / Modified files | Complexity |
|--------|---------------------|------------|
| A — `ProgressStrip` widget | `app/ProgressStrip.py` (new), `app/TimeTrackerApp.py`, `app/TodayPanel.py`, `Printer.py` | Low |
| B — WeekPanel promark redesign | `app/WeekPanel.py` | Low |
| C — `TaskSummaryPanel` widget | `app/TaskSummaryPanel.py` (new), `app/TimeTrackerApp.py` | Low–Medium |
| `l` binding for log overlay | `app/TimeTrackerApp.py` | Trivial |

All four changes are independent and can be implemented in one pass.

### Alternative A2 — (rejected)

Side-by-side progress bars were considered but rejected in favour of stacked rows for
better readability at varying terminal widths. User confirmed stacked is the right choice.

---

## Future Ideas

- **Configurable week target** — allow `TARGET_HOURS * 5` to be overridden for weeks
  with a holiday.
- **Week progress click-to-log** — clicking the week bar opens the log overlay
  (mouse support is a non-goal for now, but natural future step).
- **Delta colouring** — colour the week progress bar differently when the week contains
  a vacation day (see `features/vacation-periods.md`).
