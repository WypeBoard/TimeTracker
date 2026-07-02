# TUI

## Purpose

The Textual TUI is the sole interaction surface for TimeTracker. It provides a
persistent, full-screen dashboard that stays open all day. All time-tracking
commands are entered through the command bar at the bottom of the screen.

---

## Current Behaviour

Running `python TimeTracker.py` always launches the TUI. There is no one-shot
CLI mode — all commands are entered from within the running application.

---

## Layout

```
┌─ TimeTracker ───────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─ Today: 2026-06-22 ────────────────────┐  ┌─ Week 26 ─────────────────┐ │
│  │  #  Start  End      Hours  Task        │  │  2026-06-16  Mon  07:30→17:00  7:30 │ │
│  │  #1  07:30  11:20   3:50h  Epic-42     │  │  2026-06-17  Tue  08:00→15:45  7:15 │ │
│  │  #2  11:50  now ▶   2:10h  Epic-42     │  │  2026-06-18  Wed  —             │ │
│  │                                        │  │  2026-06-19  Thu  08:30→now ▶  4:00 │ │
│  │  ⏳ Remaining 1:30   🚪 Leave ~16:15   │  │  2026-06-20  Fri  —             │ │
│  └────────────────────────────────────────┘  └───────────────────────────────┘ │
│                                                                             │
│  ┌─ Task Summary — Week 26 ────────────────────────────────────────────────┐ │
│  │  Mon   Epic-42   7:30                                                   │ │
│  │  Tue   Epic-42   4:00                                                   │ │
│  │        Epic-55   3:15                                                   │ │
│  │  Wed   —                                                                │ │
│  │  Thu   Epic-42   3:30 ▶                                                 │ │
│  │  Fri   —                                                                │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─ Progress ──────────────────────────────────────────────────────────────┐ │
│  │  Today   6:00 / 7:24   ████████████████░░░░░░░░  81%                   │ │
│  │  Week   32:30 / 29:36  ██████████████████████    110%                  │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─ Output ────────────────────────────────────────────────────────────────┐ │
│  │  ▶  Started #2 — 11:50  Epic-42  (carried forward)                     │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│  > type a command…                                                          │
│  [l] Log  [ctrl+q] Quit                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

Vertical order: Today + Week → Task Summary → Progress → Output → Command input → Footer.

---

## Panels

### Today panel (left, top row)

Shows today's completed sessions plus the active session (if any) marked
`now ▶`, and an estimated leave time (when a session is active).

The progress bar has been moved to the **Progress** strip below — the Today
panel now shows only the session table and leave-time line.

Auto-refreshes every 60 seconds while a session is running.

### Week panel (right, top row)

Displays Mon–Fri for the current ISO week in promark style:

```
2026-06-16  Mon  07:30 → 17:00  7:30
2026-06-17  Tue  08:00 → 15:45  7:15
2026-06-18  Wed  —
2026-06-19  Thu  08:30 → now ▶  4:00
2026-06-20  Fri  —
```

- Each row: `Date  Day  HH:MM → HH:MM  Xh`.
- Promark end = `first_start + total_hours + 30 min lunch` (same algorithm as
  the `promark` command).
- Today's row shows `now ▶` for the end time when a session is active.
- Days with no sessions show `Date  Day  —`.
- All hours in base-60 clock format (`H:MM`).
- Refreshes every 60 seconds and after every mutating command.

### Task Summary panel (full width, below top row)

Pivot view of which tasks were worked on each weekday and the aggregated hours:

```
Mon   Epic-42   7:30
Tue   Epic-42   4:00
      Epic-55   3:15
Wed   —
Thu   Epic-42   3:30 ▶
Fri   —
```

- One row per (day, task) combination. The day name appears only on the first
  task row; continuation rows have a blank day cell.
- Tasks are aggregated across sessions — three sessions tagged `Epic-42`
  become one row.
- Sessions with no task label are shown as `(no task)`.
- The `▶` marker appears on the task row that includes the currently active
  session. If the active session shares a task with completed sessions, their
  hours are merged and the combined row carries the marker.
- Days with no sessions show `Day  —`.
- Hours in base-60 clock format (`H:MM`).
- Border title: `Task Summary — Week N`.
- Refreshes every 60 seconds and after every mutating command.

### Progress strip (full width, below Task Summary)

Two stacked progress bars:

```
Today   6:00 / 7:24   ████████████████░░░░░░░░  81%
Week   32:30 / 29:36  ██████████████████████    110%
```

- **Today** row: logged hours vs. `TARGET_HOURS` (7.4 h).
- **Week** row: this week's total hours vs. the *dynamic week target*
  (`TARGET_HOURS × number of weekdays with at least one session`). This gives
  a meaningful signal on Monday instead of always showing ~20%.
- Edge case — no sessions yet this week: the Week row renders `0:00 / —`
  (dim, no bar) so the layout does not shift when the first session starts.
- Bars are green when the target is met; yellow otherwise.
- All times in base-60 clock format (`H:MM`).
- Refreshes every 60 seconds and after every mutating command.

### Output panel

Scrollable log of confirmation and error messages from mutation commands
(`start`, `stop`, `pause`, `resume`, `task`). The `status` command does not
write here — it refreshes the Today panel directly.

---

## Commands

All commands are entered via the command bar. See `docs/commands.md` for full
reference including syntax, arguments, and output examples.

| Command | Behaviour in TUI |
|---------|-----------------|
| `start [hhmm] [epic]` | Opens session; confirmation in Output; shows Task–Epic modal if task is new |
| `pause [hhmm]` | Closes session; confirmation in Output |
| `stop [hhmm]` | Closes session; all panels refresh |
| `resume [hhmm]` | Close + reopen, carrying epic; shows Task–Epic modal if carried task is new |
| `task <epic> [-s N]` | Tags session; confirmation in Output; shows Task–Epic modal if task is new |
| `status` | Refreshes Today panel immediately (no Output message) |
| `log [wNN]` | Opens the Log overlay |
| `promark [wNN]` | Writes the Promark table to Output |
| `epic add <name>` | Creates a new Epic; confirmation in Output |
| `epic list` | Lists all Epics alphabetically in Output |
| `epic summary [wNN]` | Opens the Epic Summary overlay |

---

## Log Overlay

Typing `log` (or pressing `l`) pushes a full-screen overlay showing every
session for the week with task labels, daily totals, and a week total.

```
┌─ Week 26 — Jun 16–20, 2026 ──────────────────────────────────────────────┐
│                                                                           │
│    Mon  #1  08:30–12:00  3.50h  Epic-42                                  │
│         #2  12:30–16:30  4.00h  Epic-42                                  │
│             daily total  7.50h                                            │
│    Tue  #1  08:45–16:30  7.25h  Epic-55                                  │
│    Wed  —                                                                 │
│    Thu  #1  07:30 → now ▶  ...                                            │
│    Fri  —                                                                 │
│                                                                           │
│    Week total:  ...                                                       │
│                                                                           │
│  [Esc] close   [←] prev week   [→] next week                             │
└───────────────────────────────────────────────────────────────────────────┘
```

Navigation:
- `←` / `→` — browse between weeks (forward navigation is capped at the current week).
- `Esc` — close the overlay and return to the dashboard.

---

## Task–Epic Modal

Appears automatically when a task identifier used in `start`, `resume`, or
`task` has no entry in the Epic Catalog (`task_catalog`). The modal fires at
most once per task — after a link is written it does not reappear.

**State 1 — Epic selection list:**

```
┌─ New task: TASK-789 ──────────────────────────────────────┐
│  Select an Epic to link this task, or press Esc to skip.  │
│                                                           │
│  ► Platform Team                                          │
│    Mobile App                                             │
│                                                           │
│  [ + New epic… ]                                          │
│                                                           │
│  [↑↓] navigate   [Enter] select   [Esc] save as (Misc)   │
└───────────────────────────────────────────────────────────┘
```

- `↑` / `↓` navigate; `Enter` confirms the selection.
- Selecting an existing Epic writes the `task_catalog` entry and closes the modal.
- Selecting `[ + New epic… ]` transitions to State 2.
- `Esc` closes without linking; the task is treated as `(Misc)` in `epic summary`.

**State 2 — Inline Epic creation:**

```
┌─ New task: TASK-789 ──────────────────────────────────────┐
│  New Epic name:                                           │
│  ┌───────────────────────────────────────────────────┐   │
│  │ Platform Team_                                    │   │
│  └───────────────────────────────────────────────────┘   │
│                                                           │
│  [Enter] create & link   [Esc] back to list               │
└───────────────────────────────────────────────────────────┘
```

- `Enter` with a non-empty name: creates the Epic, writes `task_catalog`, closes modal.
- `Enter` with an empty name: no-op (stays open).
- Duplicate name: inline error shown; stays in State 2.
- `Esc`: returns to State 1.

---

## Epic Summary Overlay

Opened by `epic summary [wNN]`. Shows time grouped by **day first**, then by
Epic within each day. Navigation matches the Log overlay.

```
┌─ 📊  Epic Summary — Week 26  (Jun 16 – Jun 20) ──────────────────────────┐
│                                                                            │
│  Monday Jun 16                                     12:30                  │
│    Platform Team                                   10:00                  │
│      TASK-123                                       7:30                  │
│      TASK-456                                       2:30                  │
│    (Misc)                                           2:30                  │
│      TASK-789                                       2:30                  │
│  Tuesday Jun 17                                     4:15                  │
│    Platform Team                                    4:15                  │
│      TASK-123                                       4:15                  │
│                                                                            │
│  Week total:  16:45                                                        │
│                                                                            │
│  [Esc] close   [←] prev week   [→] next week                              │
└────────────────────────────────────────────────────────────────────────────┘
```

- Each day is a bold header line with the daily total.
- Epics are indented under their day with a per-day Epic total.
- Tasks are double-indented under their Epic with per-day task totals.
- Tasks with no `task_catalog` entry are grouped under `(Misc)` within that day.
- `(Misc)` is a virtual group — it is not stored and does not appear in
  `epic list`.
- Hours in base-60 clock format (`H:MM`).
- `←` / `→` navigate weeks; `Esc` closes.

---

## Keyboard Reference

| Key | Action |
|-----|--------|
| `Enter` | Submit command |
| `↑` / `↓` | Browse command history (within the session) |
| `Esc` | Clear command input (or close overlay) |
| `Tab` / `Shift+Tab` | Cycle focus between panels |
| `l` | Open the Log overlay for the current week |
| `ctrl+q` | Quit the TUI |
| `←` / `→` (in Log / Epic Summary overlay) | Navigate between weeks |
| `↑` / `↓` (in Task–Epic modal) | Navigate the Epic list |
| `Enter` (in Task–Epic modal) | Select Epic or confirm new name |
| `Esc` (in Task–Epic modal State 1) | Skip linking (save as Misc) |
| `Esc` (in Task–Epic modal State 2) | Return to Epic selection list |

---

## Auto-Refresh

The Today panel, Task Summary panel, and Progress strip refresh automatically
every **60 seconds** while the TUI is running. This keeps the `active_hours`
counter, the task pivot, and the progress bars current without any user action.

The Week panel also runs a 60-second timer so its running total stays current.

The Output panel does not use a timer — it updates only in response to commands.

---

## Limitations

- Mouse support is not implemented (keyboard only).
- Command history is session-scoped — it is not persisted to disk.
- The `?` help keybinding is not yet implemented.
- The `status` command refreshes the Today panel but does not write to Output.
- Week navigation in the Log overlay is capped at the current week; future
  weeks cannot be viewed.
- The Task Summary panel does not scroll. If a week has an unusually large
  number of task/day combinations the content will overflow the widget boundary.
- The dynamic week target in the Progress strip counts any weekday with at
  least one session. No adjustment is made for vacation days or public holidays.

---

## Related Features

- `features/textual.md` — original Textual TUI design document.
- `features/tui-dashboard-enhancements.md` — design document for the dashboard
  enhancements (WeekPanel redesign, TaskSummaryPanel, ProgressStrip).
- `docs/commands.md` — full command reference.
- `docs/epic-catalog.md` — Epic Catalog: managing Epics, task–Epic linking, and the modal.