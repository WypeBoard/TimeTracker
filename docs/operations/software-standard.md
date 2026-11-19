# Software Standard

## Purpose

The rules all code in this repository must follow. This document covers *how*
code is written; [`AGENTS.md`](../../AGENTS.md) covers *when* it may be
written. Where the two overlap, this document is authoritative on technical
matters and `AGENTS.md` is authoritative on process.

---

## Current Behaviour

### Language and tooling

| Item | Value |
|------|-------|
| Language | Python 3.12+ |
| UI | Textual + Rich |
| Database | SQLite (`sqlite3`, standard library) |
| Tests | pytest |
| Runtime dependencies | `requirements.txt` |
| Development dependencies | `requirements-dev.txt` |

---

## Code Style

### Prefer explicitness over cleverness

Readability wins over idiom. The codebase must stay understandable to
developers whose primary language is not Python. Do not add complexity purely
to make code more "Pythonic".

### Explain advanced language features

When a feature below is genuinely the right tool, use it — but add a comment
explaining why it was chosen:

`TypeVar` · `ParamSpec` · `Protocol` · `Annotated` · `Self` · generics ·
`overload` · descriptors · metaclasses · `contextvars`

and the special methods `__new__`, `__getattr__`, `__getattribute__`,
`__class_getitem__`, plus property-heavy APIs.

Code is optimised for whoever reads it next.

### Type hints

Public functions carry type hints. Hints are updated with the code they
describe — a stale hint is worse than no hint.

### Module docstrings

Modules that render anything the user sees document what is displayed and
where the rule comes from. `app/QuickStatsPanel.py` is the reference example:
every displayed value is described, with a link back to the feature that
defined it.

---

## Architectural Rules

The layering chain is mandatory. Full description in
[Architecture](../design/architecture.md).

```
app/  →  Commands.py  →  *Storage.py  →  db/repository.py  →  db/connection.py
```

- No layer may skip a level.
- `Commands.py` never imports from `db/`.
- Nothing outside `db/` imports from `db/` except the `*Storage.py` modules.
- Derived values (totals, projections) are computed in one place and called
  from everywhere else — never recomputed in a panel.

When a domain area grows large enough it gets its own `*Storage.py` module
(as `SettingsStorage.py` and `EpicStorage.py` did) following the same rules.

---

## Database Conventions

Every new table follows the pattern established by `sessions` / `sessions_h`.

### Naming

| Purpose | Pattern |
|---------|---------|
| Main table | `<noun>` — `sessions`, `settings` |
| History table | `<noun>_h` — `sessions_h`, `settings_h` |

### History tables

Every main table has an `_h` shadow table recording every INSERT, UPDATE and
DELETE via triggers. **Application code never writes to `_h` tables.**

Three columns are prepended:

| Column | Type | Notes |
|--------|------|-------|
| `h_id` | INTEGER | Primary key, auto-incremented |
| `h_operation` | TEXT | `'I'` Insert · `'U'` Update · `'D'` Delete |
| `h_timestamp` | TEXT | ISO-8601 UTC (`datetime('now')`) |

Remaining columns mirror the main table exactly — same names, same types,
same nullability — except that primary-key constraints are dropped.

```sql
CREATE TABLE IF NOT EXISTS widgets (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL,
    value TEXT
);

CREATE TABLE IF NOT EXISTS widgets_h (
    h_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    h_operation TEXT    NOT NULL,
    h_timestamp TEXT    NOT NULL,
    id          INTEGER NOT NULL,
    name        TEXT    NOT NULL,
    value       TEXT
);
```

### Triggers

One per DML operation, all `CREATE TRIGGER IF NOT EXISTS` and all `AFTER`:

```sql
CREATE TRIGGER IF NOT EXISTS widgets_after_insert
AFTER INSERT ON widgets
BEGIN
    INSERT INTO widgets_h (h_operation, h_timestamp, id, name, value)
    VALUES ('I', datetime('now'), NEW.id, NEW.name, NEW.value);
END;

CREATE TRIGGER IF NOT EXISTS widgets_after_update
AFTER UPDATE ON widgets
BEGIN
    INSERT INTO widgets_h (h_operation, h_timestamp, id, name, value)
    VALUES ('U', datetime('now'), NEW.id, NEW.name, NEW.value);
END;

CREATE TRIGGER IF NOT EXISTS widgets_after_delete
AFTER DELETE ON widgets
BEGIN
    INSERT INTO widgets_h (h_operation, h_timestamp, id, name, value)
    VALUES ('D', datetime('now'), OLD.id, OLD.name, OLD.value);
END;
```

Rules:
- DELETE triggers reference `OLD.*`; INSERT and UPDATE reference `NEW.*`.
- `h_timestamp` is always UTC — it is an audit value, not a user-visible time.
- Triggers run in the originating transaction, so history commits or rolls
  back atomically with the change.

### DDL location

All DDL — main tables, history tables, triggers — lives in `create_schema()`
in `Storage.py`. It runs once at startup and uses `IF NOT EXISTS` throughout,
making it a safe no-op afterwards. **No DDL may exist outside this function.**

---

## Dependency Policy

Established, widely adopted libraries are considered before any custom
implementation. Preferred where relevant:

- **Textual / Rich** — terminal UI and formatting
- **SQLAlchemy** — database access and ORM
- **Pydantic** — validation and settings
- **Click / Typer** — CLI argument parsing

A custom implementation is acceptable when the scope is small and
self-contained, no established library fits well, or the dependency would
cost more than the complexity it removes.

Each new dependency must document: why it is needed, what alternatives were
considered (including writing it), what is gained, and the maintenance
implications. Avoid sprawl — but do not reject a proven library merely to
avoid a dependency.

---

## Testing

- Tests live in `tests/` and run with `pytest`.
- Tests are added or updated alongside the change they cover.
- Behaviour described in `docs/` should be reachable from a test.

---

## Refactoring

Refactoring is encouraged where it improves readability, maintainability,
simplicity, or removes duplication.

- Pure refactoring that does not change behaviour may proceed.
- Behaviour-changing refactoring requires approval.
- When in doubt, ask.

---

## Definition of Done

A change is complete only when all applicable items are done:

- Implementation complete
- Tests added or updated
- Documentation updated
- Type hints updated
- Existing functionality verified
- Feature status updated where relevant

---

## Decisions

**2025 — `sqlite3` from the standard library instead of an ORM**
- Decision: Database access uses `sqlite3` through a thin repository layer.
- Rejected: SQLAlchemy, despite the dependency policy preferring known
  libraries.
- Driver: `Technical` — the query set is small and fully known, and the
  trigger-based history design needs raw DDL anyway.

**2025 — Audit history via triggers rather than an application audit log**
- Decision: `_h` tables populated by SQLite triggers.
- Rejected: Audit writes in the storage layer.
- Driver: `Technical` — a trigger cannot be bypassed by a new code path.

**2025 — `h_timestamp` in UTC while session times stay local**
- Decision: Audit timestamps are UTC; `start` / `end` are local `HH:MM`.
- Rejected: Storing everything in UTC.
- Driver: `Business` — session times are compared against a working day and a
  payroll system that are both local; audit times are for forensics and must
  be unambiguous.

**2026 — Explicitness preferred over idiomatic Python**
- Decision: Plain, verbose code with comments on advanced language features.
- Rejected: Concise idiomatic Python.
- Driver: `Preference` — the maintainer's primary background is not Python.

---

## Notes

- `Workbook.py`, `Summary.py`, and `Styles.py` are no longer imported and are
  pending deletion. `openpyxl` has already been removed from
  `requirements.txt`.

---

## Related Documents

- [Documentation Index](../index.md)
- [Architecture](../design/architecture.md) — the structure these rules protect.
- [SQLite Datasource](../detailed-design/sqlite-datasource.md) — the schema as built.
- [`AGENTS.md`](../../AGENTS.md) — development process and feature workflow.
