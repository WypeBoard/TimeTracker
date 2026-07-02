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

## Code Structure

```
db/
    __init__.py       — package marker
    query_type.py     — QueryType enum (READ / WRITE)
    connection.py     — Connection context manager
    repository.py     — execute / fetch_one / fetch_many helpers
Storage.py            — session domain layer (sessions / sessions_h DDL)
EpicStorage.py        — Epic domain layer (epics / task_catalog DDL queries)
Constants.py          — DB_FILE path constant
```

### Layer rules

- `Commands.py` → calls `Storage.py` and `EpicStorage.py` only.
- `Storage.py` / `EpicStorage.py` → call `db/repository.py` only (except
  `create_schema` in `Storage.py`, which uses `Connection` directly to batch
  all DDL in one transaction).
- `db/repository.py` → calls `db/connection.py` only.
- Nothing outside `db/` imports from `db/` except `Storage.py` and `EpicStorage.py`.

---

## Usage

### Startup

`create_schema()` is called automatically at the start of `main()`. No manual
setup is required.

### Commands that write data

| Command          | Storage call(s)                                          |
|------------------|----------------------------------------------------------|
| `start`          | `open_session(date, start, task)`                        |
| `pause`          | `close_session(id, end)`                                 |
| `stop`           | `close_session(id, end)`                                 |
| `restart`        | `close_session(id, end)` + `open_session(...)`           |
| `task`           | `update_session_task(id, epic)`                          |
| `epic add`       | `add_epic(name)`                                         |
| Task–Epic modal  | `add_epic(name)` (optional) + `link_task_to_epic(task_id, epic_id)` |

### Commands that read data

| Command          | Storage call(s)                                          |
|------------------|----------------------------------------------------------|
| `status`         | `get_today_sessions()`, `get_open_session()`             |
| `log`            | `read_log()`                                             |
| `promark`        | `read_log()`                                             |
| `epic list`      | `list_epics()`                                           |
| `epic summary`   | `get_epic_summary_data(week_num, year)`                  |

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

## Notes

- `h_timestamp` in `sessions_h` is stored in UTC. User-visible times
  (`start`, `end`) remain in local `HH:MM` format as entered.
- Week numbers are derived from the date at query time using
  `datetime.isocalendar()` — they are not stored.
- `openpyxl` has been removed from `requirements.txt`. The files
  `Workbook.py`, `Summary.py`, and `Styles.py` are no longer imported and
  can be safely deleted.

---

## Related Features

- `commands.md` — documents all CLI commands that read/write session data.
- `docs/epic-catalog.md` — Epic Catalog feature: Epics and task–Epic linking.
