# Feature: Configuration View

Status: Brainstorming

## Purpose

Provide a persistent, user-editable configuration layer that lets the user control application behaviour without touching code. The most immediate needs are:

1. **Excluded tasks/epics** — certain logged tasks (e.g. Lunch) should not count toward the daily working-hours target.
2. **Daily work target** — the number of hours that constitutes a full working day (e.g. 7h 24m for a 37-hour week, or 8h for a 40-hour week).

Configuration is accessed through a dedicated TUI screen and stored persistently in the existing SQLite database.

---

## Prerequisites

This feature may not be implemented until the following features are in `Implemented` status:

- **Epic Catalog** (`features/epic-catalog.md`) — excluding a task/epic from working hours requires epics to be first-class entities in the data model. Without the Epic Catalog, "excluded epics" has no stable reference to exclude against.

---

## Requirements

_Not yet fully defined — initial brainstorm only._

### Access

- The configuration screen can be opened by:
  - Typing `config` in the TUI command input.
  - A keybinding (see open question below — `Ctrl+C` conflicts with terminal conventions; an alternative must be agreed).
- The screen is a full Textual `Screen` pushed onto the screen stack.
- Pressing `Escape` or an explicit **Close** action returns to the main dashboard without discarding saved changes.

### Excluded tasks / epics

- The user can maintain a list of task or epic identifiers that are excluded from working-hours calculations.
- A typical entry is `Lunch` (or whatever identifier is used to log lunch breaks).
- Excluded entries are stored persistently in the database.
- The daily progress bar, leave-time estimate, and any other "hours worked" calculation must respect this exclusion list.
- Time logged against excluded tasks is still recorded — it is only omitted from the working-hours target comparison.
- Exclusions reference epic/task identifiers from the Epic Catalog where possible, but should also allow free-text identifiers for tasks not yet catalogued.

### Always-separate tasks / epics

- The user can maintain a second list of task or epic identifiers that are **always reported as standalone rows** in the Promark output, rather than being folded into the day's consolidated start/end entry.
- A typical entry is `Omsorgsdage` (Danish statutory care days) — these hours must be registered as worked time but must appear separately from the normal working day in Promark.
- Always-separate entries are stored persistently in the database.
- **Distinction from excluded tasks:**
  - *Excluded* tasks do not count toward the daily work target at all (e.g. Lunch in a 37-hour model — pure overhead).
  - *Always-separate* tasks **do** count as worked/registered hours, but must be broken out as their own Promark rows instead of being merged into the consolidated daily entry.
- Impact on the Promark calculation (`Promark.py`):
  - Sessions tagged with an always-separate task are removed from the session list before computing `first_start` and `total_hours` for the consolidated entry.
  - Each always-separate session (or contiguous block of same-task sessions on the same day) is emitted as an additional row in the Promark table, showing its own hours.
- Time logged against always-separate tasks is still fully visible in the TUI Today panel, week log, and status command — the separation only affects the Promark output.
- Always-separate entries reference task/epic identifiers from the Epic Catalog where possible, but should also accept free-text identifiers.

### Daily work target

- The user can set a daily work target expressed in decimal hours (e.g. `7.4` or `8.0`).
- Common presets should be offered for convenience:
  - **37-hour week** → `7.4h` per day (7h 24m)
  - **40-hour week** → `8.0h` per day
  - **Custom** → free-text decimal input
- The target is used everywhere the application calculates progress or remaining time (today panel, status command, leave-time estimate).
- The target is stored persistently and survives application restarts.

### Storage

- Configuration is stored in a new `settings` table in the existing SQLite database.
- The `settings` table uses a key-value structure so new settings can be added without schema migrations.
- Following the project convention (see `AGENTS.md` — Database Conventions), a companion `settings_h` shadow table and three triggers provide a full audit trail automatically.

**Main table:**

```sql
CREATE TABLE IF NOT EXISTS settings (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TEXT NOT NULL   -- ISO 8601 local datetime; human-readable last-write timestamp
);
```

**Shadow / history table** (populated only by triggers — never written to directly):

```sql
CREATE TABLE IF NOT EXISTS settings_h (
    h_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    h_operation TEXT    NOT NULL,   -- 'I' Insert · 'U' Update · 'D' Delete
    h_timestamp TEXT    NOT NULL,   -- ISO 8601 UTC datetime (datetime('now'))
    key         TEXT    NOT NULL,
    value       TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL
);
```

**Triggers:**

```sql
CREATE TRIGGER IF NOT EXISTS settings_after_insert
AFTER INSERT ON settings
BEGIN
    INSERT INTO settings_h (h_operation, h_timestamp, key, value, updated_at)
    VALUES ('I', datetime('now'), NEW.key, NEW.value, NEW.updated_at);
END;

CREATE TRIGGER IF NOT EXISTS settings_after_update
AFTER UPDATE ON settings
BEGIN
    INSERT INTO settings_h (h_operation, h_timestamp, key, value, updated_at)
    VALUES ('U', datetime('now'), NEW.key, NEW.value, NEW.updated_at);
END;

CREATE TRIGGER IF NOT EXISTS settings_after_delete
AFTER DELETE ON settings
BEGIN
    INSERT INTO settings_h (h_operation, h_timestamp, key, value, updated_at)
    VALUES ('D', datetime('now'), OLD.key, OLD.value, OLD.updated_at);
END;
```

All DDL above belongs in `create_schema()` in `Storage.py` (or a dedicated `SettingsStorage.py` if the domain grows large), following the existing pattern.

- Excluded tasks are stored as a JSON array under a well-known key (e.g. `excluded_tasks`).
- Always-separate tasks are stored as a JSON array under a well-known key (e.g. `always_separate_tasks`).
- The daily work target is stored as a plain decimal string under a well-known key (e.g. `daily_work_target_hours`).
- A settings repository layer (following the existing `db/repository.py` pattern) provides typed read/write access.
- Sensible defaults are applied in code when a key is absent — the application must work correctly without any prior configuration.

---

## Non-Goals

_Not yet defined._

---

## Open Questions

1. **Keybinding conflict** — `Ctrl+C` is the standard terminal interrupt signal and is commonly bound to "quit" or "copy" in terminal emulators and Textual itself. Using it for "open config" is likely to conflict. Alternatives to consider:
   - `Ctrl+,` (VS Code convention for settings)
   - A dedicated footer button (click to open)
   - Just `config` command (no keybinding at all until a safe key is agreed)

2. **Excluded task resolution** — When the Epic Catalog is not yet complete, the user may want to exclude a task that is not yet in the catalog. Should the exclusion list accept free-text values in addition to catalogued epic keys?

3. **Per-day targets** — Some work patterns have different daily targets per weekday (e.g. a compressed schedule or a shorter Friday). Should this be in scope for v1, or deferred to a future idea?

4. **Promark lunch offset** — The Promark view currently hard-codes a 30-minute lunch offset. Should this also be configurable from the configuration screen, or is it a separate concern?

5. **Notification interval** — The Toast Notifications feature hard-codes a 5-minute polling interval and lists configurability as a future idea. Should that setting live here?

---

## Brainstorm Notes

### Motivation — the Danish lunch context

In Denmark many employers operate a **37-hour** working week where lunch is on top of billable hours (i.e. a full day at the office is ~7h 24m of work + ~30m lunch). Other employers run **40-hour** weeks where lunch is included.

TimeTracker currently shows a hard-coded 7.5-hour target (based on reading the `status` output). Both the target and the treatment of lunch/non-billable time must be configurable so the application gives accurate leave-time estimates in either model.

**Exclusion model:**
- If Lunch is *on top of* working hours (37-hour model): log `Lunch` sessions, exclude them from the working-hours total, and the progress bar only counts real work.
- If Lunch is *included in* working hours (40-hour model): do not exclude `Lunch`; all logged time counts toward the target.

The same exclusion mechanism could serve other non-billable categories: internal admin, all-hands meetings excluded from client-facing work, etc.

### TUI screen design sketch

The configuration screen is a full-screen Textual `Screen`:

```
┌─ Configuration ──────────────────────────────────────────────┐
│                                                              │
│  Daily work target                                           │
│  ○ 37-hour week  (7h 24m)                                    │
│  ○ 40-hour week  (8h 00m)                                    │
│  ● Custom:  [ 7.4 ] hours                                    │
│                                                              │
│  Excluded from working hours                                 │
│  Tracked but not counted toward the daily target.            │
│                                                              │
│  ┌─────────────────────┐                                     │
│  │ Lunch               │  [Remove]                           │
│  └─────────────────────┘                                     │
│  [ Add exclusion... ]                                        │
│                                                              │
│  Always separate  (Promark only)                             │
│  Counted as hours but reported as standalone rows in         │
│  the Promark view, not merged into the daily entry.          │
│                                                              │
│  ┌─────────────────────┐                                     │
│  │ Omsorgsdage         │  [Remove]                           │
│  └─────────────────────┘                                     │
│  [ Add always-separate... ]                                  │
│                                                              │
│                                          [Save]  [Close]     │
└──────────────────────────────────────────────────────────────┘
```

### Settings repository

Rather than accessing the `settings` table directly from the screen, a thin repository class should provide typed getters/setters:

```python
class SettingsRepository:
    def get_daily_work_target(self) -> float: ...          # default: 7.4
    def set_daily_work_target(self, hours: float): ...
    def get_excluded_tasks(self) -> list[str]: ...         # default: []
    def set_excluded_tasks(self, tasks: list[str]): ...
    def get_always_separate_tasks(self) -> list[str]: ...  # default: []
    def set_always_separate_tasks(self, tasks: list[str]): ...
```

Defaults are encoded in the repository, not the database, so the database remains clean on first run.

### Impact on existing calculations

**Excluded tasks** — all code that computes "hours worked today" or "remaining time" must be updated to:
1. Fetch `excluded_tasks` from the settings repository.
2. Filter out sessions whose `task` field matches any entry in the exclusion list before summing durations.

This affects at minimum:
- `status` command (progress bar, remaining time, leave-time estimate)
- TUI Today panel
- Potentially the Week panel daily totals

**Always-separate tasks** — the Promark calculation in `Promark.py` must be updated to:
1. Fetch `always_separate_tasks` from the settings repository.
2. Partition each day's session list into *normal* sessions and *always-separate* sessions.
3. Run the existing `promark_entry()` consolidation only on the *normal* sessions.
4. Emit one additional Promark row per always-separate task present on that day, showing the summed hours for that task (no consolidated start/end — hours only, or actual start/end of that session block depending on what Promark requires).

Always-separate sessions are **not** filtered from the `status` command or the TUI panels — the separation is a Promark-only concern.

### Suggestions for the user to consider

The following ideas emerged during brainstorming and are listed here for review — none are committed to scope:

1. **Per-day work targets** — e.g. 7.4h Mon–Thu and 6.0h on Friday for flex schedules. Low complexity to store (7 keys), moderate complexity to surface in the UI.

2. **Promark lunch offset** — currently hard-coded to 30 minutes. Moving it here would make the Promark output accurate for both 37-hour (lunch separate) and 40-hour (lunch included) workplaces. The offset could simply be `0` when lunch is included.

3. **Toast notification interval** — the `features/toast.md` future-ideas section already flags this as worth making configurable. It is a natural fit for the config screen.

4. **Layout density persistence** — `features/layout-density.md` explicitly lists persistence as a future idea. A single `layout_density` key in the `settings` table would satisfy it with minimal effort.

5. **Working days** — e.g. Mon–Fri vs a 4-day week. Would affect weekly hour calculations.

---

## Future Ideas

- Per-day work targets (e.g. shorter Fridays).
- Configurable Promark lunch offset.
- Configurable toast notification interval (linking to `features/toast.md`).
- Layout density persistence (linking to `features/layout-density.md`).
- Configurable working days (e.g. 4-day week).
- Export/import settings as JSON for backup or sharing across machines.

---

## Manual Changes

2026-06-25
- Feature document created based on user request.
- Prerequisites identified: TUI-Only Interaction, Epic Catalog.
- Open keybinding conflict for `Ctrl+C` flagged — must be resolved before Proposed status.
- "Always-separate tasks" concept added: tasks that count as hours but are broken out as standalone rows in the Promark view (e.g. Omsorgsdage).

---

## Documentation Plan

| File | Action | Description |
|------|--------|-------------|
| `docs/configuration.md` | Create | New doc describing the configuration screen, all available settings, defaults, and storage. |
| `docs/commands.md` | Update | Add `config` command entry; note that excluded tasks affect the `status` command output and always-separate tasks affect the `promark` output. |
| `docs/tui.md` | Update | Add the configuration screen to the TUI reference (keybinding, navigation). |
| `docs/sqlite-datasource.md` | Update | Document the new `settings` and `settings_h` table schemas and their triggers. |

---

## Next Step

> **Current status:** Brainstorming
> **To reach Proposed:** Resolve open questions (especially the `Ctrl+C` keybinding conflict and the scope of v1 exclusions), then consolidate into a concrete Requirements list and Non-Goals section.
