# Feature — Textual TUI

> Status: Future / not started  
> Prerequisite: All items in `BRAINSTORM.md` ("Tasks — getting the Task column in") must
> be complete and stable before this work begins.

---

## Goal

Replace the one-shot CLI with a persistent **Textual** TUI
(https://textual.textualize.io/) that stays open all day and provides a live dashboard.

Textual is by the same author as `rich`, which this project already uses. The `Panel`
and `Table` objects produced by `Printer.py` slot into Textual widgets with minimal
changes. All business logic stays in `Commands.py` untouched — only the presentation
and input-handling layer is replaced.

---

## What the TUI would look like

```
┌─ TimeTracker ────────────────────────────────────────────────────────────┐
│                                                                          │
│  ┌─ Today: 2026-06-11 ──────────────┐  ┌─ Week 24 ───────────────────┐ │
│  │  ▶  08:30 → now    3.25h active  │  │  Mon  08:30–16:15   7.42h  │ │
│  │     12:15 → 13:00  0.75h lunch   │  │  Tue  08:45–16:30   7.25h  │ │
│  │                                  │  │  Wed  —                     │ │
│  │  Epic-42                         │  │  Thu  —                     │ │
│  │  Progress ████████░░  68%        │  │  Fri  —                     │ │
│  │  Leave at ~16:42                 │  └─────────────────────────────┘ │
│  └──────────────────────────────────┘                                   │
│                                                                          │
│  ┌─ Command ──────────────────────────────────────────────────────────┐ │
│  │  > _                                                               │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Key capabilities unlocked

- **Live status panel** — auto-refreshes every 60 s while a session is active. No need
  to manually run `status`.
- **Persistent session** — stays open all day; commands feel instant.
- **Contextual prompts** — after `stop`, the app can ask "add an epic for that
  session?"; after `start`, it can pre-fill from the previous session. Impossible in
  one-shot mode.
- **Inline editing** — click a session row to correct its Task/Epic ID.
- **Week overview always visible** — no need to run `log` separately.
- **Mouse support** — scroll, click, hover.

---

## Architecture

```
TimeTracker.py
  └── main()
        ├── args present → one-shot dispatch (unchanged, kept for scripting)
        └── no args      → TimeTrackerApp().run()

app/
  ├── TimeTrackerApp   — Textual App subclass; mounts all widgets
  ├── StatusPanel      — today's sessions, progress bar, leave time (auto-refresh)
  ├── WeekPanel        — current week summary
  ├── CommandInput     — Input widget; dispatches to Commands.py on Enter
  └── SessionTable     — clickable DataTable of today's rows
```

`Commands.py` is called exactly as it is today — the Textual layer is purely
presentation and input routing.

---

## Entry-point strategy

```
python TimeTracker.py            → Textual TUI (replaces current dumb prompt)
python TimeTracker.py start      → one-shot, exits immediately (unchanged)
python TimeTracker.py log        → one-shot, exits immediately (unchanged)
```

Existing aliases and scripts continue to work.

---

## Dependency

```
textual>=0.60   # add to requirements.txt when this phase begins
```

`textual` vendors its own `rich` internally but is fully compatible with the `rich`
objects already produced by `Printer.py`.

---

## Implementation order (draft)

| # | What | Files |
|---|------|-------|
| 1 | Scaffold `TimeTrackerApp` with placeholder panels | `app/TimeTrackerApp.py` (new) |
| 2 | `StatusPanel` widget — renders today's sessions, refreshes on timer | `app/StatusPanel.py` (new) |
| 3 | `WeekPanel` widget — renders current week summary | `app/WeekPanel.py` (new) |
| 4 | `CommandInput` widget — dispatches text to `Commands.py` | `app/CommandInput.py` (new) |
| 5 | Wire `TimeTrackerApp` into `TimeTracker.py` no-args entry-point | `TimeTracker.py` |
| 6 | `SessionTable` widget — clickable rows, inline Task/Epic editing | `app/SessionTable.py` (new) |
| 7 | Contextual post-`stop` / post-`start` prompts inside the app | `app/TimeTrackerApp.py` |
