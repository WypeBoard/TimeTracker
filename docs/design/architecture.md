# Architecture

## Purpose

Describes how TimeTracker is put together: the modules, the layers they are
allowed to call, and the process model. This document explains the *shape* of
the system. What each part does in detail belongs in
[Detailed Design](../detailed-design/commands.md); how it is operated belongs
in [Operations](../operations/logging.md).

---

## Current Behaviour

TimeTracker is a single-process, single-user desktop application. It has no
server, no network calls, and no background workers. Everything runs inside
one Python process that stays open for the working day.

Starting the application:

```powershell
python TimeTracker.py
```

`TimeTracker.py` calls `create_schema()` once, then launches the Textual
application. There is no one-shot command mode — every interaction happens
inside the running TUI.

---

## Module Map

```
TimeTracker.py        — Entry point; schema creation and TUI launch
Commands.py           — Command implementations (start, stop, pause, …)
Printer.py            — Rich-based output formatting and shared projections
Promark.py            — Promark report calculation
Constants.py          — DB_FILE path and application constants
logger.py             — Logging configuration and crash capture
app_context.py        — Application context protocol

Storage.py            — Session domain layer (sessions / sessions_h)
EpicStorage.py        — Epic domain layer (epics / task_catalog)
SettingsStorage.py    — Settings domain layer (settings / settings_h)

db/
    query_type.py     — QueryType enum (READ / WRITE)
    connection.py     — Connection context manager
    repository.py     — execute / fetch_one / fetch_many helpers

app/
    TimeTrackerApp.py — Textual App; owns the screen and key bindings
    TuiAppContext.py  — Context implementation for TUI mode
    CommandInput.py   — Command bar and history
    *Panel.py         — Dashboard panels
    *Screen.py        — Full-screen overlays
    EpicModal.py      — Task–Epic linking modal
    utils.py          — Shared TUI helpers

tests/                — pytest suite
docs/                 — Documentation (this folder)
features/             — Feature design documents
```

---

## Layering

The data path is a strict chain. No layer may skip a level.

```
app/  →  Commands.py  →  *Storage.py  →  db/repository.py  →  db/connection.py
```

| Layer | Responsibility | May call |
|-------|---------------|----------|
| `app/` | Rendering and input only. Holds no business rules. | `Commands.py` |
| `Commands.py` | Command semantics and orchestration. | `*Storage.py` |
| `*Storage.py` | Domain layer. The only code that knows the schema. | `db/repository.py` |
| `db/repository.py` | Query execution helpers. | `db/connection.py` |
| `db/connection.py` | Transaction and connection lifetime. | `sqlite3` |

Enforced rules:

- Nothing outside `db/` imports from `db/` except `Storage.py`,
  `EpicStorage.py`, and `SettingsStorage.py`.
- `Commands.py` never imports from `db/`.
- `app/` never imports from `db/` or issues SQL.
- All DDL lives in `create_schema()` in `Storage.py` and nowhere else.

### Why the TUI calls `Commands.py`

Panels import from `Commands.py` and `Printer.py` rather than computing
values themselves. `QuickStatsPanel` calls `_build_day_status()` and
`leave_projection()` for exactly this reason: a calculation implemented twice
will eventually disagree with itself.

---

## Process Model

Single-threaded. Textual's event loop drives everything.

| Mechanism | Used for |
|-----------|----------|
| Timers (`set_interval`) | Panel refresh — 1 s for the running counter, 60 s for aggregates |
| Message handlers | Command submission, key bindings, modal results |
| Direct calls | `TuiAppContext.on_session_changed()` refreshes all panels after a mutating command |

Database access is synchronous. Queries are small enough and the database
local enough that blocking the event loop is not observable.

---

## Data Storage

A single SQLite file at `%APPDATA%\TimeTracker\timetracker.db`, created on
first run. Every main table has a `_h` shadow table populated by triggers,
giving a complete audit trail without application code. See
[SQLite Datasource](../detailed-design/sqlite-datasource.md).

---

## Limitations

- **Windows only** — the database path depends on `%APPDATA%`.
- **Single machine** — the database is local with no sync.
- **Single user** — no authentication or multi-user concept.
- **No migrations** — schema evolution relies on `IF NOT EXISTS` DDL; there
  is no versioned migration mechanism.
- **Deprecated modules remain** — `Workbook.py`, `Summary.py`, and `Styles.py`
  are no longer imported and are pending deletion.

---

## Decisions

**2025 — SQLite rather than Excel**
- Decision: Sessions are stored in a local SQLite database.
- Rejected: The original `.xlsx` workbook via `openpyxl`.
- Driver: `Technical` — SQLite gives ACID writes and SQL querying with no
  third-party dependency, and does not break when the file is open elsewhere.

**2025 — Strict layered dependency chain**
- Decision: `Commands → Storage → db/repository → db/connection`, with no
  level skipping and all DDL in `create_schema()`.
- Rejected: Direct `sqlite3` access from command functions.
- Driver: `Technical` — it keeps schema knowledge in one layer, so a column
  change has exactly one blast radius.

**2025 — History tables by trigger, not by application code**
- Decision: Every table has a `_h` shadow table written by SQLite triggers.
- Rejected: Writing audit rows from the storage layer.
- Driver: `Technical` — triggers fire inside the originating transaction, so
  history cannot be skipped by a code path that forgot to write it.

**2026 — TUI-only, no one-shot CLI**
- Decision: `python TimeTracker.py` always launches the TUI; all commands are
  typed into the command bar.
- Rejected: Keeping the one-shot `python TimeTracker.py start` form.
- Driver: `Preference` — the application is meant to stay open all day, and
  two entry paths meant two output formats to maintain.

**2026 — Calculations live in `Commands.py` / `Printer.py`, not in panels**
- Decision: TUI panels call shared functions for all derived values.
- Rejected: Panels computing their own totals and projections.
- Driver: `Technical` — duplicated calculations drift apart silently.

---

## Notes

- Week numbers are never stored. They are derived at query time with
  `datetime.isocalendar()`.
- Times are stored as local `HH:MM` strings exactly as entered. Only audit
  timestamps (`h_timestamp`) are UTC.

---

## Related Documents

- [Documentation Index](../index.md)
- [Software Standard](../operations/software-standard.md) — the coding rules that enforce this architecture.
- [SQLite Datasource](../detailed-design/sqlite-datasource.md) — schema detail.
- [User Interface Design](user-interface-design.md) — the presentation layer.
