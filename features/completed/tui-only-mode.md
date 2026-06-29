# Feature: TUI-Only Mode

Status: Documented

## Purpose

Make the Textual TUI the single, exclusive interaction surface for the application.
The old one-shot CLI mode (running `python TimeTracker.py start`, `python TimeTracker.py stop`, etc. from a terminal) is removed. Users open the TUI and never leave it.

This is a direct evolution of the original `tui-only-interaction.md` scope, narrowed to the *interaction model* question only (layout and command redesign are tracked separately).

---

## Next Step

> **Current status:** Documented
> **To reach Completed:** User confirms the documentation is accurate and the feature is working as described.

---

## Requirements

- Launching `python TimeTracker.py` (no arguments) always opens the TUI.
- Launching with command arguments (e.g. `python TimeTracker.py start`) is no longer supported. The argument-parsing block in `TimeTracker.py` is removed entirely.
- All CLI-dispatching code in `TimeTracker.py` (the `sys.argv` switch and any supporting helpers used exclusively by that path) is deleted — hard removal, no deprecation.
- All unused code revealed by that removal is also deleted. Nothing is left behind "just in case".
- All interactive workflows — starting, stopping, pausing, resuming, tagging, reviewing — are performed inside the TUI.
- Existing inline `input()` / `readline`-style prompts are removed; no new ones may be introduced.
- `--help` / `-h` flags are also removed: they existed only to describe CLI commands that are now gone.
- No automation escape hatch is provided. There is no `--no-tui` / `--batch` flag. If a scripted use case emerges it must be designed separately.

## Non-Goals

- This feature does not change the *shape* of commands or the TUI layout — those are covered by **command-redesign** and **ui-layout-redesign**.
- No deprecation warnings or redirect messages. The old CLI path simply does not exist.

## Manual Changes

### 2026-06-26
- Spawned from `tui-only-interaction.md`, which has been superseded by three focused features.
  Previous brainstorm notes in that document remain as context.

### 2026-06-26 — Open questions resolved

| # | Question | Decision |
|---|----------|----------|
| 1 | Hard removal vs. deprecation | **Hard removal.** The application is Alpha; breaking changes are expected. No deprecation period. |
| 2 | Automation escape hatch | **None.** Remove all unused code revealed by the CLI removal. No `--no-tui` / `--batch` flag. |
| 3 | Entry point cleanup scope | **This feature.** `command-redesign` is ready and waiting for this feature; it does not impose requirements here. Entry point cleanup belongs entirely to this feature. |

## Documentation Plan

| File | Action | Description |
|------|--------|-------------|
| `docs/commands.md` | Update | Remove the one-shot CLI usage section; clarify that all commands are entered via the TUI command bar |
| `docs/tui.md` | Update | Update Purpose section to reflect TUI-only entry point |

## Brainstorm Notes

### 2026-06-26 — Initial capture

**Current state:**  
`docs/commands.md` still describes `python TimeTracker.py <command>` as the primary usage pattern.
`docs/tui.md` describes the TUI as an *alternative* launched when no arguments are given.
Both need to be flipped — TUI is the primary, CLI invocation is gone.

## Future Ideas

- Linting or CI check to prevent re-introduction of `input()` calls.
