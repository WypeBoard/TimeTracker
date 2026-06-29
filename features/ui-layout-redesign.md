# Feature: UI Layout Redesign

Status: Brainstorming

## Purpose

Rework the TUI dashboard from its current asymmetric arrangement (two half-width panels in the top row, two full-width panels below, plus a footer) into a balanced four-quadrant grid with a footer strip.

The current layout grew organically. Some panels overlap in content. This redesign is an opportunity to reconsider what each quadrant should show and whether any panels should be merged, split, or repurposed.

---

## Prerequisites

- **TUI-Only Mode** (`features/tui-only-mode.md`) should be `Approved` first so the target interaction model is stable before the layout is redesigned.

---

## Requirements

*To be refined during brainstorming.*

- The dashboard uses a 2×2 quad grid (top-left, top-right, bottom-left, bottom-right).
- A footer strip spans the full width below the grid (command input, progress, key hints, or some combination).
- Existing panel content is redistributed across the four quads; nothing is silently dropped without a conscious decision.
- Panels that overlap significantly in content are candidates for merging.
- The layout is responsive to terminal width within reasonable bounds.

## Non-Goals

- New data or functionality is not introduced by this feature — it is purely a layout and content-organisation change.
- Command changes are covered by `features/command-redesign.md`.

## Manual Changes

### 2026-06-26
- Created from the split of `tui-only-interaction.md`.
- User noted that current panels overlap in content and that the layout should be reconsidered, not just reshuffled.
- **Command log (Output panel) moves to the footer.** It should show a compact scrollable view of the most recent command confirmations / errors. It does not need its own quadrant.
- **Four quads are confirmed:** Today (TL), Week (TR), Task Summary (BL), Progress (BR). The two existing full-width panels (Task Summary and Progress) each become a bottom quadrant rather than a full-width row.
- Progress is a bottom quadrant, *not* in the footer — it has enough visual content (two bars) to justify its own space.
- Footer composition: command input + compact command log (few lines, scrollable) + key hints.

## Documentation Plan

| File | Action | Description |
|------|--------|-------------|
| `docs/tui.md` | Update | Replace Layout section ASCII art and Panels descriptions to reflect new quad arrangement |

## Brainstorm Notes

### 2026-06-26 — Initial capture

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

Top row is already 2 quads (Today / Week). The problem is Task Summary, Progress, and Output each consume a full-width row, leaving little vertical space for the top quads on typical terminal heights.

**Target layout concept:**

```
┌─ TimeTracker ──────────────────────────────────────────────────────────────┐
│  ┌─ TL ───────────────────────────┐  ┌─ TR ──────────────────────────────┐ │
│  │                                │  │                                   │ │
│  │                                │  │                                   │ │
│  └────────────────────────────────┘  └───────────────────────────────────┘ │
│  ┌─ BL ───────────────────────────┐  ┌─ BR ──────────────────────────────┐ │
│  │                                │  │                                   │ │
│  │                                │  │                                   │ │
│  └────────────────────────────────┘  └───────────────────────────────────┘ │
│  [ footer: progress + command input + key hints ]                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Panel inventory and overlap analysis:**

| Panel | Currently | Content | Overlap with |
|-------|-----------|---------|--------------|
| Today | TL | Session rows + leave time | Task Summary (both show today's tasks) |
| Week | TR | Mon–Fri promark rows + daily totals | Task Summary (both show task-per-day breakdown) |
| Task Summary | Full-width row | Day × Task pivot with hours | Week (daily totals), Today (today's tasks) |
| Progress | Full-width row | Today bar + Week bar | Week (week total hours), Today (today hours) |
| Output | Full-width row | Command confirmations / errors | — |

**Key overlaps to discuss:**

- **Today** and **Task Summary** both show today's tasks and hours. Task Summary adds the weekly cross-day breakdown, but for *today* there is clear redundancy.
- **Week** shows daily totals. Task Summary adds the task dimension but repeats the daily structure.
- **Progress** shows today and week totals that are also derivable from Today and Week panels.

**Possible quad assignments (options to discuss):**

*Option A — Consolidate progress into footer*
- TL: Today (sessions)
- TR: Week (promark rows)
- BL: Task Summary
- BR: Output (command log)
- Footer: Progress bars + command input + key hints

*Option B — Merge Task Summary into Week*
- TL: Today (sessions + leave time)
- TR: Week (promark rows + task breakdown per day, expanded)
- BL: Output
- BR: Progress (both bars, larger visualisation)
- Footer: command input + key hints

*Option C — Rethink panels entirely*
- TL: Today (sessions only, no task breakdown)
- TR: Task Summary (this week, full task pivot)
- BL: Week overview (promark + totals, compact)
- BR: Output
- Footer: Progress bars + command input + key hints

**Decided direction (2026-06-26):**

Output (command log) moves to the footer — compact, a few lines, scrollable. This frees up the fourth quadrant for Progress. The agreed layout is:

- **TL:** Today (sessions + leave time)
- **TR:** Week (Mon–Fri promark rows + daily totals)
- **BL:** Task Summary (day × task pivot for the current week)
- **BR:** Progress (Today bar + Week bar, with more vertical room than the current strip)
- **Footer:** Command input + compact command log (scrollable, last N lines) + key hints

```
┌─ TimeTracker ──────────────────────────────────────────────────────────────┐
│  ┌─ Today ────────────────────────┐  ┌─ Week ────────────────────────────┐ │
│  │  session rows                  │  │  Mon–Fri promark rows             │ │
│  │  leave-time line               │  │  daily totals                     │ │
│  └────────────────────────────────┘  └───────────────────────────────────┘ │
│  ┌─ Task Summary ─────────────────┐  ┌─ Progress ────────────────────────┐ │
│  │  day × task pivot              │  │  Today  6:00 / 7:24  ████░░  81%  │ │
│  │                                │  │  Week  32:30 / 29:36 █████  110%  │ │
│  └────────────────────────────────┘  └───────────────────────────────────┘ │
│  ┌─ Command log (scrollable) ─────────────────────────────────────────────┐ │
│  │  ▶ Started #2 — 11:50  Epic-42  (carried forward)                     │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  > command input                                                            │
│  [l] Log  [ctrl+q] Quit                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

The command log area in the footer is intentionally compact — it shows the last few lines and supports scrolling up for history. It does not need to be large; its primary purpose is feedback confirmation after a command is issued.

**Remaining open questions:**

1. How many lines should the compact command log show by default (2–4)?
2. Should the command log be separately focusable for scroll, or scrollable with a modifier key?
3. Does the Progress quadrant benefit from any additional content now that it has more vertical room (e.g. historical sparkline, vacation-aware target)?
4. Should any panel be scrollable / expandable on demand rather than always fixed?

## Future Ideas

- Collapsible panels / a layout toggle for users who want more space for one panel.
- A "focus mode" that expands a single panel to full screen.
- Mouse support for panel interaction (resize, scroll).
