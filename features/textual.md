# Feature: Textual TUI

Status: Proposed

## Purpose

Replace the current one-shot CLI and crude numbered-menu fallback with a persistent
**Textual** TUI (https://textual.textualize.io/) that stays open all day and provides a
live dashboard of today's sessions, week totals, and a command input — all in one screen.

The motivation is that the current flow requires the user to repeatedly re-run the CLI
to check status, making passive awareness of tracked time inconvenient. A persistent TUI
solves this by keeping all context visible at all times without extra commands.

Textual is by the same author as `rich`, which the project already depends on. The
business logic in `Commands.py` is already cleanly separated from presentation, so the
Textual layer replaces only the input and rendering surfaces.

---

## Requirements

- `python TimeTracker.py` (no args) launches the TUI instead of the current numbered menu.
- `python TimeTracker.py <command>` (with args) continues to work as a one-shot CLI — no
  behaviour change for scripts and aliases.
- A **Today panel** displays today's sessions, the active session if running, progress bar,
  and estimated leave time. It auto-refreshes while a session is active.
- A **Week panel** displays the current week's daily totals (Mon–Fri) at all times.
- A **Command input** accepts the same command syntax as the CLI (`start`, `stop 1715`,
  `task Epic-42`, `log w23`, etc.) and dispatches to `Commands.py`.
- Command feedback for mutation commands (`start`, `stop`, `pause`, `resume`, `task`)
  appears in a dedicated Output panel. `status` triggers an immediate panel refresh
  instead.
- `log` / `log w23` opens a full-screen week detail overlay showing per-day sessions and
  task labels. The overlay supports `←`/`→` week navigation and closes with `Esc`.
- The TUI exits cleanly on `Ctrl+C` / `q`, restoring the terminal.
- All functionality accessible by keyboard alone.

---

## Non-Goals

- Does not replace the one-shot CLI for scripting or alias use.
- Does not implement inline session editing in this initial version (deferred to Future Ideas).
- Does not add new commands — only exposes existing commands in a new interface.
- Does not require mouse support (but must not break it either).
- Does not change `Commands.py` business logic or `Storage.py`. `Commands.py` function
  signatures will be updated to accept an `AppContext` parameter, but no logic changes.

---

## Manual Changes

2026-06-19
- Command feedback resolved: dedicated Output panel (Option A).
- `log` / `log w23` resolved: full-screen overlay with `←`/`→` week navigation.
- Output routing resolved: `AppContext` Protocol with `CliAppContext` / `TuiAppContext`.
- `restart` rename: **`resume`** confirmed. `resume` covers all cases including
  zero-gap boundaries. No separate `split` command needed. `restart` kept as a
  deprecated alias printing a deprecation notice.
- Smoke test requirements added.

---

## Brainstorm Notes

### Layout Paradigm

Based on the TUI design skill, the best fit for this app is a **Widget Dashboard**:

```
┌─ TimeTracker ────────────────────────────────────────────────────────────┐
│                                                                          │
│  ┌─ Today: 2026-06-19 ──────────────┐  ┌─ Week 25 ───────────────────┐ │
│  │  #1  08:30 → 09:15  0.75h        │  │  Mon  08:30–16:15   7.42h  │ │
│  │  #2  09:15 → now ▶  3.25h active │  │  Tue  08:45–16:30   7.25h  │ │
│  │                                  │  │  Wed  —                     │ │
│  │  Logged  4.00h / 7.50h           │  │  Thu  08:30 → now   4.00h  │ │
│  │  ████████░░░░░░░░░░  53%         │  │  Fri  —                     │ │
│  │  Leave at ~15:45                 │  └─────────────────────────────┘ │
│  └──────────────────────────────────┘                                   │
│                                                                          │
│  ┌─ Output ───────────────────────────────────────────────────────────┐ │
│  │  ▶  Started at 09:15 — Epic-42 (carried forward)                  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│  ┌─ Command ──────────────────────────────────────────────────────────┐ │
│  │  > _                                                               │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│  [Tab] focus  [↑↓] history  [q] quit  [?] help                          │
└──────────────────────────────────────────────────────────────────────────┘
```

The "Widget Dashboard" paradigm (per SKILLS.md) fits because:
- All panels are self-contained and simultaneously visible.
- Users build spatial memory — Today is always left, Week always right.
- There is no hierarchical drill-down; everything relevant is on one screen.

---

### Command Feedback

Command feedback uses a **dedicated Output panel** (Option A, as shown in the wireframe).

The Output panel is relevant primarily for mutation commands: `start`, `stop`, `pause`,
`resume`, `task`. These produce a short confirmation or error message that the user
should be able to glance at after the fact.

`status` and `log` are not candidates for the Output panel — `status` is already
represented live by the Today panel, and `log` has its own dedicated view (see below).
This keeps the Output panel focused and uncluttered.

---

### Command Input Design

The command input should:
- Accept the same syntax as the CLI: `start`, `start 0830 Epic-42`, `stop 1715`,
  `task Epic-42`, `task Epic-42 -s 2`, `resume`, `log`, `log w23`, `promark`, `status`.
- Submit on Enter, clear the field.
- Support `↑`/`↓` arrow keys for command history within the session.
- Display an error inline or in the Output panel for unrecognised commands.

`status` in TUI mode forces an immediate refresh of the Today panel. It does not write
to the Output panel since the panel already reflects live data.

---

### Auto-Refresh

The Today panel should refresh on a timer while an active session is running, so the
`active_hours` and `Leave at` estimate stay current without user action.

Proposed refresh interval: **60 seconds** (original doc). Could be 30 seconds for better
responsiveness, at negligible CPU cost.

The Week panel only needs to refresh when a `stop` or `pause` command is issued (day
total changes). Refreshing it on timer is unnecessary.

---

### AppContext Protocol — Output and Refresh Signals

`Commands.py` currently uses `print()` for all user-facing output. In TUI mode, raw
`print()` calls would corrupt the Textual display.

#### Why not a full "entry point" Protocol?

A broader design would give CLI and TUI each their own class implementing a shared
Protocol covering the full parse → dispatch → render flow. The appeal is a clean seam
between modes. The problem is that command parsing and dispatch are *identical* in both
modes — only two things actually differ:

1. How feedback messages are delivered (stdout vs. Output panel widget).
2. Which UI state needs refreshing after a command (nothing in CLI; Today/Week panels
   in TUI).

A full entry-point split would force both sides to duplicate routing logic that is
already correct and shared. The `AppContext` Protocol below targets exactly what differs,
and nothing else.

#### The `AppContext` Protocol

```
# Conceptual sketch — not final code

class AppContext(Protocol):
    # Output delivery
    def info(self, message: str) -> None: ...
    def warning(self, message: str) -> None: ...
    def error(self, message: str) -> None: ...

    # Post-command refresh signals (no-ops in CLI)
    def on_session_changed(self) -> None: ...
    # Called after start/stop/pause/resume — refreshes Today and Week panels.

class CliAppContext:
    # Delivers messages via Rich console / plain print.
    # on_session_changed() does nothing — CLI exits after each command.

class TuiAppContext:
    # Delivers messages to the Output panel widget.
    # on_session_changed() triggers Today and Week panel refreshes.
```

`TimeTracker.py` (one-shot path) instantiates `CliAppContext` and passes it through.
`TimeTrackerApp` (TUI path) instantiates `TuiAppContext` wired to the live panels.

`Commands.py` function signatures gain an `AppContext` parameter. Business logic is
untouched — only `print()` calls are replaced with `ctx.info()` / `ctx.warning()` /
`ctx.error()`, and `on_session_changed()` is called at the end of mutating commands.

> **Python note:** `Protocol` (from `typing`) describes a structural interface. Any class
> that implements the required methods satisfies it, without needing to inherit from it.
> This is Python's equivalent of a Go interface or a TypeScript `interface`.

If the app grows significantly — more commands, complex routing per mode — revisiting a
full entry-point Protocol would be reasonable. At current scale it adds indirection
without adding value.

---

### Log View (Week Detail Overlay)

`log` and `log w23` open a **full-screen overlay** showing the detailed week log: every
session per day with its task label and per-day totals. This is the primary view for
Antura registration, where the user needs to know exactly which tasks were worked on for
each day of the week.

```
┌─ Week 25 — Jun 16–20, 2026 ──────────────────────────────────────────────┐
│                                                                           │
│  Mon  2026-06-16                                                          │
│    #1  08:30–12:00  3.50h  Epic-42                                        │
│    #2  12:30–16:30  4.00h  Epic-42                                        │
│    daily total  7.50h                                                     │
│                                                                           │
│  Tue  2026-06-17                                                          │
│    #1  08:45–16:30  7.25h  Epic-55                                        │
│                                                                           │
│  Wed  2026-06-18                                                          │
│    —                                                                      │
│                                                                           │
│  Thu  2026-06-19  ◀ today                                                 │
│    #1  08:30–12:15  3.75h  Epic-42                                        │
│    #2  13:00 → now ▶  2.50h  Epic-42                                      │
│                                                                           │
│  Fri  2026-06-20                                                          │
│    —                                                                      │
│                                                                           │
│  Week total  21.00h                                                       │
│                                                                           │
│  [Esc] close   [←] prev week   [→] next week                             │
└───────────────────────────────────────────────────────────────────────────┘
```

Key behaviours:
- `log` (no arg) opens at the current week.
- `log w23` opens at week 23.
- `←` / `→` navigate between weeks without re-typing the command.
- `Esc` closes the overlay and returns to the dashboard.
- The overlay is scrollable if the week has many sessions.
- Today's date is highlighted and the active session (if any) shows as `→ now ▶`.

---

### Architecture (Draft)

```
TimeTracker.py
  └── main()
        ├── args present → one-shot dispatch (CliAppContext)
        └── no args      → TimeTrackerApp().run()

app_context.py             — AppContext Protocol + CliAppContext
Commands.py                — accepts AppContext parameter; logic unchanged

app/
  ├── __init__.py
  ├── TimeTrackerApp.py    — Textual App subclass; mounts widgets, routes commands
  ├── TodayPanel.py        — Today's sessions, progress bar, leave time; timer-refreshed
  ├── WeekPanel.py         — Current week daily totals; refreshed after mutating commands
  ├── OutputPanel.py       — Scrollable read-only log of mutation feedback
  ├── CommandInput.py      — Input widget; parses and dispatches to Commands.py on Enter
  ├── LogScreen.py         — Full-screen overlay for week log detail (push_screen / pop)
  └── TuiAppContext.py     — AppContext impl that posts to OutputPanel + refreshes panels
```

`Printer.py` stays in place for one-shot mode. The TUI builds its own widget renderers
reading from the same data layer (`Commands._build_day_status()`, `read_log()`, etc.).

---

### Keyboard Design

Following the L0/L1/L2 layering from SKILLS.md:

| Layer | Keys | Purpose |
|-------|------|---------|
| L0 | `Tab` / `Shift+Tab` | Cycle focus between panels |
| L0 | `Enter` | Submit command |
| L0 | `Esc` | Clear command input / dismiss overlay |
| L0 | `q` | Quit the TUI |
| L1 | `↑` / `↓` in input | Command history |
| L2 | `?` | Show help overlay |

Footer bar (always visible):
```
[Tab] focus  [↑↓] history  [q] quit  [?] help
```

---

### Color / Theming

`Printer.py` already defines a colour palette (`_C_OK`, `_C_WARN`, `_C_ACTIVE`, etc.)
These map naturally to Textual CSS variables. The TUI should define a theme that mirrors
these so the visual language is consistent between one-shot and TUI mode.

Per SKILLS.md semantic slot mapping:
- `_C_OK` / `_C_ACTIVE` (bold green) → `$success`
- `_C_WARN` (bold yellow) → `$warning`
- `_C_VALUE` (bold cyan) → `$accent`
- `_C_DIM` (dim) → `$text-muted`
- `_C_BORDER` (steel_blue1) → border colour for focused panels

---

### Dependency

`textual` is the natural fit: same author as `rich`, already in the dependency chain
indirectly, and explicitly called out in `AGENTS.md` as a preferred library for TUI work.

```
textual>=0.60   # add to requirements.txt when implementation begins
```

The current `rich>=13.0` dependency can remain — Textual bundles a compatible version
but external Rich usage in `Printer.py` (one-shot mode) continues to work.

---

### Relationship to `toast.md`

`features/toast.md` notes that the Textual feature is a prerequisite for Toast
Notifications. The Toast feature is a separate concern and its design will be revisited
once this feature is complete.

---

### Renaming `restart` → `resume`

The actual use case driving this rename:

```
start 0700 TASK-1234   → begin work
pause 1120             → stop for lunch (session closed)
                         [lunch break]
resume 1150            → resume after break, carry TASK-1234 forward
stop 1445
```

`resume` is the natural inverse of `pause`. The pair reads as plain English and maps
directly to the user's mental model: clock out → break → clock back in.

```
python TimeTracker.py pause 1120     → clock out for lunch
python TimeTracker.py resume 1150    → clock back in, epic carried forward
```

**Resolved: `resume` covers all cases.** If called with no gap (same time as a
preceding `pause`), it behaves like the old `restart`. No separate "instant boundary"
command is needed.

**Behaviour of `resume`:**
- Looks up the last session for today (open or closed) and carries its epic forward.
- If a session is currently open, closes it first at the given time, then opens the new
  one — so `resume 1200` against an open session is equivalent to `pause 1200` +
  `resume 1200`.
- Prints the carried epic in the confirmation so the user can verify at a glance.

`restart` is kept as a **deprecated alias** — it prints a deprecation notice pointing
to `resume` and then runs the same logic. It can be removed in a future cleanup.

---

### Required Smoke Tests

The `AppContext` refactor touches every `Commands.py` function. Before the feature can be
considered implemented, a smoke test suite must pass that exercises a complete normal
working day end-to-end against a real (file-backed) test database.

These are **integration tests** (`tests/test_smoke.py`), not unit tests — they test the
full command → storage → read-back cycle. They do not test the TUI widgets.

#### Normal day scenario

```
start 0700 TASK-1234       → session #1 opens at 07:00, epic = TASK-1234
pause 1120                 → session #1 closes at 11:20
resume 1150                → session #2 opens at 11:50, epic = TASK-1234 (carried)
status (≈ 14:00)           → sessions #1 and #2 visible; active_start = 11:50
stop 1445                  → session #2 closes at 14:45
start 2100                 → session #3 opens at 21:00, no epic
stop 2130                  → session #3 closes at 21:30
```

**Assertions after the full sequence:**
- 3 completed sessions, 0 open sessions.
- Session #1: 07:00–11:20, 4.33h, task = TASK-1234.
- Session #2: 11:50–14:45, 2.92h, task = TASK-1234.
- Session #3: 21:00–21:30, 0.50h, task = (empty).
- Total logged: 7.75h.
- `status` mid-sequence (between `start 1150` and `stop 1445`) must show:
  - 1 completed session, 1 active session.
  - Active session start = 11:50.
  - Leave time estimate is present and plausible.

#### Additional cases to cover

| Scenario | What to verify |
|----------|---------------|
| `resume` (formerly `restart`) | New session opens at given time; epic carried from last session; two sessions in DB. |
| `task <epic> -s N` | Updates the correct session row; other sessions unaffected. |
| Double `start` guard | Second `start` before `stop`/`pause` prints a warning; session count unchanged. |
| `stop` with no open session | Prints error; session count unchanged. |
| `log w<N>` | Returns sessions for the correct ISO week; cross-week sessions not included. |

The test file should use a **temporary SQLite database** (via `tempfile` or `tmp_path` in
pytest) so tests are isolated and leave no side-effects.

---

## Future Ideas

- **Inline session editing** — correct a session's Task/Epic from the Today panel without
  typing a `task` command. See `features/session-editing.md`.
- **Contextual prompts** — after `stop`, prompt "add an epic for that session?"; after
  `start`, pre-fill from the previous session's epic.
- **Mouse support** — scroll panels, click session rows.
- **Persistent command history** — save input history to disk across restarts.
- **`status` command becomes a no-op** in TUI mode (panel is always live).
- **Week navigation** — `←`/`→` keys inside the Week panel to browse previous weeks.
- **Configurable refresh interval** for the Today panel.
- **Minimum terminal size gate** — show a "terminal too small" message below 80×24.