# Feature: UI Layout Redesign

Status: Refinement

## Purpose

Rework the TUI dashboard from its current panel arrangement — which has grown organically and is heavily oriented toward historical data — into
a layout that prioritises the current moment: what you are working on right now, how long you have worked today, and what context is relevant to
the current task.

The existing panels (Today, Week, Task Summary, Progress) are largely four different representations of the same historical session data. This
redesign removes the duplication and reclaims that screen space for higher-value information: the active session, today's timeline, and (
eventually) task notes.

---

## Prerequisites

- **TUI-Only Mode** (`features/tui-only-mode.md`) should be `Approved` first so the target interaction model is stable before the layout is
  redesigned.

---

## Requirements

*To be refined during brainstorming.*

- The permanent dashboard is focused on the current moment, not historical aggregates.
- Weekly / historical data is accessible via an overlay (not permanently visible).
- The layout is responsive to terminal width within reasonable bounds.
- Nothing is silently dropped — panels removed from the permanent dashboard must be explicitly accounted for (overlay, merged into another
  panel, or deliberately cut).

## Non-Goals

- New data or functionality is not introduced by this feature — it is a layout and content-organisation change.
- Obsidian / notes integration is a future feature. The Task Notes panel is a placeholder in the design to reserve the space; it will not be
  wired up as part of this feature.
- Command changes are covered by `features/command-redesign.md`.

## Manual Changes

### 2026-06-26

- Created from the split of `tui-only-interaction.md`.

### 2026-08-17

- Major direction change following extended design review.
- Previous direction (2×2 quad grid: Today / Week / Task Summary / Progress) is superseded entirely.
- New direction: **current-focused cockpit** — permanent dashboard shows active session, today's timeline, task notes placeholder, and a compact
  stats sidebar. Historical aggregate panels (Week, Task Summary, Progress bars) move to an overlay.
- All prior brainstorm decisions before 2026-08-17 are superseded.

## Documentation Plan

| File          | Action | Description                                                                                                  |
|---------------|--------|--------------------------------------------------------------------------------------------------------------|
| `docs/tui.md` | Update | Replace Layout section ASCII art and Panels descriptions to reflect the new cockpit layout and overlay model |

## Brainstorm Notes

### 2026-06-26 — Initial capture (superseded)

**Current layout (for reference):**

```
┌─ TimeTracker ──────────────────────────────────────────────────────────────┐
│  ┌─ Today ────────────────────────┐  ┌─ Week ────────────────────────────┐ │
│  │  session rows                  │  │  Mon–Fri promark rows             │ │
│  │  leave-time line               │  │                                   │ │
│  └────────────────────────────────┘  └───────────────────────────────────┘ │
│  ┌─ Task Summary ─────────────────────────────────────────────────────────┐ │
│  │  day × task pivot                                                      │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌─ Progress ──────────────────────────────────────────────────────────────┐ │
│  │  Today bar  /  Week bar                                                │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌─ Output ────────────────────────────────────────────────────────────────┐ │
│  │  command confirmation / error messages                                 │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  > command input                                                            │
│  [l] Log  [ctrl+q] Quit                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

*Direction from this session (2×2 quad grid) was superseded on 2026-08-17. See notes below.*

---

### 2026-08-17 — Direction change: current-focused cockpit

**Core diagnosis**

The current dashboard is almost entirely backward-looking:

| Panel        | Orientation                      |
|--------------|----------------------------------|
| Today        | Past sessions for today          |
| Week         | Past sessions Mon–Fri            |
| Task Summary | Aggregated past sessions by task |
| Progress     | Aggregated past sessions as bars |

For most of the working day the user cares about:

1. What am I working on **right now**?
2. How long have I worked **today**?
3. What notes / context belong to the **current task**?

Weekly summaries are only relevant a few times per day — they do not need permanent screen space.

**Proposed permanent dashboard**

```
┌─ TimeTracker ──────────────────────────────────────────────────────────────┐
│                                                                            │ 
│ ┌─────────────────────────────────────────────┬──────────────────────┐     │
│ │ Active Session                              │ Quick Stats          │     │
│ │                                             │                      │     │
│ │ TASK-4321                                   │ Today: 5.8h / 7.4h   │     │
│ │ Platform Migration                          │ Remaining: 1.6h      │     │
│ │                                             │ Leave: ~15:42        │     │
│ │ Running: 02:37                              │ Week: 31.2h          │     │
│ │ Started: 09:00                              │ Sessions: 3          │     │
│ └─────────────────────────────────────────────┴──────────────────────┘     │
│                                                                            │ 
│ ┌────────────────────────────────────────────────────────────────────┐     │
│ │ Today's Timeline                                                   │     │
│ │                                                                    │     │
│ │ #1  07:00–09:00  TASK-1234                             2.00h       │     │
│ │ #2  09:00–Now    TASK-4321                             2.50h  ▶    │     │
│ └────────────────────────────────────────────────────────────────────┘     │
│                                                                            │ 
│ ┌────────────────────────────────────────────────────────────────────┐     │
│ │ Task Notes  (placeholder — Obsidian integration future feature)    │     │
│ │                                                                    │     │
│ │ # TASK-4321                                                        │     │
│ │                                                                    │     │
│ │ - Investigate timeout issue                                        │     │
│ │ - Update deployment pipeline                                       │     │
│ └────────────────────────────────────────────────────────────────────┘     │
│                                                                            │ 
│ ┌────────────────────────────────────────────────────────────────────┐     │
│ │ Output  (compact command log)                                      │     │
│ └────────────────────────────────────────────────────────────────────┘     │
│ > _                                                                        │
│ [w] Week  [l] Log  [ctrl+q] Quit                                           │
└────────────────────────────────────────────────────────────────────────────┘
```

**Panel breakdown**

| Panel            | Size                       | Content                                                                                                   |
|------------------|----------------------------|-----------------------------------------------------------------------------------------------------------|
| Active Session   | Top-left (wide)            | Current task ID + name, running duration, start time                                                      |
| Quick Stats      | Top-right (narrow sidebar) | Today logged / target, remaining hours, projected leave time, week total, session count                   |
| Today's Timeline | Full-width                 | Numbered session rows for today — start, end (or "Now"), task ID, duration, active indicator              |
| Task Notes       | Full-width                 | Placeholder for Obsidian-linked notes for the active task (content to be defined in the Obsidian feature) |
| Output           | Compact footer             | Scrollable command log (last few lines of confirmations / errors)                                         |
| Command input    | Footer                     | Text input                                                                                                |
| Key hints        | Footer                     | Contextual key bindings                                                                                   |

**Panels moved to overlay**

The following panels are **removed from the permanent dashboard** and replaced by an overlay (accessible via a key binding, e.g. `[w]`):

| Removed panel                   | Disposition                                       |
|---------------------------------|---------------------------------------------------|
| Week (Mon–Fri promark rows)     | Weekly Log overlay                                |
| Task Summary (day × task pivot) | Weekly Log overlay (Tasks tab)                    |
| Progress bars (Today / Week)    | Quick Stats sidebar (metrics only, no bar widget) |

The Weekly Log overlay may use tabs to combine related views:

```
╭──────────────────────────────╮
│  Sessions │ Tasks │ Epics    │
╰──────────────────────────────╯
```

This mirrors the existing Log screen and Epic Summary screen pattern rather than introducing a new separate screen.

**Why the sidebar replaces the progress bars**

The Progress panel's bars visualise today and week totals, but those same numbers fit in two lines of the Quick Stats sidebar. The bar widget
occupied a full-width row for information that is more compact as plain text. The sidebar format also makes it trivially glanceable — values are
consistently placed, not scattered across panels.

**Why Task Notes becomes first-class**

Once Obsidian integration arrives, the most valuable information for any given session is the task's associated notes. Reserving a panel for
this now means the layout does not need to change again when that feature ships. For now the panel can display a placeholder or static content.

**Open questions for refinement**

1. Should the Active Session panel display the Epic name in addition to the task ID?
2. Should Today's Timeline be scrollable when the session count is large?
3. How many lines should the compact Output log show by default (2–4)?
4. Should the Weekly Log overlay be a dedicated screen (like the existing Log screen) or a modal?
5. Should Quick Stats show Epic information (current epic, epic progress)?
6. What is shown in the Active Session panel when no session is active?

---

### 2026-08-18 — Overlay consolidation analysis

**Current overlay inventory**

| Screen               | Type        | Key binding | Content                                          | Navigation      |
|----------------------|-------------|-------------|--------------------------------------------------|-----------------|
| `LogScreen`          | ModalScreen | `[l]`       | Session log — one week of promark rows per day   | ← / → by week   |
| `EpicSummaryScreen`  | ModalScreen | `[e]`       | Time grouped by Epic for one week                | ← / → by week   |
| `ConfigScreen`       | ModalScreen | —           | Settings / configuration                         | None            |
| `EpicModal`          | ModalScreen | —           | Tasks-to-Epic assignment overview                | None            |

**Structural duplication between LogScreen and EpicSummaryScreen**

Looking at the implementation, `LogScreen` and `EpicSummaryScreen` are nearly identical:

- Both extend `ModalScreen`.
- Both use a 90% × 90% `ScrollableContainer` with identical CSS.
- Both share the same `Binding` set: `escape` / `left` / `right`.
- Both navigate by ISO week using the same `_max_week_of_year` helper — the function is **copy-pasted** into each file.
- The only difference is which `Printer` function populates the `Static` widget.

They are the same screen with different content. Keeping them separate means any future change to the overlay chrome (size, border style, navigation behaviour) must be made in two places.

**Proposed consolidation: a single tabbed Weekly Overview overlay**

Replace both screens with one `WeeklyOverviewScreen` that hosts tabs for different views of the same week:

```
╭────────────────────────────────────────────╮
│  Sessions  │  Tasks  │  Epics              │
╰────────────────────────────────────────────╯
```

- A single week-navigation state shared across all tabs (switching tab does not reset the week).
- `_max_week_of_year` exists once.
- Adding a future tab (e.g. Promark preview) requires only a new content renderer, not a new screen class.
- A single key binding opens the overlay; tabs are navigable by `tab` / `shift+tab` or labelled number keys.

**Screens confirmed as out of scope for this change**

- `ConfigScreen` — purpose is distinct; no consolidation needed.
- `EpicModal` (Tasks-to-Epic assignment) — purpose is distinct; no consolidation needed.

**New open questions arising from this analysis**

7. Should the tabbed overlay open on the Sessions tab by default, or remember the last-viewed tab?
8. Should the `Tasks` tab reproduce the current Task Summary pivot exactly, or is this a chance to simplify it?
9. What key binding opens the unified overlay? (`[w]` was suggested earlier — does that still hold?)

---

### 2026-08-18 — View definitions (answers to open questions 1–9, revised same day)

This section works through each open question and defines the exact content and appearance of every view.
Answers marked **revised** reflect user feedback received on 2026-08-18 that supersedes the first-pass answers.

---

#### Active Session panel (questions 1 and 6)

**Q1 — Should the Epic name appear?**

Yes. The Epic name provides immediate context without requiring the user to open an overlay. It occupies one line and does not crowd the panel.
If no Epic is assigned to the current task, the Epic line is omitted rather than shown as blank.

**Q6 — What is shown when no session is active?**

The panel switches to an idle state. It shows a clear "No active session" message and, as a secondary reference, the task ID and end time of the
most recently completed session for today (if one exists). This gives the user orientation without wasting the panel space entirely.

**Active state:**

```
┌─ Active Session ────────────────────────────────────────────────┐
│  TASK-4321  ·  Platform Migration                               │
│  Epic: Platform Ops                                             │
│                                                                 │
│  Running   02:37:14                    Started   09:00          │
└─────────────────────────────────────────────────────────────────┘
```

- Line 1: `{task_id}  ·  {task_name}` — bold.
- Line 2: `Epic: {epic_name}` — omitted if no Epic is assigned.
- Line 3: blank separator.
- Line 4: `Running  {HH:MM:SS}` (live, updates every second) and `Started  {HH:MM}` aligned to opposite sides.

**Idle state (no active session):**

```
┌─ Active Session ────────────────────────────────────────────────┐
│  No active session                                              │
│                                                                 │
│  Last ended   11:42                   (TASK-1234)               │
└─────────────────────────────────────────────────────────────────┘
```

- "No active session" is dimmed/muted text.
- Last session line is omitted if no sessions exist today.

**Idle state (first session of the day — no history at all):**

```
┌─ Active Session ────────────────────────────────────────────────┐
│  No active session                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

#### Quick Stats sidebar (question 5)

**Q5 — Should Epic information appear? (revised)**

No. Epic weekly totals are only relevant when registering time in external systems, which already happens in the Weekly Overview overlay.
They do not provide useful at-a-glance information on the dashboard. The Epic block is omitted entirely.

```
┌─ Quick Stats ───────┐
│  Today   5.8h/7.4h  │
│  Rem.    1.6h       │
│  Leave  ~15:42      │
│  Week   31.2h       │
│  Sessions  3        │
└─────────────────────┘
```

- `Today`: hours logged today / daily target.
- `Rem.`: remaining hours to reach daily target.
- `Leave`: projected leave time based on remaining hours (same logic as current Today panel).
- `Week`: total hours logged this ISO week (Mon–Sun).
- `Sessions`: number of sessions today.

---

#### Today's Timeline panel (question 2)

**Q2 — Should it be scrollable?**

Yes. The panel has a fixed visible height (showing approximately 5–6 rows). When today's session count exceeds the visible rows, the panel
becomes internally scrollable. The active session row is always visible — it is pinned to the bottom or scrolled into view automatically.

**Columns:**

| Column     | Format                   | Notes                                         |
|------------|--------------------------|-----------------------------------------------|
| Number     | `#N`                     | 1-based index                                 |
| Start      | `HH:MM`                  |                                               |
| Separator  | `–`                      |                                               |
| End        | `HH:MM` or `Now`         | "Now" for the active session                  |
| Task ID    | `TASK-XXXX`              |                                               |
| Duration   | Right-aligned `N.Nh`     |                                               |
| Indicator  | `▶`                      | Active session only; blank for closed sessions |

```
┌─ Today's Timeline ──────────────────────────────────────────────┐
│  #1   07:00 – 08:30   TASK-1111   Design review        1.50h    │
│  #2   08:30 – 09:00   TASK-2222   Standup              0.50h    │
│  #3   09:00 – Now     TASK-4321   Platform Migration   2.62h  ▶ │
└─────────────────────────────────────────────────────────────────┘
```

The active row is visually highlighted (bold or accent colour). Closed rows are normal weight.

**Empty state (no sessions today):**

```
┌─ Today's Timeline ──────────────────────────────────────────────┐
│  No sessions recorded today.                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

#### Task Notes panel (placeholder)

This panel is a static placeholder for this feature. Its content does not change; it simply reserves the space for the future Obsidian
integration feature. The panel renders a fixed message and a visual hint that it is not yet functional.

**Sizing:** The Task Notes panel fills all remaining vertical space on the dashboard after the fixed-height panels (Active Session + Quick
Stats row, Today's Timeline, Output, footer) have been allocated. In Textual this is expressed as `height: 1fr`, meaning the panel expands
to consume whatever space is left — making it as large as possible without pushing any other element off-screen.

```
┌─ Task Notes ────────────────────────────────────────────────────┐
│                                                                 │
│  Notes for the active task will appear here.                    │
│  (Obsidian integration — not yet implemented)                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

Text is dimmed/muted to distinguish it from live data.

---

#### Output panel (question 3)

**Q3 — How many lines?**

3 lines. This is enough to show the result of the most recent command (confirmation or error) plus one or two prior lines for context. More
than 3 lines pushes the command input too far down the screen. The panel is not scrollable from the dashboard; the full session log is
accessible via `[w]` (Weekly Overview overlay).

```
┌─ Output ────────────────────────────────────────────────────────┐
│  ✓  Session started: TASK-4321 at 09:00                         │
│  ✓  Previous session closed: TASK-1234 (1.50h)                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

Error messages use a distinct style (red / bold). Success messages are normal or green.

---

#### Weekly Overview overlay (questions 4, 7, 8, 9)

**Q4 — Modal or dedicated screen?**

Modal (`ModalScreen`), consistent with `LogScreen` and `EpicSummaryScreen`. Same 90 % × 90 % size.

Both time-registration systems the user works with must be supported simultaneously: one uses decimal hours (100-based, e.g. `1.50h`) and
the other uses actual hours (60-based, e.g. `1:30`). The Sessions view therefore renders **both formats as separate columns** on each row,
so the user can read off either format without switching views or doing mental conversion.

**Q7 — Tabs or separate overlays? (revised)**

No tabs in the Weekly Overview. The overlay shows **Sessions only**. The Tasks and Epics views remain as separate overlays, each accessible
via their own key binding or command. This keeps each overlay focused and avoids a tab management layer entirely.

- `[w]` → Weekly Sessions overlay (this screen)
- Tasks overlay key binding: **open question 10** (see below)
- Epics overlay key binding: **open question 11** (see below)

**Q8 — Tasks tab content — reproduce or simplify?**

Moot. The Tasks view is no longer a tab in this overlay. Its content and key binding are deferred to the open questions below.

**Q9 — Key binding and week navigation?**

`[w]` opens the Weekly Sessions overlay. Week navigation with `←` / `→` is confirmed — pressing `←` moves to the previous ISO week;
pressing `→` moves to the next ISO week (up to the current week).

**Weekly Sessions overlay chrome:**

```
╔═ Weekly Overview ════════════════════════════════════════════════╗
║                                              ◄  Week 34/2026  ► ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  (sessions content here)                                         ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
  [esc] close   [←][→] prev/next week
```

- Week number and year shown in the header, right-aligned.
- Week navigation (`←` / `→`) advances or retreats by one ISO week.
- `[esc]` closes the overlay and returns to the dashboard.

**Sessions overlay content (revised — mirrors Epic Summary format):**

The user's primary logging concern is time spent per Epic collectively across each day, not individual session rows. The `[w]` overlay
therefore uses the same structure as the current `EpicSummaryScreen`: days as top-level groups, Epics as sub-groups, tasks within each Epic.

Individual session rows (the current `LogScreen` format) are **not** shown here. Access to the raw session log is deferred to open
question 12.

Both duration formats are shown side-by-side on every row (day total, epic total, task total):

```
║  Monday 17 Aug                                    4:00    4.00   ║
║    Platform Ops                                   2:30    2.50   ║
║      TASK-4321  Platform Migration                2:30    2.50   ║
║    (Misc)                                         1:30    1.50   ║
║      TASK-1111  Design review                     1:30    1.50   ║
║                                                                   ║
║  Tuesday 18 Aug                                   2:00    2.00   ║
║    Platform Ops                                   2:00    2.00   ║
║      TASK-4321  Platform Migration                2:00    2.00   ║
║                                                                   ║
║  Week total                                       6:00    6.00   ║
```

- Left duration column: `HH:MM` — actual hours and minutes (60-based).
- Right duration column: decimal — hundredths of an hour (100-based, no `h` suffix to visually distinguish).
- Day header rows, Epic rows, and task rows all carry both columns.
- `(Misc)` group for tasks with no Epic assignment, consistent with current `EpicSummaryScreen`.
- Column headers or a legend may be added for clarity (styling to be finalised during implementation).

---

#### Open questions 10, 11, and 12 — resolved

All three questions are resolved by the same decision: **there is exactly one log overlay**, opened with `[w]`. The current `LogScreen`
(individual session rows) and `EpicSummaryScreen` (time per Epic per day) are collapsed into this single view, which was already defined
above as the Epic Summary format with dual duration columns.

| # | View                 | Resolution                                                         |
|---|----------------------|--------------------------------------------------------------------|
| 10 | Tasks pivot overlay | **Cut.** Not a separate overlay. No key binding.                   |
| 11 | Epics overlay       | **Cut.** `[w]` fully replaces `EpicSummaryScreen`.                 |
| 12 | Raw session log     | **Cut.** `LogScreen` individual-session rows are not carried over. |

The `LogScreen` and `EpicSummaryScreen` classes will be removed and replaced by the single `WeeklyOverviewScreen`.

---

#### Final key binding footer

```
[w] Weekly Overview   [ctrl+q] Quit
```

All overlay key bindings are now fully resolved. No further open questions remain on the overlay design.

## Future Ideas

- **Obsidian / Task Notes integration** — wire the Task Notes panel to pull live note content for the active task.
- **Context tile** — extend Quick Stats or Active Session to show Epic, linked note filename, last note modification time, and related tasks —
  transforming the app into a "work session cockpit".
- Collapsible panels / a layout toggle for users who want more space for one panel.
- A "focus mode" that expands a single panel to full screen.
- Mouse support for panel interaction (resize, scroll).
