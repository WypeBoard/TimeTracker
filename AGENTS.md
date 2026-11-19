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
Completed
```

Implementation may only begin once the feature status is:

```text
Approved
```

**Important:** Setting the status to `Approved` does NOT trigger implementation.
The LLM must never begin implementing a feature on its own initiative, even if the status is `Approved`.
Implementation begins only when the user explicitly requests it in a new session, with a direct reference to the feature document.

When a feature reaches `Completed` status it must be moved to `features/completed/<feature>.md`.
It must not be deleted — the completed folder is the permanent archive of finished work.

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
> **To reach Completed:** All files listed in the Documentation Plan are created or updated, then move the feature document to `features/completed/`.

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
| `docs/detailed-design/commands.md` | Update | Add new `export` command to the command reference |
| `docs/detailed-design/export.md` | Create | New doc describing export behavior and options |
| `docs/index.md` | Update | Register the new document |

> Note: A single feature may require changes to multiple documentation files.
> Always check existing docs before creating a new file - it may be more appropriate to extend an existing one.

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

Documentation describes the current state of the application.

## Document Types

Documentation is organised by **document type**, not by module. Each folder
answers a different question for a different reader:

| Folder | Type | Answers |
|--------|------|---------|
| `docs/design/` | User Design, Architecture | What the user sees; how the system is shaped |
| `docs/detailed-design/` | Detailed Design | What each process does; the data model |
| `docs/operations/` | Operations | How it is run, supported, and written |

`docs/index.md` is the catalogue of every document and must be updated when a
document is added, moved, or removed.

Before writing anything new, find the type it belongs to. Creating a new file
is a last resort â€” prefer extending an existing document.

## Decisions Are Mandatory

Every document carries a `## Decisions` section recording **why** the
behaviour is what it is. Each entry uses a fixed shape:

```md
**YYYY-MM-DD - Short title**
- Decision: What the application does now.
- Rejected: The alternative that was considered and not taken.
- Driver: `Law` | `Business` | `Technical` | `Preference`
```

The driver is the important field â€” it tells a future reader how freely the
rule may be changed. See `docs/index.md` for the driver definitions.

Decisions are append-only. A reversed decision keeps its original entry and
gains a new one that supersedes it.

## Multiple Files May Need Updating

A single feature can affect more than one documentation file. Before writing
any documentation:

1. Review all folders under `docs/` to identify files that already cover
   related behavior.
2. Prefer **updating** an existing file over creating a new one.
3. Create a new file only for a genuinely distinct topic â€” and register it in
   `docs/index.md`.

Every affected documentation file must be updated â€” not just the most obvious
one.

## Suggested Sections

```md
# Feature Name

## Purpose

## Current Behaviour

## Usage

## Limitations

## Decisions

## Notes

## Related Documents
```

`features/` documents hold the *reasoning*; `docs/` holds the *result*. When a
feature completes, its durable conclusions move into a `## Decisions` section
in `docs/`.

Future ideas remain in `feature/<feature>.md` rather than user-facing
documentation.

See the Status Lifecycle section above for archiving rules â€” completed
features are moved to `features/completed/`.

---

# Technical Standards

All code-level rules â€” Python style, layering, database conventions,
dependency policy, testing, refactoring, and the Definition of Done â€” live in:

```text
docs/operations/software-standard.md
```

That document is authoritative on **how** code is written. This document is
authoritative on **when** it may be written. Do not duplicate technical rules
here.

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
