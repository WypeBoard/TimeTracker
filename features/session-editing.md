# Feature: Inline Session Editing

Status: Brainstorming

## Purpose

Allow the user to correct a session's Task/Epic ID directly from the Today panel in the
TUI, without typing a `task <epic> -s N` command. The target case is a quick correction
after the fact — wrong epic entered at `start`, or a session left without a task label.

---

## Prerequisites

- **Textual TUI** feature must be `Completed` before this work begins.

---

## Requirements

_Not yet defined — initial brainstorm only._

---

## Non-Goals

_Not yet defined._

---

## Manual Changes

_None yet._

---

## Brainstorm Notes

### Core idea

The Today panel shows a list of today's sessions. The user navigates to a session row
and activates edit mode on the Task/Epic cell. They type the correction and confirm with
`Enter`. The change is written to storage immediately via the existing `cmd_task` / 
`update_session_task` path.

This does not introduce a new storage operation — it routes through the same code that
the `task` command already uses.

### Interaction sketch

```
  #1  08:30 → 09:15  0.75h  [Epic-42      ]   ← edit mode, cursor visible
  #2  09:15 → now ▶  3.25h  TASK-1234
```

- `↑`/`↓` (or mouse click) selects a row in the Today panel.
- `Enter` or `e` activates edit mode on the Task/Epic field of the selected row.
- `Esc` cancels without saving.
- `Enter` confirms and writes back; panel refreshes.

### Open questions

- Should editing be limited to the Task/Epic field only, or also allow correcting start/end
  times? (Time edits are riskier — they affect hour calculations and promark entries.)
- Should the active (open) session be editable, or only completed sessions?
- Is row selection within the Today panel a separate focusable state, or does `Tab` cycle
  into it from the Command input?

---

## Future Ideas

- Extend editing to start/end times (higher risk, requires validation).
- Batch-edit: apply the same epic to multiple sessions at once.
