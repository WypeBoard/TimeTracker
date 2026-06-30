# Feature: Obsidian Notes Integration

Status: Brainstorming

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

Status files (`Status/2026/NN.md`) are **never written to** — Obsidian's Dataview query
auto-discovers tasks from `uge` frontmatter, so they require no maintenance.

---

## Prerequisites

This feature may not be implemented until the following features are in `Implemented`
status:

- **Epic Catalog** (`features/epic-catalog.md`) — the epic key is the Opgave file name;
  the epic description becomes the `beskrivelse` frontmatter value. Without the Epic
  Catalog, there is no stable epic identity or description to write.
- **Configuration View** (`features/configuration-view.md`) — the vault root path is
  stored as a setting in the `settings` table. Without Configuration View the settings
  table does not exist and there is nowhere to persist the vault path.

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

## Non-Goals

_Not yet defined — this section will be filled in during Refinement._

---

## Open Questions

~~1. **Trigger**~~ — **Resolved:** Auto-triggered on session start.

~~2. **Ticket ID source**~~ — **Resolved:** The epic key from the Epic Catalog is the
Opgave file name. Hard dependency on Epic Catalog.

~~3. **New file template — `beskrivelse`**~~ — **Resolved:** Populated from the epic's
description in the Epic Catalog. Left blank only if the epic has no description.

~~4. **Breadcrumb sync direction**~~ — **Resolved:** Additive only. Entries are never
removed.

~~5. **Vault path**~~ — **Resolved:** Stored in the `settings` table. Hard dependency
on Configuration View.

6. **YAML frontmatter parsing** — Option B (string manipulation, no new dependency) is
   recommended. Not yet explicitly confirmed. Needs user sign-off during Refinement.

7. **Write safety** — Atomic writes via `os.replace()` are planned. No new dependency.
   Needs explicit confirmation during Refinement.

8. **`uge` update on session start** — When a session starts:
   - If the file does not exist → create it with `uge: [current week]`.
   - If the file exists and `uge` already contains the current week → sync breadcrumb
     only (no write to `uge` needed).
   - If the file exists but the current week is missing from `uge` → add the current
     week to `uge`, then sync breadcrumb.
   The third case requires a write to the frontmatter. Confirm this behaviour is desired.

9. **Epics without a ticket ID pattern** — The vault uses Jira-style IDs (`EVD-XXXX`).
   If the Epic Catalog contains epics that do not follow this pattern (e.g. `Lunch`,
   `Omsorgsdage`), should they also get Opgave files, or should only pattern-matching
   epics be eligible? A configurable filter (e.g. `EVD-` prefix only) could limit the
   integration to "real" tickets.

10. **Vault path setting key** — What key name to use in the `settings` table
    (e.g. `obsidian_vault_path`)? Confirm during Refinement alongside Configuration View.

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

**Option B — string manipulation (no new dependency):**
- Split the file on `---` delimiters to isolate the frontmatter block.
- Use line-by-line parsing to read/write the `uge` list.
- Acceptable because the frontmatter schema is small and stable (three known keys, flat
  types only).
- Risk: fragile on unusual YAML formatting. Mitigation: treat parse failure as a hard
  error and abort without writing.

**Option A — PyYAML (`pyyaml`):**
- Requires adding `pyyaml` to `requirements.txt`.
- Handles all YAML edge cases correctly.
- Risk: may reformat the YAML block on write (reorder keys, change quoting style).
  Mitigation: use PyYAML only for reading; write the `uge` block back via string
  manipulation to avoid reformatting.

Recommendation: **Option B** for initial implementation. Migrate to PyYAML if string
manipulation proves fragile in practice.

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

Not all epics in the Epic Catalog are Jira tickets deserving a formal task document.
Examples of epics that should probably not create Opgave files:
- `Lunch` (excluded from working hours)
- `Omsorgsdage` (always-separate, administrative)
- `Misc` / `Non-billable`

A configurable prefix filter (e.g. only epics matching `EVD-\d+`) stored as a setting
in the `settings` table would let the user control which epics trigger Opgave creation.
If no filter is configured, all epics create Opgave files (safe default — Obsidian just
gets extra files).

Alternatively: a boolean flag `obsidian_sync` could be added to the Epic Catalog itself,
letting the user opt individual epics in/out at epic-definition time.

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

## Future Ideas

- `opgave open EVD-4325` — launch the file in Obsidian via `obsidian://open` URI.
- File browser TUI screen for navigating the vault without leaving TimeTracker.
- Plain-text preview of an Opgave file in a TUI panel.
- `state` transitions from the TUI (e.g. `opgave done EVD-4325` sets `state: Complete`).
- Bulk sync: scan all Opgave files in the vault and report out-of-sync breadcrumbs.
- Epic-level opt-in/out flag for Obsidian sync in the Epic Catalog.
- Fuzzy search across `beskrivelse` fields to find a ticket by description.

---

## Manual Changes

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

---

## Documentation Plan

_To be defined when the feature reaches Proposed status._

---

## Next Step

> **Current status:** Brainstorming
> **To reach Refinement:** All primary design decisions are resolved. Remaining steps:
>
> 1. Confirm YAML approach (Option B — string manipulation, no new dep).
> 2. Confirm atomic write pattern is acceptable.
> 3. Confirm `uge` update behaviour on session start (the three cases described in OQ 8).
> 4. Decide epic filter strategy (prefix pattern in `settings` vs opt-in flag on Epic
>    Catalog) — OQ 9.
> 5. Agree on the `settings` key name for the vault path — OQ 10.
> 6. Write the Requirements and Non-Goals sections from the confirmed decisions.
>
> The document is ready to move to Refinement once these are addressed.