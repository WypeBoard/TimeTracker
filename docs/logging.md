# Logging

## Purpose

TimeTracker writes a persistent application log to disk so that crashes,
unexpected behaviour, and database errors can be diagnosed after the fact.
The log file is also intended to be readable by an LLM to help trace and fix
issues.

## Current Behavior

### Log files

| Path | Description |
|------|-------------|
| `logs/app.log` | Current (active) log file |
| `logs/app.log.YYYY-MM-DD` | Rotated weekly archive files |

The `logs/` directory is created automatically on first startup alongside the
project root.

Log files rotate weekly at **midnight on Monday**. The most recent 8 weeks of
archives are retained (~2 months), after which the oldest file is deleted
automatically.

### Log format

Each line follows this structure:

```
2026-07-20 14:35:02,123 | INFO     | module.name | message
```

Fields are separated by ` | ` for easy splitting.

### Log levels

| Level | Used for |
|-------|----------|
| `DEBUG` | Detailed trace — individual DB calls (disabled by default) |
| `INFO` | Startup/shutdown, schema creation, every command invoked |
| `WARNING` | Recoverable unexpected states (e.g. session already open) |
| `ERROR` | Caught exceptions that degraded behavior; DB errors |
| `CRITICAL` | Unhandled exceptions / application crash |

Default level is **INFO**. `DEBUG` lines are not written unless explicitly enabled.

## Usage

### Adjusting the log level

Set the `TT_LOG_LEVEL` environment variable before launching the application:

```powershell
$env:TT_LOG_LEVEL = "DEBUG"
python TimeTracker.py
```

Valid values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
The value is case-insensitive. Any unrecognised value falls back to `INFO`.

### Reading the logs

Open `logs/app.log` in any text editor, or pass it to an LLM for analysis.

To view only errors and above:

```powershell
Select-String -Path logs\app.log -Pattern "\| ERROR|\| CRITICAL"
```

To view the last 50 lines:

```powershell
Get-Content logs\app.log -Tail 50
```

## Crash capture

An `sys.excepthook` is installed at application startup. Any unhandled exception
that would otherwise crash the process is logged at `CRITICAL` level (with full
traceback) before the process exits. This means crash information is always
captured even when no `try/except` block is present higher up in the call stack.

`KeyboardInterrupt` (Ctrl+C) is treated as a normal exit and is not logged as a
crash.

## What gets logged

| Module | Events logged |
|--------|--------------|
| `TimeTracker` | Startup (`INFO`), shutdown (`INFO`), unhandled exceptions (`CRITICAL`) |
| `Storage` | Schema verified/created (`INFO`), open/close/update session (`DEBUG`) |
| `EpicStorage` | Epic created (`INFO`), task linked (`INFO`), duplicate epic attempt (`WARNING`) |
| `Commands` | Every command dispatch (`INFO` or `DEBUG`), no-session warnings (`WARNING`) |
| `db.repository` | Query failures (`ERROR`) |
| `db.connection` | Connection failures, commit failures (`ERROR`) |

## Limitations

- No log viewer inside the TUI — logs are for post-mortem review only.
- No per-module log level control — a single global level applies to all modules.
- Rotated files are plain text (no compression).
- Log directory is always `logs/` relative to the project root. The path is not
  configurable.

## Decisions

- **`TimedRotatingFileHandler(when='W0')`** — Python's standard library handles
  Monday midnight rotation natively; no custom scheduling is needed.
- **File only, no console** — the Textual TUI owns the terminal. A `StreamHandler`
  to stdout/stderr would corrupt the TUI display.
- **`backupCount=8`** — ~2 months of history with negligible disk use for a
  plain-text log produced by a single daily-use application.
- **Central `logger.py`** — all modules call `get_logger(__name__)` from a single
  module. This prevents duplicate handler registration and keeps configuration
  in one place.

## Related Features

- [SQLite datasource](sqlite-datasource.md) — database layer that logging covers for errors
