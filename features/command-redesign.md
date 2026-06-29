# Feature: Command Redesign

Status: Approved

## Purpose

Rethink the full command set for a TUI-first world.

In the current application, commands are typed as free-text CLI-style strings into a command bar (e.g. `start 0830 Epic-42`). This made sense when the app was a one-shot CLI tool. Now that the TUI is the only interaction surface, the command set and its ergonomics can be redesigned from the ground up — better defaults, fewer flags to memorise, and modal flows where they make more sense than text input.

---

## Prerequisites

- **TUI-Only Mode** (`features/tui-only-mode.md`) must be `Approved` before this work begins, so the target interaction model is stable.

---

## Requirements

- Commands: `start`, `stop`, `resume`, `task`, `log`, `help`.
- `add` is a permanent alias for `start`; `pause` is a permanent alias for `stop`. Both aliases are fully supported and appear alongside their primary names in the `help` overlay.
- `start` accepts an optional `-d yyyymmdd` flag to open a session on a date other than today. `stop` does **not** accept `-d` — a forgotten open session on a past day requires direct database correction.
- `resume` accepts an optional `hhmm` time argument; no `-d` flag.
- `log` is retained. It opens the full-screen Log overlay (with Left/Right arrow navigation for past weeks). It is the only command-level access to previous-week history.
- `task` retains the `-s N` flag until inline session editing (`features/session-editing.md`) is implemented.
- `help` opens a full-screen overlay listing all commands and their aliases. No keyboard shortcut — `Ctrl+H` was considered but is reserved for backspace across terminals.
- On application startup, the Output panel displays a short hint: `Type 'help' for available commands.`
- `restart`, `status`, and `promark` are removed. `promark` is workplace-specific and not general enough to retain.

## Non-Goals

- Changes to the underlying storage layer or data model are out of scope unless forced by command redesign decisions.
- UI layout changes are covered by `features/ui-layout-redesign.md`.

## Manual Changes

### 2026-06-26
- Created from the split of `tui-only-interaction.md`.
- User flagged `features/session-editing.md` as a candidate for merging into this feature, because session editing is fundamentally about how the user issues corrections via the TUI command surface.
- **Decision (2026-06-26):** Session editing remains a separate feature. The scope of inline editing (panel row selection, edit mode, keyboard interaction, validation) is large enough to warrant its own design cycle, independent of the command-set redesign. The two features should be sequenced — command redesign first, then session editing builds on top of the stable command model. The `task -s N` flag stays in scope here as a candidate for removal *only* if session editing is approved and implemented before this feature closes.
- **Decision (2026-06-26):** `log` is retained — it is the only command-level path to previous-week history in the Log overlay.
- **Decision (2026-06-26):** `promark` is removed — it is workplace-specific and not a general-purpose feature.
- **Decision (2026-06-26):** `stop -d` is dropped. A forgotten open session on a past day is treated as an edge case requiring direct database correction. The added Storage complexity is not justified.

## Documentation Plan

| File | Action | Description |
|------|--------|-------------|
| `docs/commands.md` | Update | Full rewrite to reflect the redesigned command set and TUI-only usage |
| `docs/tui.md` | Update | Update Commands table and keyboard reference to match new command set |

## Brainstorm Notes

### 2026-06-26 — Initial capture

**Current command inventory:**

| Command | Purpose | Notes |
|---------|---------|-------|
| `start [hhmm] [epic]` | Open a session | |
| `pause [hhmm]` | Close, intend to resume | |
| `stop [hhmm]` | Close, end of day | Prints day summary |
| `resume [hhmm]` | Close + reopen with same epic | |
| `restart [hhmm]` | Alias for resume | *Deprecated — remove* |
| `task <epic> [-s N]` | Tag a session with an epic | `-s N` is the only flag |
| `status` | Refresh Today panel | Arguably redundant in TUI |
| `log [wNN]` | Open log overlay | |
| `promark [wNN]` | Print promark table to Output | |

**Questions to resolve:**

1. **`pause` vs `stop`** — Both close the current session. The only difference is `stop` prints a day summary. In a TUI that always shows a live summary, is this distinction still useful? Or should they merge into a single `stop` that the TUI handles gracefully?

2. **`status`** — In a TUI context, `status` just refreshes the Today panel. Is this still needed as an explicit command, or does a keybinding (e.g. `r` for refresh) cover it better?

3. **`task` flag syntax** — `-s N` is a CLI-ism. In the TUI, session editing (see below) may replace this entirely. Is `-s N` still needed?

4. **Inline session editing** — `features/session-editing.md` handles the direct row-edit interaction in the Today panel. If session editing ships before this feature closes, `task -s N` can be dropped here as part of the command cleanup. If not, it stays.

5. **Discoverability** — Free-text commands require memorisation. Should some commands have dedicated keybindings or shortcut hints in the footer?

6. **Time argument format** — `0830` (four digits, no colon) is currently the only accepted format. Should this be relaxed (e.g. `8:30`, `830`) for ease of typing?

**Session editing relationship:**

`features/session-editing.md` remains a separate feature and will be sequenced after this one. Once the command model is stable, session editing builds on top of it. If session editing ships before this feature closes, the `task -s N` flag can be removed as part of the cleanup here.

---

### 2026-06-26 — User input: proposed command set

The user has sketched a target command inventory. Notes and open questions follow each entry.

| Command | Purpose | Notes |
|---------|---------|-------|
| `start [hhmm] [epic] [-d yyyymmdd]` | Open a session | `-d` allows adding a session to a previous day |
| `add [hhmm] [epic] [-d yyyymmdd]` | Alias for `start` | Routes directly to `start`; improves discoverability |
| `stop [hhmm] [-d yyyymmdd]` | Close the current session | `-d` mirrors `start` for symmetry |
| `resume [hhmm]` | Close current + reopen with same epic | No `-d` flag discussed |
| `task <epic> [-s N]` | Tag a session with an epic | `-s N` retained for now; removal deferred to session-editing feature — see `features/session-editing.md` |
| `help` | Open a help view listing all commands | New command |
| *(keybinding)* `Ctrl+H` | Shortcut to `help` | *Dropped — `Ctrl+H` is backspace in terminals* |

**Commands not yet addressed in this round** (still open from initial capture):

- `pause` — relationship to `stop` not yet resolved (merge or keep separate?)
- `status` — still a candidate for removal; a keybinding may suffice
- `log [wNN]` — retained as-is or modified?
- `promark [wNN]` — retained as-is or modified?
- `restart` — confirmed for removal

**Open questions from this session:**

1. **`-d` on `stop`** — Should `stop -d yyyymmdd` close a session on a *past* day, or does it only make sense for `start`/`add`? A past-day `stop` implies there is an open session on that date, which is an edge case. Needs validation logic discussion.

2. **`add` as alias** — Is `add` a permanent alias or a temporary bridge? Aliases can cause confusion if the documentation surface area grows. A decision to keep both permanently should be explicit.

3. **`help` view** — Is this a full-screen overlay (like `log`), a modal, or output to the Output panel? Impacts implementation scope.

4. **`Ctrl+H`** — In many terminals `Ctrl+H` sends a backspace signal. Worth verifying this is safe in Textual's key handling before committing to this binding.

5. **`pause` fate** — Not mentioned by user. Is it retained, removed, or merged into `stop`?

6. **`resume` and `-d`** — Should `resume` also accept `-d` for symmetry, or is resuming always "right now"?

---

### 2026-06-26 — User decisions on open questions

**Resolved:**

| # | Question | Decision |
|---|----------|----------|
| 2 | `add` as alias | **Permanent alias** for `start`. Both `add` and `start` are kept. The `help` overlay must list both with clear labelling so the user knows `add` routes to `start`. |
| 3 | `help` view form | **Full-screen overlay** (same pattern as the existing `log` overlay). |
| 4 | `Ctrl+H` binding | **Dropped.** `Ctrl+H` is the backspace signal across terminals — not safe to bind. No keyboard shortcut for `help`. Discoverability is handled by the startup hint instead (see below). |
| 5 | `pause` fate | **Permanent alias** for `stop`. Same rule as `add`/`start`: both names work, both appear in `help`. The edge case of an accidentally unclosed session at end of day is explicitly out of scope — it requires direct database correction. No special command will be added for this. |
| 6 | `resume -d` | **Not needed.** `resume [hhmm]` is sufficient. Resuming always means "right now (or at the given time today)". |
| 7 | `log [wNN]` | **Retained.** It is the only command-level access to previous-week history. The Log overlay's Left/Right arrow navigation handles week browsing once open. |
| 8 | `promark [wNN]` | **Removed.** Workplace-specific; not a general-purpose feature. |
| 9 | `-d` on `stop` | **Dropped.** A forgotten open session on a past day is treated as an edge case requiring direct database correction. The added Storage complexity is not justified. |

**`status`** — By the same reasoning as `promark` (the TUI panels refresh live), `status` is redundant and removed.

**Startup hint** — On application startup, the Output panel prints: `Type 'help' for available commands.` This replaces the need for a keyboard shortcut as the primary discoverability mechanism.

**All open questions resolved.** The command set is now fully drafted — see the Proposed inventory below.

---

### 2026-06-26 — Consolidated proposed command inventory

All decisions from this brainstorm round in one place.

| Command | Aliases | Arguments | Purpose | Notes |
|---------|---------|-----------|---------|-------|
| `start` | `add` | `[hhmm] [epic] [-d yyyymmdd]` | Open a new session | `-d` for past-day entry; `add` is a permanent alias |
| `stop` | `pause` | `[hhmm]` | Close the current session | `pause` is a permanent alias; no `-d` flag |
| `resume` | — | `[hhmm]` | Close current session and reopen with same epic | Always today; no `-d` |
| `task` | — | `<epic> [-s N]` | Tag a session with an epic | `-s N` retained until inline session editing ships |
| `log` | — | `[wNN]` | Open the full-screen Log overlay | Retained — primary access to previous-week history |
| `help` | — | — | Open full-screen help overlay listing all commands | Aliases listed alongside primary names; no keyboard shortcut |

**Startup behaviour:** On launch, the Output panel prints `Type 'help' for available commands.`

**Removed from the old inventory:**

| Command | Reason |
|---------|--------|
| `restart` | Deprecated alias for `resume` — removed |
| `status` | Redundant — TUI panels refresh live |
| `promark [wNN]` | Workplace-specific — not a general feature |

**Alias display rule:** Both the primary name and its alias must appear in the `help` overlay with clear labelling (e.g. `start / add`). Aliases are not second-class — they are permanent and fully supported.

## Future Ideas

- A command palette (fuzzy-search over available commands) instead of a free-text bar.
- Auto-complete / suggestions for epic names based on recent usage.
- A dedicated "quick tag" keybinding that opens an inline picker for the active session's epic.