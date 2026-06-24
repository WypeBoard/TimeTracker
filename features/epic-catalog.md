# Feature: Epic Catalog

Status: Brainstorming

## Purpose

Provide a way to define and manage Epics within TimeTracker. Each task logged in the system should be associated with an Epic, allowing the summary panel to group and report time by Epic. Because a task identifier (e.g. `TASK-123`) always belongs to the same Epic, the mapping is stored centrally so users never have to repeat themselves when logging time against a known task.

## Requirements

*To be refined during brainstorming.*

- A new `epic` command to create and manage Epics.
- An Epic has at minimum a unique identifier/key and a display name.
- A task catalog that maps task identifiers to Epics (e.g. `TASK-123 → Epic: Platform`).
- When logging time against a task, the system looks up the Epic automatically from the task catalog.
- The summary panel should be able to group/display logged time by Epic.
- The task–Epic mapping should be persistent (stored in the database).

## Non-Goals

*To be refined during brainstorming.*

- Epics are not hierarchical (no sub-epics at this stage).
- No external system integration (e.g. Jira) for syncing Epics or tasks.
- No time tracking directly against an Epic without a task.

## Manual Changes

### 2026-06-23
- Inline terminal prompts are explicitly out of scope and to be considered deprecated going forward. All interactive user input must go through the TUI. This applies to the `task <task-id>` flow and any other interaction this feature introduces.

## Brainstorm Notes

### 2026-06-23 — Initial capture

**Background context:**
- The app already tracks time against task identifiers (e.g. `TASK-123`).
- Currently there is no grouping concept above the task level.
- The summary panel would benefit from an Epic-level rollup.

**Open questions to resolve:**

1. **Epic identifier format** — Should Epics have a short key (e.g. `PLATFORM`) and a long name (e.g. "Platform Team"), or just a free-text name?

2. **Task catalog — implicit vs explicit registration** — Two possible approaches:
   - *Explicit*: The user must run a command to register `TASK-123 → PLATFORM` before logging time against it. The system rejects unknown tasks.
   - *Implicit / lazy*: The first time a task is logged, the user is prompted (or required via flag) to specify its Epic. Subsequent logs auto-resolve.
   - *Soft enforcement*: Tasks without an Epic are allowed but flagged as "unlinked" in the summary.

3. **Command surface** — Possible sub-commands under `epic`:
   - `epic add <key> <name>` — create a new Epic
   - `epic list` — list all defined Epics
   - `epic remove <key>` — remove an Epic (what happens to linked tasks?)

   **`task <task-id>` command (2026-06-23):**
   Running `task TASK-321` when the task is not yet registered opens an interactive **TUI screen** (not an inline terminal prompt) that:
   - Displays all existing Epics so the user can select one to link the task to.
   - Offers an option to define a brand-new Epic inline (without leaving the view).
   - Saves the task→Epic mapping on confirmation.

   If the task is already registered, the same view opens in an "edit/re-link" mode showing the current Epic association.

   **Decided (2026-06-23): All interaction is TUI-only.** Inline terminal prompts are phased out. The `task` command must open a TUI screen — no readline/input() style prompts are acceptable.

4. **Retroactive linking** — If a task has already been logged without an Epic, should the user be able to link it after the fact and have historical entries updated?

5. **Summary panel impact** — The summary panel currently shows per-task totals. The new view would add an Epic-level grouping. Should this replace or augment the existing view?

6. **Storage** — Two new tables seem natural:
   - `epics(id, key, name, created_at)`
   - `task_catalog(task_id, epic_id, created_at)`  ← links a task identifier to an Epic

7. **Enforcement strictness** — Should the app hard-block logging time against a task with no Epic, or allow it with a warning?

## Future Ideas

- Epic-level reporting (hours per sprint/week grouped by Epic).
- Bulk import of task→Epic mappings (e.g. from a CSV).
- Epic archiving (hide from active lists without deleting history).
- Color-coding Epics in the TUI for quick visual identification.
