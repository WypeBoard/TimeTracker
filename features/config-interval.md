# Feature: Configurable Notification Interval

Status: Brainstorming

## Purpose

Allow the user to control how frequently the Toast Notifications feature polls for reminders, rather than relying on a hard-coded 5-minute interval.

This feature is a sub-concern of the broader Configuration View (`features/configuration-view.md`) and the Toast Notifications feature (`features/toast.md`). It is tracked separately so it can be scheduled and approved independently.

---

## Prerequisites

- **Configuration View** (`features/configuration-view.md`) — the `settings` table and `SettingsStorage` module must exist before this feature can store its setting.
- **Toast Notifications** (`features/toast.md`) — the polling interval must be wired into the toast notification loop.

---

## Requirements

_Not yet defined — brainstorm only._

---

## Non-Goals

_Not yet defined._

---

## Open Questions

1. What is the minimum sensible interval? (e.g. 1 minute? 30 seconds?)
2. Should the interval be expressed in minutes, seconds, or offered as a set of presets (e.g. 1 min / 5 min / 15 min)?
3. Should a value of `0` disable notifications entirely, or is that a separate toggle?

---

## Brainstorm Notes

### 2026-07-07 — Diverted from configuration-view.md

The toast notification interval was flagged as a natural fit for the config screen during brainstorming of `configuration-view.md`. It is diverted here to keep that feature's scope focused.

The Toast Notifications feature (`features/toast.md`) already lists configurability of the polling interval as a future idea. This document is the designated home for that work.

**Likely implementation:** a single `notification_interval_minutes` key in the `settings` table, read by the toast polling loop at startup (or dynamically if the loop supports live config reload).

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
