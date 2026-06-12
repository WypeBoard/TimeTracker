# Feature: Replace Excel with a Structured Datasource

Status: Brainstorming

## Purpose

The Excel file currently serves two distinct roles:

1. **Data storage** — the `Time Log` sheet holds raw session records.
2. **Derived reporting** — the `Summary` and `Promark` sheets are computed views
   rebuilt on every `stop` or `promark` command.

Originally keeping everything in Excel made sense because users needed to
manually edit entries, and the formatted sheets provided an easy visual overview.
As the application matures with more CLI commands, manual editing is becoming
less necessary, and the Excel dependency is adding complexity without equivalent
benefit.

The goal of this feature is to replace the Excel file with a lighter-weight
datasource that is easier to maintain, requires fewer dependencies, and better
separates raw data from presentation.

---

## Requirements

- All existing session data (date, start, end, task/epic) must be preserved.
- Commands `start`, `pause`, `stop`, `restart`, `task`, `status`, `log`,
  and `promark` must continue to work identically from the user's perspective.
- The new datasource must be durable — a crash mid-write must not corrupt
  existing data.
- Week number must be derived from the date programmatically, not stored
  (it is already computed this way in `read_log`).
- A migration path for existing `.xlsx` files should be considered.

## Non-Goals

- This feature does not change the terminal output format.
- This feature does not redesign the data model beyond what is needed to
  remove Excel.
- Exporting back to Excel for external sharing is out of scope for now.

---

## Manual Changes

*(None yet — initial brainstorm.)*

---

## Brainstorm Notes

### What Excel currently provides

| Concern | Current Excel approach | Replacement responsibility |
|---|---|---|
| Persistent storage | `.xlsx` file on disk | New datasource file |
| Human-readable log | Time Log sheet | Terminal `log` command (already exists) |
| Weekly summary view | Summary sheet | Terminal `log` / future TUI |
| Promark view | Promark sheet | Terminal `promark` command (already exists) |
| Week number | `=WEEKNUM()` formula | `datetime.isocalendar()` (already done in code) |
| Hours calculation | `=IF(D{r}<>"",ROUND(...))` formula | Python arithmetic (already done in `read_log`) |

The terminal commands already reproduce every piece of information in the
derived sheets. The Excel reporting layer is largely redundant at this point.

---

### Candidate datasources

#### Option A — JSON (user suggestion)

A single `.json` file containing a list of session objects.

```json
[
  {
    "date": "2026-06-12",
    "start": "08:30",
    "end": "12:00",
    "task": "Epic-42"
  },
  {
    "date": "2026-06-12",
    "start": "12:45",
    "end": null,
    "task": "Epic-42"
  }
]
```

**Pros:**
- Zero new dependencies — `json` is part of the standard library.
- Human-readable and hand-editable in any text editor (replaces the manual
  editing use case when needed).
- Simple flat structure maps directly to the current data model.
- Easy to debug, diff, and back up.

**Cons:**
- The entire file must be loaded and rewritten on every mutation. For years of
  time tracking this is unlikely to be a performance concern (a full year of
  daily entries is well under 500 KB).
- No atomic write built in — needs a write-to-temp-then-rename pattern to
  prevent corruption on crash.
- No built-in querying — filtering by week is done in Python (already the case today).

**Verdict:** A strong, simple fit. The `openpyxl` dependency drops to zero for
the datasource layer. Retains hand-editability in any text editor.

---

#### Option B — SQLite

A single `.db` file using the stdlib `sqlite3` module.

Schema sketch:
```sql
CREATE TABLE sessions (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    date    TEXT NOT NULL,   -- YYYY-MM-DD
    start   TEXT NOT NULL,   -- HH:MM
    end     TEXT,            -- HH:MM, NULL if open
    task    TEXT DEFAULT ''
);
```

**Pros:**
- Zero new dependencies — `sqlite3` is part of the standard library.
- ACID transactions — writes are atomic by default, no manual temp-file dance needed.
- SQL querying — filtering by date range or week is simple and fast.
- Scales to very large datasets without loading everything into memory.
- An open session check becomes a simple `WHERE end IS NULL` query.

**Cons:**
- Binary format — not hand-editable without an external SQLite tool (e.g.
  DB Browser for SQLite or the `sqlite3` CLI).
- More code to write and maintain (schema creation, SQL strings, migration).
- Loses the "open in a text editor" convenience of JSON.

**Verdict:** The most technically robust choice. Best fit if manual editing is
considered fully obsolete. Slightly higher implementation complexity than JSON.

---

#### Option C — TOML

A `.toml` file, readable by the Python 3.11+ stdlib `tomllib`.

**Pros:**
- Human-readable, arguably the most ergonomic plain-text config format.

**Cons:**
- `tomllib` (stdlib) is **read-only**. Writing TOML requires the third-party
  `tomli_w` package — introducing a dependency.
- TOML is designed for configuration, not append-heavy record storage.
  A list of hundreds of sessions in TOML becomes unwieldy.

**Verdict:** Not well suited to this use case. Ruled out.

---

#### Option D — CSV

A `.csv` file using the stdlib `csv` module.

**Pros:**
- Zero dependencies, extremely simple.
- Directly openable in Excel/LibreOffice if needed.

**Cons:**
- No schema enforcement — type coercion and quoting edge cases.
- All values are strings; null handling (`end` during an open session) is
  ambiguous by convention.
- Structurally fragile — a missing comma corrupts an entire row.

**Verdict:** CSV is simpler than JSON but offers fewer guarantees. JSON is
preferred when hand-editability is the goal.

---

### Recommendation summary

| Option | New dependencies | Hand-editable | Crash-safe | Implementation complexity |
|---|---|---|---|---|
| JSON | None (stdlib) | ✅ Yes | ⚠️ Needs temp-rename pattern | Low |
| SQLite | None (stdlib) | ⚠️ Needs external tool | ✅ ACID built-in | Medium |
| TOML | `tomli_w` (3rd party) | ✅ Yes | ⚠️ Needs temp-rename pattern | Low–Medium |
| CSV | None (stdlib) | ⚠️ Fragile | ⚠️ Needs temp-rename pattern | Low |

**If hand-editability is a priority → JSON.**
**If robustness and queryability are the priority → SQLite.**

Both leading options eliminate the `openpyxl` dependency entirely.

---

### Impact on existing modules

| Module | Change needed |
|---|---|
| `Constants.py` | Replace `EXCEL_FILE`, `LOG_SHEET`, `SUM_SHEET` with a new file path constant |
| `Workbook.py` | Replace entirely with a new datasource module (e.g. `Storage.py`) |
| `Summary.py` | Can be removed — its content is already covered by terminal commands |
| `Styles.py` | Can be removed — all styling is Excel-specific |
| `Commands.py` | Replace `load_workbook` / openpyxl calls with datasource reads/writes |
| `Promark.py` | Minimal change — reads via `read_log`, which lives in `Workbook.py` today |
| `Printer.py` | No change expected |
| `requirements.txt` | Remove `openpyxl` |

---

### Migration

Users with existing `.xlsx` files should be able to migrate their data. A
one-shot migration utility could:

1. Load the existing `.xlsx` using `openpyxl`.
2. Read all rows from the `Time Log` sheet.
3. Write them to the new datasource file.
4. Rename or archive the `.xlsx`.

This could be a separate `migrate` subcommand or a standalone script, and
does not need to be part of the initial implementation.

---

### Open questions for design approval

1. **JSON vs SQLite** — Which trade-off matters more: hand-editability (JSON)
   or robustness without a temp-file pattern (SQLite)?

2. **File location** — Should the new file live in `~` like the current `.xlsx`,
   or move to a more conventional path such as `~/.local/share/timetracker/`?

3. **Summary and Promark sheets** — Once Excel is removed these sheets disappear.
   Is that acceptable, given that `log` and `promark` commands already cover the
   same information in the terminal?

4. **Migration** — Should a migration utility be in scope for this feature, or
   treated as a separate follow-up?

5. **Single file vs. per-year files** — Keep all sessions in one file, or split
   by year (e.g. `timetracker-2026.json`)?

---

## Future Ideas

- Export to CSV or Excel for sharing/reporting to external tools.
- Backup/sync support (cloud or git-tracked data file).
- Multi-machine support via a shared SQLite file or lightweight remote API.
