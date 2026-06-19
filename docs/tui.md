# TUI

## Purpose

The Textual TUI provides a persistent, full-screen dashboard that stays open
all day. It replaces the old numbered prompt (which required re-running the
script to check status). All time-tracking commands are available from a
single screen without leaving the application.

---

## Current Behaviour

Running `python TimeTracker.py` with **no arguments** launches the TUI.
Running it **with arguments** continues to work as a one-shot CLI — no
change for scripts and aliases.

---

## Layout

```
┌─ TimeTracker ────────────────────────────────────────────────────────────┐
│                                                                          │
│  ┌─ Today: 2026-06-19 ─────────────────┐  ┌─ Week 25 ────────────────┐ │
│  │  #  Start  End      Hours  Task      │  │  Mon  7.42h              │ │
│  │  #1  07:00  11:20   4.33h  TASK-1234 │  │  Tue  7.25h              │ │
│  │  #2  11:50  now ▶   2.25h  TASK-1234 │  │  Wed  —                  │ │
│  │                                      │  │  Thu  6.58h ▶            │ │
│  │  Logged  6.58h / 7.40h               │  │  Fri  —                  │ │
│  │  ████████████████████░░  89%         │  └──────────────────────────┘ │
│  │  ⏳ Remaining 0.82h  🚪 Leave ~15:44 │                               │
│  └──────────────────────────────────────┘                               │
│                                                                          │
│  ┌─ Output ───────────────────────────────────────────────────────────┐ │
│  │  ▶  Started #2 — 11:50  TASK-1234  (carried forward)              │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│  > type a command…                                                       │
│ [ctrl+q] Quit                                                            │
└──────────────────────────────────────────────────────────────────────────┘
```

### Today panel (left)

Shows today's completed sessions plus the active session (if any) marked
`now ▶`. Below the session table: logged hours vs. target, a progress bar,
and an estimated leave time (when a session is active).

Auto-refreshes every 60 seconds while a session is running.

### Week panel (right)

Shows Mon–Fri daily totals for the current ISO week. Today's row includes
the active session's partial hours and a `▶` indicator. Updates after every
mutating command.

### Output panel

Scrollable log of confirmation and error messages from mutation commands
(`start`, `stop`, `pause`, `resume`, `task`). The `status` command does not
write here — it refreshes the Today panel directly.

### Command input

The bottom bar. Type any command and press Enter to execute.

---

## Commands

All commands accepted by the one-shot CLI are available here with the same
syntax. See `docs/commands.md` for full reference.

| Command | Behaviour in TUI |
|---------|-----------------|
| `start [hhmm] [epic]` | Opens session; confirmation in Output |
| `pause [hhmm]` | Closes session; confirmation in Output |
| `stop [hhmm]` | Closes session; panels refresh |
| `resume [hhmm]` | Close + reopen, carrying epic; confirmation in Output |
| `task <epic> [-s N]` | Tags session; confirmation in Output |
| `status` | Refreshes Today panel immediately (no Output message) |
| `log [wNN]` | Opens the Log overlay |
| `promark [wNN]` | Writes the Promark table to Output |

---

## Log Overlay

Typing `log` or `log w23` pushes a full-screen overlay showing every session
for the week with task labels, daily totals, and a week total.

```
┌─ Week 25 — Jun 16–20, 2026 ──────────────────────────────────────────────┐
│                                                                           │
│    Mon  #1  08:30–12:00  3.50h  Epic-42                                  │
│         #2  12:30–16:30  4.00h  Epic-42                                  │
│             daily total  7.50h                                            │
│    Tue  #1  08:45–16:30  7.25h  Epic-55                                  │
│    Wed  —                                                                 │
│    Thu  #1  08:30–11:20  2.83h  TASK-1234   ◀ today                      │
│         #2  11:50 → now ▶  ...                                            │
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

## Keyboard Reference

| Key | Action |
|-----|--------|
| `Enter` | Submit command |
| `↑` / `↓` | Browse command history (within the session) |
| `Esc` | Clear command input (or close Log overlay) |
| `Tab` / `Shift+Tab` | Cycle focus between panels |
| `ctrl+q` | Quit the TUI |
| `←` / `→` (in Log overlay) | Navigate between weeks |

---

## Auto-Refresh

The Today panel refreshes automatically every **60 seconds** while the TUI
is running. This keeps the `active_hours` counter and the estimated leave
time current without any user action.

The Week panel and Output panel do not use a timer — they update only in
response to commands.

---

## Limitations

- Mouse support is not implemented (keyboard only).
- Command history is session-scoped — it is not persisted to disk.
- The `?` help keybinding is not yet implemented.
- The `status` command refreshes the Today panel but does not write to Output.
- Week navigation in the Log overlay is capped at the current week; future
  weeks cannot be viewed.

---

## Related Features

- `features/textual.md` — original design document
- `docs/commands.md` — full command reference
