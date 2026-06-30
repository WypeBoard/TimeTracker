# Feature: Command Redesign

Status: Brainstorming

## Purpose

Rethink the full command set for a TUI-first world.

In the current application, commands are typed as free-text CLI-style strings into a command bar (e.g. `start 0830 Epic-42`). This made sense when the app was a one-shot CLI tool. Now that the TUI is the only interaction surface, the command set and its ergonomics can be redesigned from the ground up — better defaults, fewer flags to memorise, and modal flows where they make more sense than text input.

---

## Prerequisites

- **TUI-Only Mode** (`features/tui-only-mode.md`) must be `Approved` before this work begins, so the target interaction model is stable.
- **Epic Catalog** (`features/epic-catalog.md`) must be `Approved` before this work begins, so the `task` command surface can be designed against a stable data model for epics and task→epic mappings.

---

## Next Step

> **Current status:** Brainstorming
> **To reach Refinement:** Resolve the three open questions from the 2026-06-29 session (promark fate, past-week entry ergonomics, task command post-epic-catalog), and confirm whether this feature is fully blocked on epic-catalog or can proceed in parallel for the non-`task` portions.

## Requirements

> ⚠️ **Note:** This section reflects the requirements from the previous `Approved` cycle. The feature has been reverted to `Brainstorming`. These requirements are preserved as historical context and are under active review. They are **not** binding.

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

### 2026-06-29
- Status reverted from `Approved` back to `Brainstorming`.
- **Concern raised:** Removing `promark` eliminates the only mechanism for producing a formatted time-registration export. The "workplace-specific" label was too narrow — the *need* to export a weekly summary is general; only the *format* is opinionated. This decision is under review.
- **Concern raised:** Even with `log` retained, the previous approval cycle did not fully address the Monday catch-up scenario — viewing past weeks and *entering* sessions on past dates are related but distinct needs. The `start -d` flag alone may not be sufficient UX.
- **Added prerequisite:** `features/epic-catalog.md` must be `Approved` before this feature proceeds. The `task` command cannot be fully designed until the epic/task-catalog data model is stable.
- Previous Requirements and consolidated command inventory are preserved below as historical context. They are under review and not binding at `Brainstorming` status.

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

### 2026-06-29 — Reopen: promark, past-week entry, and epic-catalog dependency

**Why the feature was reverted:**

Two concerns surfaced that were not fully resolved in the previous cycle:

1. **`promark` removal** — The justification was "workplace-specific", but the underlying need — producing a structured weekly time-registration export — is a general and essential workflow. Without it, there is no mechanism to produce a summary a user can submit to an external time-tracking system. The format may be opinionated, but the function is not optional.

2. **Past-week session entry** — `log` with Left/Right navigation lets the user *view* past weeks. `start -d yyyymmdd` lets the user *add* a session to a past date. But the Monday catch-up workflow — entering a full week's sessions from memory on the following Monday — is cumbersome with today's command-bar-only entry. The interaction model for past-day entry may need more thought.

3. **Epic Catalog dependency** — The `task` command's entire surface changes once epic-catalog exists. Designing `task` command arguments, validation, and TUI flows without knowing the catalog data model is premature.

**Open questions (new round):**

1. **`promark` generalisation** — Three options:
   - *Retain as-is*: Accept it is opinionated. It works; it is tested; removing it actively harms the user's workflow.
   - *Rename to `report` or `export`*: Keep the capability but give it a more neutral name. The format stays the same for now, but the door opens for future format options.
   - *Make format configurable*: Tie into `features/configuration-view.md` — the output format is a setting, not hardcoded. Higher complexity; deferred.

2. **Past-week entry ergonomics** — Options:
   - *`start -d` is sufficient*: The user types `start 0900 TASK-123 -d 20260623` for each session. Verbose but unambiguous.
   - *Log overlay entry*: The Log overlay (opened via `log`) adds an "add session" action when browsing a past week. Overlaps heavily with `features/session-editing.md` — scope risk.
   - *`log` accepts a date argument*: `log 20260623` jumps directly to the week containing that date rather than requiring Left/Right navigation. Low-cost improvement to discoverability.

3. **`task` command post-epic-catalog** — Once the catalog exists, `task TASK-123` can auto-resolve the epic from the catalog. If the task is unknown, a TUI picker opens (per `features/epic-catalog.md` brainstorm notes). Does this change the `task` command's argument signature? Does `-s N` still make sense in that world?

4. **Sequencing with Epic Catalog** — Should this feature be fully blocked until epic-catalog reaches `Approved`, or can the non-`task` parts of the command redesign proceed independently?

---

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