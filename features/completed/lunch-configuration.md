# Feature: Lunch Configuration

Status: Completed

## Purpose

Lunch is treated differently from workplace to workplace. Under Danish practice
a lunch break is often the employee's *own* time — unpaid, undisturbed, and not
counted as work. Other workplaces pay for the lunch break and expect the
employee to remain available.

TimeTracker must support both models, and — when lunch is the employee's own
time — must help the user answer the two questions that actually matter:

1. *When can I leave today?* (with and without a lunch break)
2. *What start/end times do I register for this day?*

Before this feature the second question was answered incorrectly: the day span
shown in the Weekly Overview implied a **zero-minute** lunch by default, which
caused the user to work ~30 minutes longer than required.

## Next Step

> **Current status:** Completed
> All documentation listed in the Documentation Plan has been updated and this
> document has been moved to `features/completed/`.

## Requirements

1. The configuration screen has a single **Lunch** section with:
   - A radio group: *Included in working hours* / *Excluded from working hours*.
   - A **Lunch duration** input in minutes (default `30`, valid range `0–240`).
2. The former **Promark offset** setting is retired. One duration value drives
   every lunch-related calculation.
3. When Lunch is **excluded** from working hours:
   - `Lunch` sessions do not count toward the daily target (unchanged).
   - The consolidated day span (Weekly Overview day header and the `promark`
     command) is `first_start + worked_minutes + lunch_duration_minutes`.
     The addition is **flat and unconditional** — the actual length of the
     logged `Lunch` session does not influence it. A 20-minute lunch is still
     registered as a 30-minute lunch.
   - The Quick Stats **Leave** row shows two projections:
     `~15:00 / ~15:30 (w/e lunch)`. The second value is the first plus
     `lunch_duration_minutes`.
   - The second projection disappears as soon as a `Lunch` session exists for
     the day (projected until logged).
4. When Lunch is **included** in working hours:
   - `Lunch` sessions count like any other session.
   - No addition is made to the consolidated day span.
   - The **Leave** row shows a single projection, never the `(w/e lunch)` variant.
5. `lunch_duration_minutes` is stored in the `settings` table like every other
   setting, with a documented default so a fresh database behaves correctly.
6. A one-time read fallback migrates an existing non-zero
   `lunch_promark_offset_minutes` into `lunch_duration_minutes`.

## Non-Goals

- Making the reserved task name `"Lunch"` configurable. It stays hardcoded.
- Capping the span addition at the actual lunch length. A 45-minute lunch is
  still registered as `lunch_duration_minutes` — this is intentional.
- Per-day or per-weekday lunch rules.
- Automatic insertion of a `Lunch` session when none is logged.

## Manual Changes

2026-10-27
- User decided the day span must **always** include `lunch_duration_minutes`
  when lunch is excluded worktime, regardless of the actual logged duration,
  and regardless of whether a `Lunch` session exists at all.
  This supersedes the earlier `max(0, offset − actual)` behaviour.
- User decided the `(w/e lunch)` leave variant is shown only when lunch is
  configured as excluded worktime.
- User decided `"Lunch"` remains a hardcoded reserved string for now.

## Documentation Plan

| File | Action | Description |
|------|--------|-------------|
| `docs/configuration.md` | Update | Rewrite the Lunch section; replace the Promark offset with Lunch duration in the settings table |
| `docs/tui.md` | Update | Describe the dual `Leave` projection and the day-span rule |
| `docs/commands.md` | Update | Update the `promark` and `lunch` command notes |

## Brainstorm Notes

- Two separate lunch settings (`lunch_excluded`, `lunch_promark_offset_minutes`)
  described the same real-world concept from two angles and drifted apart. One
  duration value is simpler and matches how the user thinks about it.
- The old `max(0, offset − actual)` formula modelled "pay me back the lunch I
  didn't take". What the user actually registers is a fixed contractual lunch,
  so a flat addition is correct.
- The pre-redesign CLI already showed a `with lunch HH:MM` variant with a
  hardcoded `+30`. This feature restores that behaviour and makes the 30
  configurable.

## Future Ideas

- Per-weekday lunch durations for compressed schedules.
- A warning when the actual logged lunch deviates significantly from the
  configured duration.
- Making the reserved `"Lunch"` task name configurable.
