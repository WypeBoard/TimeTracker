# Feature: TUI-Only Interaction

Status: Brainstorming

## Purpose

Phase out all inline terminal prompts (e.g. `input()`, `readline`-style input) in favour of the Textual TUI. All interactive user input should happen inside the TUI, keeping the experience consistent and avoiding a split between two interaction paradigms.

## Requirements

*To be refined during brainstorming.*

- No new features may introduce inline terminal prompts.
- Existing inline prompts are identified and replaced with equivalent TUI flows.
- Commands that previously triggered a prompt should instead open a TUI screen or modal.
- The TUI remains the single point of interactive input.

## Non-Goals

- Non-interactive CLI usage (e.g. `--help`, scripted/piped commands that produce output without requiring input) is not affected.
- Batch or automation use cases that pass all arguments via command-line flags do not need a TUI replacement.

## Manual Changes

### 2026-06-23
- Decision originated from the Epic Catalog brainstorm: all interactive input must go through the TUI going forward. Inline terminal prompts are to be considered deprecated.

## Brainstorm Notes

### 2026-06-23 — Initial capture

**Motivation:**
The Epic Catalog feature raised the question of whether new interactive flows (e.g. linking a task to an Epic) should use inline prompts or the TUI. The decision was made that the TUI is the correct and only interaction surface. This feature tracks the work of making that true across the whole application.

**Open questions to resolve:**

1. **Audit** — Which existing commands or code paths currently use `input()` or similar? A full audit is needed before scope can be estimated.

2. **Replacement pattern** — What is the standard TUI pattern for replacing a prompt?
   - A modal/dialog overlay (e.g. Textual's `ModalScreen`)?
   - A dedicated full screen pushed onto the screen stack?
   - An inline widget that appears in the command output panel?

3. **Phasing** — Should this be a single migration effort, or done incrementally as each affected feature is touched?

4. **CLI-only mode** — The app can be used without the TUI (pure CLI). How should commands that currently prompt behave in CLI-only mode after the migration? Options:
   - Require all necessary arguments to be passed as flags (no prompt fallback).
   - Print an error directing the user to use the TUI.
   - Simply fail gracefully with a clear message.

## Future Ideas

- A general-purpose TUI dialog/form component that can be reused across features needing user input.
- Linting or test coverage to catch any re-introduction of `input()` calls.
