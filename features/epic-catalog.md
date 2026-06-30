# Feature: Epic Catalog

Status: Refinement

## Purpose

Provide a way to define and manage Epics within TimeTracker. Each task logged in the system should be associated with an Epic, allowing the summary panel to group and report time by Epic. Because a task identifier (e.g. `TASK-123`) always belongs to the same Epic, the mapping is stored centrally so users never have to repeat themselves when logging time against a known task.

## Next Step

> **Current status:** Refinement
> **To reach Proposed:** All requirements are specific, Non-Goals are explicit, and no new ideas are being added.

Open items before Proposed:
- None. All items resolved. Ready for user review and approval.

## Requirements

### Epic management commands

- `epic add <name>` — creates a new Epic with a free-text human-readable name (e.g. `epic add "Platform Team"`). The ID is auto-assigned by the database. If an Epic with that name already exists, the command prints an error (e.g. `⚠  An Epic with that name already exists.`) and does nothing.
- `epic list` — lists all defined Epics, sorted alphabetically by name. Output goes to the Output panel (no overlay). Format: one Epic per line showing ID and name.

### Task–Epic linking

- A task catalog persistently maps task identifiers to Epics (e.g. `TASK-123 → Platform Team`).
- The same Epic lookup applies uniformly across `start`, `resume`, and `task` (including `task -s N`). There is no difference in how these commands handle the Epic association.
- When a task identifier is used, the system checks `task_catalog` for an existing Epic link.
- If the task already has a linked Epic, no further interaction is required — the label is saved immediately.
- If the task has no linked Epic, a **modal popup** is shown before the session/label is saved (see below).

#### Task–Epic modal (new task detected)

Implemented as a Textual `ModalScreen`, consistent with the existing `LogScreen` pattern.

The modal has two states:

**State 1 — Epic selection:**

```
┌─ New task: TASK-789 ──────────────────────────────────────┐
│  Select an Epic to link this task, or press Esc to skip.  │
│                                                           │
│  ► Platform Team                                          │
│    Mobile App                                             │
│                                                           │
│  [ + New epic… ]                                          │
│                                                           │
│  [↑↓] navigate   [Enter] select   [Esc] save as (Misc)   │
└───────────────────────────────────────────────────────────┘
```

- The list shows all Epics from `epic list`, sorted alphabetically.
- The `[ + New epic… ]` option is always present at the bottom.
- `↑` / `↓` navigate the list; `Enter` confirms the selection.
- Selecting an existing Epic: writes the `task_catalog` entry and closes the modal. The original command then completes.
- `Esc`: closes the modal without writing any `task_catalog` entry. The original command completes and the task is treated as `(Misc)` in the summary view.
- If no Epics have been created yet, the list shows only `[ + New epic… ]`.

**State 2 — Inline Epic creation (entered by selecting `[ + New epic… ]`):**

```
┌─ New task: TASK-789 ──────────────────────────────────────┐
│  New Epic name:                                           │
│  ┌───────────────────────────────────────────────────┐   │
│  │ Platform Team_                                    │   │
│  └───────────────────────────────────────────────────┘   │
│                                                           │
│  [Enter] create & link   [Esc] back to list               │
└───────────────────────────────────────────────────────────┘
```

- `Enter` with a non-empty name: creates the Epic in `epics`, writes the `task_catalog` entry, closes the modal. The original command then completes.
- `Enter` with an empty name: no-op (field stays open).
- If the entered name already exists: shows an inline error (`⚠  An Epic with that name already exists.`) and keeps State 2 open.
- `Esc`: returns to State 1 (the selection list).

**Virtual `(Misc)` grouping:** tasks with no `task_catalog` entry — either because the user pressed Esc, or because they were logged before this feature existed — appear under a `(Misc)` group in `epic summary`. This group is computed at query time and is not stored in the database.

### Epic summary command

- `epic summary [wNN]` — opens a full-screen overlay (same navigation pattern as `log`) showing time grouped by Epic for the target week. Defaults to the current week; `wNN` selects a specific ISO week number.

  Proposed layout:

  ```
  ┌─ Epic Summary — Week 26 — Jun 16–20, 2026 ──────────────────────┐
  │                                                                   │
  │  Platform Team                                      12:30        │
  │    TASK-123                                          7:30        │
  │    TASK-456                                          5:00        │
  │  (Misc)                                              4:15        │
  │    TASK-789                                          4:15        │
  │                                                                   │
  │  Week total:  16:45                                              │
  │                                                                   │
  │  [Esc] close   [←] prev week   [→] next week                    │
  └───────────────────────────────────────────────────────────────────┘
  ```

  - Each Epic is a header line with total hours for the week.
  - Tasks linked to that Epic are indented below it.
  - Tasks with no entry in `task_catalog` are grouped under `(Misc)`. This is a virtual group — it is not stored in the database and not returned by `epic list`.
  - Hours in base-60 clock format (`H:MM`), consistent with existing panels.

### Storage

- Two new database tables following project conventions:
  - `epics(id, name, created_at)` — Epic definitions.
  - `task_catalog(task_id, epic_id, created_at)` — links a task identifier to an Epic.
- Both tables must have corresponding `_h` shadow tables and INSERT/UPDATE/DELETE triggers, following the same pattern as `sessions` / `sessions_h`.
- All DDL belongs in `Storage.py` inside `create_schema()`.

### Existing views

- The existing Task Summary panel, Today panel, Week panel, `log`, and `promark` views remain unchanged.

## Non-Goals

- Epics are not hierarchical (no sub-epics at this stage).
- No external system integration (e.g. Jira) for syncing Epics or tasks.
- No time tracking directly against an Epic without a task.
- No `epic remove` command in this version.
- No ability to re-link a task to a different Epic in this version (v2 concern).
- No retroactive Epic assignment for historical sessions via any dedicated backfill command — tagging a session with `task -s N` applies the same (Misc auto-assignment) logic as a current session. Historical sessions that already have a task label are not re-checked.

## Manual Changes

### 2026-06-23
- Inline terminal prompts are explicitly out of scope and to be considered deprecated going forward. All interactive user input must go through the TUI. This applies to the `task <task-id>` flow and any other interaction this feature introduces.

### 2026-06-30 — Open questions resolved
- **Epic format (#1):** Free-text human-readable name only. No short key/slug.
- **Enforcement (#2, #7):** Hard implicit. Every task must have a linked Epic before time can be logged. A "Miscellaneous" Epic is an acceptable workaround for off-tasks.
- **Commands (#3):** `epic add <name>` and `epic list` only. `epic remove` is out of scope.
  - `task <task-id>` behavior: if the task already has a linked Epic → no-op. If unlinked/unknown → TUI screen to pick or create an Epic.
- **Retroactive linking (#4):** Out of scope. Enforcement is based on whether the task has a linked Epic at the time of logging, not whether it has been seen before.
- **Summary panel (#5):** A new Epic-level view is added. Existing per-task views are preserved.
- **Storage (#6):** Two tables: `epics` (epic definitions) and a relation table linking task identifiers to Epics.

### 2026-06-30 — Remaining open items resolved
- **start/resume enforcement:** The same Epic lookup applies to `start`, `resume`, and `task` (including `-s N`). All three commands behave identically with respect to Epic association.
- **Unlinked task handling:** The blocking TUI screen (pick/create Epic) is removed. Tasks with no entry in `task_catalog` are silently treated as "(Misc)" at display time. No database entry is written. The session proceeds without interruption. Previous brainstorming and requirements describing a blocking TUI screen are superseded by this decision.
- **`epic add` duplicates:** Attempting to add an Epic whose name already exists is an error. The command prints a message such as `⚠  An Epic with that name already exists.` and does nothing.
- **`epic list` format:** Alphabetical by name.
- **`task -s N` with Epic check:** Treated identically to any other task command. Tagging a closed historical session follows the same (Misc auto-assignment) logic.

### 2026-06-30 — Task–Epic modal reinstated
- The "no TUI screen" decision from the earlier session was based on a misunderstanding — user intended a panel-style popup, not a full blocking screen.
- A `ModalScreen` popup (same pattern as `LogScreen`) is reinstated. It appears when a task identifier has no entry in `task_catalog`.
- The modal is two-state: Epic selection list, and inline Epic creation input.
- Pressing Esc from the selection list skips linking; the task is saved and treated as `(Misc)` in `epic summary`.
- The "(Misc)" virtual group is preserved for tasks that skip the modal or predate the feature.

## Testing Notes

Tests follow the established project pattern: command/storage-layer behaviour is covered by integration tests using `RecordingContext` and an isolated SQLite database (see `tests/test_smoke.py`). TUI/modal behaviour requires the Textual testing infrastructure tracked separately in `features/textual-testing.md`.

### Testable without Textual (command + storage layer)

| Area | What to test |
|------|-------------|
| `epic add` | Epic is created; `epic list` returns it. |
| `epic add` duplicate | Error message returned; no new row written. |
| `epic list` | Returns Epics alphabetically; empty list when none exist. |
| `task_catalog` lookup | Known task → no modal triggered (label saved immediately). |
| `epic summary` query | Returns correct Epic → task grouping; unlinked tasks appear in `(Misc)`. |
| `epic summary` empty week | Renders without error when no sessions exist. |

### Requires Textual testing infrastructure (`features/textual-testing.md`)

| Area | What to test |
|------|-------------|
| Modal opens | Unknown task via `task`, `start`, or `resume` triggers the modal. |
| Modal State 1 — select Epic | Selecting an existing Epic writes `task_catalog` and completes the command. |
| Modal State 1 — `[ + New epic… ]` | Transitions to State 2. |
| Modal State 2 — create Epic | Valid name creates Epic, writes `task_catalog`, closes modal. |
| Modal State 2 — duplicate name | Inline error shown; modal stays open. |
| Modal State 2 — Esc | Returns to State 1. |
| Modal State 1 — Esc | Task saved; no `task_catalog` entry; task appears as `(Misc)` in summary. |
| `epic summary` overlay | Opens, navigates weeks with `←`/`→`, closes with `Esc`. |

## Documentation Plan

| File | Action | Description |
|------|--------|-------------|
| `docs/commands.md` | Update | Add `epic add`, `epic list`, and `epic summary` to the command reference; update `task` to describe Epic enforcement behaviour |
| `docs/epic-catalog.md` | Create | New doc describing Epics: purpose, `epic` commands, task–Epic linking, the `epic summary` overlay, and storage layout |
| `docs/tui.md` | Update | Add `epic add`, `epic list`, `epic summary` to the commands table; document the task–Epic modal (two states, keyboard nav, Esc behaviour) and the `(Misc)` virtual grouping |
| `docs/sqlite-datasource.md` | Update | Document the `epics`, `epics_h`, `task_catalog`, and `task_catalog_h` tables and their triggers |

## Brainstorm Notes

### 2026-06-23 — Initial capture

**Background context:**
- The app already tracks time against task identifiers (e.g. `TASK-123`).
- Currently there is no grouping concept above the task level.
- The summary panel would benefit from an Epic-level rollup.

**Open questions (resolved 2026-06-30):**

1. **Epic identifier format** — ~~Should Epics have a short key (e.g. `PLATFORM`) and a long name (e.g. "Platform Team"), or just a free-text name?~~
   **Resolved:** Free-text human-readable name only. No short key.

2. **Task catalog — implicit vs explicit registration** — ~~Two possible approaches...~~
   **Resolved:** Hard implicit. All tasks must have an Epic. A "Miscellaneous" Epic covers off-tasks.

3. **Command surface** — ~~Possible sub-commands under `epic`...~~
   **Resolved:**
   - `epic add <name>` — create a new Epic
   - `epic list` — list all defined Epics
   - No `epic remove` in this version.
   - `task <task-id>`: if task already has a linked Epic → no-op. If unlinked/unknown → TUI screen to pick or create an Epic.

4. **Retroactive linking** — ~~If a task has already been logged without an Epic, should the user be able to link it after the fact?~~
   **Resolved:** No. Epic check is made at time-of-logging. Historical unlinked sessions remain as-is.

5. **Summary panel impact** — ~~Should Epic grouping replace or augment the existing view?~~
   **Resolved:** A new Epic-level view is added. Old views stay.

6. **Storage** — Two new tables:
   - `epics(id, name, created_at)` — Epic definitions
   - `task_catalog(task_id, epic_id, created_at)` — links a task identifier to an Epic

7. **Enforcement strictness** — See #2.

## Future Ideas

- Epic-level reporting (hours per sprint/week grouped by Epic).
- Bulk import of task→Epic mappings (e.g. from a CSV).
- Epic archiving (hide from active lists without deleting history).
- Color-coding Epics in the TUI for quick visual identification.
- Ability to re-link a task to a different Epic (v2).