# Configuration

## Purpose

The configuration screen lets the user control application behaviour without
touching code. Settings are stored in the SQLite database and apply immediately
on the next data refresh.

Configurable settings:

1. **Daily work target** — the number of hours that constitutes a full working day.
2. **Lunch handling** — whether `Lunch` sessions count toward the daily target, and
   how they affect the Promark synthetic end time.
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
tagged as `Lunch`) are treated.

#### Excluded / Included toggle

| Option | Behaviour |
|--------|-----------|
| Excluded (default) | `Lunch` sessions are filtered out before any hours-worked calculation. They do not count toward the daily target or appear in the progress bars. |
| Included | `Lunch` sessions are counted like any other session. |

The exclusion applies only to hours totals and progress bars. Lunch sessions
are always stored in the database and visible in the Today panel and session
tables.

#### Promark offset (minutes)

An integer number of minutes representing the expected lunch duration.

- Default: `0` (disabled).
- Blank is treated as `0`.
- When a day's actual `Lunch` session duration is shorter than the offset, the
  shortfall is added to that day's Promark consolidated end time.
- Formula: `promark_addition = max(0, offset_minutes − actual_lunch_minutes)`.
- This models the expectation that a lunch break of a fixed length is
  "invisible" in Promark — if the user took less lunch than expected, the
  remaining time pushes the day's end time forward.

**Validation**: must be a non-negative integer or blank.

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
| `lunch_excluded` | `"true"` / `"false"` | `"true"` | Whether Lunch sessions are excluded from hours total |
| `lunch_promark_offset_minutes` | integer string | `"0"` | Expected lunch duration for Promark offset |
| `excluded_tasks` | JSON array | `"[]"` | Task identifiers excluded from hours |
| `always_separate_tasks` | JSON array | `"[]"` | Task identifiers for standalone Promark rows |

Defaults are encoded in `SettingsStorage.SettingsRepository` — the application
works correctly with an empty `settings` table (fresh database).

All changes written by [Save] use `INSERT OR REPLACE` and are shadowed by the
`settings_h` history table via triggers.

---

## Limitations

- **Per-day targets** are not supported — a single daily target applies to all
  weekdays. Compressed or flex schedules are deferred to a future version.
- **Epic-level exclusion** is not supported — exclusion is task-string based.
  Excluding all tasks linked to a given Epic is a future addition.
- **Export / import** of settings is not supported. Settings are local to the
  database file.

---

## Notes

- Settings are read at call time in every function that needs them. There is no
  in-memory singleton — changing settings takes effect immediately after Save.
- The `Lunch` task is a first-class concept and has its own dedicated
  configuration section. It cannot be added to the general `excluded_tasks` or
  `always_separate_tasks` lists.

---

## Related Features

- `docs/commands.md` — `lunch` and `config` command reference
- `docs/tui.md` — TUI keybinding reference (Ctrl+,)
- `docs/sqlite-datasource.md` — `settings` and `settings_h` table schemas
