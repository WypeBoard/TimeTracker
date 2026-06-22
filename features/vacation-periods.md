# Feature: Vacation Periods

Status: Brainstorming

## Purpose

Allow the user to register planned vacation periods in the local datasource so the application can reason about them — for example, to cross-check that an upcoming or active vacation has also been submitted through official channels (Outlook calendar).

## Requirements

_Not yet defined — initial brainstorm only._

## Non-Goals

_Not yet defined._

## Manual Changes

2026-06-22
- Feature stub created to support the Vacation cross-check requirement in `features/toast.md`.

## Brainstorm Notes

### Motivation

The Toast Notifications feature needs to compare locally registered vacation periods against today's Outlook calendar entries. This requires that vacation periods are first-class data in the application's datasource.

### Data model sketch

A vacation period likely needs at minimum:
- Start date
- End date
- Optional label / description (e.g. "Summer holiday")
- Status (planned, active, past)

### Datasource changes

- A new table or data structure must be added to store vacation periods.
- Existing datasource and command layers (`Storage.py`, `Commands.py`, `db/`) will need to be extended.
- Should follow the same patterns already established for session and task storage.

### Command layer sketch

Possible commands:
- `vacation add <start> <end> [label]` — register a new vacation period.
- `vacation list` — show all registered vacation periods.
- `vacation remove <id>` — remove a vacation period.

### Open questions

- Should vacation periods affect session tracking (e.g. suppress "no active session" warnings during a vacation)?
- Should vacation periods be visible in the TUI (Today panel, Week panel)?
- How should the Outlook cross-check identify a matching Outlook event — by date range overlap, keyword match, or both?
- Should the cross-check warn once per vacation period, or on every background tick?

## Future Ideas

- Integrate vacation display into the TUI Week panel.
- Suppress "no active session" toasts automatically during an active vacation period.
- Sync vacation periods bidirectionally with Outlook (out of scope for initial implementation).
