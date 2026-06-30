# Feature: Textual Testing Infrastructure

Status: Brainstorming

## Purpose

Establish a pattern for writing automated tests that exercise Textual TUI widgets, screens, and user interactions — beyond what the current `RecordingContext` + SQLite integration tests can cover.

The `epic-catalog` feature is the first to introduce a meaningful TUI interaction (the task–Epic modal) that cannot be tested at the command layer alone. Without UI tests, the modal's keyboard navigation, state transitions, and error display go unverified by the test suite.

## Next Step

> **Current status:** Brainstorming
> **To reach Refinement:** Brainstorm notes are rich enough to evaluate — move to critical review mode.

## Brainstorm Notes

### 2026-06-30 — Initial capture

**Background context:**
- The project already has `pytest`-based integration tests in `tests/test_smoke.py`.
- Those tests explicitly exclude TUI widget testing.
- `requirements-dev.txt` only contains `pytest>=8.0`.
- Textual ships `textual.testing` with a `Pilot` class for async UI testing.
- The `epic-catalog` modal is the first concrete motivation for TUI tests.

**What Textual testing gives us:**
- `app.run_test()` — async context manager that starts the app without a real terminal.
- `Pilot.press(key)` — simulate keystrokes.
- `Pilot.click(selector)` — simulate mouse clicks.
- `app.query_one(selector)` — inspect widget state.
- Tests run headlessly and deterministically in CI.

**Approach options:**

1. **Test the full `TimeTrackerApp`** — push the real app and interact with it.
   - Pro: highest fidelity.
   - Con: requires a real DB, more setup, slower.

2. **Test individual screens/modals in isolation** — instantiate `EpicLinkModal` directly without the full app.
   - Pro: fast, focused, no DB needed for pure UI state tests.
   - Con: some integration points (e.g. modal result bubbling) may be missed.

3. **Hybrid** — isolate pure UI tests (State 1 → State 2 transitions, Esc behaviour) from integration tests that verify the full command → modal → DB round trip.

**Dependencies needed:**
- `pytest-asyncio` — required for `async def test_*` functions that `await` pilot calls.
- Textual itself is already a runtime dependency; its `textual.testing` module requires no extra install.

**Open questions:**
- Should tests use a real database (monkeypatched `DB_FILE` like smoke tests) or mock the storage layer entirely?
- Should the full `TimeTrackerApp` be tested, or modals in isolation, or both?
- Is `pytest-asyncio` the right async runner, or does Textual recommend something else?
- Where do TUI tests live — alongside `test_smoke.py` in `tests/`, or a separate `tests/tui/` subdirectory?

## Future Ideas

- Screenshot / snapshot testing via Textual's SVG export for visual regression.
- CI integration that runs TUI tests headlessly.
