# Configuration

## Purpose

The configuration screen lets the user control application behaviour without
touching code. Settings are stored in the SQLite database and apply immediately
on the next data refresh.

Configurable settings:

1. **Daily work target** — the number of hours that constitutes a full working day.
2. **Lunch handling** — whether the lunch break is paid working time or the
   employee's own time, and how long the contractual break is.
3. **Excluded tasks** — arbitrary tasks that should not count toward the daily target.
4. **Always-separate tasks** — tasks that appear as standalone rows in Promark output
   rather than being folded into the consolidated day entry.

---

## Current Behaviour

### Opening the configuration screen

| Method | Description |
|--------|-------------|
| Type `config` in the command bar | Opens the configuration screen |
| Press `Ctrl+,` | Opens the configuration screen (VS Code convention) |

The screen is a scrollable modal overlay. All edits are held in memory until
the user saves.

### Interaction model

- **[Save]**: validates all fields; if valid, writes all values to the database
  and closes the screen. If any field is invalid, shows an inline error on the
  offending field and stays open.
- **[Close] / Esc**: discards all unsaved in-memory changes and closes the
  screen without writing to the database.

---

## Usage

### Daily work target

Three options are presented as a radio group:

| Option | Hours stored | Description |
|--------|-------------|-------------|
| 37-hour week | `7.4` h | Standard Danish 37-hour week (7h 24m per day) |
| 40-hour week | `8.0` h | Standard 40-hour week (8h per day) |
| Custom | user-entered | Any positive decimal number of hours (> 0, ≤ 24) |

When the screen opens, the option matching the stored value is pre-selected.
Selecting a preset disables the custom input and fills it with the preset value
for display. Selecting "Custom" enables the input.

**Validation**: the custom value must parse as a positive float (> 0 and ≤ 24).
An invalid value shows an inline error and blocks Save.

---

### Lunch section

Controls how `Lunch` sessions (sessions created with the `lunch` command or
tagged as `Lunch`) are treated. `"Lunch"` is a hardcoded reserved task name.

#### Included / Excluded radio

| Option | Behaviour |
|--------|-----------|
| Included in working hours | The break is paid time. `Lunch` sessions count toward the daily target like any other session, nothing is added to the registered day span, and the `Leave` row shows a single projection. |
| Excluded from working hours (default) | The break is your own time. `Lunch` sessions are filtered out before any hours-worked calculation, the configured lunch duration is always reserved in the registered day span, and the `Leave` row shows the `(w/e lunch)` variant until lunch has been logged. |

The exclusion applies only to hours totals and progress bars. Lunch sessions
are always stored in the database and visible in the timeline and session
tables.

#### Lunch duration (minutes)

The contractual length of the lunch break.

- Default: `30`. Blank is treated as the default.
- Valid range: `0`–`240`, whole minutes.

When lunch is **excluded** from working hours this single value drives:

1. **The registered day span** (Weekly Overview day header and the `promark`
   command): `end = first_start + worked_minutes + lunch_duration_minutes`.
   The addition is flat and unconditional — if you took only 20 minutes of
   lunch the day is still registered with a 30-minute break, and a day with
   no `Lunch` session at all still reserves it.
2. **The `Leave` projection**: the `(w/e lunch)` figure is the normal leave
   time plus the lunch duration, shown only until a `Lunch` session exists
   for the day.

When lunch is **included** in working hours the value is not used.

**Validation**: must be a whole number of minutes between 0 and 240, or blank.

---

### Excluded tasks section

A list of free-text task identifiers that are excluded from working-hours
calculations.

- Time logged against excluded tasks is **still recorded** in the database
  and **visible** in all panels — it is only omitted from hours totals and
  the progress bar.
- Exclusion matching is case-sensitive.
- `"Lunch"` cannot be added to this list — it is configured in the Lunch
  section above.

**UI interaction:**

1. Click **"Add exclusion…"** to reveal an inline input below the list.
2. Type the task name and press `Enter` to add it.
3. Press `Esc` to cancel without adding.
4. Click **Remove** next to any item to remove it from the in-memory list.

Changes take effect only when **[Save]** is pressed.

---

### Always-separate tasks section

A list of free-text task identifiers that must appear as **standalone rows**
in Promark output rather than being folded into the consolidated day entry.

- Time logged against always-separate tasks **does count** toward the
  working-hours total. The separation is exclusively a Promark concern.
- Always-separate tasks are fully visible in the Today panel, Week panel,
  Task Summary, and Epic summary.
- Each distinct always-separate task type on a day produces its own Promark
  row (hours only — no synthetic time range).
- `"Lunch"` cannot be added to this list.

The UI interaction is identical to the Excluded tasks section.

---

## Settings Storage

Settings are stored in the `settings` SQLite table as key-value pairs.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `daily_work_target_hours` | decimal string | `"7.4"` | Daily work target in hours |
| `lunch_excluded` | `"true"` / `"false"` | `"true"` | Whether lunch is the employee's own time (excluded from hours) |
| `lunch_duration_minutes` | integer string | `"30"` | Contractual lunch length, used for the day span and the leave projection |
| `excluded_tasks` | JSON array | `"[]"` | Task identifiers excluded from hours |
| `always_separate_tasks` | JSON array | `"[]"` | Task identifiers for standalone Promark rows |

> **Retired key:** `lunch_promark_offset_minutes` is no longer written. If it
> holds a non-zero value and `lunch_duration_minutes` has never been written,
> the old value is read once as the lunch duration. The old row is left in
> place and is otherwise ignored.

Defaults are encoded in `SettingsStorage.SettingsRepository` — the application
works correctly with an empty `settings` table (fresh database).

All changes written by [Save] use `INSERT OR REPLACE` and are shadowed by the
`settings_h` history table via triggers.

### Protection against accidental overwrites

[Save] writes **all** settings, so the screen must never display state it
failed to load:

- If a stored task list cannot be parsed as a JSON array of strings, the error
  is logged with the raw value, the list is shown as empty, and **Save is
  blocked** with an inline error. Repair or clear the stored value first.
- Text left in an open "add task" input is committed before saving, so
  clicking [Save] directly after typing a task name no longer discards it.

---

## Limitations

- **Per-day targets** are not supported — a single daily target applies to all
  weekdays. Compressed or flex schedules are deferred to a future version.
- **Epic-level exclusion** is not supported — exclusion is task-string based.
  Excluding all tasks linked to a given Epic is a future addition.
- **Export / import** of settings is not supported. Settings are local to the
  database file.

---

## Decisions

**2026 — Lunch excluded from working hours by default**
- Decision: `lunch_excluded` defaults to `"true"`.
- Rejected: Treating lunch as paid time by default.
- Driver: `Law` — the Danish working-time norm is an unpaid break; the
  37-hour week is exclusive of lunch. The setting exists because other
  employment terms do include it.

**2026 — 7.4 hours as the default daily target**
- Decision: `daily_work_target_hours` defaults to `"7.4"`.
- Rejected: 8.0 hours.
- Driver: `Business` — 7.4 h is the decimal form of 7 h 24 m, one fifth of
  the standard 37-hour week.

**2026 — Configured lunch duration, not the measured break**
- Decision: `lunch_duration_minutes` is applied flat to the day span,
  regardless of the actual `Lunch` session length or whether one was logged.
- Rejected: Deriving the deduction from the logged session.
- Driver: `Law` — the contractual break is a fixed quantity. Registering the
  measured value would under- or over-report against the employment terms.

**2026 — Exclusion is task-string based, not Epic based**
- Decision: `excluded_tasks` matches on the task label.
- Rejected: Excluding every task linked to a given Epic.
- Driver: `Technical` — excluded activities (commute, coffee walk) are
  typically unlinked anyway, and Epic-level exclusion would make the hours
  total depend on catalog state.

**2026 — `Lunch` cannot be added to the generic task lists**
- Decision: Lunch has a dedicated configuration section and is rejected from
  `excluded_tasks` and `always_separate_tasks`.
- Rejected: Treating it as an ordinary configurable task.
- Driver: `Technical` — two independent switches over the same task would
  allow contradictory states.

**2026 — Settings read at call time, with no in-memory cache**
- Decision: Every function reads settings when it needs them.
- Rejected: A cached singleton loaded at startup.
- Driver: `Technical` — changes take effect immediately after Save with no
  invalidation logic, and the query cost is negligible against a local file.

**2026 — `Esc` discards configuration changes**
- Decision: Closing the screen without Save discards all in-memory edits.
- Rejected: Auto-saving on change.
- Driver: `Preference` — settings alter historical calculations, so the
  change should be deliberate.

---

## Notes

- Settings are read at call time in every function that needs them. There is no
  in-memory singleton — changing settings takes effect immediately after Save.
- The `Lunch` task is a first-class concept and has its own dedicated
  configuration section. It cannot be added to the general `excluded_tasks` or
  `always_separate_tasks` lists.

---

## Related Documents

- [Documentation Index](../index.md)
- [Commands](commands.md) — `lunch` and `config` command reference
- [SQLite Datasource](sqlite-datasource.md) — `settings` and `settings_h` table schemas
- [User Interface Design](../design/user-interface-design.md) — configuration screen layout and `Ctrl+,`
