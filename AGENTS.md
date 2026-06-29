# AGENTS.md

## Project Overview

This is a Python 3.12 CLI/TUI application.

The project is developed using AI-assisted ("vibe coded") workflows, but design decisions remain under human control. The primary goal is to maintain a clear separation between design discussions and implementation work.

---

# Core Principles

## Human Approval Before Implementation

New features must be designed before they are implemented.

For every new feature:

1. Create a feature design document at:

```text
feature/<feature>.md
```

2. Use the feature document for brainstorming and design iterations.

3. The feature document may go through multiple revisions between the user and the LLM.

4. No implementation is allowed until the user explicitly approves the design.

If design approval is unclear, assume implementation is not allowed.

---

## Design Documents Drive Development

Every implemented feature must have a corresponding feature document.

All behavior introduced by the codebase should be traceable to either:

* An approved feature design
* A bug fix

If neither exists, implementation should not proceed.

---

## Documentation Is Mandatory

Every implemented feature must be documented.

Feature documentation belongs in:

```text
docs/<feature>.md
```

The documentation should describe the feature as it currently exists in the application.

Documentation must reflect reality, not future plans.

Code and documentation must never intentionally diverge.

---

# Feature Workflow

## Status Lifecycle

Feature documents should contain a status field.

Example:

```md
Status: Draft
```

Valid states:

```text
Brainstorming
Refinement
Proposed
Approved
Implemented
Documented
Completed
```

Implementation may only begin once the feature status is:

```text
Approved
```

**Important:** Setting the status to `Approved` does NOT trigger implementation.
The LLM must never begin implementing a feature on its own initiative, even if the status is `Approved`.
Implementation begins only when the user explicitly requests it in a new session, with a direct reference to the feature document.

When the feature is in `Completed` and has been documented it may be removed. 

---

## Recommended Feature Template

```md
# Feature: Example Feature

Status: Brainstorming

## Purpose

Describe why the feature exists.

## Next Step

State what must happen before the status can advance to the next stage.
Update this section every time the status changes.

Example:

> **Current status:** Brainstorming
> **To reach Refinement:** Brainstorm notes are rich enough to evaluate — move to critical review mode.

> **Current status:** Refinement
> **To reach Proposed:** All requirements are specific, Non-Goals are explicit, and no new ideas are being added.

> **Current status:** Proposed
> **To reach Approved:** User reviews and explicitly approves the design.

> **Current status:** Approved
> **To reach Implemented:** User opens a new session and explicitly requests implementation with a reference to this feature document.

> **Current status:** Implemented
> **To reach Documented:** All files listed in the Documentation Plan are created or updated.

> **Current status:** Documented
> **To reach Completed:** User confirms the documentation is accurate and the feature is working as described.

## Requirements

Functional requirements.

## Non-Goals

What this feature explicitly does not do.

## Manual Changes

Record human decisions that override previous discussions.

Example:

2026-06-12
- User changed validation rule.
- Previous brainstorming decisions on this topic are superseded.

## Documentation Plan

List every documentation file that must be created or updated when this feature is implemented.

For each entry, state whether the file should be **created** (new) or **updated** (existing), and briefly describe what changes are needed.

Example:

| File | Action | Description |
|------|--------|-------------|
| `docs/commands.md` | Update | Add new `export` command to the command reference |
| `docs/export.md` | Create | New doc describing export behavior and options |

> Note: A single feature may require changes to multiple documentation files.
> Always check existing docs before creating a new file — it may be more appropriate to extend an existing one.

## Brainstorm Notes

Discussion history and ideas.

## Future Ideas

Ideas that may be useful later but are NOT approved work.
```

---

## AI Behavior by Feature Status

When assisting with a feature document, the LLM should adjust its approach based on the current status.

### Brainstorming

**Goal:** Generate a wide solution space. Do not self-filter.

- Explore multiple approaches, even contradictory ones
- Raise adjacent problems the user may not have considered
- Suggest unconventional or non-obvious solutions
- Do not yet evaluate feasibility or scope
- Do not produce a Requirements list — that comes later
- Capture all ideas under `## Brainstorm Notes`

### Refinement

**Goal:** Critically evaluate the brainstorm and converge on what is realistic.

- Review `## Brainstorm Notes` and identify what is feasible given the project's scope and constraints
- Flag ideas that are vague, overly ambitious, or out of scope
- Begin drafting a concrete `## Requirements` list
- Begin drafting `## Non-Goals` — explicit exclusions are as important as inclusions
- Prefer the simplest solution that satisfies the core need
- Do not invent new ideas; work only with what was captured during brainstorming

**To reach Proposed:** All requirements must be specific enough that a developer could implement them without further design discussion.

### Proposed and beyond

Normal focused behavior — answer precisely, avoid speculation, stay within approved scope.

---

# Bug Fix Workflow

Bug fixes do not require a feature design document.

However, before implementing a bug fix, determine whether the change alters feature behavior.

If the bug fix changes documented behavior, update:

```text
docs/<feature>.md
```

accordingly.

---

# Documentation Rules

Documentation should focus on the current state of the application.

## Multiple Files May Need Updating

A single feature can affect more than one documentation file. Before writing any documentation:

1. Review all existing files under `docs/` to identify any that already cover related behavior.
2. Prefer **updating** an existing file over creating a new one when the content logically belongs there.
3. Create a new file only when the feature introduces a genuinely distinct topic.

Every affected documentation file must be updated — not just the most obvious one.

## Suggested Sections

Suggested sections for a documentation file:

```md
# Feature Name

## Purpose

## Current Behavior

## Usage

## Limitations

## Notes

## Related Features
```

Future ideas should generally remain in:

```text
feature/<feature>.md
```

rather than user-facing documentation.

---

# Python Guidelines

## Prefer Explicitness Over Cleverness

Readability is preferred over advanced Python tricks.

The codebase should remain understandable to developers whose primary background is not Python.

Avoid introducing complexity solely to achieve more "Pythonic" code.

---

## Explain Advanced Python Features

When using advanced Python-specific language features, prioritize clarity.

Examples include:

* TypeVar
* ParamSpec
* Protocol
* Annotated
* Self
* Generic types
* overload
* descriptor protocols
* metaclasses
* contextvars

and special methods such as:

* **new**
* **getattr**
* **getattribute**
* **class_getitem**
* property-heavy APIs

When such features are genuinely beneficial:

1. Add explanatory comments.
2. Explain why the feature was chosen.
3. Prefer maintainability over cleverness.

Code should optimize for future understanding.

---

# Dependency Policy

## Prefer Battle-Tested Libraries Over Custom Implementations

Well-established, widely adopted libraries should always be considered before writing a custom solution.

Examples of libraries that should be preferred when relevant:

* **Textual / Rich** — terminal UI and formatting
* **SQLAlchemy** — database access and ORM
* **Pydantic** — data validation and settings management
* **Click / Typer** — CLI argument parsing

A custom implementation is acceptable when:

* The required scope is small and self-contained
* No well-known library covers the use case well
* The added dependency would far exceed the complexity it replaces

When proposing or accepting a dependency, document:

* Why it is needed
* Alternatives considered (including a custom implementation)
* Benefits gained
* Maintenance implications

Avoid dependency sprawl — each dependency must justify its inclusion. But do not reject a proven library simply to avoid a dependency.

---

# Database Conventions

Every new SQLite table introduced to the project must follow the conventions already established by the `sessions` / `sessions_h` pair. These rules ensure a consistent, auditable data layer.

## Table Naming

| Purpose | Naming pattern |
|---------|---------------|
| Main data table | `<noun>` (e.g. `sessions`, `settings`) |
| History / shadow table | `<noun>_h` (e.g. `sessions_h`, `settings_h`) |

## History / Shadow Table

Every main table must have a corresponding `_h` shadow table that records every INSERT, UPDATE, and DELETE automatically via SQLite triggers. Application code **never writes to `_h` tables directly**.

The `_h` table always has these extra columns prepended:

| Column | Type | Notes |
|--------|------|-------|
| `h_id` | INTEGER | Primary key, auto-incremented |
| `h_operation` | TEXT | `'I'` Insert · `'U'` Update · `'D'` Delete |
| `h_timestamp` | TEXT | ISO-8601 UTC datetime (`datetime('now')`) |

All remaining columns mirror the main table exactly (same names, same types, same nullability — except primary-key constraints are dropped).

Example for a hypothetical `widgets` table:

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

## Triggers

Three triggers must be created — one for each DML operation. All use `CREATE TRIGGER IF NOT EXISTS` and fire `AFTER` the statement:

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

Key rules:
- DELETE triggers reference `OLD.*`; INSERT and UPDATE triggers reference `NEW.*`.
- `h_timestamp` is always UTC — it is an audit timestamp, not a user-visible time.
- Triggers fire inside the same transaction as the originating statement, so history rows are committed or rolled back atomically.

## Schema Location

All DDL (main table, history table, and triggers) belongs in `Storage.py` inside the `create_schema()` function. This function is called once at application startup and uses `IF NOT EXISTS` throughout, making it a safe no-op after the first run.

No DDL may be placed outside `create_schema()`.

## Layer Rules

The data access layer follows a strict dependency chain — no layer may skip a level:

```
Commands.py  →  Storage.py  →  db/repository.py  →  db/connection.py
```

- `Commands.py` calls `Storage.py` functions only. It never imports from `db/`.
- `Storage.py` calls `db/repository.py` helpers only (except `create_schema`, which uses `Connection` directly to batch all DDL in one transaction).
- `db/repository.py` calls `db/connection.py` only.
- Nothing outside `db/` imports from `db/` except `Storage.py`.

When a new domain area is large enough (e.g. settings, epics), it may live in a separate `*Storage.py` module (e.g. `SettingsStorage.py`) that follows the same rules.

---

# Refactoring Guidelines

Refactoring is encouraged when it improves:

* Readability
* Maintainability
* Simplicity
* Reduction of duplication

Behavior-changing refactors require approval.

Pure refactoring that does not alter behavior may proceed.

When in doubt, ask.

---

# Definition of Done

A task is not complete until all applicable items are complete:

* Implementation completed
* Tests added or updated
* Documentation updated
* Type hints updated
* Existing functionality verified
* Feature status updated when appropriate

---

# Change Summary Requirements

After implementation, provide a summary containing:

## Files Changed

List all modified files.

## Reasoning

Explain why each change was made.

## Risks

Describe potential side effects or concerns.

## Follow-Up Suggestions

Optional improvements that may be worth considering later.

---

# Guiding Rule

The most important rules in this repository are:

1. No implementation before feature approval.
2. Documentation and code must be updated together.
3. Every behavior change must be traceable to a feature design or bug fix.

When uncertain, stop and ask for clarification rather than making assumptions.
