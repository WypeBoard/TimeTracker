# Documentation Index

This project's documentation is organised by **document type**, not by module.
Each type answers a different question and targets a different reader. Before
writing anything new, find the type it belongs to below — creating a new file
is a last resort.

---

## Document Types

| Type | Folder | Answers | Audience |
|------|--------|---------|----------|
| User Design | `docs/design/` | What does the user see, and how do the screens connect? | User, tester, designer |
| Architecture | `docs/design/` | How is the system put together, and why in that shape? | Developer joining the project |
| Detailed Design | `docs/detailed-design/` | What does each process do, and what is the data model? | Developer implementing or changing behaviour |
| Operations | `docs/operations/` | How is it run, supported, and kept consistent? | Whoever has to fix it at 23:00 |

---

## Documents

### Design — `docs/design/`

| Document | Description |
|----------|-------------|
| [User Interface Design](design/user-interface-design.md) | UI guidelines (colour, duration formats, refresh cadence, empty states) followed by the applied design of every screen and overlay, and the navigation map between them. |
| [Architecture](design/architecture.md) | Module map, the layered dependency chain, process model, and the rules that keep them intact. |

### Detailed Design — `docs/detailed-design/`

| Document | Description |
|----------|-------------|
| [Commands](detailed-design/commands.md) | Every command: syntax, arguments, processing, and output. |
| [Configuration](detailed-design/configuration.md) | Every setting, its default, and which calculations it affects. |
| [Epic Catalog](detailed-design/epic-catalog.md) | Epics, task–Epic linking, and the `(Misc)` grouping rule. |
| [SQLite Datasource](detailed-design/sqlite-datasource.md) | Database location, table and trigger schemas, storage API. |

### Operations — `docs/operations/`

| Document | Description |
|----------|-------------|
| [Logging](operations/logging.md) | Log location, rotation, crash capture, and what gets logged. |
| [Software Standard](operations/software-standard.md) | Python style, layering rules, database conventions, and test expectations that all code must follow. |

---

## Decision Records

Every document carries a `## Decisions` section. This is the part that Jira
tickets and commit messages cannot preserve: **why the current behaviour is
what it is, and what was rejected to get there.**

Each entry uses a fixed shape:

| Field | Meaning |
|-------|---------|
| Date | When the decision was taken (`YYYY-MM-DD`) |
| Decision | What the application does now |
| Rejected | The alternative that was considered and not taken |
| Driver | Why — see the driver table below |

### Drivers

| Driver | Meaning |
|--------|---------|
| `Law` | Required by legislation or regulation. Not negotiable; changing it requires legal review. |
| `Business` | A deliberate business or process decision. Can change, but only by the same authority that made it. |
| `Technical` | Forced by a technical constraint — a library limit, a platform behaviour, performance. |
| `Preference` | Taste, habit, or convenience. The weakest driver — safe to revisit at any time. |

The driver matters more than the decision. A reader who knows a rule is
`Preference` can change it freely; one who knows it is `Law` knows not to
touch it without asking. An undocumented rule is indistinguishable from an
accident.

Decisions are **append-only**. When a decision is reversed, keep the original
entry and add a new one that supersedes it — the history of a reversal is
often more useful than the reversal itself.

---

## Rules

1. Documentation describes the application **as it is**, never as it is planned
   to be. Future ideas belong in `features/`.
2. A single change may touch several documents. Check all four folders before
   deciding where an update belongs.
3. Every document ends with `## Related Documents` linking its neighbours, so
   a reader can navigate without returning here.
4. Feature design documents (`features/`) are the *reasoning* record;
   `docs/` is the *result* record. When a feature completes, its durable
   conclusions move into a `## Decisions` section here.

---

## Related Documents

- [`AGENTS.md`](../AGENTS.md) — the development process these documents serve.
- [`README.md`](../README.md) — project overview and installation.
