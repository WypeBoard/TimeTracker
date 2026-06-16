# Commands

## Purpose

TimeTracker is a one-shot CLI tool that logs work sessions to a SQLite
database (`%APPDATA%\TimeTracker\timetracker.db`). Every command is a single
`python TimeTracker.py <command>` call — Python starts, does its thing, and
exits. There is no persistent process.

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

### `start [hhmm] [epic]`

Opens a new session. Both arguments are optional and can be combined in any
order, except that the time (if given) must come before the epic.

```
python TimeTracker.py start
python TimeTracker.py start 0830
python TimeTracker.py start Epic-42
python TimeTracker.py start 0830 Epic-42
```

- `hhmm` — four-digit time override (e.g. `0830` → `08:30`). Defaults to `now`.
- `epic` — task/epic ID. If omitted, task is left blank and can be filled
  later with `task`.

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
python TimeTracker.py pause
python TimeTracker.py pause 1015
```

---

### `stop [hhmm]`

Closes the current session and prints a day summary panel. Use this at the
end of the working day.

```
python TimeTracker.py stop
python TimeTracker.py stop 1715
```

---

### `restart [hhmm]`

Closes the running session and immediately opens a new one, carrying the
Task/Epic value of the previous session forward. Useful for returning from a
break without retyping the epic.

```
python TimeTracker.py restart
python TimeTracker.py restart 1015
```

Output:

```
⏸  Closed #1 — 08:32 → 10:15
▶  Started #2 — 10:15  Epic-42  (carried forward)
```

---

### `status`

Displays today's sessions (numbered `#1`, `#2`, …) with task labels, a
progress bar, and an estimated leave time.

```
python TimeTracker.py status
```

Output example:

```
╭─ 📅  2026-06-11  —  🕐 10:58 ──────────────────────────────╮
│   #  Start   End      Hours   Task                           │
│   #1  08:30   10:15   1.75h   Epic-42                        │
│   #2  10:15   now ▶   0.72h   Epic-42                        │
│                                                               │
│   Logged   2.47h / 7.50h   ████████░░░░░░░░░░░░░░░░  33%   │
│   ⏳  Remaining 5.03h   🚪  Leave at 16:01                   │
╰───────────────────────────────────────────────────────────────╯
```

---

### `task <epic> [-s N]`

Tags a session with a Task/Epic ID.

```
python TimeTracker.py task Epic-42
python TimeTracker.py task Epic-11 -s 2
```

- Without `-s` — targets the currently open session; falls back to the last
  session for today.
- `-s N` — targets session number N (1-indexed) for today.

Output:

```
📌  #1  Epic-42  saved.
```

---

### `log [wNN]`

Prints a full week of sessions with task labels, daily totals, and a week
total. Defaults to the current week; `wNN` selects a specific ISO week number.

```
python TimeTracker.py log
python TimeTracker.py log w23
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

Prints the Promark-style table (single consolidated start/end per day,
including a 30-minute lunch offset). Defaults to the current week; `wNN`
selects a specific ISO week number.

```
python TimeTracker.py promark
python TimeTracker.py promark w23
```

---

### Interactive mode

Running `python TimeTracker.py` with no arguments launches a numbered prompt:

```
What do you want to do?
  1) start    2) pause    3) stop     4) restart
  5) status   6) task     7) log      8) promark
Enter 1–8:
```

Commands that require arguments (e.g. `task` asks for the epic interactively)
are supported; time overrides are not available through the interactive prompt.

---

## Limitations

- `wNN` week selection always uses the current year — year-boundary ambiguity
  is not yet handled.
- Weekend sessions (Saturday, Sunday) are stored in the database but `log`
  only displays Mon–Fri.
- The interactive prompt does not support time overrides.

---

## Notes

- `restart` always carries the Task/Epic of the *previous* session; there is
  no flag to override the carried epic in the same call (use `task`
  afterwards if needed).
- One task per session is by design. For genuine task switches use
  `pause` → `start <epic>` or `restart` followed by `task`.

---

## Related Features

- `features/commands.md` — original design document
- `docs/sqlite-datasource.md` — database schema and storage layer