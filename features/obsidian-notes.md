# Feature: Obsidian Notes Integration

Status: Refinement

## Purpose

Allow TimeTracker to interact with the user's personal Obsidian work-tracking vault
so that task documents are created and kept structurally consistent automatically —
without the user having to remember to do it.

The vault tracks software development tasks (called **Opgaver**) week-by-week.
TimeTracker already knows *which tasks are being worked on* and *which week it is* — this
feature uses that knowledge to automate the bookkeeping that today requires manual edits
in Obsidian.

The two automated operations, triggered whenever a session is started:

1. **Create an Opgave file** — if no `Opgaver/{epic_key}.md` exists for the session's
   epic, create one using the epic's description and the current ISO week.
2. **Sync breadcrumb navigation** — if the file already exists, ensure the
   `## breadcrumb navigation` section contains a `[[NN]]` link for every week in the
   `uge` frontmatter array. Entries are only ever added, never removed.

Additionally, a **read-only Opgave panel** is displayed in the TUI showing the content
of the active session's Opgave file. This panel is always read-only.

Status files (`Status/2026/NN.md`) are **never written to** — Obsidian's Dataview query
auto-discovers tasks from `uge` frontmatter, so they require no maintenance.

---

## Prerequisites

Both prerequisites are now complete:

- **Epic Catalog** — `Completed` (`features/completed/epic-catalog.md`)
- **Configuration View** — `Documented` (`features/configuration-view.md`)

The `vault_path` setting will be added to the existing Configuration screen as part of
this feature (see Requirements — Configuration screen).

---

## Vault Structure (Nykredit vault — documented 2026-06-29)

### `Opgaver/` — Task files

One file per ticket. Named by Jira-style epic key: `EVD-2213.md`, `EVD-4325.md`, etc.

**YAML frontmatter:**
```yaml
---
beskrivelse: Short human-readable description of the task
state: Todo | Awaiting | Complete
uge:
  - 2026-W21
  - 2026-W22
---
```

- `beskrivelse` — display label used by Dataview queries in Status files.
  **Source:** the epic's description from the Epic Catalog.
- `state` — lifecycle state. Known values: `Todo`, `Awaiting`, `Complete`.
  Always initialised to `Todo` on file creation. **Never written by this integration
  after creation** — state transitions are manual in Obsidian.
- `uge` — list of ISO week identifiers (`YYYY-Www`). **This is the integration backbone.**
  It is the only field that connects a task to a week. The integration reads this field
  to sync breadcrumbs and writes it to add the current week when a session starts.

**Body sections (in order):**
- `## breadcrumb navigation` — manual `[[NN]]` wiki-links back to Status files.
  Derived from `uge`; kept in sync by this integration (additive only).
- `## Opgave` — free-text task description (left empty on creation).
- `## Tasks` — Markdown checklist (left empty on creation).
- `## Accept` — acceptance criteria (left empty on creation).

### `Status/2026/` — Weekly overview files

Auto-managed by Obsidian. Created from the `Ugenlig.md` Templater template (see below).
**This integration never reads or writes Status files.**

**Confirmed Ugenlig.md template:**
```
<%*
const weekNum = tp.date.now("WW")
const year = tp.date.now("GGGG")
const week = `${year}-W${weekNum}`
const startOfWeek = tp.date.now("DD. MMM", 0, tp.date.weekday("YYYY-MM-DD", 1))
const endOfWeek = tp.date.now("DD. MMM YYYY", 0, tp.date.weekday("YYYY-MM-DD", 7))
const prevWeekNum = String(parseInt(weekNum) - 1).padStart(2, "0")
const nextWeekNum = String(parseInt(weekNum) + 1).padStart(2, "0")
_%>

## <% week %> — <% startOfWeek %> til <% endOfWeek %>

← [[<% prevWeekNum %>|Uge <% prevWeekNum %>]] | [[<% nextWeekNum %>|Uge <% nextWeekNum %>]] →

```dataview
TABLE beskrivelse AS "Beskrivelse", state AS "State"
FROM "Opgaver"
WHERE contains(uge, "<% week %>")
SORT file.name ASC
```

---

## Non-tracked opgaver

| Opgave | Beskrivelse | State |
| ------ | ----------- | ----- |
|        |             |       |

Because the Dataview query uses `contains(uge, "<week>")`, adding a week to an Opgave
file's `uge` array is sufficient to make the task appear in that week's Status view.
No edit to the Status file is ever needed.

### The dual-linking contract

```
Opgave file (EVD-4325.md)
  frontmatter.uge: [2026-W25, 2026-W26]   ← source of truth (written by this integration)
  breadcrumb: [[25]], [[26]]               ← derived; synced by this integration (additive)

Status file (25.md)
  Dataview: WHERE contains(uge, "2026-W25")
  → discovers EVD-4325 automatically — no write needed
```

---

## Requirements

### Configuration screen — vault path

- A **Vault path** field is added to the existing Configuration screen (opened via
  `config` command or `Ctrl+,`).
- The field accepts a plain file-system path string (e.g. `C:\Users\...\Vault`).
- It is stored in the `settings` table under the key `vault_path`.
- The field is optional — leaving it blank disables the integration silently.
- Validation: if a path is entered, it must point to an existing directory. An invalid
  path shows an inline error and blocks Save.

### Vault folder layout

The integration uses two hard-coded subfolders under `vault_path`:

| Folder | Purpose | Contents |
|--------|---------|----------|
| `{vault_path}/tasks/` | Task (Opgave) files | One `.md` file per task identifier |
| `{vault_path}/epics/` | Epic documentation files | One `.md` file per epic name |

- Both folders are created automatically if they do not exist when a sync runs.
- The `vault_path` directory itself must already exist (validated on config save).
- Folder names are hard-coded for v1. Configurable paths are a future enhancement.

### Filename sanitisation

Task identifiers and epic names are used as filenames. A **replacement map** handles
special characters:

```python
# Replacement map: character → replacement string.
# Empty string means "remove the character".
# Characters not in this map are kept as-is.
FILENAME_REPLACEMENTS: dict[str, str] = {
    "§": "paragraph",
    "/": "",
    "\\": "",
    ":": "",
    "*": "",
    "?": "",
    '"': "",
    "<": "",
    ">": "",
    "|": "",
}
```

**Algorithm:**
1. For each character in the input string:
   - If it has an entry in `FILENAME_REPLACEMENTS` → substitute the replacement value
     (which may be empty, effectively removing the character).
   - Otherwise → keep as-is (spaces, accented characters, hyphens, etc. preserved).
2. Strip leading/trailing whitespace from the result.
3. If the result is empty after sanitisation → abort sync with a warning.

Examples:
- `EVD-4325` → `EVD-4325.md`
- `Valuation principle §14` → `Valuation principle paragraph14.md`
- `Mortgage valuation` → `Mortgage valuation.md`

All replaceable characters live in a single `dict`. Characters mapped to `""` are
removed; characters mapped to a non-empty string get a meaningful substitution. The
map is stored as a Python `dict` in code. A future iteration will expose it as a
configurable mapping in the Configuration screen (stored as JSON in the `settings`
table).

### File sync — triggered on session start

When a session is started (`cmd_start`), after the session is written to the database:

1. If `vault_path` is not configured → skip silently.
2. If the session's `task` field is empty → skip silently.
3. If the session's `task` is in `excluded_tasks` or `always_separate_tasks` → skip
   silently. These are administrative task identifiers (e.g. `Lunch`, `commute`, `Sick`,
   `Doctor`, `Bank meeting`) that have no associated ticket.
4. Otherwise → run the sync:
   a. Look up the task's epic via `task_catalog` → `epics`. If the task has an epic
      link, use the epic `name` as `beskrivelse`. If no epic link exists, `beskrivelse`
      is an empty string.
   b. Derive the current ISO week (`YYYY-Www`) from the session date.
   c. Sanitise the task identifier to produce a safe filename.
   d. If `{vault_path}/tasks/{sanitised_task}.md` does not exist → **create** it.
   e. If the file exists → **sync** `uge` and `## breadcrumb navigation`.
   f. If the task has an epic link and `{vault_path}/epics/{sanitised_epic_name}.md`
      does not exist → **create** the epic file.
5. Failure at any point in step 4 must **not** prevent the session from being recorded.
   A warning is emitted via `ctx.warning()`; the session is committed regardless.

### Create task file

New file written to `{vault_path}/tasks/{sanitised_task}.md`:

```markdown
---
beskrivelse: {epic name, or empty string if no epic link}
state: Todo
uge:
  - {current ISO week}
---

## breadcrumb navigation
- [[{two-digit week number}]]

## Opgave

## Tasks

## Accept
```

- Two-digit week number: extracted from ISO week, padded with leading zero
  (`2026-W07` → `07`).
- Written atomically via a `.tmp` file and `os.replace()`.
- File encoding: UTF-8.

### Create epic file

New file written to `{vault_path}/epics/{sanitised_epic_name}.md`:

```markdown
# {epic name}
```

- Created only once — the integration never updates epic files after creation.
- Minimal template (heading only). A richer template will be designed in a future
  iteration.
- Written atomically via `.tmp` + `os.replace()`.
- File encoding: UTF-8.

### Sync operation (existing task file)

1. Read the file. Parse YAML frontmatter using PyYAML.
2. If the current ISO week is not in `uge` → append it. Write the `uge` block back
   via string manipulation (to preserve key order and formatting).
3. Extract two-digit week numbers from the full `uge` list.
4. Parse `## breadcrumb navigation` for existing `[[NN]]` entries.
5. Append any week numbers present in `uge` but missing from the breadcrumb section,
   maintaining sorted order.
6. Write the file back atomically only if any change was made.
7. If the `## breadcrumb navigation` section is missing entirely → create it before
   the first body section (`## Opgave`) and add entries.
8. If `uge` is empty → no-op.
9. If parse fails at any step → abort without writing; emit `ctx.warning()`.

### Read-only Opgave panel

- A new `OpgavePanel` widget is always present in the TUI layout, between the top
  panel row (`TodayPanel` / `WeekPanel`) and `TaskSummaryPanel`.
- The panel uses `height: 1fr` and takes the remaining vertical space.
- The panel is **always read-only**. No input, no edit mode.
- **No user action is needed to show the panel** — it appears automatically whenever a
  session with a task is active. The user does not configure or toggle it.

#### Content displayed

| Condition | Panel shows |
|-----------|-------------|
| No active session | *"No active session"* placeholder |
| Active session, task is empty | *"No task set"* placeholder |
| Active session, task is administrative (excluded/always-separate) | *"No task file for this task"* placeholder |
| `vault_path` not configured | *"Vault not configured"* placeholder |
| Task file missing after sync attempt failed | Warning message |
| File exists | Task identifier + epic name header, then `## Opgave`, `## Tasks`, `## Accept` content |

- `## breadcrumb navigation` is never shown in the panel.
- Empty sections are shown as empty — no placeholder text is injected into blank
  sections.

#### Refresh behaviour

The panel refreshes on the same hook as all other session panels
(`refresh_session_panels()` in `TimeTrackerApp`). It does not watch the file system.

### Dependency

- PyYAML (`pyyaml`) added to `requirements.txt`.

---

## Non-Goals

- **No Status file writes** — Dataview auto-discovers tasks; Status files are never
  touched by this integration.
- **No in-app editing** — the Opgave panel is strictly read-only. In-app editing is a
  separate future feature.
- **No dedicated epic filter setting** — filtering is handled by the existing
  `excluded_tasks` and `always_separate_tasks` settings. Epics in either list are
  administrative tasks (e.g. `Lunch`, `Omsorgsdage`) and do not get Opgave files.
- **No file system watching** — the panel re-reads the file on session change only; it
  does not poll or watch for external edits.
- **No Obsidian process integration** — TimeTracker does not communicate with Obsidian
  directly. It only reads and writes plain files.
- **No bulk backfill** — the integration only acts on session start. It does not
  retroactively scan past sessions to create or update missing Opgave files.
- **No `state` management** — the `state` frontmatter field is set to `Todo` at creation
  and never written again. State transitions remain manual in Obsidian.

---

## Open Questions

~~1. **Trigger**~~ — **Resolved:** Auto-triggered on session start.

~~2. **Ticket ID source**~~ — **Resolved (revised 2026-07-21):** The session's **task
identifier** (the value stored in the `task` column of `sessions`) is used as the
Opgave filename. This is the string the user types in `start <task>` or sets via the
`task` command. The Epic Catalog is used only to determine *whether* the task is linked
to an epic (and therefore eligible for sync) — it does not provide the filename.

~~3. **New file template — `beskrivelse`**~~ — **Resolved (revised 2026-07-21):** The
`epics` table has no `description` column — it only stores `name`. The `beskrivelse`
frontmatter field is populated from the **epic name** (the group label the task is
linked to via `task_catalog`). If the task has no epic link, `beskrivelse` is left as
an empty string. Full task documentation lives in the Opgave file itself (in the vault
filesystem), not in the database.

~~4. **Breadcrumb sync direction**~~ — **Resolved:** Additive only. Entries are never
removed.

~~5. **Vault path**~~ — **Resolved:** Stored in the `settings` table. Hard dependency
on Configuration View.

~~6. **YAML frontmatter parsing**~~ — **Resolved:** PyYAML (`pyyaml`) is acceptable.
Added to `requirements.txt`. Used for reading; `uge` block written back via string
manipulation to avoid key reordering / reformatting.

~~7. **Write safety**~~ — **Resolved:** Atomic writes via `os.replace()` are confirmed.
No external library needed.

~~8. **`uge` update on session start**~~ — **Resolved:** All three cases confirmed:
  - File does not exist → create with current week.
  - File exists, current week already in `uge` → sync breadcrumb only.
  - File exists, current week missing from `uge` → add week to `uge`, then sync breadcrumb.

~~9. **Epics without a ticket ID pattern**~~ — **Resolved:** No dedicated filter setting.
The `excluded_tasks` and `always_separate_tasks` settings identify administrative tasks
(e.g. `Lunch`, `Omsorgsdage`, `commute`, `Sick`). These are **task identifiers** checked
against the session's `task` field — not epic names. Sessions whose task is in either
list are skipped silently. All other sessions with a non-empty task trigger the
integration automatically.

~~10. **Vault path setting key**~~ — **Resolved:** Key name is `vault_path`.
Kept generic — not Obsidian-specific, allowing the setting to be repurposed if needed.

~~11. **Folder structure within the vault**~~ — **Resolved (2026-07-29):** Hard-code
default subfolder names for the first build. The integration uses
`{vault_path}/tasks/` for Opgave files and `{vault_path}/epics/` for epic-level
documentation. No custom path configuration in v1 — configurable paths are a future
enhancement. Subfolders are created automatically if missing.

~~12. **Filename sanitisation**~~ — **Resolved (2026-07-29):** Use a **replacement map**
(Python `dict`). Characters with meaningful replacements get substituted (e.g.
`§` → `paragraph`). Characters that are illegal on Windows (`/\:*?"<>|`) and have no
meaningful replacement are simply removed. The map is stored as a dict in code,
making it straightforward to expose as a configurable mapping in the Configuration
screen in a future iteration.

---

## Brainstorm Notes

### Why this is a natural fit for TimeTracker

TimeTracker already has:
- The current ISO week (it tracks sessions by date).
- The epic identifier for each session (from the Epic Catalog).
- A persistent database to store vault configuration.

The Obsidian vault's `uge` field is essentially a list of weeks a ticket was worked on.
TimeTracker already *knows* which weeks a ticket was worked on from session data. The
integration closes the loop by writing that knowledge back into the vault automatically,
so the user never has to manually update `uge` or the breadcrumb.

---

### Operation: Create Opgave file

**Trigger:** session started with an epic whose Opgave file does not yet exist.

**Input:** epic key, epic description (from Epic Catalog), current ISO week.

**Output:** new file at `{vault_root}/Opgaver/{epic_key}.md`:

```markdown
---
beskrivelse: {epic description from Epic Catalog}
state: Todo
uge:
  - {current ISO week, e.g. 2026-W26}
---

## breadcrumb navigation
- [[26]]

## Opgave

## Tasks

## Accept
```

**Notes:**
- Week number in breadcrumb = two-digit week extracted from ISO week identifier
  (`2026-W26` → `26`, `2026-W07` → `07`).
- If the epic has no description, `beskrivelse` is written as an empty string.
- If the file already exists, this operation is skipped and the sync operation runs
  instead.

---

### Operation: Sync breadcrumb navigation

**Trigger:** session started with an epic whose Opgave file already exists.

**Logic:**
1. Read the file content.
2. Parse the YAML frontmatter to extract the `uge` array.
3. If the current ISO week is not in `uge`, add it (write back to frontmatter).
4. Extract two-digit week numbers from `uge`.
5. Parse the `## breadcrumb navigation` section for existing `[[NN]]` entries.
6. Compute which week numbers are in `uge` but not in the breadcrumb.
7. If there are any missing entries, append them (sorted) to the breadcrumb section.
8. Write the file back atomically only if a change was made.

**Edge cases:**
- Breadcrumb section missing entirely → create it before adding entries.
- `uge` is empty → sync is a no-op.
- Current week already in `uge` and breadcrumb → no write; operation completes silently.

---

### YAML frontmatter parsing approach

~~**Option B — string manipulation (no new dependency)**~~ — superseded.

**Confirmed: Option A — PyYAML (`pyyaml`):**
- PyYAML used for **reading** the frontmatter reliably.
- The `uge` block is written back via **string manipulation** to preserve key order
  and formatting (avoiding PyYAML's tendency to reorder keys or change quoting).
- `pyyaml` added to `requirements.txt`.

This hybrid approach gets the correctness of a real YAML parser for reads, and
the formatting stability of string manipulation for writes.

---

### Atomic file writes

```python
import os, pathlib

def write_atomic(path: pathlib.Path, content: str) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)   # atomic on the same volume (Windows-safe)
```

`os.replace()` is atomic on Windows when source and destination are on the same volume.
No external library needed.

---

### Trigger integration point in TimeTracker

When a session is started (`cmd_start` or equivalent), after writing the session to
storage, the integration runs as a side-effect:

```
session start
  → write session to DB
  → if vault_path is configured AND epic is set:
      → run obsidian_sync(epic_key, epic_description, current_iso_week)
          → if Opgave file does not exist: create it
          → if Opgave file exists: sync uge + breadcrumb
      → report result to OutputPanel (silent on success, warning on failure)
```

Failure in the Obsidian sync must **never** prevent the session from being recorded.
The sync is a best-effort side-effect, not a transaction.

---

### Epic filter — which epics get Opgave files?

**Confirmed (and clarified 2026-07-20):** The `excluded_tasks` and `always_separate_tasks`
settings identify administrative tasks that have **no epic** attached (e.g. `Lunch`,
`Omsorgsdage`). These tasks are logged by task name only — not against a Jira ticket —
so there is nothing to create an Opgave file for. The integration skips them silently.

All other sessions carry a real epic key, and the Opgave panel appears for them
automatically. There is no opt-in mechanism and no user configuration required to show
the panel for a given epic.

---

### Vault folder structure (added 2026-07-21, resolved 2026-07-29)

The original design assumed a hard-coded `Opgaver/` subfolder. User feedback during
refinement raised two concerns:

1. The folder name should be configurable, not hard-coded to `Opgaver/`.
2. An additional **epics folder** is needed for epic-level documentation (one markdown
   file per epic, where the epic's description and long-form notes live).

**Current epic names in the database:** `Valuation principle §14`, `Miscellaneous`,
`Mortgage valuation`, `Mainframe Exit`. These are human-readable group labels — not
Jira ticket IDs. The task identifier typed by the user (e.g. `EVD-4325`) is the value
stored in the session's `task` field and is the natural Opgave filename.

**Resolution:** Hard-code default subfolder names for the first build:
- `{vault_path}/tasks/` — Opgave files (one per task identifier).
- `{vault_path}/epics/` — epic-level documentation (one per epic name). Created
  automatically when the first task linked to that epic triggers a sync. Uses a
  minimal empty template for now (just a heading). A richer template will be designed
  later.

Subfolders are created automatically if they don't exist. Configurable paths are
deferred to a future iteration.

---

### Filename sanitisation (added 2026-07-21, resolved 2026-07-29)

The session's task identifier becomes the Opgave filename. Task identifiers are
free-text strings — the user types them directly. Examples from the current data:

- `EVD-2213` → `EVD-2213.md` ✓ (safe)
- `Valuation principle §14` → contains space and `§` (needs handling)

**Resolution:** Use a single **replacement map** stored as a Python `dict`.

```python
# Replacement map: character → replacement string.
# Empty string means "remove the character".
# Characters not in this map are kept as-is.
FILENAME_REPLACEMENTS: dict[str, str] = {
    "§": "paragraph",
    "/": "",
    "\\": "",
    ":": "",
    "*": "",
    "?": "",
    '"': "",
    "<": "",
    ">": "",
    "|": "",
}
```

**Sanitisation algorithm:**
1. For each character in the input string:
   - If it has an entry in `FILENAME_REPLACEMENTS` → substitute the replacement value
     (which may be empty, effectively removing the character).
   - Otherwise → keep as-is (spaces, accented characters, hyphens, etc. preserved).
2. Strip leading/trailing whitespace from the result.
3. If the result is empty after sanitisation → abort sync with a warning.

Examples:
- `EVD-4325` → `EVD-4325.md`
- `Valuation principle §14` → `Valuation principle paragraph14.md`
- `Mortgage valuation` → `Mortgage valuation.md`

**Future:** The replacement map will be exposed as a configurable mapping in the
Configuration screen, stored as a JSON dict in the `settings` table. The in-code dict
serves as the default/fallback.

---

### Refinement review findings (added 2026-07-21)

Issues identified during code audit against the feature requirements:

**1. No `description` column on `epics` table.**
The `epics` table schema is `(id, name, created_at)`. There is no description field.
**Resolution (user feedback):** Epic descriptions live in the filesystem (vault), not
the database. The `beskrivelse` frontmatter field is populated from the epic `name`.
Long-form documentation belongs in the vault's epics folder, not in the DB.

**2. Epic name vs. task identifier — which is the filename?**
The session stores a `task` field (e.g. `EVD-4325`). The `task_catalog` links that
task to an epic `name` (e.g. `Mortgage valuation`). The Opgave file should be named
after the **task identifier** (the specific ticket/item), not the epic name (the group).

**3. Filter logic is task-based, not epic-based.**
The `excluded_tasks` and `always_separate_tasks` settings contain **task identifiers**
(e.g. `Lunch`, `commute`, `Sick`, `Doctor`, `Bank meeting`). The integration checks the
session's `task` field against these lists. If the task is in either list → skip.

**4. Skip condition ordering.**
The precise skip logic on session start:
1. `vault_path` not configured → skip
2. Session task is empty (`""`) → skip
3. Session task is in `excluded_tasks` or `always_separate_tasks` → skip
4. Otherwise → run sync (look up epic via `get_task_epic(task)` for `beskrivelse`)

**5. `Opgaver/` directory creation.**
If `{vault_path}/tasks/` (or whichever configured folder) does not exist, it should be
created automatically. The vault path itself must exist (validated on config save), but
the subfolders are the integration's responsibility.

---

### Risk assessment

| Risk | Severity | Notes |
|------|----------|-------|
| Corrupting an Opgave file | Medium | Mitigated by atomic writes; abort on parse failure |
| Frontmatter parse failure | Low–Medium | Treat as non-fatal warning; session is still recorded |
| Writing to a file Obsidian has open | Low | Obsidian re-reads on focus; safe on Windows |
| Vault path not configured | Low | Silent skip; no error unless vault path is set |
| Epic without description | Low | `beskrivelse` written as empty string; user fills it in Obsidian |
| Non-ticket epics getting Opgave files | Low–Medium | Mitigated by epic filter setting |

---

---

### In-app note display — read-only Opgave panel

**Context:** The user confirmed that in-app editing is out of scope for this feature.
The goal is to get a reliable read-only note view working first. Editing is a separate
future feature.

#### Panel placement

The Opgave panel sits between the top panel row (`TodayPanel` / `WeekPanel`) and the
`TaskSummaryPanel`, taking all remaining vertical space that is not claimed by other
panels. In the layout diagram:

```
┌─ Header ─────────────────────────────────────────────┐
│  ┌─ Today ──────────────────┐  ┌─ Week ─────────────┐ │
│  │                          │  │                    │ │
│  └──────────────────────────┘  └────────────────────┘ │
│  ┌─ Opgave ───────────────────────────────────────────┐│   ← NEW
│  │  EVD-4325 — Payment gateway refactor               ││
│  │  ## Opgave  [content]                              ││
│  │  ## Tasks   [content]                              ││
│  │  ## Accept  [content]                              ││
│  └───────────────────────────────────────────────────┘│
│  ┌─ Task Summary ─────────────────────────────────────┐│
│  │  ...                                               ││
│  └───────────────────────────────────────────────────┘│
│  ┌─ Progress ─────────────────────────────────────────┐│
│  │  ...                                               ││
│  └───────────────────────────────────────────────────┘│
│  ┌─ Output ───────────────────────────────────────────┐│
│  └───────────────────────────────────────────────────┘│
│  > command input                                       │
└─ Footer ──────────────────────────────────────────────┘
```

The panel uses `height: 1fr` to fill the available space.

#### What the panel shows

1. **Header line:** Epic key and description (e.g. `EVD-4325 — Payment gateway refactor`),
   sourced from the Epic Catalog.
2. **`## Opgave` section** — free-text task description.
3. **`## Tasks` section** — Markdown checklist.
4. **`## Accept` section** — acceptance criteria.

The `## breadcrumb navigation` section is structural metadata and is not shown.

#### Empty / missing states

- **No active session:** Panel shows a placeholder (e.g. *"No active session"*).
- **Active session but no epic:** Panel shows a placeholder (e.g. *"No epic linked"*).
- **Active session with epic but vault not configured:** Panel is hidden or shows
  *"Vault not configured"*.
- **Opgave file does not exist yet:** File is created automatically when the session
  starts (see Create Opgave file operation). If creation fails, panel shows a warning.
- **File exists but sections are empty:** Sections are shown as empty — no placeholder
  text injected.

#### Update behaviour

The panel refreshes whenever the active session changes (same hook as `refresh_session_panels()`
in `TimeTrackerApp`). It does not poll or watch the file system — it re-reads the file
on demand.

#### Write access

The panel is strictly read-only. There is no edit command, no `TextArea`, and no save
path in this feature. In-app editing is deferred to a future feature.

---

### Writing notes — deferred

Full in-app editing of Opgave sections is explicitly out of scope for this feature.
It is captured in `## Future Ideas` and will require its own design document when the
time comes. Key concerns that will need to be addressed then:

- Concurrent-access race with Obsidian (no file lock on Windows).
- Section boundary parsing robustness.
- Round-trip fidelity (preserve all content outside the edited section).
- Command-gated edit mode (explicit unlock, not default).
- Inline editing in the same panel (not a modal).

---

## Future Ideas

- **In-app Opgave editing** — command-gated edit mode that turns the read-only panel
  into an inline `TextArea`. Full section replacement, atomic save, concurrent-access
  warning. Deferred from this feature intentionally.
- `opgave open EVD-4325` — launch the file in Obsidian via `obsidian://open` URI.
- File browser TUI screen for navigating the vault without leaving TimeTracker.
- `state` transitions from the TUI (e.g. `opgave done EVD-4325` sets `state: Complete`).
- Bulk sync: scan all Opgave files in the vault and report out-of-sync breadcrumbs.
- Epic-level opt-in/out flag for Obsidian sync in the Epic Catalog.
- Fuzzy search across `beskrivelse` fields to find a ticket by description.

---

## Manual Changes

2026-07-29 (revision 6 — OQ 11 & OQ 12 resolved)
- OQ 11 resolved: hard-code default subfolder names for v1 (`tasks/` and `epics/`
  under `vault_path`). Configurable paths deferred to a future iteration.
- Epic file creation: Option A chosen — integration creates an epic file automatically
  (minimal empty template: just a heading with the epic name) when the first task
  linked to that epic triggers a sync. A richer template will be designed later.
- OQ 12 resolved: filename sanitisation uses a replacement map (`dict`). Characters
  with meaningful substitutions (e.g. `§` → `paragraph`) are replaced; Windows-illegal
  characters (`/\:*?"<>|`) are removed. The map is stored in code, with a future path
  to exposing it as a configurable mapping in the Configuration screen.
- All open questions are now resolved.

2026-07-21 (revision 5 — refinement review)
- Code audit performed: `epics` table has no `description` column (only `id`, `name`,
  `created_at`). User confirmed descriptions should live in filesystem files, not DB.
- `beskrivelse` source changed: populated from the epic `name` field (the group label
  from `task_catalog` → `epics`), not a non-existent description column.
- User clarified their epic names: `Valuation principle §14`, `Miscellaneous`,
  `Mortgage valuation`, `Mainframe Exit`. These are human-readable group labels, not
  Jira ticket IDs. The session `task` field (typed by user) is the Opgave filename.
- Filename sanitisation flagged as a new open question (OQ 12) — epic names and task
  identifiers may contain characters like `§` and spaces.
- Filter logic confirmed as task-based: `excluded_tasks` / `always_separate_tasks`
  contain task identifiers (e.g. `Lunch`, `commute`, `Sick`, `Doctor`, `Bank meeting`).
- Skip condition ordering documented explicitly (vault_path → empty task → excluded →
  sync).
- User requested configurable folder paths: task files folder and epic files folder.
  Two modes proposed: default (subfolders of vault_path) vs. custom (explicit paths).
  Flagged as new open question (OQ 11).
- OQ 2 revised: Opgave file named after session task identifier, not epic name.
- OQ 3 revised: `beskrivelse` from epic `name`, not a description column.
- OQ 9 revised: clarified that the check is against the session `task` field, and
  listed concrete examples (`Lunch`, `commute`, `Sick`, `Doctor`, `Bank meeting`).

2026-06-29
- Feature document created based on user request.
- User noted this is "kinda out of scope" — design should stay minimal and non-invasive.
- Direct editing flagged as a stretch goal, not a hard requirement.
- Dependency on Configuration View (for vault path storage) noted — likely a prerequisite.

2026-06-29 (revision 1)
- User provided full vault structure documentation (Nykredit vault).
- Initial use case clarified: create Opgave files + sync breadcrumb navigation.
- Feature document rewritten around concrete vault structure and the two core operations.

2026-06-29 (revision 2)
- All six primary design questions answered by user:
  1. Trigger: auto on session start (not manual commands).
  2. Epic Catalog: hard prerequisite; epic key = file name, epic description = beskrivelse.
  3. Description: from Epic Catalog. Left blank if epic has no description.
  4. Breadcrumb: additive only.
  5. Configuration View: hard prerequisite (vault path lives in settings table).
  6. Status files confirmed auto-discovered via Dataview; never written to.
- Confirmed Ugenlig.md Templater template recorded in vault structure section.
- Prerequisites section added with hard dependencies on Epic Catalog and Configuration View.
- Trigger integration point and failure-safety contract documented.
- Epic filter open question raised (not all epics should get Opgave files).
- Remaining open questions (6–10) identified for Refinement.

2026-07-20 (revision 4)
- Prerequisites confirmed complete by user (Epic Catalog: Completed, Configuration
  View: Documented).
- OQ9 interpretation corrected: excluded_tasks / always_separate_tasks identify tasks
  WITHOUT epics (administrative). All sessions with a real epic trigger the integration
  automatically — no user opt-in needed.
- Panel behaviour clarified: always present in the layout; no user action to show it.
- Config screen requirement added: vault_path field added to the existing Configuration
  screen (config command / Ctrl+,), with directory-existence validation.
- vault_path field is optional — blank disables the integration silently.
- All remaining open questions (6–10) resolved by user:
  - OQ 6: PyYAML confirmed for reading; string manipulation for writing uge back.
  - OQ 7: Atomic writes via os.replace() confirmed.
  - OQ 8: All three uge update cases on session start confirmed.
  - OQ 9: Epic filter uses existing excluded_tasks / always_separate_tasks settings.
    No new setting needed.
  - OQ 10: Settings key is `vault_path` (kept generic, not Obsidian-specific).
- Status advanced to Refinement.
- Requirements and Non-Goals sections written from confirmed decisions.
- YAML brainstorm note updated to reflect PyYAML decision.
- Epic filter brainstorm note updated to reflect settings-based approach.

---

## Documentation Plan

_To be defined when the feature reaches Proposed status._

---

## Next Step

> **Current status:** Refinement
> **To reach Proposed:** Requirements section has been updated with all resolved
> decisions. User review needed:
>
> 1. Confirm the Requirements section is complete and accurate.
> 2. Confirm no requirements have been missed or misrepresented.
> 3. Once confirmed, advance status to Proposed.
