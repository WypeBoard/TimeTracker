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

When the feature is in `Completed` and has been documented it may be removed. 

---

## Recommended Feature Template

```md
# Feature: Example Feature

Status: Brainstorming

## Purpose

Describe why the feature exists.

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

## Brainstorm Notes

Discussion history and ideas.

## Future Ideas

Ideas that may be useful later but are NOT approved work.
```

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

Suggested sections:

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

## Prefer the Standard Library

Before introducing a dependency, consider whether the Python standard library already provides a sufficient solution.

Dependencies should only be added when they provide meaningful value.

When proposing a new dependency, explain:

* Why it is needed
* Alternatives considered
* Benefits gained
* Maintenance implications

Small solutions are preferred over dependency sprawl.

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
