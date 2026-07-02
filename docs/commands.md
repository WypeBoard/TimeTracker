# Commands

## Purpose

TimeTracker is a TUI application. All commands are entered through the command
bar at the bottom of the TUI screen. Opening the application is done with:

```
python TimeTracker.py
```

There is no one-shot CLI mode. Every interaction happens inside the running TUI.

---

## Current Behaviour

### Data shape

Each work session is one row in the `sessions` table:

| Column  | Type        | Notes                                      |
|---------|-------------|--------------------------------------------|
| `id`    | Integer     | Auto-incremented primary key               |
| `date`  | Text        | `YYYY-MM-DD` (local date)                  |
| `start` | Text        | `HH:MM` (local time)                       |
| `end`   | Text / NULL | `HH:MM`; NULL while the session is running |
| `task`  | Text        | Short ID such as `Epic-42`; empty if unset |

Week numbers are derived from `date` at query time via `datetime.isocalendar()`
and are not stored. An open session is one where `end IS NULL`; at most one
open session should exist at a time.

---

## Usage

Commands are typed into the command bar (`> type a command…`) and submitted
with `Enter`. All time arguments use the four-digit `hhmm` format (e.g. `0830`
for 08:30).

### `start [hhmm] [epic]`

Opens a new session. Both arguments are optional and can be combined in any
order, except that the time (if given) must come before the epic.

```
start
start 0830
start Epic-42
start 0830 Epic-42
```

- `hhmm` — four-digit time override (e.g. `0830` → `08:30`). Defaults to `now`.
- `epic` — task/epic ID. If omitted, task is left blank and can be filled
  later with `task`.

If the task identifier has no entry in the Epic Catalog, the **Task–Epic
modal** opens. Pressing `Esc` skips linking; the task is saved and treated as
`(Misc)` in `epic summary`.

Output examples:

```
▶  Started at 08:32
▶  Started at 08:30 — Epic-42 (manually set)
```

---

### `pause [hhmm]`

Closes the current session. Use this for short breaks when you intend to
continue later.

```
pause
pause 1015
```

---

### `stop [hhmm]`

Closes the current session. Use this at the end of the working day.

```
stop
stop 1715
```

---

### `resume [hhmm]`

Opens a new session, carrying the Task/Epic of the most recent session
forward. The natural inverse of `pause`: clock out → break → clock back in.

Covers two cases:
- **Open session exists:** closes it at `hhmm` (or now), then opens a new
  session with the same epic — equivalent to `pause` + `start <same_epic>`.
- **No open session, but closed sessions exist today:** opens a new session
  carrying the last session's epic.

```
resume
resume 1150
```

Output:

```
⏸  Closed #1 — 07:00 → 11:20
▶  Started #2 — 11:50  TASK-1234  (carried forward)
```

---

### `status`

Refreshes the Today panel immediately. Does not write to the Output panel.

```
status
```

---

### `task <epic> [-s N]`

Tags a session with a Task/Epic ID.

```
task Epic-42
task Epic-11 -s 2
```

- Without `-s` — targets the currently open session; falls back to the last
  session for today.
- `-s N` — targets session number N (1-indexed) for today.

If the task identifier has no entry in the Epic Catalog (`task_catalog`), the
**Task–Epic modal** opens so the user can link the task to an Epic before
saving. Pressing `Esc` in the modal skips linking; the task is saved and
treated as `(Misc)` in `epic summary`.

Output:

```
📌  #1  Epic-42  saved.
```

---

### `epic add <name>`

Creates a new Epic with the given free-text name.

```
epic add Platform Team
epic add "Mobile App"
```

- If an Epic with that name already exists, prints a warning and does nothing.

Output:

```
✅  Epic 'Platform Team' created.
⚠  An Epic with that name already exists.
```

---

### `epic list`

Lists all defined Epics, sorted alphabetically by name. Output goes to the
Output panel.

```
epic list
```

Output example:

```
  1  Mobile App
  2  Platform Team
```

---

### `epic summary [wNN]`

Opens the Epic Summary overlay showing time grouped by Epic for the target
week. Defaults to the current week; `wNN` selects a specific ISO week number.

```
epic summary
epic summary w26
```

See [Epic Summary overlay](#epic-summary-overlay) in `docs/tui.md` for the
full layout and navigation reference.

---

### `log [wNN]`

Opens the Log overlay showing the full week of sessions with task labels,
daily totals, and a week total. Defaults to the current week; `wNN` selects a
specific ISO week number.

```
log
log w23
```

Output example:

```
╭─ 📅  Week 24, 2026  (Jun 09 – Jun 13) ─────────────────────╮
│   Mon  #1  08:30–16:15  7.42h  Epic-42                       │
│   Tue  #1  08:45–12:00  3.25h  Epic-42                       │
│        #2  12:30–16:30  4.00h  Epic-11                       │
│            daily total  7.25h                                 │
│   Wed  —                                                      │
│   Thu  —                                                      │
│   Fri  —                                                      │
│                                                               │
│   Week total:  14.67h                                         │
╰───────────────────────────────────────────────────────────────╯
```

> **Year-boundary note:** `wNN` is resolved against the current year. Week 1
> at the turn of the year may be ambiguous. This is a known edge case.

---

### `promark [wNN]`

Writes the Promark-style table (single consolidated start/end per day,
including a 30-minute lunch offset) to the Output panel. Defaults to the
current week; `wNN` selects a specific ISO week number.

```
promark
promark w23
```

---

## Limitations

- `wNN` week selection always uses the current year — year-boundary ambiguity
  is not yet handled.
- Weekend sessions (Saturday, Sunday) are stored in the database but `log`
  only displays Mon–Fri.

---

## Notes

- `resume` always carries the Task/Epic of the *most recent* session (open
  or closed); there is no flag to override the carried epic in the same call
  (use `task` afterwards if needed).
- One task per session is by design. For genuine task switches use
  `pause` → `start <epic>` or `resume` followed by `task`.

---

## Related Features

- `docs/sqlite-datasource.md` — database schema and storage layer
- `docs/tui.md` — TUI usage and keybinding reference
- `docs/epic-catalog.md` — Epic Catalog: managing Epics and the task–Epic modal