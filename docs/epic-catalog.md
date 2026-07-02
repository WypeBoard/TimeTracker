# Epic Catalog

## Purpose

Provides a way to define named Epics and associate task identifiers with them.
This allows the `epic summary` view to group and report time by Epic across
any week.

Because a task identifier (e.g. `TASK-123`) always belongs to the same Epic,
the association is stored once in the `task_catalog` table and reused
automatically on every subsequent use of that task.

---

## Current Behavior

### Epics

An Epic is a free-text human-readable label (e.g. `Platform Team`,
`Mobile App`). Epics are defined by the user via `epic add` and listed via
`epic list`.

- Epic IDs are auto-assigned by the database.
- Epic names must be unique. Attempting to add a duplicate name prints a
  warning and does nothing.
- There is no `epic remove` command — deletion is out of scope.

### Task–Epic linking

When a task identifier is used in any of `start`, `resume`, or `task`
(including `task -s N`), the system checks `task_catalog` for an existing link:

- **Task already linked** — the Epic association is applied silently. No user
  interaction required.
- **Task not linked** — the **Task–Epic modal** opens (see below).

The modal allows the user to:
1. Select an existing Epic from the list.
2. Create a new Epic inline and link the task in one step.
3. Press `Esc` to skip linking.

When the user presses `Esc`, the session/task is saved normally and the task
is treated as `(Misc)` in `epic summary`. No entry is written to `task_catalog`.

### Task–Epic modal

A `ModalScreen` popup that appears when a task identifier has no
`task_catalog` entry.

**State 1 — Epic selection:**

```
┌─ New task: TASK-789 ──────────────────────────────────────┐
│  Select an Epic to link this task, or press Esc to skip.  │
│                                                           │
│  ► Platform Team                                          │
│    Mobile App                                             │
│                                                           │
│  [ + New epic… ]                                          │
│                                                           │
│  [↑↓] navigate   [Enter] select   [Esc] save as (Misc)   │
└───────────────────────────────────────────────────────────┘
```

- `↑` / `↓` navigate the list.
- `Enter` on an existing Epic writes the `task_catalog` entry and closes the modal.
- `Enter` on `[ + New epic… ]` transitions to State 2.
- `Esc` closes the modal without writing anything — the task is treated as `(Misc)`.
- If no Epics exist, only `[ + New epic… ]` appears in the list.

**State 2 — Inline Epic creation:**

```
┌─ New task: TASK-789 ──────────────────────────────────────┐
│  New Epic name:                                           │
│  ┌───────────────────────────────────────────────────┐   │
│  │ Platform Team_                                    │   │
│  └───────────────────────────────────────────────────┘   │
│                                                           │
│  [Enter] create & link   [Esc] back to list               │
└───────────────────────────────────────────────────────────┘
```

- `Enter` with a non-empty name creates the Epic, writes the `task_catalog`
  entry, and closes the modal.
- `Enter` with an empty name is a no-op (the input field stays open).
- If the name already exists, an inline error is shown and the modal stays open.
- `Esc` returns to State 1 without creating anything.

---

## Usage

### Managing Epics

```
epic add Platform Team         # create a new Epic
epic add "Mobile App"          # names with spaces work fine
epic list                      # list all Epics alphabetically
```

### Epic summary

```
epic summary                   # current week
epic summary w26               # specific ISO week
```

The Epic Summary overlay groups time by **day first**, then by Epic within
each day. Each day is a bold header with a daily total. Epics are indented
under the day, and tasks are indented under their Epic. Tasks with no
`task_catalog` entry appear under `(Misc)` within that day.

Example layout:

```
  Monday Jun 16            12:30
    Platform Team          10:00
      TASK-123              7:30
      TASK-456              2:30
    (Misc)                  2:30
      TASK-789              2:30
  Tuesday Jun 17            4:15
    Platform Team           4:15
      TASK-123              4:15

  Week total:  16:45
```

---

## Limitations

- No `epic remove` command. Epics cannot be deleted in this version.
- No ability to re-link a task to a different Epic. Once a task is linked, it
  stays linked.
- No retroactive bulk assignment. Tasks that predate this feature, or tasks
  where the user pressed `Esc`, remain unlinked and appear under `(Misc)`.
- `wNN` week selection in `epic summary` uses the current year. Year-boundary
  ambiguity is a known edge case.

---

## Notes

- `(Misc)` is a virtual group — it is not stored in the database and does not
  appear in `epic list`. It is computed at query time from sessions whose task
  has no `task_catalog` entry.
- Sessions with no task label at all are excluded from `epic summary` entirely.
- The modal fires at most once per task identifier: after a `task_catalog`
  entry is written, no modal will appear for that task again.

---

## Related Features

- `docs/commands.md` — full command reference including `epic add`, `epic list`,
  `epic summary`, and the updated `start`, `resume`, and `task` descriptions
- `docs/tui.md` — Epic Summary overlay layout and keyboard navigation
- `docs/sqlite-datasource.md` — `epics`, `epics_h`, `task_catalog`, and
  `task_catalog_h` table schemas
