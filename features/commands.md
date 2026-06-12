# Feature: Commands — Task/Epic tagging & new CLI commands

Status: Documented

---

## Purpose

Extend the CLI with task/epic tracking per session (column F in the Time Log sheet),
and add the commands that make that data useful day-to-day:

- `start` — accept an epic directly so a separate `task` call is not needed
- `restart` — bounce between breaks without losing the current task context
- `task` — retroactively tag or correct a session's epic
- `log` — readable week view with task labels and daily totals (replaces `promark` for daily use)
- `status` — session list with `#N` numbering and inline task labels

---

## Requirements

- Column F (`Task/Epic`) added to the Time Log sheet; auto-migrated for existing workbooks.
- `start [hhmm] [epic]` — optional epic written to F on the new row.
- `restart [hhmm]` — close current session, open new one carrying the previous epic forward.
- `task <epic> [-s N]` — write epic to column F; targets open/last session by default; `-s N` targets session #N.
- `status` — session rows numbered `#1 … #N`; task label shown per row.
- `log [wNN]` — per-day session list with task labels, daily totals, week total; defaults to current week.
- `promark` kept for backward compatibility.
- Single source of truth: the Excel file.  No sidecar files.

---

## Non-Goals

- Multi-task sessions (one task per session row is intentional).
- Year-boundary handling for `wNN` (deferred).
- Time override support in the interactive prompt.

---

## Manual Changes

2026-06-11
- User confirmed design and implementation proceeded.

2026-06-12
- Implementation verified working.
- Documentation written (`docs/commands.md`); status updated to Documented.

---

## Brainstorm Notes

Design was tracked iteratively in the previous version of this file (see git history).
Key decisions reached:

- One task per session row — task switches require `pause` + `start` or `restart`.
- `restart` carries the epic automatically; no inline override flag in the same call.
- `log` replaces `promark` for daily use; `promark` remains available for sheet rebuilds.
- Column F auto-migration ensures old workbooks continue to work on upgrade.

---

## Future Ideas

- Year-boundary handling for `wNN` in `log` / `promark`.
- Weekend session display in `log`.
- Time override support in the interactive prompt.
- Autocomplete for epic IDs sourced from previous entries.