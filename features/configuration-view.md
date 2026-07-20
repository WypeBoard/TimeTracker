# Feature: Configuration View

Status: Documented

## Purpose

Provide a persistent, user-editable configuration layer that lets the user control application behaviour without touching code. The most immediate needs are:

1. **Lunch handling** — a dedicated `lunch` command creates Lunch sessions; the config screen controls whether they count toward the daily target and how Promark treats them.
2. **Excluded tasks** — arbitrary tasks (other than Lunch, which has its own section) that should not count toward the daily working-hours target.
3. **Daily work target** — the number of hours that constitutes a full working day (e.g. 7h 24m for a 37-hour week, or 8h for a 40-hour week).

Configuration is accessed through a dedicated TUI screen and stored persistently in the existing SQLite database.

---

## Prerequisites

- **Epic Catalog** (`features/completed/epic-catalog.md`) — ✅ **Completed (2026-07-03).** This prerequisite is satisfied.

---

## Requirements

### Access

- The configuration screen can be opened by:
  - Typing `config` in the TUI command input.
  - The keybinding `Ctrl+,` (VS Code convention for settings).
- A new `cmd_config(ctx)` function in `Commands.py` calls `ctx.show_config()`.
- `show_config()` is added to the `AppContext` Protocol in `app_context.py`.
- The TUI implementation of `show_config()` pushes a new `ConfigScreen` onto the Textual screen stack.
- `Ctrl+,` is registered as a BINDING in `TimeTrackerApp` with action `show_config`.

### Config screen interaction model

- All edits are held in memory while the screen is open — nothing is written to the database during editing.
- **[Save]**: validates all fields; if valid, writes all values to the database and closes the screen; if invalid, shows an inline error on the offending field and stays open.
- **[Close] / Escape**: discards all unsaved in-memory changes and closes the screen without writing anything.

### `lunch` command

- A new `cmd_lunch(ctx, time_override=None)` function is added to `Commands.py`.
- It starts a session with `task = "Lunch"`, following the same auto-close flow as `cmd_resume`.
- If a session is already active: the running session is **automatically closed** at `time_str` first, then the Lunch session is opened (no separate `pause` is required).
- On success: writes the session to the database, emits `ctx.info("▶  Started Lunch at {time}")`, and calls `ctx.on_session_changed()`.
- **Does NOT** call `_notify_if_new_task` — Lunch is intentionally never linked to an Epic.
- `Lunch` sessions are stored like any other session and are not placed in `task_catalog`.

### Daily work target section

- The config screen presents three options as a radio group:
  - **37-hour week** (7h 24m) — stores `"7.4"`.
  - **40-hour week** (8h 00m) — stores `"8.0"`.
  - **Custom** — activates a text input where the user types a decimal number of hours.
- When the screen opens, if the stored value is `"7.4"` the first preset is pre-selected; if `"8.0"` the second is pre-selected; otherwise "Custom" is pre-selected with the stored value pre-filled.
- Selecting a preset radio disables the custom input and populates it with the preset value for display.
- Selecting "Custom" enables the input.
- **Validation**: the custom value must parse as a positive float (> 0 and ≤ 24). An out-of-range or non-numeric value shows an inline error and blocks Save.

### Lunch section

- **Excluded / Included toggle**: controls whether `Lunch` sessions count toward the working-hours total.
  - *Excluded* (default): `Lunch` sessions are filtered out before any hours-worked calculation.
  - *Included*: `Lunch` sessions are counted like any other session.
- **Promark offset** (integer, minutes, default `0`):
  - A text input accepting a non-negative integer.
  - Blank is treated as `0`.
  - If the actual `Lunch` duration on a given day is shorter than the offset, the shortfall is added to that day's Promark consolidated total.
  - Formula: `promark_addition = max(0, offset_minutes − actual_lunch_minutes)`.
  - This replaces the hard-coded `LUNCH_MINUTES = 30` constant in `Promark.py`.
- **Validation**: the offset must be a non-negative integer or blank. A negative value or non-integer shows an inline error and blocks Save.
- `Lunch` is **not** in the general `excluded_tasks` list; its exclusion is controlled entirely by the toggle above.

### Excluded tasks section

- A list of free-text task identifiers that are excluded from working-hours calculations.
- Each list entry displays the task string alongside a **[Remove]** button.
- An **"Add exclusion…"** button reveals an inline text input below the list. Pressing **Enter** validates and adds the item; pressing **Escape** cancels and hides the input.
- **Validation**:
  - The item must be a non-empty string after trimming whitespace.
  - `"Lunch"` is explicitly rejected with an inline error: "Lunch is configured in the Lunch section above".
  - Submitting an item already in the list is silently ignored (no duplicate is added).
- Time logged against excluded tasks is still recorded in the database and visible in all panels — it is only omitted from working-hours totals and the progress bar.
- Exclusion matching is a case-sensitive string comparison against the `task` field of sessions.

### Always-separate tasks section

- A list of free-text task identifiers that must appear as standalone rows in Promark output rather than being folded into the consolidated day entry.
- Same list UI, Add/Remove interaction, and validation rules as the Excluded tasks section (including the `"Lunch"` rejection).
- Time logged against always-separate tasks **does** count toward the working-hours total — the separation is exclusively a Promark concern.
- Always-separate tasks are still fully visible in the TUI Today panel, Week panel, status command, and Epic summary.

### Impact on hours-worked calculations

All code that computes "hours worked today" or "remaining time" must apply both filters before summing durations:

1. If `lunch_excluded` is `True`: filter out sessions where `task == "Lunch"`.
2. For each task in `excluded_tasks`: filter out sessions where `task` matches that entry.

Sessions for always-separate tasks are **not** filtered here — they remain in the hours-worked total.

Affected panels and commands at minimum: `TodayPanel`, `WeekPanel`, `ProgressStrip`, `_build_day_status()` in `Commands.py` (which drives the CLI `status` command and the TUI Today/Week panels).

Settings are read at call time by instantiating `SettingsRepository` inside the function that needs them. No singleton. No settings state held in widgets.

### Impact on Promark calculation

`Commands.py` reads settings values via `SettingsRepository` and passes them as plain arguments to `Promark.py` functions. `Promark.py` does not import `SettingsStorage.py` directly.

For each day in the Promark view, the calculation proceeds as follows:

1. Partition sessions into **always-separate** (task in `always_separate_tasks`) and **normal** (everything else).
2. From the **normal** pool, optionally remove `Lunch` sessions (controlled by `lunch_excluded`).
3. Run the consolidated entry calculation (existing `promark_entry()` logic) on the remaining normal sessions.
   - Apply `promark_addition = max(0, lunch_promark_offset_minutes − actual_lunch_minutes)` to the consolidated total hours.
   - `actual_lunch_minutes` = sum of minutes from `Lunch`-task sessions on that day (regardless of the `lunch_excluded` setting; the offset adjusts the Promark representation independently).
4. For each distinct task name in the always-separate pool, emit one standalone row showing: task name and summed hours for that day (hours only — no start/end time).
5. **Edge case**: if a day has zero normal sessions after filtering (all sessions are always-separate and/or Lunch), no consolidated row is emitted for that day.

### Storage

Configuration is stored in a new `settings` table following the project's key-value convention.

**Module**: a new `SettingsStorage.py` module (following `EpicStorage.py` as the direct template). DDL for `settings` and `settings_h` belongs in `Storage.py → create_schema()`, following the same pattern as the Epic tables.

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

**Note on `updated_at`**: this is the local datetime at the moment `SettingsStorage.py` writes the row, produced in Python as `datetime.now().isoformat(timespec='seconds')`. It is a human-readable "last edited" timestamp, distinct from the UTC audit timestamp `h_timestamp` written by the trigger.

**Settings keys:**

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `daily_work_target_hours` | decimal string | `"7.4"` | Daily work target in hours |
| `lunch_excluded` | `"true"` / `"false"` | `"true"` | Whether Lunch sessions are excluded from working-hours total |
| `lunch_promark_offset_minutes` | integer string | `"0"` | Expected lunch duration; shortfall is added to Promark consolidated total |
| `excluded_tasks` | JSON array of strings | `"[]"` | Task identifiers excluded from working-hours (not including Lunch) |
| `always_separate_tasks` | JSON array of strings | `"[]"` | Task identifiers that appear as standalone Promark rows |

Defaults are encoded in `SettingsRepository` methods, not in the database. The application must work correctly with an empty `settings` table.

**`SettingsRepository` interface:**

```python
class SettingsRepository:
    def get_daily_work_target(self) -> float: ...             # default: 7.4
    def set_daily_work_target(self, hours: float) -> None: ...
    def get_lunch_excluded(self) -> bool: ...                 # default: True
    def set_lunch_excluded(self, excluded: bool) -> None: ...
    def get_lunch_promark_offset_minutes(self) -> int: ...    # default: 0
    def set_lunch_promark_offset_minutes(self, minutes: int) -> None: ...
    def get_excluded_tasks(self) -> list[str]: ...            # default: []
    def set_excluded_tasks(self, tasks: list[str]) -> None: ...
    def get_always_separate_tasks(self) -> list[str]: ...     # default: []
    def set_always_separate_tasks(self, tasks: list[str]) -> None: ...
```

Each setter writes a single key using `INSERT OR REPLACE` with the current local datetime as `updated_at`.

### Affected files

| File | Change |
|------|--------|
| `Storage.py` | Add `settings` + `settings_h` DDL + 3 triggers to `create_schema()` |
| `SettingsStorage.py` | **New file** — `SettingsRepository` class |
| `Constants.py` | No functional change; `TARGET_HOURS = 7.4` remains as the documented default value |
| `Commands.py` | Add `cmd_lunch()`, `cmd_config()`; update `_build_day_status()` and `cmd_promark()` to read and apply settings |
| `Promark.py` | Update `promark_entry()` to accept settings as plain parameters; add always-separate partitioning; remove unused `LUNCH_START`, `LUNCH_END`, and `LUNCH_MINUTES` constants |
| `app_context.py` | Add `show_config()` to the `AppContext` Protocol |
| `app/TuiAppContext.py` | Implement `show_config()` → `self._app.push_screen(ConfigScreen())` |
| `app/TimeTrackerApp.py` | Add `Ctrl+,` BINDING → `action_show_config()`; add `action_show_config()` method |
| `app/CommandInput.py` | Route `lunch` → `cmd_lunch`; route `config` → `cmd_config` |
| `app/ConfigScreen.py` | **New file** — configuration TUI screen |

---

## Non-Goals

- **Notification interval** — configuring the toast polling interval is out of scope for this feature; tracked separately in `features/config-interval.md`.
- **Layout density persistence** — configuring and persisting the TUI layout density is out of scope for this feature; tracked separately in `features/config-layout.md`.
- **Per-day work targets** — a single daily target applies to all weekdays. Compressed or flex schedules are deferred to a future iteration.
- **Epic-level exclusion** — excluding all tasks linked to a given Epic (requires a JOIN against `task_catalog`) is deferred to a future iteration.
- **Configurable Promark row format for always-separate tasks** — the row format (hours only, no synthetic time range) is fixed; it is not user-configurable in v1.
- **Export/import of settings** — no JSON backup or cross-machine sharing in v1.

---

## Open Questions

All open questions are resolved. See Manual Changes for the resolution history.

---

## Brainstorm Notes

### 2026-07-07 — Always-separate: multiple buckets on the same day

A realistic day may contain several different payroll categories:

```
07:00 → 09:00  Work
09:00 → 10:00  Doctor            ← always-separate (own payroll bucket)
10:00 → 14:00  Work + Lunch
14:00 → 15:00  Børns første sygedag  ← always-separate (own payroll bucket)
```

Promark must produce **three rows** — one per distinct bucket:

| Promark row | Content |
|-------------|---------|
| Regular work | `07:00 → 13:30` (synthetic: work sessions only, stacked + lunch offset) |
| Doctor | `1h` (hours only) |
| Børns første sygedag | `1h` (hours only) |

Each always-separate task type is its own payroll bucket and must never be merged with another always-separate task, even if both appear on the same day.

**Important:** the consolidated work row is derived purely from the sessions that are *not* on the always-separate list. The synthetic end time (`first_start + stacked_work_hours + lunch_offset`) automatically reflects only the real work time.

---

### 2026-07-07 — Always-separate concrete example: Sick/Syg

**Scenario:** Work from 07:00 to 13:00 (with a lunch session in the middle), then leave sick for the rest of the day. Register a `Sick`/`Syg` session for the remaining hours.

Promark must output **two rows**, because these are different payroll/registration buckets:

| Row | Content |
|-----|---------|
| Regular work | `07:00 → 13:00` (synthetic: `first_start + stacked_work_hours + lunch_offset`) |
| Sick | `X hours` (hours-only, no time range — separate bucket) |

This confirms the Q6 resolution: the always-separate row shows **hours only**. The Sick bucket does not need a synthetic time range — it is a standalone hours registration in a different Promark category.

**Distinction from excluded tasks:**
- `Lunch` (when excluded): not counted toward the daily target, not a Promark row at all — it just disappears from the totals.
- `Sick`/`Syg` (always-separate): the hours **do** fill the day and count toward the full registered day; they simply appear in a separate Promark bucket rather than being folded into the regular work row.

**Impact on the consolidated row calculation:**
When Sick sessions are removed from the normal pool, the consolidated work row's stacked hours reflect only the actual worked time (e.g. the morning sessions). The sick hours are not double-counted — they appear only in the separate row.

---

### 2026-07-07 — Promark model clarified & Q6 resolved

**How Promark currently works:**
Promark does not record actual session timestamps. It computes a single synthetic time range per day:
- `start` = first session start of the day (e.g. `07:00`)
- `end` = `start + stacked_hours + lunch_offset`

Sessions are treated as if they were back-to-back regardless of gaps (e.g. a drive to work between two sessions is invisible). The lunch offset (currently hard-coded to 30 min) adds a fixed break to the end time.

Example:
```
07:00 → 09:00  (work)
-- gap: drive to work --
09:30 → 11:30  (work)
-- gap: lunch --
11:50 → 15:50  (work)

Promark shows: 07:00 → 15:20
(2h + 2h + 4h = 8h worked, + 0:30 lunch = 8:30 total span from 07:00)
```

**Always-separate row format (Q6):**
Because the consolidated entry is synthetic, there is no meaningful time range to compute for an always-separate task. Removing those sessions from the pool already adjusts the consolidated end time correctly. The always-separate row therefore shows **hours only** — no start/end — as a standalone hours registration in Promark.

**Promark lunch offset interaction:**
The `lunch_promark_offset_minutes` setting replaces the hard-coded 30-minute addition to the synthetic end time. `max(0, offset − actual_lunch_minutes)` is the net addition.

---

### 2026-07-07 — Lunch redesign & divert decisions

**`lunch` command:**
A new `lunch` command (alongside `start`, `stop`, etc.) creates a session with `task = "Lunch"`. This removes the need to type a task name manually and makes Lunch a first-class concept in the CLI/TUI. The session is stored like any other; the special handling is entirely in the config layer and the calculations that read it.

**Lunch config replaces the general exclusion approach for Lunch:**
Rather than placing `"Lunch"` in the generic `excluded_tasks` list, Lunch gets its own config section. This allows the Promark offset to be attached directly to the Lunch concept without polluting the generic excluded-tasks list with Promark-specific data.

**Promark offset logic:**
```
promark_addition = max(0, lunch_promark_offset_minutes - actual_lunch_minutes_on_day)
```
This addition is applied to the consolidated day entry in Promark, not as a separate row. The offset models the expectation that a lunch break of a fixed duration is "invisible" in Promark — if you took less than that, the remainder effectively extends your working time.

**Diverted features:**
- Toast notification interval → `features/config-interval.md` (stub created).
- Layout density persistence → `features/config-layout.md` (stub created).

### 2026-07-03 — Epic Catalog review & code audit

**Epic Catalog implementation — what was built:**
- `epics(id, name, created_at)` and `task_catalog(task_id TEXT, epic_id, created_at)` tables with `_h` shadow tables and triggers, all in `Storage.py → create_schema()`.
- `EpicStorage.py` is a dedicated storage module following exactly the pattern that `SettingsStorage.py` must follow.
- The `AppContext` protocol in `app_context.py` already has `show_epic_summary()` and `on_new_task()` — `show_config()` would be added in the same style.

**Exclusion model — clarified by the data model:**
Sessions store a `task` field as free-text (e.g. `"Lunch"`, `"TASK-123"`, `"Omsorgsdage"`). This is the field that exclusions and always-separate lists must match against.

**Hard-coded values that config must replace:**

| Location | Symbol | Value | Config key |
|----------|--------|-------|------------|
| `Constants.py` | `TARGET_HOURS` | `7.4` | `daily_work_target_hours` |
| `Promark.py` | `LUNCH_MINUTES` | `30` | `lunch_promark_offset_minutes` |

`TARGET_HOURS` is imported by `Commands.py` and used in `_build_day_status()` → `DayStatus(target_hours=TARGET_HOURS)`. Every call site that currently uses `TARGET_HOURS` must switch to reading the setting at runtime. `Constants.py` can keep the value as the documented default.

### 2026-06-25 — Motivation — the Danish lunch context

In Denmark many employers operate a **37-hour** working week where lunch is on top of billable hours (i.e. a full day at the office is ~7h 24m of work + ~30m lunch). Other employers run **40-hour** weeks where lunch is included.

TimeTracker currently shows a hard-coded 7.5-hour target. Both the target and the treatment of lunch/non-billable time must be configurable.

### TUI screen design sketch

```
┌─ Configuration ──────────────────────────────────────────────┐
│                                                              │
│  Daily work target                                           │
│  ○ 37-hour week  (7h 24m)                                    │
│  ○ 40-hour week  (8h 00m)                                    │
│  ● Custom:  [ 7.4 ] hours                                    │
│                                                              │
│  Lunch                                                       │
│  ● Excluded from working hours (not counted toward target)   │
│  ○ Included in working hours                                 │
│  Promark offset:  [ 30 ] minutes  (0 or blank = disabled)    │
│  If actual lunch < offset, the difference is added to the   │
│  day's Promark total.                                        │
│                                                              │
│  Excluded from working hours                                 │
│  Tracked but not counted toward the daily target.            │
│                                                              │
│  ┌─────────────────────┐                                     │
│  │ OtherTask           │  [Remove]                           │
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

---

## Future Ideas

- Per-day work targets (e.g. shorter Fridays).
- Configurable working days (e.g. 4-day week).
- Export/import settings as JSON for backup or sharing across machines.
- **Epic-level exclusion** — exclude all tasks linked to a given Epic (requires a JOIN against `task_catalog`). Task-level free-text exclusion covers v1 needs; this is a clean v2 addition.
- `Lunch` sessions optionally linked to an Epic in the future (currently always unlinked).

---

## Manual Changes

2026-07-16 — Bug fixes post-testing
- `cmd_lunch`: changed from "error if session active" to "auto-close the running session first", matching user expectation that `lunch 1120` = pause at 11:20 + start Lunch at 11:20. This mirrors `cmd_resume` behaviour.
- `cmd_resume`: changed task-carry logic to skip all non-work session types when looking for the task to carry forward: `"Lunch"` (always), any task in `excluded_tasks` (e.g. commute, coffee walk), and any task in `always_separate_tasks` (e.g. Sick, Doctor, Bank meeting). Resuming after any non-work marker now restores the last real work task.
- Feature document and `docs/commands.md` updated to reflect the corrected behaviour.

2026-07-07 — Refinement pass
- Removed stale "Not yet fully defined — initial brainstorm only" caveat from Requirements.
- Status advanced from Refinement → Proposed.
- Added explicit interaction model for the config screen: edits are held in memory; [Save] writes + closes; [Close] / Escape discards.
- Clarified `cmd_lunch()` behaviour when a session is already active (errors out, same as `cmd_start`).
- Clarified that `cmd_lunch()` must NOT call `_notify_if_new_task` — Lunch is intentionally epic-free.
- Added validation rules for all input fields (daily target, Promark offset, list items).
- Resolved "or a dedicated SettingsStorage.py" ambiguity: use `SettingsStorage.py`; DDL still in `Storage.py → create_schema()`.
- Resolved how settings flow into `Promark.py`: passed as plain values by `Commands.py`; `Promark.py` does not import `SettingsStorage.py`.
- Added edge case: if a day has zero normal sessions (all sessions are always-separate/Lunch), no consolidated Promark row is emitted for that day.
- Added note to remove unused `LUNCH_START`, `LUNCH_END`, and `LUNCH_MINUTES` constants from `Promark.py`.
- Specified `updated_at` format: local datetime via `datetime.now().isoformat(timespec='seconds')`.
- Added "Add exclusion…" UI interaction: inline input revealed on button click; Enter adds, Escape cancels.
- Added explicit Affected Files table.
- Fixed Next Step section (was still describing Brainstorming → Refinement).

2026-07-07
- Resolved Q1 (keybinding): both `Ctrl+,` and the `config` command open the config screen.
- Resolved Q4 (Promark lunch offset): `LUNCH_MINUTES` is replaced by the configurable `lunch_promark_offset_minutes` setting. Redesigned as part of a dedicated Lunch configuration section.
- Resolved Q6 (always-separate Promark row format): always-separate rows show **hours only**, no synthetic time range. Promark model documented: consolidated entry is `first_start + stacked_hours + lunch_offset`; removing always-separate sessions from the pool adjusts the end time; generating a synthetic range for the separate row is unnecessary.
- Added concrete always-separate example: Sick/Syg session on a partial work day. The regular work sessions produce the consolidated Promark row; the sick hours appear as a separate hours-only row in a different payroll bucket. Confirms that always-separate tasks count toward the full registered day but not as regular worked hours in the consolidated entry.
- Clarified always-separate multi-bucket behaviour: each distinct always-separate task type on a given day produces its own dedicated Promark row — types are never merged together. Example: Doctor + Børns første sygedag + Work → three separate Promark rows. Requirements updated to reflect this explicitly.
- Added `lunch` command requirement: a new command that creates a session with `task = "Lunch"`, not linked to any epic.
- Lunch now has a first-class config section (included/excluded toggle + Promark offset) instead of being a generic entry in the `excluded_tasks` list.
- Q3 (per-day targets) deferred to Future Ideas.
- Q5 (notification interval) diverted to `features/config-interval.md`.
- Layout density persistence diverted to `features/config-layout.md`.
- Non-Goals section populated.
- TUI screen sketch and settings repository updated to reflect Lunch section.

2026-07-03 — Epic Catalog review
- Epic Catalog is now Completed. The prerequisite is satisfied; this feature may proceed to design.
- Open question #2 (free-text exclusions) resolved.
- Code audit findings added to Brainstorm Notes.
- Epic-level exclusion added to Future Ideas; not in v1 scope.

2026-06-25
- Feature document created based on user request.
- Prerequisites identified: TUI-Only Interaction, Epic Catalog.
- "Always-separate tasks" concept added.

---

## Documentation Plan

| File | Action | Description |
|------|--------|-------------|
| `docs/configuration.md` | Create | New doc describing the configuration screen, all available settings, defaults, and storage. |
| `docs/commands.md` | Update | Add `config` and `lunch` command entries; note that excluded tasks affect the `status` command output and always-separate tasks affect the `promark` output. |
| `docs/tui.md` | Update | Add the configuration screen to the TUI reference (keybinding `Ctrl+,`, navigation, Save/Close behaviour). |
| `docs/sqlite-datasource.md` | Update | Document the new `settings` and `settings_h` table schemas and their triggers. |

---

## Next Step

> **Current status:** Documented
> **To reach Completed:** User confirms the documentation is accurate and the feature is working as described.
