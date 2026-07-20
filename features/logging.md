# Feature: Application Logging

Status: Documented

## Purpose

Capture runtime events, warnings, and errors to persistent log files so that
application crashes or unexpected behavior can be diagnosed after the fact —
including by an LLM reviewing the logs.

## Next Step

> **Current status:** Documented
> **To reach Completed:** User confirms the documentation is accurate and the feature is working as described.

## Requirements

1. **Python `logging` module** — use the standard library `logging` module.
   No third-party logging dependency is needed.

2. **Rolling weekly log files** — one log file per ISO week, rotating at
   midnight on Monday (start of new ISO week).
   - Handler: `logging.handlers.TimedRotatingFileHandler`
   - `when='W0'` (rotate on Monday), `atTime=datetime.time(0, 0)`
   - `backupCount=8` — retains ~2 months of weekly files

3. **File naming** — files live in the `logs/` directory at the project root.
   - Active file: `logs/app.log`
   - Rotated files: `logs/app.log.YYYY-MM-DD` (default suffix from handler)

4. **Log format** — machine-readable enough for LLM review:
   ```
   2026-07-20 14:35:02,123 | ERROR    | module_name | message
   ```
   Format string:
   ```
   %(asctime)s | %(levelname)-8s | %(name)s | %(message)s
   ```

5. **Log levels**:
   - `DEBUG` — detailed trace info (disabled by default; enable via env var `TT_LOG_LEVEL=DEBUG`)
   - `INFO` — startup/shutdown, schema creation, command execution
   - `WARNING` — recoverable unexpected states
   - `ERROR` — caught exceptions that degraded behavior
   - `CRITICAL` — unhandled exceptions / crash-level events

6. **Default log level** — `INFO` unless `TT_LOG_LEVEL` environment variable
   overrides it. Accepted values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

7. **Unhandled exception capture** — install a `sys.excepthook` in `TimeTracker.py`
   `main()` so that any unhandled exception is logged at `CRITICAL` level before
   the process exits.

8. **Central logger factory** — a single `logger.py` module at the project root
   exposes one function:
   ```python
   def get_logger(name: str) -> logging.Logger
   ```
   All modules obtain their logger by calling `get_logger(__name__)`. This keeps
   logger creation consistent and avoids duplicate handler registration.

9. **`logs/` directory** — created automatically on startup (same pattern as the
   `db/` directory in `Storage.py`).

10. **No console output** — logs go to file only. The TUI owns the terminal;
    a `StreamHandler` to stdout/stderr would corrupt the display.

11. **Logging placement** — add log calls to the following locations at minimum:
    - `TimeTracker.py` — startup, shutdown, unhandled exceptions
    - `Storage.py` / `EpicStorage.py` / `SettingsStorage.py` — schema creation, key read/write operations
    - `Commands.py` — each command dispatch (INFO) and any raised exceptions (ERROR)
    - `db/connection.py` and `db/repository.py` — connection errors (ERROR)

## Non-Goals

- No log viewer inside the TUI (logs are for post-mortem / LLM review only).
- No structured JSON logging (plain text is sufficient for the stated use case).
- No remote log shipping or alerting.
- No per-module log level configuration (global level via env var is enough).
- No compression of rotated files.

## Manual Changes

*(none yet)*

## Documentation Plan

| File | Action | Description |
|------|--------|-------------|
| `docs/logging.md` | Create | Describe log file location, rotation schedule, how to adjust log level, and how to read logs |

## Brainstorm Notes

User requirements captured directly:
- Logs saved to file for crash investigation
- Rolling weekly logs, new file each Monday
- Files in `logs/log<rollback>.txt` or similar
- Formatting unimportant — will be reviewed by LLM

Design decisions made during drafting:
- Python's `TimedRotatingFileHandler(when='W0')` handles Monday rotation natively.
- `logs/app.log` with date-stamped rotated copies is cleaner than embedding the
  roll number in the filename (the date is self-documenting).
- `backupCount=8` gives ~2 months retention with negligible disk use for a text log.
- `sys.excepthook` is the right hook for unhandled exceptions — it fires before
  the process exits and before any `atexit` cleanup.
- A central `logger.py` prevents modules from each configuring the root logger,
  which can cause duplicate log lines.

## Future Ideas

- Add a `logs` TUI command to show the last N lines of the current log file.
- Structured JSON mode toggled by env var for machine-parsing pipelines.
