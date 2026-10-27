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

### `lunch [hhmm]`

Opens a new session with `task = "Lunch"`. Use this to clock the lunch break
as a first-class session rather than typing `start 1200 Lunch` manually.

```
lunch
lunch 1200
```

- `hhmm` — optional four-digit time override. Defaults to `now`.
- If a session is already running, it is **automatically closed** at `hhmm`
  (or now) before the Lunch session is opened — no separate `pause` is needed.
- Lunch sessions are **never** linked to an Epic — the Task–Epic modal does not
  appear.
- Whether Lunch sessions count toward the daily working-hours target is
  controlled by the **Lunch** section of the configuration screen.

Output example (when a session was already running):

```
⏸  Closed #1 — 08:30 → 12:00
▶  Started Lunch at 12:00
```

Output example (no prior session):

```
▶  Started Lunch at 12:00
▶  Started Lunch at 12:00 (manually set)
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

Opens a new session, carrying the Task/Epic of the most recent **work** session
forward. The natural inverse of `pause`: clock out → break → clock back in.

"Work" sessions are those whose task is **not** one of the following:
- `"Lunch"` (always skipped)
- Any task in the **Excluded from working hours** list (e.g. `commute`, `coffee walk`)
- Any task in the **Always separate** list (e.g. `Sick`, `Doctor`, `Bank meeting`)

Covers two cases:
- **Open session exists:** closes it at `hhmm` (or now), then opens a new
  session with the carried task — equivalent to `pause` + `start <same_epic>`.
- **No open session, but closed sessions exist today:** opens a new session
  carrying the last work session's task.

The typical lunchtime flow:

```
lunch 1200      # closes work session, starts Lunch
resume 1230     # closes Lunch, resumes the pre-lunch task
```

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

Refreshes the cockpit panels (Active Session, Quick Stats, Today's
Timeline) immediately. Does not write to the Output panel.

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

Opens the Weekly Overview overlay for the target week. Defaults to the
current week; `wNN` selects a specific ISO week number. The overlay shows
time grouped day → Epic → task with both `HH:MM` and decimal duration
columns on every row.

```
epic summary
epic summary w26
```

Same overlay as the `[w]` key binding and the `log` command — see
[Weekly Overview overlay](tui.md#weekly-overview-overlay) in `docs/tui.md`.

---

### `log [wNN]`

Opens the Weekly Overview overlay showing hours grouped day → Epic → task
for the target week. Defaults to the current week; `wNN` selects a specific
ISO week number.

```
log
log w23
```

Same overlay as the `[w]` key binding and the `epic summary` command. The
previous individual-session log format has been retired — see
[Weekly Overview overlay](tui.md#weekly-overview-overlay) in `docs/tui.md`
for the current format.

> **Year-boundary note:** `wNN` is resolved against the current year. Week 1
> at the turn of the year may be ambiguous. This is a known edge case.

---

### `promark [wNN]`

Writes the Promark-style table to the Output panel. Defaults to the current
week; `wNN` selects a specific ISO week number.

```
promark
promark w23
```

The table applies the following settings (configured via the `config` screen):

- **Always-separate tasks**: listed tasks appear as standalone rows (hours only,
  no synthetic time range) instead of being merged into the consolidated day
  entry.
- **Lunch excluded**: if enabled, Lunch sessions are removed from the normal
  session pool before computing the consolidated start/end range.
- **Promark offset**: if set, `max(0, offset_minutes − actual_lunch_minutes)`
  is added to the consolidated day's synthetic end time.

Sessions tagged as excluded tasks (from the configuration screen) are still
included in the Promark output — exclusion only affects hours totals and
progress bars, not Promark rows.

---

### `config`

Opens the configuration screen.

```
config
```

Alternative: press `Ctrl+,`.

See `docs/configuration.md` for full reference.

---

## Limitations

- `wNN` week selection always uses the current year — year-boundary ambiguity
  is not yet handled.
- Weekend sessions (Saturday, Sunday) are stored in the database but `log`
  only displays Mon–Fri.

---

## Notes

- `resume` carries the Task/Epic of the *most recent work session* — skipping
  `Lunch`, tasks in the **Excluded from working hours** list, and tasks in the
  **Always separate** list. There is no flag to override the carried epic in
  the same call (use `task` afterwards if needed).
- One task per session is by design. For genuine task switches use
  `pause` → `start <epic>` or `resume` followed by `task`.

---

## Related Features

- `docs/sqlite-datasource.md` — database schema and storage layer
- `docs/tui.md` — TUI usage and keybinding reference
- `docs/epic-catalog.md` — Epic Catalog: managing Epics and the task–Epic modal
- `docs/configuration.md` — configuration screen: settings and their effects