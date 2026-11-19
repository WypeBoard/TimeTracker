# SQLite Datasource

## Purpose

Replaces the Excel file (`.xlsx`) as the persistent data store for work
sessions. SQLite provides ACID-safe writes, SQL querying, and zero new
dependencies (`sqlite3` is part of the Python standard library).

---

## Current Behavior

All session data is stored in a single SQLite database file located at:

```
%APPDATA%\TimeTracker\timetracker.db
```

The directory is created automatically on first run if it does not exist.

The database is initialised at application startup via `create_schema()`,
which is called once at the top of `main()` in `TimeTracker.py` before any
command is dispatched. All DDL uses `IF NOT EXISTS`, so subsequent startups
are a no-op.

---

## Schema

### `sessions` table

Stores one row per work session.

| Column | Type    | Notes                              |
|--------|---------|------------------------------------|
| `id`   | INTEGER | Primary key, auto-incremented      |
| `date` | TEXT    | `YYYY-MM-DD` (local date)          |
| `start`| TEXT    | `HH:MM` (local time)               |
| `end`  | TEXT    | `HH:MM` (local time), NULL if open |
| `task` | TEXT    | Task/epic label, empty string if unset |

An open session is one where `end IS NULL`. At most one open session should
exist at a time; this is enforced by application logic in `Commands.py`.

### `sessions_h` table (history / shadow)

A full audit trail of every change to `sessions`. Populated automatically
by SQLite triggers — application code never writes to this table directly.

| Column        | Type    | Notes                                       |
|---------------|---------|---------------------------------------------|
| `h_id`        | INTEGER | Primary key, auto-incremented               |
| `h_operation` | TEXT    | `'I'` Insert, `'U'` Update, `'D'` Delete   |
| `h_timestamp` | TEXT    | ISO-8601 UTC datetime of the operation      |
| `id`          | INTEGER | Mirrors `sessions.id`                       |
| `date`        | TEXT    | Mirrors `sessions.date`                     |
| `start`       | TEXT    | Mirrors `sessions.start`                    |
| `end`         | TEXT    | Mirrors `sessions.end`                      |
| `task`        | TEXT    | Mirrors `sessions.task`                     |

History rows are committed in the same transaction as the originating
statement — they are never out of sync with the main table.

---

### `epics` table

Stores one row per defined Epic.

| Column       | Type    | Notes                                |
|--------------|---------|--------------------------------------|
| `id`         | INTEGER | Primary key, auto-incremented        |
| `name`       | TEXT    | Unique free-text Epic name           |
| `created_at` | TEXT    | ISO-8601 UTC datetime of creation    |

### `epics_h` table (history / shadow)

Full audit trail for `epics`. Populated automatically by triggers.

| Column        | Type    | Notes                                       |
|---------------|---------|---------------------------------------------|
| `h_id`        | INTEGER | Primary key, auto-incremented               |
| `h_operation` | TEXT    | `'I'` Insert, `'U'` Update, `'D'` Delete   |
| `h_timestamp` | TEXT    | ISO-8601 UTC datetime of the operation      |
| `id`          | INTEGER | Mirrors `epics.id`                          |
| `name`        | TEXT    | Mirrors `epics.name`                        |
| `created_at`  | TEXT    | Mirrors `epics.created_at`                  |

---

### `task_catalog` table

Stores the mapping from a task identifier (e.g. `TASK-123`) to an Epic.
Each task identifier appears at most once.

| Column       | Type    | Notes                                        |
|--------------|---------|----------------------------------------------|
| `task_id`    | TEXT    | Primary key — the task identifier string     |
| `epic_id`    | INTEGER | Foreign key → `epics.id`                     |
| `created_at` | TEXT    | ISO-8601 UTC datetime the link was created   |

### `task_catalog_h` table (history / shadow)

Full audit trail for `task_catalog`. Populated automatically by triggers.

| Column        | Type    | Notes                                       |
|---------------|---------|---------------------------------------------|
| `h_id`        | INTEGER | Primary key, auto-incremented               |
| `h_operation` | TEXT    | `'I'` Insert, `'U'` Update, `'D'` Delete   |
| `h_timestamp` | TEXT    | ISO-8601 UTC datetime of the operation      |
| `task_id`     | TEXT    | Mirrors `task_catalog.task_id`              |
| `epic_id`     | INTEGER | Mirrors `task_catalog.epic_id`              |
| `created_at`  | TEXT    | Mirrors `task_catalog.created_at`           |

---

### `settings` table

Key-value store for user-configurable application settings.

| Column       | Type | Notes |
|--------------|------|-------|
| `key`        | TEXT | Primary key — the setting name |
| `value`      | TEXT | String-encoded value (decimal, `"true"`/`"false"`, or JSON) |
| `updated_at` | TEXT | ISO-8601 **local** datetime of the last write (human-readable audit) |

`updated_at` is the local time at which `SettingsStorage.py` wrote the row.
It is a human-readable "last edited" timestamp and is distinct from the UTC
audit timestamp `h_timestamp` written by triggers.

Known keys and their defaults (when the key is absent):

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `daily_work_target_hours` | decimal string | `"7.4"` | Daily work target in hours |
| `lunch_excluded` | `"true"` / `"false"` | `"true"` | Whether lunch is the employee's own time (excluded from hours total) |
| `lunch_duration_minutes` | integer string | `"30"` | Contractual lunch length, used for the day span and the leave projection |
| `excluded_tasks` | JSON array of strings | `"[]"` | Task identifiers excluded from hours totals |
| `always_separate_tasks` | JSON array of strings | `"[]"` | Task identifiers appearing as standalone Promark rows |

Retired key: `lunch_promark_offset_minutes` is no longer written. A non-zero
value is read once as the lunch duration when `lunch_duration_minutes` has
never been written; the row itself is left untouched.

Defaults are encoded in `SettingsStorage.SettingsRepository` — the application
works correctly with an empty `settings` table.

### `settings_h` table (history / shadow)

Full audit trail for `settings`. Populated automatically by triggers.

| Column        | Type    | Notes                                       |
|---------------|---------|---------------------------------------------|
| `h_id`        | INTEGER | Primary key, auto-incremented               |
| `h_operation` | TEXT    | `'I'` Insert, `'U'` Update, `'D'` Delete   |
| `h_timestamp` | TEXT    | ISO-8601 UTC datetime of the operation      |
| `key`         | TEXT    | Mirrors `settings.key`                      |
| `value`       | TEXT    | Mirrors `settings.value`                    |
| `updated_at`  | TEXT    | Mirrors `settings.updated_at`               |

---

## Code Structure

```
db/
    __init__.py       — package marker
    query_type.py     — QueryType enum (READ / WRITE)
    connection.py     — Connection context manager
    repository.py     — execute / fetch_one / fetch_many helpers
Storage.py            — session domain layer (sessions / sessions_h DDL)
EpicStorage.py        — Epic domain layer (epics / task_catalog DDL queries)
SettingsStorage.py    — settings domain layer (settings / settings_h queries)
Constants.py          — DB_FILE path constant
```

### Layer rules

- `Commands.py` → calls `Storage.py`, `EpicStorage.py`, and `SettingsStorage.py` only.
- `Storage.py` / `EpicStorage.py` / `SettingsStorage.py` → call `db/repository.py`
  only (except `create_schema` in `Storage.py`, which uses `Connection` directly
  to batch all DDL in one transaction).
- `db/repository.py` → calls `db/connection.py` only.
- Nothing outside `db/` imports from `db/` except `Storage.py`, `EpicStorage.py`,
  and `SettingsStorage.py`.

---

## Usage

### Startup

`create_schema()` is called automatically at the start of `main()`. No manual
setup is required.

### Commands that write data

| Command          | Storage call(s)                                          |
|------------------|----------------------------------------------------------|
| `start`          | `open_session(date, start, task)`                        |
| `lunch`          | `open_session(date, start, "Lunch")`                     |
| `pause`          | `close_session(id, end)`                                 |
| `stop`           | `close_session(id, end)`                                 |
| `restart`        | `close_session(id, end)` + `open_session(...)`           |
| `task`           | `update_session_task(id, epic)`                          |
| `epic add`       | `add_epic(name)`                                         |
| Task–Epic modal  | `add_epic(name)` (optional) + `link_task_to_epic(task_id, epic_id)` |
| `config` → Save  | `SettingsRepository.set_*()` for each changed setting    |

### Commands that read data

| Command          | Storage call(s)                                          |
|------------------|----------------------------------------------------------|
| `status`         | `get_today_sessions()`, `get_open_session()`             |
| `log`            | `read_log()`                                             |
| `promark`        | `read_log()`, `SettingsRepository.get_*()`               |
| `epic list`      | `list_epics()`                                           |
| `epic summary`   | `get_epic_summary_data(week_num, year)`                  |
| config screen    | `SettingsRepository.get_*()` (on open)                   |

---

## Limitations

- **Windows only** — the database path uses `%APPDATA%`, which is a
  Windows environment variable. The application does not run on Linux/macOS
  without changing `Constants.py`.
- **No migration from Excel** — existing `.xlsx` data is not automatically
  imported. A separate migration utility is planned as a future feature.
- **No multi-machine support** — the database file is local. Sync across
  machines is not supported.
- **Single file for all years** — all sessions are stored in one database
  regardless of age.

---

## Decisions

**2025 — SQLite replaces the Excel workbook**
- Decision: Sessions are stored in a local SQLite database.
- Rejected: The `.xlsx` workbook driven by `openpyxl`.
- Driver: `Technical` — ACID writes, SQL querying, no third-party dependency,
  and no file lock when the workbook happens to be open.

**2025 — Database in `%APPDATA%`, not beside the source**
- Decision: `%APPDATA%\TimeTracker\timetracker.db`.
- Rejected: A file in the working directory or repository.
- Driver: `Technical` — keeps real working-time data out of version control
  and survives moving or reinstalling the application.

**2025 — Week numbers derived, never stored**
- Decision: ISO week is computed from `date` at query time.
- Rejected: Storing a week column.
- Driver: `Technical` — a stored week is a second source of truth that can
  disagree with the date it came from.

**2025 — Times stored as local `HH:MM` text**
- Decision: `start` and `end` are local wall-clock strings; only audit
  timestamps are UTC.
- Rejected: UTC or epoch storage with conversion on read.
- Driver: `Business` — the values are compared against a local working day
  and a local payroll system. Storing what the user typed removes an entire
  class of conversion bugs.

**2025 — `IF NOT EXISTS` DDL instead of versioned migrations**
- Decision: `create_schema()` runs on every startup and is idempotent.
- Rejected: A migration framework with a schema version table.
- Driver: `Technical` — single-user, single-machine, additive-only schema so
  far. This will need revisiting on the first destructive schema change.

**2026 — `settings.updated_at` local, `h_timestamp` UTC**
- Decision: The two timestamps are deliberately different.
- Rejected: Making both UTC for consistency.
- Driver: `Preference` — `updated_at` is a human-readable "last edited" value
  read directly by the user; `h_timestamp` is forensic and must be absolute.

**2026 — Retired setting keys are read but never rewritten**
- Decision: `lunch_promark_offset_minutes` is read once as a fallback and
  otherwise left untouched.
- Rejected: Deleting or migrating the row.
- Driver: `Technical` — leaving it preserves the audit trail and avoids a
  one-off migration path for a single key.

---

## Notes

- `h_timestamp` in `sessions_h` is stored in UTC. User-visible times
  (`start`, `end`) remain in local `HH:MM` format as entered.
- Week numbers are derived from the date at query time using
  `datetime.isocalendar()` — they are not stored.
- `openpyxl` has been removed from `requirements.txt`. The files
  `Workbook.py`, `Summary.py`, and `Styles.py` are no longer imported and
  can be safely deleted.

---

## Related Documents

- [Documentation Index](../index.md)
- [Commands](commands.md) — all commands that read or write session data
- [Epic Catalog](epic-catalog.md) — Epics and task–Epic linking
- [Configuration](configuration.md) — the settings table in use
- [Software Standard](../operations/software-standard.md) — table, history, and trigger conventions
- [Architecture](../design/architecture.md) — the layering this schema sits behind
