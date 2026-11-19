# TimeTracker

A Python 3.12 TUI application for logging daily work sessions to a local SQLite database.

---

## Overview

TimeTracker records when you clock in and out, associates sessions with task or epic IDs, and gives you a clear picture of your day and week.

It runs as a single full-screen Textual dashboard that stays open all day. All commands are typed into the command bar at the bottom of the screen — there is no one-shot CLI mode.

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

Launch the dashboard:

```powershell
python TimeTracker.py
```

The TUI shows the active session, quick stats, today's timeline, task notes, an output log, and a command input bar — all in one screen. Press `ctrl+q` to quit.

![TUI dashboard](docs/images/TUI%20dashboard.png)

### Commands

All commands are typed into the command bar and submitted with `Enter`.

| Command | Description |
|---------|-------------|
| `start [hhmm] [epic]` | Clock in — open a new session |
| `lunch [hhmm]` | Close any open session and start a Lunch session |
| `pause [hhmm]` | Clock out temporarily |
| `resume [hhmm]` | Resume after a break, carrying the task/epic forward |
| `stop [hhmm]` | Clock out for the day |
| `status` | Refresh the cockpit panels |
| `task <epic> [-s N]` | Tag a session with a task/epic ID |
| `log [wNN]` | Open the Weekly Overview overlay |
| `epic add <name>` | Create a new Epic |
| `epic list` | List all Epics |
| `epic summary [wNN]` | Open the Weekly Overview overlay |
| `promark [wNN]` | Show Promark-style consolidated entries |
| `config` | Open the configuration screen |

The optional `hhmm` argument is a four-digit time override (e.g. `0830` for 08:30). The optional `wNN` argument selects an ISO week number (e.g. `w23`).

#### Examples

```
start
start 0830
start 0830 Epic-42
lunch 1200
resume 1230
stop 1715
task Epic-42 -s 2
log w23
promark
```

Full reference: [`docs/detailed-design/commands.md`](docs/detailed-design/commands.md)

---

## TUI Keyboard Reference

| Key | Action |
|-----|--------|
| `Enter` | Submit command |
| `↑` / `↓` | Browse command history |
| `Esc` | Clear input (or close the current overlay) |
| `Tab` / `Shift+Tab` | Cycle focus between panels |
| `w` | Open the Weekly Overview overlay |
| `ctrl+,` | Open the configuration screen |
| `ctrl+q` | Quit |
| `←` / `→` (Weekly Overview) | Navigate between weeks |

---

## Project Structure

```
TimeTracker.py        — Entry point; schema creation and TUI launch
Commands.py           — Command implementations (start, stop, pause, …)
Storage.py            — Session domain layer (the only file that knows the schema)
EpicStorage.py        — Epic domain layer
SettingsStorage.py    — Settings domain layer
Constants.py          — DB_FILE path and application constants
logger.py             — Logging configuration and crash capture
app_context.py        — Application context protocol
Printer.py            — Rich-based output formatting
Promark.py            — Promark report logic
app/                  — Textual TUI components
db/                   — Database connection and repository helpers
docs/                 — Documentation, organised by document type
features/             — Feature design documents
tests/                — pytest test suite
```

See [`docs/design/architecture.md`](docs/design/architecture.md) for the module map and layering rules.

---

## Documentation

Documentation is organised by **document type**. Start at the index:

**[`docs/index.md`](docs/index.md)** — catalogue of all documents

| Area | Documents |
|------|-----------|
| Design | [User Interface Design](docs/design/user-interface-design.md) · [Architecture](docs/design/architecture.md) |
| Detailed Design | [Commands](docs/detailed-design/commands.md) · [Configuration](docs/detailed-design/configuration.md) · [Epic Catalog](docs/detailed-design/epic-catalog.md) · [SQLite Datasource](docs/detailed-design/sqlite-datasource.md) |
| Operations | [Logging](docs/operations/logging.md) · [Software Standard](docs/operations/software-standard.md) |

Every document carries a `## Decisions` section recording why the behaviour is what it is, and whether the driver was law, business, technical constraint, or preference.

---

## Running Tests

```powershell
pytest
```

---

## Contributing

This project follows a design-first workflow. New features require an approved design document in `features/` before any implementation begins. See [`AGENTS.md`](AGENTS.md) for the full process.
