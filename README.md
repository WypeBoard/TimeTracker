# TimeTracker

A Python 3.12 CLI/TUI application for logging daily work sessions to a local SQLite database.

---

## Overview

TimeTracker records when you clock in and out, associates sessions with task or epic IDs, and gives you a clear picture of your day and week. It runs in two modes:

- **One-shot CLI** — run a command, get output, exit.
- **Interactive TUI** — a full-screen Textual dashboard that stays open all day.

Data is stored in a SQLite database at `%APPDATA%\TimeTracker\timetracker.db`. The directory and schema are created automatically on first run.

> **Platform note:** The database path uses the Windows `%APPDATA%` environment variable. The application currently targets Windows only.

---

## Requirements

- Python 3.12+
- Dependencies listed in `requirements.txt`:
  - `rich >= 13.0`
  - `textual >= 0.60`

---

## Installation

```powershell
git clone <repo-url>
cd TimeTracker
pip install -r requirements.txt
```

For development (adds `pytest`):

```powershell
pip install -r requirements-dev.txt
```

---

## Usage

### Interactive TUI

Run with no arguments to launch the full-screen dashboard:

```powershell
python TimeTracker.py
```

The TUI shows today's sessions, a week overview, a task summary, progress bars, an output log, and a command input bar — all in one screen. Press `ctrl+q` to quit.

![TUI dashboard](docs/images/TUI%20dashboard.png)

### CLI Commands

All commands follow the pattern `python TimeTracker.py <command> [args]`.

| Command | Description |
|---------|-------------|
| `start [hhmm] [epic]` | Clock in — open a new session |
| `pause [hhmm]` | Clock out temporarily |
| `resume [hhmm]` | Resume after a break, carrying the task/epic forward |
| `stop [hhmm]` | Clock out for the day and show a day summary |
| `status` | Show today's sessions and estimated leave time |
| `task <epic> [-s N]` | Tag a session with a task/epic ID |
| `log [wNN]` | Show the full week log (default: current week) |
| `promark [wNN]` | Show Promark-style consolidated entries |

The optional `hhmm` argument is a four-digit time override (e.g. `0830` for 08:30). The optional `wNN` argument selects an ISO week number (e.g. `w23`).

#### Examples

```powershell
python TimeTracker.py start
python TimeTracker.py start 0830
python TimeTracker.py start 0830 Epic-42
python TimeTracker.py pause
python TimeTracker.py resume 1150
python TimeTracker.py stop 1715
python TimeTracker.py status
python TimeTracker.py task Epic-42
python TimeTracker.py task Epic-11 -s 2
python TimeTracker.py log
python TimeTracker.py log w23
python TimeTracker.py promark
python TimeTracker.py promark w21
```

---

## TUI Keyboard Reference

| Key | Action |
|-----|--------|
| `Enter` | Submit command |
| `↑` / `↓` | Browse command history |
| `Esc` | Clear input (or close Log overlay) |
| `l` | Open the Log overlay |
| `Tab` / `Shift+Tab` | Cycle focus between panels |
| `ctrl+q` | Quit |
| `←` / `→` (Log overlay) | Navigate between weeks |

---

## Project Structure

```
TimeTracker.py        — Entry point; CLI argument parsing and TUI launch
Commands.py           — Command implementations (start, stop, pause, …)
Storage.py            — Session domain layer (the only file that knows the schema)
Constants.py          — DB_FILE path and application constants
app_context.py        — App context for CLI mode
Printer.py            — Rich-based output formatting
Promark.py            — Promark report logic
app/                  — Textual TUI components
db/                   — Database connection and repository helpers
docs/                 — Feature documentation
features/             — Feature design documents
tests/                — pytest test suite
```

---

## Documentation

Detailed documentation lives in the `docs/` directory:

- [`docs/commands.md`](docs/commands.md) — Full CLI command reference
- [`docs/tui.md`](docs/tui.md) — TUI layout, panels, and keyboard reference
- [`docs/sqlite-datasource.md`](docs/sqlite-datasource.md) — Database schema and storage layer

---

## Running Tests

```powershell
pytest
```

---

## Contributing

This project follows a design-first workflow. New features require an approved design document in `features/` before any implementation begins. See [`AGENTS.md`](AGENTS.md) for the full process.
