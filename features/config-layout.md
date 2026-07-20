# Feature: Configurable Layout Density

Status: Brainstorming

## Purpose

Allow the user to choose a preferred TUI layout density (e.g. compact vs. comfortable) and have that preference persist across application restarts.

This feature is a sub-concern of the broader Configuration View (`features/configuration-view.md`) and the Layout Density feature (`features/layout-density.md`). It is tracked separately so it can be scheduled and approved independently.

---

## Prerequisites

- **Configuration View** (`features/configuration-view.md`) — the `settings` table and `SettingsStorage` module must exist before this feature can store its setting.
- **Layout Density** (`features/layout-density.md`) — the density toggle must already exist as an in-session feature before it can be persisted.

---

## Requirements

_Not yet defined — brainstorm only._

---

## Non-Goals

_Not yet defined._

---

## Open Questions

1. Where in the config screen does the layout density setting live — in the Configuration screen, or only toggled via the existing in-session mechanism?
2. Should the setting take effect immediately when changed in the config screen, or only after restarting?
3. What are the valid density values? Are they defined by `features/layout-density.md`?

---

## Brainstorm Notes

### 2026-07-07 — Diverted from configuration-view.md

Layout density persistence was flagged as a natural fit for the config screen during brainstorming of `configuration-view.md`. It is diverted here to keep that feature's scope focused.

The Layout Density feature (`features/layout-density.md`) already lists persistence as a future idea. This document is the designated home for that work.

**Likely implementation:** a single `layout_density` key in the `settings` table (e.g. `"compact"` / `"comfortable"`), read at application startup to set the initial density before the first render.

---

## Future Ideas

_None yet._

---

## Documentation Plan

_To be defined when the feature reaches Proposed._

---

## Next Step

> **Current status:** Brainstorming
> **To reach Refinement:** Brainstorm notes are rich enough to evaluate — answer the open questions and move to critical review mode.
