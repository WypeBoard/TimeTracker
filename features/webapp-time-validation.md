# Feature: Web App Time-Entry Validation

Status: Brainstorming

## Purpose

The web app's mutating session endpoints (`POST /sessions/new`, `/resume`, `/lunch`, `/stop`, and their `/now` variants) all accept a user-supplied clock time (Start Time or End Time) and, in the New Session/Resume/Lunch cases, silently auto-close whatever session is currently open at that submitted time (see `features/standalone-web-app.md`, Manual Changes 2026-11-26, "New Session: auto-close the running session instead of rejecting").

That auto-close has no validation today: nothing stops a submitted time from producing a nonsensical result — e.g. closing the open session at a time *earlier* than when it started, or a Stop/End Time earlier than the session's own start. The auto-close behavior itself is correct and wanted; what's missing is a guard that the submitted time actually makes sense relative to the session it is about to close, surfaced as an **inline validation error in the modal itself**, not as a silent bad write and not as a generic post-submit error banner elsewhere on the page.

This feature is a quality/correctness fast-follow raised directly out of implementing the New Session auto-close gap fix. It applies to the web app only — this does not revisit any TUI command validation.

## Next Step

> **Current status:** Brainstorming
> **To reach Refinement:** Brainstorm notes are rich enough to evaluate — move to critical review mode once the user has had a chance to add/adjust ideas here.

## Requirements

_Not yet defined — Requirements are drafted during Refinement, not Brainstorming. See Brainstorm Notes below for the raw material._

## Non-Goals

_Not yet defined — Non-Goals are drafted during Refinement, alongside Requirements._

## Manual Changes

_None yet._

## Brainstorm Notes

### Triggering problem (2026-11-26)

- `today_service.do_new_session` (and `do_resume`/`do_lunch`, which already had the auto-close pattern before the New Session gap fix) call `_close_open_session_if_any(start_time)`, which blindly does `UPDATE sessions SET end = ? WHERE id = ?` with the submitted time — no comparison against the open session's own `start` value.
- Concretely reported scenario: starting a New Session (or Resume/Lunch) at a time that is **earlier** than the currently-open session's start time silently produces a session with `end < start` — a backwards-in-time session — instead of being rejected.
- The fix should not remove the auto-close behavior itself (that was the point of the New Session gap fix); it should only add a validity check on *what* gets auto-closed.

### Where the validation error should surface

- **Must be shown inside the modal that is still open**, not as a generic error banner appearing after the fragment re-renders elsewhere on the page. The user is actively looking at the New Session/Resume/Lunch/Stop modal when they submit a bad time — the correction prompt belongs right there, next to the field they need to fix.
- Today's mutating endpoints all return `_today_fragment.html` (Quick Stats + session table + an inline error alert) via an HTMX swap targeting `#today-dynamic`, which is **outside** the modal. A validation error rendered into `_today_fragment.html` would appear "after" the modal has already visually closed (Bootstrap's default behavior on a form `submit` is to let the HTMX request fire; nothing currently keeps the modal open to display an error next to the bad field).
- This means the fix is not just a backend validation rule — it also needs a UI/HTMX wiring change so that:
  - the modal **stays open** when validation fails, and
  - the specific field (Start Time / End Time) gets an inline error (e.g. Bootstrap's `is-invalid` + `invalid-feedback` pattern), not just a top-of-page alert.
- The Settings page already has a precedent for "re-render with inline field errors, nothing persisted" (see `features/standalone-web-app.md` Manual Changes, 2026-11-24, "Settings page..."), but that's a full-page form, not a modal — the modal case needs the HTMX swap target to be the modal body itself (or a dedicated response that re-opens the modal with errors) rather than the page's shared `_today_fragment.html` target.

### What "doesn't make sense" means, concretely (candidate rules to refine later)

- **New Session / Resume / Lunch (auto-close path):** the submitted Start Time must not be earlier than the open session's own `start` time. (The literal case the user raised: "traverses more than the previous task" — the new start time would make the auto-closed session have negative duration.)
- **Stop:** the submitted End Time must not be earlier than the open session's `start` time (same family of rule, no auto-close involved, but the same "end before start" problem applies).
- Possible related checks not yet confirmed as in-scope, raised here for Refinement to accept/reject:
  - Submitted time is earlier than the *previous* closed session's end time (a gap-free timeline integrity check, broader than just the one session being auto-closed).
  - Submitted time is in the future relative to "now" (debatable — backdating is an explicit supported use case per the Start Time input's design, so "future" times may need to stay allowed, e.g. for planning ahead; this needs explicit discussion, not an assumed rule).
  - Zero-duration session (`start == end` exactly) — currently allowed implicitly; decide if that should warn/block or stay allowed.

### Possible implementation shapes (not decided)

1. **Server-side only:** `today_service` functions return a structured validation error (not just a string); the route re-renders a modal-scoped fragment (e.g. `_new_session_modal.html` with an error passed in) instead of `_today_fragment.html`, and the response still needs to tell the browser to keep the modal visible (HTMX `hx-target`/`hx-swap` pointed at the modal's inner form, with Bootstrap's modal left untouched since the page itself doesn't navigate).
2. **Client-side pre-check + server-side enforcement:** a small inline script compares the typed Start/End Time against a data attribute carrying the open session's start time (similar pattern to the existing New Session Epic-field disabling script, which already reads a `data-*` JSON attribute — see `features/standalone-web-app.md` Manual Changes, 2026-11-26, "New Session modal: conditional Epic field state") and blocks/flags the submit button before it even reaches the server, with the server-side check kept as the authoritative guard (defense in depth, not a replacement).
3. Hybrid: client-side gives instant feedback (no round-trip), server-side is the one that can actually reject bad data (in case JS is stale/bypassed), and the server's rejection path is what needs the "keep modal open, show inline error" HTMX wiring regardless of which client-side convenience is added.

### Scope boundary

- This is scoped to the **web app** (`webapp/`) only. The TUI's `cmd_start`/`cmd_resume`/`cmd_lunch`/`cmd_pause`/`cmd_stop` are unaffected; this feature does not propose changing TUI validation behavior.
- This is explicitly a fast-follow to `features/standalone-web-app.md`, not a modification of that document's already-`Approved` scope — it is being tracked as its own feature so it can go through its own Refinement/Proposed/Approved cycle independently, per `AGENTS.md`.

## Future Ideas

- A general "session timeline integrity" check (no overlaps, no backwards time, no gaps if that's ever desired) could be factored into one shared validation helper used by all five mutating endpoints, rather than duplicating an `is this time valid relative to X` check per endpoint — worth considering once the exact rule set is settled in Refinement.
