# Feature: Standalone Browser Application

Status: Approved

## Purpose

Provide a browser-based interface for TimeTracker that runs locally in a pinned browser tab, so normal daily use does not require keeping the Textual TUI open.

The browser application will be a fully standalone application in relation to the existing TUI. It will use the same SQLite database, but it will not depend on `app/`, Textual widgets, TUI contexts, or TUI-only entry points.

**Scope boundary for existing feature docs:** This feature is fully independent of every other entry under `features/`. Those documents (e.g. `command-redesign.md`, `session-editing.md`, `config-interval.md`, `config-layout.md`, `toast.md`, etc.) describe TUI-only work and must not be treated as design input here — not their Requirements, not their brainstorm notes, not their in-flight decisions. The only acceptable source of "what existing functionality must the web app cover" is `features/completed/*.md`, since those describe behavior that has actually shipped and is part of the application today. Anything still sitting in `features/<name>.md` (not yet `Completed`/moved to `features/completed/`) is TUI-specific brainstorming that this feature does not need to track, mirror, or wait on.

## Next Step

> **Current status:** Approved
> **To reach Implemented:** User opens a new session and explicitly requests implementation with a reference to this feature document. Per AGENTS.md, approval alone does not trigger implementation — it must be explicitly requested in a new session.

## Requirements

- Web stack: FastAPI + Uvicorn, server-rendered with Jinja2 templates, enhanced with HTMX for partial-page updates. (Jinja2 is required regardless of HTMX, since it is how FastAPI response data is injected into HTML.)
- Page load strategy: each page (`/today`, `/weekly`, `/settings`) is served as **one synchronous full-page render** from a single consistent database read — not a set of small independent async/HTMX requests firing on load to fill in separate sections (Quick Stats, session table, etc.). HTMX is used only for **post-mutation** fragment swaps (after New Session/Resume/Lunch submit, after Settings Save), not for initial page population. (See Manual Changes, 2026-11-24, "Page load strategy.")
- Frontend assets: Bootstrap and jQuery. Referencing them via CDN is acceptable during active development, but before this feature is considered complete and merged via pull request, they must be converted to static files vendored locally in the repo. No Node.js, no TypeScript, no frontend build tooling, no package manager for JS at any stage.
- The web application is an independent process from the TUI:
  - New independent web service functions are written for the web app instead of reusing `Commands.py`/`*Storage.py`/`AppContext`.
  - The only code shared between the TUI and the web app is the `db/` package (generic SQLite infrastructure).
  - Repository restructuring is required first: every existing Python module (the current root domain modules — `Commands.py`, `Storage.py`, `EpicStorage.py`, `SettingsStorage.py`, `Promark.py`, `Printer.py`, `Constants.py`, `logger.py`, `app_context.py` — plus the existing `app/` TUI package) is TUI code and must live under `app/`. The web application starts fresh in its own new top-level `webapp/` package.
  - `webapp/` must not import from `app/`, and `app/` must not import from `webapp/`.
- The web app and TUI may run concurrently against the same SQLite database; no in-memory caching of session/epic state across requests — each request reads fresh from SQLite.
- Access model: plain `http://127.0.0.1:<port>/` URL, bound to loopback only. No authentication. Standard browser same-origin navigation (no special CORS handling needed since there is no cross-origin caller).
- Startup: manual for now. Acceptable minimal options are a `.bat` file or a Startup-folder shortcut; no Task Scheduler/service wrapper design needed at this stage.
- The user opens/pins the browser tab manually; the app does not need to auto-launch a browser.
- The server binds to a fixed, non-standard (non-well-known) localhost port; the exact number is an implementation detail, not a design decision.
- A `/health` endpoint must exist; the browser checks it on page load and shows whether the backend is up or down.
- UI shape is not yet finalized: expect to prototype one layout, get it in front of the user, and refactor the UI more than once before settling. The final shape may combine a dashboard with modals and/or dedicated subpages — this will be decided in a follow-up UI design pass before moving to Proposed.
  - Visual baseline: **Tabler** (Bootstrap 5, static HTML/CSS/JS build) is the chosen theme baseline (see Manual Changes, 2026-11-24).
  - The daily session log is rendered as **table rows**, not a calendar view and not a graphical timeline visual (see Manual Changes, 2026-11-24).
  - Navigation: **Tabler's Horizontal layout**, single minimal nav row, no logo, no user-account menu (no accounts exist in this app), 3 nav items: Today, Weekly, Settings (see Manual Changes, 2026-11-24 — the earlier 5-item list including separate Epic Summary/Promark destinations was superseded the same day).
  - Page structure: Today/Weekly/Settings are **separate dedicated pages**, each reached via the navbar. **Today is the dashboard** page (see Manual Changes, 2026-11-24).
  - Today page: navbar → quick-action buttons (New Session, Resume, Lunch) → **Quick Stats row** (Today, Rem., Leave, Week, Sessions — Tabler stat cards, mirroring the TUI's `QuickStatsPanel`) → today's session table. New Session is a plain button (modal: task + epic-if-needed). Resume and Lunch are Bootstrap split buttons (modal with Start Time, plus a Task select for Resume) with a dropdown "Now" bypass. Start Time uses a native `<input type="time" step="300">`, defaulting to now rounded to the nearest 5 minutes. (See Manual Changes, 2026-11-24, "Today page: quick-action buttons and modal design" and "Today page: Quick Stats row added.")
  - Weekly page: consolidates Weekly/Epic Summary/Promark into one page, mirroring the TUI's `WeeklyOverviewScreen` — week-navigation header (prev/next, capped forward at the current ISO week) plus a single table encoding day → Epic → task rows, each with dual duration columns (`HH:MM` + decimal), a `(Misc)` group, per-day consolidated Promark-style start/end span, and a `Week total` row. (See Manual Changes, 2026-11-24, "Weekly page: consolidates Weekly/Epic Summary/Promark into one page.")
  - Settings page: single page, direct functional port of the TUI's `ConfigScreen` (daily work target, lunch included/excluded + duration, excluded tasks list, always-separate tasks list), per `docs/detailed-design/configuration.md`. Save validates server-side and re-renders inline errors via HTMX on failure; Close/navigating away without submitting is the web equivalent of Escape-discards. (See Manual Changes, 2026-11-24, "Settings page: direct functional port of the TUI's ConfigScreen.")
  - Deliberately deferred (confirmed needed, not yet designed): an Active Session hero/ticker element (live `Running HH:MM:SS` display) for the Today page. Its shape depends on how the rest of the Today page settles, so it is picked up in a later pass rather than decided in isolation now (see Manual Changes, 2026-11-24, "Today page: Quick Stats row added").
- The v1 page/workflow scope (which panels, actions, and pages ship first — e.g. active session, timeline, epic assignment, weekly overview, Promark output, settings, and whether a command palette or session-editing equivalent is included) is deliberately left emergent: it will be discovered and adjusted through UI prototyping rather than fixed in advance. Only functionality already documented under `features/completed/*.md` is treated as a known, must-cover baseline; no other `features/*.md` document (all TUI-only and not yet completed) is used as design input for this feature.
- Logging/diagnostics: not a concern for this feature; use whatever baseline logging the rest of the app already has.

## Non-Goals

- No database replacement or migration; SQLite remains the store for the web app. Any future replacement of SQLite (and the associated transition plan) is explicitly a separate feature.
- No authentication/authorization layer.
- No CDN-hosted or npm/yarn-managed frontend dependencies in the merged/completed feature; a CDN reference is an acceptable temporary convenience during active development but must be replaced with vendored static assets before the feature is considered done and merged via pull request. No frontend build pipeline regardless.
- No automatic process supervision (Task Scheduler/Windows service) design as part of this feature.
- No automatic browser launching.
- No reuse of `Commands.py`, `*Storage.py`, or `AppContext`/`TuiAppContext` by the web app; no shared UI code between TUI and web app beyond `db/`.
- No CSRF defenses for mutating forms; the app is loopback-only and never exposed beyond the local machine.
- Command-history-style interaction is not an explicit goal for the web UI.
- No design input is taken from other `features/*.md` documents that are not yet `Completed`; those are TUI-only brainstorming out of scope for this feature.
- No dedicated Active Session hero/ticker element in v1 (see Manual Changes, 2026-11-24, "Active Session hero: v1 interim answer"). The session table's open row is the only v1 indication of the active session; a dedicated hero is a tracked fast-follow, not part of this feature's v1 scope.

## Page, Route, and Component Inventory

Derived from the UI decisions recorded in Manual Changes (2026-11-24 entries). This is the concrete inventory the "Next Step" line asked for.

### Pages (GET, server-rendered Jinja2 + Tabler/Bootstrap)

| Route | Page | Content |
|-------|------|---------|
| `GET /` | — | Redirects to `/today`. |
| `GET /today` | Today (dashboard) | Navbar → quick-action buttons (New Session, Resume, Lunch) → Quick Stats row (5 stat cards) → today's session table. Includes the three modals (New Session, Resume, Lunch) rendered inline in the page (hidden, Bootstrap-toggled) — no separate AJAX call needed to populate their `<select>` options, since Jinja2 renders them server-side as part of this same response. |
| `GET /weekly?year=YYYY&week=NN` | Weekly | Navbar → week-navigation header (prev/next, label) → day → Epic → task table with dual duration columns → Week total row. Query params default to the current ISO week when omitted. |
| `GET /settings` | Settings | Navbar → single settings form (daily work target, lunch, excluded tasks, always-separate tasks, Save/Close). |
| `GET /health` | — | JSON health-check endpoint, polled by client-side JS on page load (see Requirements). Not a navbar destination. |

### Mutating endpoints (POST, HTMX-driven where noted)

| Route | Triggered by | Behavior |
|-------|--------------|----------|
| `POST /sessions/new` | New Session modal submit | Body: task, epic (if newly linked), start time. Creates the session; response re-renders the Today page's session table (+ Quick Stats) fragment via HTMX swap. |
| `POST /sessions/resume` | Resume modal submit (main button path) | Body: task (from the today-scoped select), start time. Equivalent to `cmd_resume`. |
| `POST /sessions/resume/now` | Resume split-button dropdown → "Now" | Same as above with start time forced to current time; bypasses the modal entirely (no body needed beyond the preselected task, taken from the button's current default). |
| `POST /sessions/lunch` | Lunch modal submit (main button path) | Body: start time. Equivalent to `cmd_lunch`. |
| `POST /sessions/lunch/now` | Lunch split-button dropdown → "Now" | Same as above with start time forced to current time; bypasses the modal. |
| `POST /sessions/stop` | Stop modal submit (main button path) | Body: end time. Closes the currently open session (web equivalent of `cmd_pause`); errors if none is open. (See Manual Changes, 2026-11-26, "Stop button: closes the active session".) |
| `POST /sessions/stop/now` | Stop split-button dropdown → "Now" | Same as above with end time forced to current time; bypasses the modal. |
| `POST /settings` | Settings form Save | Validates all fields server-side. On failure: re-renders the settings form fragment with inline errors (HTMX swap, no navigation, nothing persisted). On success: persists and re-renders the form in its saved state. |

No separate JSON/REST API surface is introduced beyond `/health` — all other endpoints return HTML (full pages or HTMX fragments), consistent with the Jinja2/HTMX server-rendered approach already chosen.

### Templates / components (Jinja2)

| Template | Role |
|----------|------|
| `base.html` | `<head>` with vendored Tabler/Bootstrap/jQuery/HTMX assets; Horizontal navbar (Today / Weekly / Settings, no logo, no account menu); `/health` check script on load. |
| `today.html` | Extends `base.html`. Composes: quick-action buttons partial, Quick Stats partial, session table partial, and the three modal partials (new-session, resume, lunch). |
| `_quick_action_buttons.html` | New Session plain button; Resume and Lunch as Bootstrap split buttons (`btn-group` + `dropdown-toggle-split`, "Now" dropdown item). |
| `_quick_stats.html` | Five Tabler stat cards (Today, Rem., Leave, Week, Sessions). |
| `_session_table.html` | Today's sessions as table rows (start, end/blank, task, epic, duration); open session is the row with no end time. Re-rendered as an HTMX swap target after any of the three mutating actions. |
| `_new_session_modal.html`, `_resume_modal.html`, `_lunch_modal.html`, `_stop_modal.html` | Bootstrap modals with the fields described in Manual Changes (task/epic selection, today-scoped task select, `<input type="time" step="300">` defaulting to now rounded to 5 minutes). `_stop_modal.html` added 2026-11-26 (see Manual Changes, "Stop button: closes the active session"). |
| `weekly.html` | Extends `base.html`. Composes: week-nav header partial, weekly table partial. |
| `_week_nav_header.html` | Prev/next controls + `Week NN/YYYY` label; next disabled/capped at the current ISO week. |
| `_weekly_table.html` | Day-header rows (highlighted, with consolidated Promark-style span), nested Epic subtotal rows (incl. `(Misc)`), nested task rows, `Week total` row — all with dual `HH:MM`/decimal columns. |
| `settings.html` | Extends `base.html`. Composes the settings form partial. |
| `_settings_form.html` | The four sections (daily target, lunch, excluded tasks, always-separate tasks) plus Save/Close. Re-rendered as the HTMX swap target on both validation failure and success. |

## Manual Changes

2026-11-19
- The standalone FastAPI application must use the existing SQLite database and must not create a second database or perform a project/new-repository migration.
- Sharing database initialization/schema knowledge is an accepted cross-boundary concern. It does not require the TUI and web applications to share UI or runtime code.
- The exact location of shared schema initialization remains to be decided, but it must not accidentally couple either application to the other's implementation package.

2026-11-23
- The TUI is considered transitional, not a permanent second interface. Once the web application is complete and covers the required workflows, the user does not intend to open the TUI again, and the entire TUI codebase (`app/` TUI modules and any TUI-only entry points) is expected to be deleted.
- Until the web application reaches that point, the TUI remains the only working interface and must stay functional and unbroken.

2026-11-24 — Resolution of initial Open Questions
- Web technology: FastAPI + Uvicorn + Jinja2 + HTMX, confirmed. Jinja2 is required independent of the HTMX decision, since it is the mechanism for injecting FastAPI response data into HTML.
- Frontend assets: Bootstrap and jQuery, as previously decided. CDN references are acceptable during development; must be swapped for locally vendored static assets before the feature is completed/merged.
- Process startup/supervision: out of scope for now; a `.bat` file or Startup-folder shortcut is sufficient. No Task Scheduler or service wrapper design needed yet.
- Browser interaction model: the user manually opens and pins the tab; the app does not auto-launch a browser.
- Concurrency with the TUI: every mutating action is NOT required to work with guaranteed correctness while the TUI is running simultaneously at this stage — see the 2026-11-23 manual change above; the TUI is transitional and will eventually be deleted, so long-term dual-write concurrency hardening is not a goal of this feature.
- Code sharing: the web app uses independent web service functions; it does not reuse `Commands.py`/`*Storage.py`/`AppContext`. The only shared code between TUI and web app is `db/`.
- UI shape: deliberately left open. The page/route/modal structure will be decided through iterative prototyping and refactoring with the user before the feature can move to Proposed.
- Access/security model: standard loopback URL access, no authentication, no special CORS handling — this is a fully isolated local application.
- Environment: Python and pip package installation are both permitted, so no constrained-environment workarounds are needed.
- Database replacement: explicitly deferred to a separate future feature, which must also define the TUI-to-web transition. SQLite is expected to remain sufficient indefinitely for this local, single-user, fully isolated application.
- Logging/diagnostics: not a concern for this feature.

2026-11-24 — Resolution of pre-design gaps (round 2)
- V1 page/workflow scope: deliberately left emergent, not fixed up front. The scope will be discovered by prototyping different designs — something that works in one layout may not survive in another, and the workflow list will be adjusted as that exploration happens, rather than frozen into Requirements now.
- Session editing: this refers to the separate `features/session-editing.md` brainstorm (inline Task/Epic correction on a session). Per the scope-boundary note above, that document is TUI-only brainstorming and is explicitly out of this feature's design input. Whether the web app needs an equivalent capability is not predetermined — it falls under the same emergent, as-we-go scope discovery as the general V1 workflow list (see previous bullet), informed only by what `features/completed/*.md` says already ships today.
- Health/availability indicator: **in scope.** On page load, the browser should call FastAPI's `/health` endpoint to show whether the backend is up or down. (The earlier brainstorm's 5-minute re-poll cadence is a nice-to-have, not a hard requirement — the on-load check is the part that matters.)
- Repository restructuring ("clean root" from 2026-11-19): **not needed.** Confirmed only `db/*` is shared; the web app is an entirely new, independent application built from scratch. The elaborate move of `Commands.py`/`*Storage.py`/etc. into `app/` is not a prerequisite for this feature. The TUI keeps its current structure as-is; it is expected to be deprecated once the web app covers the basics, at which point the whole TUI codebase (not just the root modules) is deleted rather than reorganized.
- Command palette/command bar: folded into the same emergent-scope bucket as V1 workflow scope — not decided now, to be settled during UI prototyping.
- CSRF/form security posture: **not relevant.** The web app is bound to `127.0.0.1` only and never exposed beyond the local machine, so CSRF defenses are unnecessary.
- Fixed localhost port: a non-standard (non-well-known) port is sufficient; exact number to be picked during implementation, no further constraint needed.

2026-11-24 — UI visual baseline and session-log representation
- Visual baseline: **Tabler** (https://tabler.io/, static HTML/CSS/JS build, no React/Vue tooling) is chosen as the Bootstrap 5 theme baseline over SB Admin/AdminLTE-style admin templates, which are considered visually overused. Tabler's card-first, high-whitespace, muted-palette style is the starting aesthetic for the web app.
- Session-log representation: the daily session log is presented as **table rows** (a plain Bootstrap/Tabler `<table>`: start time, end time, duration, task, epic columns), not a calendar-grid view and not a graphical timeline-with-connector-lines visual.
  - This supersedes the earlier brainstorm suggestion of rendering "Today's timeline" as a `list-group`, and makes Template 3's hand-rolled vertical timeline visual (see Brainstorm Notes → Template 3) moot — it is not being used.
  - A plain table is a stock component in both Bootstrap and Tabler, so this choice removes the one layout idea that would have required custom (non-vendored) CSS to build.
- Navigation structure: **Tabler's Horizontal layout** (single top navbar) is chosen over Tabler's Vertical/sidebar and Combo layout variants. The Vertical/sidebar idea discussed earlier (mapping to Template 2 — "Browser app shell") is not being used.
  - The navbar is kept minimal: a single nav row (no secondary nav-link row beneath the header), no logo/brand mark, and no user-account dropdown. A user-account presentation does not apply here regardless of style, since the app has no authentication or user accounts (see Non-Goals).
  - Expected nav items at the time of this entry: Today, Weekly, Epic Summary, Promark, Settings — five destinations. **Superseded** by the 2026-11-24 "Weekly page" entry below, which consolidates Epic Summary and Promark into the Weekly page, leaving three nav items: Today, Weekly, Settings.
- Remaining open piece before this can move to Proposed: whether the "Today" page content itself is a single dashboard (cards + session table on one page, Template 1/4-style) or whether some of Weekly/Epics/Promark/Settings become separate dedicated pages reached via the navbar (Template 5-style) — the navbar structure above works either way, so this is about per-page content only now, not overall app shell.

2026-11-24 — Today page: quick-action buttons and modal design
- Nav structure confirmed: Today/Weekly/Settings are **separate dedicated pages**, each reached via the horizontal navbar (Epic Summary and Promark are not separate nav items — see the 2026-11-24 "Weekly page" entry below). **Today is the dashboard page.**
- Today page layout, top to bottom: navbar → a row of quick-action buttons → today's session table (see 2026-11-24 "UI visual baseline" entry above for the table-not-timeline decision).
- Quick-action buttons: **New Session**, **Resume**, **Lunch**.
  - All three open a modal to collect input before the action is submitted (no bare, un-confirmed one-click actions for any of them).
  - **New Session** is a plain button (no dropdown). Its modal requires a Task selection (from the full task catalog) and, if the chosen task has no Epic link yet, an Epic selection/creation step. Because task/epic selection is unavoidable input, there is no "Now"-style bypass for this button.
  - **Resume** and **Lunch** are Bootstrap **split buttons** (`btn-group`: main button + `dropdown-toggle-split`). This is a stock Bootstrap/Tabler component, no custom JS.
    - Clicking the main part of either button opens a modal with a Start Time input (see below). Both existing commands already take a single time argument (`cmd_resume(ctx, "11:50")`, `cmd_lunch(ctx, "12:00")`), so no other required input exists for Lunch.
    - The dropdown-toggle part reveals a single **"Now"** option that submits the action immediately using the current time, bypassing the modal entirely — a one-click shortcut for the common case where the prefilled modal value would have been accepted as-is.
  - **Resume modal field design (expanded from the original single-field idea):**
    - A **Task select** (`<select>`), populated with the distinct tasks worked on **today only** (not the full task catalog — that scope belongs to New Session), preselected to the last active (pre-interruption) task. This matches the existing `cmd_resume` behavior of auto-carrying the last non-Lunch task/epic (see `test_resume_skips_lunch_carries_work_task`), but makes the choice visible and reselectable instead of implicit.
    - The select is **always rendered**, even when today has only one distinct task so far — for visual consistency across days, not conditionally hidden.
    - A **Start Time** input, same control as Lunch's (see below).
    - No Epic field: resuming a task that already has an epic link does not need to re-ask for it.
  - **Start Time input control (Resume, Lunch, and New Session's time field):** a native `<input type="time" step="300">` (step = 300 seconds = 5 minutes). This snaps the browser's native spinner/picker to 5-minute increments, matching the usual habit of rounding to the nearest 5 minutes, while still allowing a manually typed, non-rounded value for the rarer backdated/off-grid entry. No third-party JS time-picker library is used — this keeps the no-added-dependency posture intact and is a plain Bootstrap `form-control`.
  - The modal's Start Time field defaults to **now, rounded to the nearest 5 minutes** rather than blank, so the common "just confirm" flow only requires opening the modal and submitting, while backdating is a matter of editing the prefilled value downward.

2026-11-24 — Weekly page: consolidates Weekly/Epic Summary/Promark into one page (supersedes the 5-nav-item list above)
- **Nav items reduced from five to three: Today, Weekly, Settings.** The separate "Epic Summary" and "Promark" nav destinations listed in the 2026-11-24 "UI visual baseline" entry above are retired — they are not separate pages.
- Rationale: the TUI already solved this exact consolidation in `features/completed/ui-layout-redesign.md` (§16–24). Its `WeeklyOverviewScreen` replaced the old separate `LogScreen` and `EpicSummaryScreen` with one view that shows day → Epic → task grouping, dual duration columns (`HH:MM` actual + decimal hundredths), and a per-day consolidated Promark-style start/end span — i.e. "Weekly," "Epic Summary," and "Promark" were already one concept, not three. The web app's Weekly page mirrors that shipped, working design rather than re-splitting it.
- Weekly page content (web equivalent of `WeeklyOverviewScreen` / `Printer.build_weekly_overview_panel`):
  - A week-navigation header: previous/next week controls plus a `Week NN/YYYY` label, mirroring the TUI's `◄  Week NN/YYYY  ►`. Forward navigation is capped at the current ISO week (same rule as `WeeklyOverviewScreen.action_next_week`); there is no equivalent cap on going backward.
  - Below the header, a single Bootstrap/Tabler `<table>` (consistent with the "table rows, not calendar/timeline" decision for the Today page) encoding the day → Epic → task hierarchy as row levels:
    - A day-header row per day (highlighted, e.g. `table-active`), spanning the day name/date and — when available — that day's consolidated Promark-style start→end span (from `compute_day_promark`), plus the day's two duration columns (`HH:MM` and decimal).
    - Epic subtotal rows nested under each day, indented via Bootstrap spacing utilities (e.g. `ps-3`/`ps-4` on the first cell), each with its own two duration columns. A `(Misc)` group row covers tasks with no Epic assignment, consistent with the existing `get_epic_summary_data` behavior.
    - Task rows nested under each Epic (indented one level further), each with its own two duration columns.
    - A `Week total` row at the bottom, spanning both duration columns, consistent with the TUI's current behavior.
  - No raw individual-session log view and no separate Tasks-pivot view are reintroduced — those were already cut by the TUI redesign (see `ui-layout-redesign.md` Non-Goals and §10–12 resolution) and remain cut here.
  - No distinct "export"/"copy" action is required for v1: the TUI's Promark-style span is shown inline in the day header, not via a separate output/export step. A copy-to-clipboard or export convenience may be considered later as a nice-to-have, not a v1 requirement.
- Backend data source: the same `EpicStorage.get_epic_summary_data` / `compute_day_promark` query shape the TUI already uses is the intended reference for what the web app's independent web-service function needs to compute — but per this feature's Non-Goals, the web app does not import or call `EpicStorage.py` directly; it implements its own equivalent query against the shared database.

2026-11-24 — Today page: Quick Stats row added
- The Today dashboard gains a **Quick Stats** row, carrying over the five metrics from the TUI's `QuickStatsPanel` (`features/completed/ui-layout-redesign.md` §6): **Today** (logged/target, e.g. `5.8h/7.4h`), **Rem.** (daily remaining/weekly remaining), **Leave** (projected leave time, with the `(w/ lunch)` variant per `features/completed/lunch-configuration.md`), **Week** (logged/target for the current ISO week), **Sessions** (count of sessions today).
- Rendered as a row of Tabler/Bootstrap stat cards (five cards in a responsive grid row), consistent with the Tabler card-first visual baseline already chosen — no custom widget needed.
- Placement on the Today page: navbar → quick-action buttons → **Quick Stats row** → today's session table.
- Backend logic reference: `QuickStatsPanel.refresh_data` / `_compute_week_total` / `Printer.leave_projection` describe the exact calculation (weekly target = `daily_target × days_with_registration`, lunch-aware leave projection, etc.). Per this feature's Non-Goals the web app does not import these TUI modules directly; it implements its own equivalent calculation against the shared database, using this logic as the reference specification.
- **Active Session hero display: confirmed needed, deliberately deferred — not a decision gap.** The TUI's `ActiveSessionPanel` (a live, per-second `Running HH:MM:SS` ticker for the current task) is acknowledged as something the web Today page will need. It is intentionally not designed yet because its shape (a standalone hero card above Quick Stats vs. folded into the session table's open row vs. something else) depends on how the rest of the Today page settles first, rather than being decidable in isolation. This is deferred, to be picked up once the Today page's other elements (quick-action buttons, Quick Stats, session table) are seen together — not left as an accidental gap.

2026-11-24 — Settings page: direct functional port of the TUI's ConfigScreen
- The Settings page's functionality baseline is the TUI's `ConfigScreen`, as documented in `docs/detailed-design/configuration.md` (shipped behavior, not a brainstorm document — a legitimate design input per this feature's scope-boundary rule). The web Settings page is a single page (not split into sub-pages) covering the same four sections:
  1. **Daily work target** — radio choice of 37-hour week (`7.4`h), 40-hour week (`8.0`h), or Custom (free numeric input, validated `> 0` and `≤ 24`). Selecting a preset disables the custom input and shows the preset value; selecting Custom enables it.
  2. **Lunch** — radio choice of Included / Excluded from working hours, plus a Lunch duration (minutes) input (default `30`, valid range `0`–`240`, blank treated as default).
  3. **Excluded tasks** — an add/remove list of free-text task identifiers excluded from hours totals. `"Lunch"` is rejected (owned by the Lunch section); duplicates are silently ignored on add.
  4. **Always-separate tasks** — same add/remove list pattern, for tasks that get standalone Promark-style rows instead of being folded into the consolidated day span.
- Save/Close interaction model, adapted for the web:
  - **Save** validates all fields server-side before writing anything (matches `ConfigScreen._handle_save`'s all-or-nothing validation). On validation failure, the form re-renders with inline errors next to the offending field(s) and nothing is persisted — implemented as an HTMX form POST that swaps in the same form fragment with error state, avoiding a full page reload/navigation for the "fix and retry" loop.
  - **Close/Cancel** has no special discard step on the web: since the form only holds state in the browser until submitted, simply not submitting (or navigating to another nav item) is equivalent to the TUI's Escape-discards-changes behavior. No separate "are you sure" or in-memory rollback is needed.
  - The **corrupt stored task list** guard is carried over: if a stored excluded/always-separate list can't be parsed as a JSON array of strings, Save is blocked with an inline error rather than silently overwriting it with an empty list — same rule as `ConfigScreen`/`SettingsRepository.has_corrupt_task_lists`.
- Per this feature's Non-Goals, the web app does not import or call `SettingsStorage.py`/`ConfigScreen.py` directly; it implements its own equivalent read/write logic against the shared `settings` table, using `configuration.md`'s documented key names and defaults (`daily_work_target_hours`, `lunch_excluded`, `lunch_duration_minutes`, `excluded_tasks`, `always_separate_tasks`) as the authoritative schema reference so both apps keep writing settings the same way.

2026-11-24 — Active Session hero: v1 interim answer (closes the deferred item for inventory purposes)
- The deferred Active Session hero/ticker (see "Today page: Quick Stats row added" entry above) gets an explicit v1 answer so the page/route inventory has no silent gap: **v1 ships without a dedicated Active Session hero element.** The only indication of the active session is the session table's open-ended row (no end time), which is already part of the agreed design.
- This is a deliberate, acknowledged scope cut for v1, not an oversight: a dedicated hero/ticker is tracked as a fast-follow enhancement, to be designed once the rest of the Today page (quick-action buttons, Quick Stats, session table) is actually live and can be seen together — consistent with the reasoning for deferring it in the first place.

2026-11-24 — Page load strategy: single synchronous render, not per-section async fetches
- Each page (`/today`, `/weekly`, `/settings`) is rendered as **one synchronous server-side response**: a single Python function gathers everything the page needs (Quick Stats, session table, etc.) from one consistent read of the database, and Jinja2 renders the whole page in one pass. The browser does not fire a set of small independent async requests on page load to fill in Quick Stats, the session table, etc. separately.
- Rationale:
  - **Consistency.** Splitting page-load data into separate async calls risks those calls landing at slightly different times and showing a Quick Stats row and a session table computed from different moments — a real possibility since this feature's own Requirements explicitly allow the TUI to write concurrently while the web app is open. A single request/single snapshot avoids this.
  - **No latency to hide.** The data source is a local SQLite file on loopback with no network hop; there is no slow upstream call that parallel async fetching would meaningfully help with, so the added complexity (multiple endpoints, per-section loading/error states) buys nothing.
  - **One pattern, not two.** HTMX is already scoped elsewhere in this document to *post-mutation* swaps (re-rendering the session table/Quick Stats fragment after New Session/Resume/Lunch submit) — that is a meaningfully different case (something genuinely changed, and only that part should update without disturbing the rest of the page) from *initial load*, where nothing has changed yet and a full render is simplest. Using HTMX for both load-time fan-out and post-mutation updates would mix two patterns for no benefit.
- This does not change anything about the already-agreed HTMX usage for mutating actions (New Session/Resume/Lunch submissions, Settings Save) — those remain small, targeted HTMX swaps of the affected fragment, which is the correct use case for HTMX here.

2026-11-24 — Feature approved
- User reviewed the full document — Requirements, Non-Goals, Manual Changes decisions, and the Page/Route/Component Inventory — and explicitly approved it.
- Status advanced from Proposed to **Approved**. Per `AGENTS.md`, this approval does not itself trigger implementation; implementation begins only when the user opens a new session and explicitly requests it with a reference to this feature document.

2026-11-24 — Correction: repository restructuring IS required (supersedes the "not needed" item above)
- The prior same-day entry marking repository restructuring as "not needed" is corrected: the "clean root" restructuring from 2026-11-19 is still relevant and is required before/alongside the web app's implementation.
- Rationale: every Python module that exists today — both the root domain modules (`Commands.py`, `Storage.py`, `EpicStorage.py`, `SettingsStorage.py`, `Promark.py`, `Printer.py`, `Constants.py`, `logger.py`, `app_context.py`) and the existing `app/` package — is TUI code. All of it moves under `app/` so the repository root is clean.
- The web application does not reuse any of that relocated code; it starts fresh in a new, independent top-level `webapp/` package.
- `db/` remains the only package shared between `app/` (TUI) and `webapp/` (web app).
- Updated package shape:
  ```text
  TimeTracker.py   — TUI entry/bootstrap module only (stays at root)
  app/             — all existing code: TUI Textual package plus the relocated former-root domain modules
  webapp/          — new, independent FastAPI/Jinja2/HTMX web application (shares nothing with app/ except db/)
  db/              — generic SQLite infrastructure, shared by both app/ and webapp/
  ```

2026-11-26 — New Session modal: conditional Epic field state (revisits Phase 3 simplification)
- **Decision:** the New Session modal's Epic select and New Epic name input are now disabled (grayed out) whenever the entered Task already has a linked Epic (an existing `task_catalog` entry). The fields remain enabled/open whenever the task is new or not yet linked. This replaces the Phase 3 behavior where the Epic fields were always enabled regardless of whether the task was already linked.
- Mechanism: no extra round-trip and no change to the always-rendered-fields approach. `today_service.build_today_view_model` already computed `task_has_epic` (a `{task: bool}` map for every known task) but it was unused by the template. It is now serialized into a `data-task-epic-map` attribute on the modal `<form>` via a new `tojson` Jinja filter (registered in `webapp/templating.py`, since Starlette's `Jinja2Templates` does not provide Flask's `tojson` out of the box). A small inline script toggles `disabled` on the Epic `<select>`/new-epic `<input>` and clears their values whenever the typed Task matches a key with `true` in that map.
- The backend behavior from Phase 3 is unchanged: an already-linked task still silently ignores any submitted Epic fields server-side. This is purely a client-side UX fix so the form no longer visually implies an Epic choice matters for a task that already has one.
- Status: implemented directly (not deferred further) — this is a small UI correction within the already-Approved feature's existing Phase 3 scope, not a new design.

2026-11-26 — New Session modal: show the linked Epic in the disabled select (correction)
- **Decision:** when a task already has a linked Epic, the (disabled) Epic `<select>` now shows that Epic pre-selected, instead of showing the blank "— None —" option. This corrects the immediately-preceding entry, where the disabled select was cleared to blank rather than displaying the actual linked Epic.
- Mechanism: `today_service.build_today_view_model`'s per-task map changed from `task_has_epic` (`{task: bool}`) to `task_epic_id` (`{task: epic_id | None}`), so the client has the actual linked Epic id, not just a boolean. The modal's script now sets `epicSelect.value` to that id (instead of blanking it) whenever the typed task is linked, in addition to still disabling the field. The New Epic name input is still blanked (it is never relevant once a task is linked).
- Backend behavior is unchanged: submitted Epic fields are still ignored server-side for an already-linked task.

2026-11-26 — Stop button: closes the active session (fills a Phase 3 gap)
- **Gap identified:** Phase 3 shipped New Session/Resume/Lunch but no action to simply *end* the active session without starting a replacement one. Since the web app's Non-Goals/Requirements never reuse `app.Commands`, and the Page/Route/Component Inventory never listed a stop/close action, an open session had no way to be closed from the web UI at all (the TUI's `cmd_stop`/`cmd_pause` have no web equivalent).
- **Decision:** add a fourth quick-action button, **Stop**, as a Bootstrap split button (same shape as Resume/Lunch): main button opens a modal with an **End Time** input (`<input type="time" step="300">`, defaulting to now rounded to 5 minutes, per the existing Start Time convention); the dropdown reveals a **"Now"** bypass. Stop is the web equivalent of the TUI's `cmd_pause` (closes the open session; no end-of-day summary dialog exists in the web UI to trigger, so `cmd_stop`'s extra day-summary step is not reproduced — the re-rendered Quick Stats row already reflects the closed session).
- If no session is currently open, Stop returns the same inline error style as the other actions ("No active session to stop.") rather than silently no-opping.
- New endpoints: `POST /sessions/stop` (body: end time, via a new `StopForm` Pydantic model in `webapp/schemas/today.py`) and `POST /sessions/stop/now`, both re-rendering the `_today_fragment.html` HTMX swap target like the other four mutating routes. New `webapp/templates/_stop_modal.html` partial, included from `today.html` alongside the other three modals. Page/Route/Component Inventory tables above are updated to list this as a fifth row in each table and a new template.
- Not a new design: this corrects an inventory omission in the already-Approved Phase 3 scope (the active-session close workflow was always implied by "sessions can be started" but was missed when the Requirements/Inventory were written), not a new feature requiring re-approval.

2026-11-26 — New Session: auto-close the running session instead of rejecting (fills a Phase 3 gap)
- **Gap identified:** `today_service.do_new_session` rejected the submission with "A session is already running. Resume or close it first." whenever a session was already open, requiring a separate Stop action first. This was never a deliberate design decision — it was an ad-hoc guard added when the endpoint was built, and it broke the TUI's long-standing workflow where starting the next task implicitly closes whatever is currently running (the same pattern `cmd_resume`/`cmd_lunch` already follow: auto-close-then-open, no separate stop step required).
- **Decision:** `do_new_session` now auto-closes the currently open session at the submitted start time (same `_close_open_session_if_any` helper already used by Resume/Lunch) before opening the new one, instead of returning an error. The New Session modal's Start Time field already defaults to now-rounded-to-5-minutes, so the common case (finishing one task and immediately starting the next) requires no extra step, matching Resume/Lunch's existing feel.
- Not a new design: this corrects a behavioral gap in the already-Approved/Done Phase 3 scope (the auto-close-and-start pattern was always the intended workflow, mirrored from the TUI's Resume/Lunch commands, but was missed for the New Session endpoint specifically), not a new feature requiring re-approval — same category as the 2026-11-26 "Stop button" gap fix above.
- Test updated: `tests/webapp/test_today.py`'s `test_new_session_rejects_when_session_already_open` replaced with `test_new_session_auto_closes_open_session_then_starts_new_one`, asserting the old session is closed at the submitted start time and the new one opens immediately, with no rejection message.
- **Known gap, deliberately not fixed here:** the auto-close path has no validation that the submitted time is actually valid relative to the session it closes (e.g. a Start Time earlier than the open session's own start produces a backwards/negative-duration session). This is tracked as its own fast-follow feature — see `features/webapp-time-validation.md` (Brainstorming) — rather than folded into this gap fix, since it needs its own UI design pass (inline modal validation, not just a backend guard) and shouldn't block the auto-close behavior itself from shipping.

2026-11-26 — Pydantic models for endpoint request/response shapes
- **Decision:** `webapp/` endpoints use Pydantic `BaseModel` classes for both outbound JSON responses (as a route's `response_model`, e.g. `GET /health` → `webapp/schemas/health.py`'s `HealthResponse`) and inbound HTMX form POSTs (bound via `Annotated[SomeModel, Form()]`, confirmed working against the `fastapi>=0.115` pin in `requirements-webapp.txt` — FastAPI has supported binding a whole Pydantic model from form-encoded data since 0.113, not just JSON bodies).
- Rationale: this feature's mutating endpoints (New Session/Resume/Lunch submit, Settings Save) are HTMX form POSTs, not a JSON API (see Requirements: "No separate JSON/REST API surface is introduced beyond `/health`"). Binding the whole form to one validated Pydantic model gives the same type/validation benefits FastAPI normally reserves for JSON bodies, instead of declaring each field as a separate `Form(...)` parameter by hand.
- Not a new dependency decision: `docs/operations/software-standard.md`'s Dependency Policy already lists Pydantic as a preferred library.
- New package convention: `webapp/schemas/` — one module per route group (`schemas/health.py`, and `schemas/today.py`/`schemas/settings.py` once Phases 3 and 5 need request models), mirroring the existing `webapp/routes/`/`webapp/services/` split. See `webapp/schemas/__init__.py` for the full convention writeup.
- Applied immediately to the one endpoint that exists so far: `GET /health` now declares `response_model=HealthResponse` instead of returning a bare `dict`. Phases 3–5 are expected to add `schemas/today.py` (New Session/Resume/Lunch form models) and `schemas/settings.py` (the settings form model) as those routes are built, rather than hand-rolling `Form(...)` parameter lists.

## Open Questions (pre-design gaps, raised 2026-11-24 — resolved same day)

All items below were answered on 2026-11-24; see the "round 2" Manual Changes entry above and the Requirements/Non-Goals sections. Retained here only as a historical record.

1. ~~V1 page/workflow scope not yet in Requirements.~~ Resolved: deliberately left emergent — discovered through UI prototyping rather than frozen up front.
2. ~~Session editing: in or out of v1?~~ Resolved: out of scope as a predetermined requirement; `features/session-editing.md` is TUI-only brainstorming and not a design input here (see Purpose's scope-boundary note). Falls under the same emergent-scope bucket as item 1.
3. ~~Health/availability indicator: in or out of v1?~~ Resolved: **in scope** — on-page-load `/health` check to show backend up/down.
4. ~~Is the "clean root" repository restructuring still needed?~~ Initially resolved "not needed," then corrected later the same day: **it is required.** All existing code (current root modules + existing `app/` TUI package) moves into `app/`; the web app starts fresh in a new `webapp/` package; `db/` remains the only shared package. See the later "Correction" Manual Changes entry.
5. ~~Command palette/command bar: wanted or not?~~ Resolved: folded into the emergent-scope bucket (item 1); decided during UI prototyping.
6. ~~CSRF/form security posture.~~ Resolved: not relevant — loopback-only, never exposed.
7. ~~Fixed localhost port number.~~ Resolved: any non-standard port is fine; exact number chosen during implementation.


## Implementation Plan

This section sequences the work so it can be picked up phase-by-phase in a future implementation session. It does not itself authorize implementation — per `AGENTS.md`, implementation begins only when the user opens a new session and explicitly requests it with a reference to this document.

### Phase 0 — Archive superseded TUI-only feature docs

Before touching code, clear the non-completed documents out of `features/` so the folder only contains things actually relevant going forward (this feature, plus whatever TUI work is still deliberately alive). Move every `features/<name>.md` document that is **not** `standalone-web-app.md` and **not already under `features/completed/`** into a new `features/archived/` folder. As of this writing that is:

| File | Status at archive time | Reason |
|------|------------------------|--------|
| `command-redesign.md` | Brainstorming | TUI command-bar redesign; web app has no command bar (folded into emergent-scope bucket, not pursued) |
| `config-interval.md` | Brainstorming | TUI `ConfigScreen` interval editing; web Settings page is a direct port of shipped `ConfigScreen` behavior only |
| `config-layout.md` | Brainstorming | TUI `ConfigScreen` layout brainstorming |
| `configuration-view.md` | Documented | TUI configuration view iteration, superseded by shipped `docs/detailed-design/configuration.md` |
| `layout-density.md` | Proposed | TUI Textual layout/density concern, not applicable to a browser/CSS layout |
| `logging.md` | Documented | TUI-specific logging brainstorm; a `features/completed/logging.md` already documents what actually shipped |
| `obsidian-notes.md` | Refinement | TUI/Obsidian integration idea, unrelated to the web app |
| `session-editing.md` | Brainstorming | TUI inline session editing; explicitly called out as out-of-scope design input (see Purpose and Manual Changes, 2026-11-24 round 2) |
| `textual-testing.md` | Brainstorming | Textual-framework-specific testing approach, meaningless once the TUI is deleted |
| `toast.md` | Brainstorming | TUI toast/notification widget brainstorm |
| `vacation-periods.md` | Brainstorming | Feature brainstorm not yet evaluated against the web app; TUI-oriented in its current form |

Mechanics:

- `git mv` each file from `features/<name>.md` to `features/archived/<name>.md` (preserves history).
- Do **not** edit their contents or change their `Status:` field — archiving is a location change, not a status transition in the lifecycle sense. They are not `Completed`; they are shelved.
- Add one sentence at the top of each archived file's `## Next Step` (or just under the `Status:` line) noting: `Archived <date> — superseded by features/standalone-web-app.md; TUI is being retired, see Manual Changes 2026-11-23.` This keeps the "why is this here and not actionable" context local to the file instead of only living in this plan.
- Update `docs/index.md` only if it links directly to any of these files (check first; most links there are expected to point at `docs/*`, not `features/*`).
- `features/completed/*.md` is untouched — those stay where they are per `AGENTS.md`'s archive rule for completed features.
- This phase has no code impact and can be done independently of, and before, any other phase.
- **Status: Done (2026-11-24).** All eleven non-completed `features/*.md` documents listed above were moved to `features/archived/` via `git mv`; `features/completed/` was left untouched; no links to the archived files were found in `docs/index.md`.

### Phase 1 — Repository restructuring ("clean root")

Per the 2026-11-24 "Correction" Manual Change, this must happen before/alongside `webapp/` work, not be skipped:

1. Create `app/` destinations for the root domain modules and move them with `git mv` (preserve history): `Commands.py`, `Storage.py`, `EpicStorage.py`, `SettingsStorage.py`, `Promark.py`, `Printer.py`, `Constants.py`, `logger.py`, `app_context.py` → `app/Commands.py`, `app/Storage.py`, etc.
2. Update every import site across the repo (`app/*.py`, `TimeTracker.py`, `tests/*.py`) from bare `import Commands` / `from Storage import ...` style to `app.Commands` / `from app.Storage import ...` (exact form depends on current import style — grep first).
3. `TimeTracker.py` stays at the repository root as the TUI's entry/bootstrap module, now importing from `app.*`.
4. `db/` is not moved; it already sits at the root and stays there as the shared package.
5. Run the existing test suite (`tests/`) after the move and fix any broken imports. (Per environment constraints, the user runs `pytest`/`mvn`-equivalent commands; this plan only prescribes what must pass, not that the agent executes it.)
6. No behavior change is permitted in this phase — it is a pure move/import-fix refactor. Any accidental logic change here is a bug, not a feature change.
- **Status: Done (2026-11-24).** All nine root domain modules were moved into `app/` via `git mv`; every import site across `app/*.py`, `TimeTracker.py`, `tests/app/test_smoke.py`, and `db/*.py` (which also imported `Constants`/`logger` directly) was updated to the `app.`-prefixed form. `db/` itself was left in place. One incidental behavior-preserving fix was required: `app/logger.py`'s `_PROJECT_ROOT` path resolution was adjusted (one extra `os.path.dirname`) so the `logs/` directory still resolves to the repository root instead of `app/logs/` after the move. The test suite (`tests/app/`) was additionally reorganized into a subpackage mirroring `app/`, mirroring the 1:1 app/webapp test boundary that will exist once `webapp/` is added. Full test suite run: `61 passed`.

### Phase 2 — `webapp/` skeleton

1. Create the new top-level `webapp/` package: `webapp/__init__.py`, `webapp/main.py` (FastAPI app + Uvicorn entry point), `webapp/templates/`, `webapp/static/` (for vendored Bootstrap/jQuery/HTMX/Tabler assets once development settles — CDN references are acceptable as a temporary stand-in per Requirements).
2. Add `webapp/routes/` (or flat modules, TBD during implementation) for the route groups: today, weekly, settings, health.
3. Add `webapp/services/` (or similarly named module) for the independent web-service functions that read/write the shared SQLite database directly — these do not import `app.Commands`/`app.Storage`/etc. per Non-Goals.
4. Wire up `db/` usage from `webapp/` the same way `app/` uses it, confirming no domain schema knowledge leaks into `db/` (per the Brainstorm Notes' `db/` boundary discussion).
5. Implement `GET /health` first — smallest possible vertical slice to prove the FastAPI process runs, binds to `127.0.0.1`, and reads the environment correctly.
6. Add `webapp/__main__.py` or a small `.bat`/Startup-shortcut launcher per the deferred-but-minimal startup requirement.
- **Status: Done (2026-11-26).** `webapp/` created with `__init__.py`, `Constants.py` (HOST/PORT), `templating.py` (shared `Jinja2Templates`), `main.py` (FastAPI app, static mount, router wiring, `/` → `/today` redirect), `__main__.py` (`python -m webapp` → Uvicorn on `127.0.0.1:8765`), `routes/{health,today,weekly,settings}.py`, `services/health_service.py`, `templates/{base,today,weekly,settings}.html` (Tabler/Bootstrap/jQuery/HTMX via CDN per Requirements — vendoring is Phase 6), and `static/.gitkeep`. Today/Weekly/Settings are intentionally skeleton stubs (real content lands in Phases 3–5); `/health` is fully implemented, calling a new `webapp/services/health_service.py` that runs a trivial `SELECT 1` through `db/repository.py` directly. A root-level `start_webapp.bat` is the manual launcher. New dependencies recorded in `requirements-webapp.txt` (fastapi, uvicorn, jinja2, python-multipart) and `httpx` added to `requirements-dev.txt` for `TestClient`-based tests. New tests in `tests/webapp/test_main.py` (6 tests) cover routing, template rendering, and both healthy/degraded `/health` outcomes.
  - **Prerequisite fix required and applied:** `db/connection.py` and `db/repository.py` previously imported `app.logger`/`app.Constants`, which meant importing `db/` at all transitively imported the `app/` TUI package — a direct violation of "`webapp/` must not import from `app/`". Fixed by moving the `DB_FILE` path constant into a new `db/config.py` (a path value, not domain schema knowledge — permitted in `db/` per the Brainstorm Notes "`db/` boundary" discussion) and switching both `db/` modules to plain `logging.getLogger(__name__)` (behaviorally identical to `app.logger.get_logger`, which is a thin wrapper around the same call). `app/Constants.py` now re-exports `DB_FILE` from `db/config.py` for backward compatibility; no `app/` behavior changed.
  - **Incidental bug fix:** `tests/app/test_smoke.py` still had a stale `sys.path.insert(0, .../tests)` plus bare `from Storage import ...` / `from Commands import ...` / `from SettingsStorage import ...` / `from EpicStorage import ...` / `from Promark import ...` / `from Printer import ...` imports left over from before the Phase 1 move. Beyond simply failing on their own, the `sys.path.insert` call shadowed the real `app/` package with the unrelated `tests/app/` test package for every test collected afterwards in the same session, breaking `tests/app/test_utils.py`'s correct `from app.utils import format_hhmm` import too. All of these were corrected to their `app.`-prefixed form and the `sys.path.insert` calls were removed from both `test_smoke.py` and `test_utils.py` (pytest's own package-mode `rootdir` insertion already makes this unnecessary). Full suite after the fix: `67 passed` (61 existing TUI tests + 6 new webapp tests).

### Phase 3 — Today page

1. Implement the independent query function(s) for: today's sessions (table rows), Quick Stats (today/remaining/leave/week/sessions), using `QuickStatsPanel`/`Printer.leave_projection` logic as the reference spec only (no import).
2. Build `base.html` (navbar: Today/Weekly/Settings, `/health` on-load check script) and `today.html` with the quick-action buttons, Quick Stats cards, and session table partials.
3. Implement `POST /sessions/new`, `/sessions/resume`, `/sessions/resume/now`, `/sessions/lunch`, `/sessions/lunch/now`, each returning the HTMX-swapped session table + Quick Stats fragment. Each POST body is bound to a `webapp/schemas/today.py` Pydantic model via `Annotated[Model, Form()]` (see Manual Changes, 2026-11-26), not individually declared `Form(...)` parameters.
4. Modals: new-session (task + conditional epic), resume (today-scoped task select + time), lunch (time only) — per the Page/Route/Component Inventory table.
- **Status: Done (2026-11-26).** New `webapp/services/{sessions_service,epics_service,settings_service,today_service}.py` (independent of `app.Storage`/`app.EpicStorage`/`app.SettingsStorage`/`app.Commands` per Non-Goals; `app.QuickStatsPanel`/`app.Printer.leave_projection`/`app.Commands` used only as the reference spec for `today_service`'s Quick Stats and resume carry-forward logic). `webapp/schemas/today.py` adds `NewSessionForm`/`ResumeForm`/`LunchForm`, each bound via `Annotated[Model, Form()]`. `today.html` now composes `_quick_action_buttons.html`, `_quick_stats.html` (5 Tabler stat cards), `_session_table.html`, and the three modal partials (`_new_session_modal.html`, `_resume_modal.html`, `_lunch_modal.html`); a `_today_fragment.html` partial (Quick Stats + session table, plus an inline error alert) is the HTMX swap target for all five mutating routes, wired via `#today-dynamic`.
  - **Simplification applied, partially revisited (see Manual Changes, 2026-11-26, "New Session modal: conditional Epic field state"):** the New Session modal always renders the Epic select/new-epic-name fields, but they are now disabled client-side whenever the entered task already has a linked Epic (resolved without an extra round-trip, by serializing the already-computed `task_has_epic` map into the page). The backend still only *acts* on submitted Epic fields when the task has no existing `task_catalog` entry yet — an already-linked task silently ignores any submitted Epic selection, so relinking remains out of scope. The New Session task field is a free-text input backed by an HTML5 `<datalist>` of known tasks (`epics_service.list_known_tasks()` — the union of distinct `sessions.task` values and `task_catalog.task_id`), not a strict `<select>`, so a brand-new task can always be typed.
  - Tests: `tests/webapp/conftest.py` adds a schema-creating `isolated_db` fixture (sessions/epics/task_catalog/settings, no triggers) shared by `test_main.py` (updated to use it, since `GET /today` now queries real tables) and the new `tests/webapp/test_today.py` (12 tests covering the empty state, session+epic rendering, all five mutating endpoints including the already-running-session guard and the lunch-skipping resume carry-forward, and Quick Stats rendering). Full suite: `79 passed`.
  - **Gap fix (2026-11-26, see Manual Changes "Stop button: closes the active session"):** a sixth mutating endpoint pair, `POST /sessions/stop` and `/sessions/stop/now`, plus a fourth quick-action button and `_stop_modal.html`, were added after the user noticed the Today page shipped with no way to close an open session short of editing the database directly. `today_service.do_stop`/`do_stop_now` and `schemas/today.py`'s `StopForm` follow the same pattern as the existing five actions. Three new tests added to `tests/webapp/test_today.py` (stop closes the open session, stop with none open returns an inline error, stop/now uses the current time).
  - **Gap fix (2026-11-26, see Manual Changes "New Session: auto-close the running session instead of rejecting"):** `today_service.do_new_session` no longer rejects with "A session is already running..." when a session is open; it auto-closes the open session at the submitted start time first (same pattern as Resume/Lunch), then opens the new one. `tests/webapp/test_today.py`'s rejection test was replaced with an auto-close assertion test.

### Phase 4 — Weekly page

1. Implement the independent equivalent of `EpicStorage.get_epic_summary_data`/`compute_day_promark` against the shared database.
2. Build `weekly.html` with week-nav header (prev/next, capped forward at current ISO week) and the day → Epic → task table with dual duration columns and `Week total` row.

### Phase 5 — Settings page

1. Implement independent read/write logic against the `settings` table using the key names documented in `docs/detailed-design/configuration.md` (`daily_work_target_hours`, `lunch_excluded`, `lunch_duration_minutes`, `excluded_tasks`, `always_separate_tasks`), including the corrupt-task-list guard.
2. Build `settings.html`/`_settings_form.html` with the four sections and server-side validation, HTMX-swapped inline errors on failure. The Save POST body is bound to a `webapp/schemas/settings.py` Pydantic model via `Annotated[Model, Form()]` (see Manual Changes, 2026-11-26); Pydantic validators/field constraints are the mechanism for the per-field inline error messages.

### Phase 6 — Asset vendoring and cleanup

1. Replace any CDN references for Bootstrap/jQuery/HTMX/Tabler with locally vendored static files under `webapp/static/`.
2. Confirm no Node.js/build tooling crept in.
3. Final pass against the Requirements/Non-Goals checklist in this document before calling the feature `Implemented`.

### Phase 7 — Documentation and TUI retirement (separate, later trigger)

- Per Manual Changes (2026-11-23), TUI deletion is a distinct, later decision — not automatic once `webapp/` works. Do not delete `app/`/`TimeTracker.py` as part of this feature's completion; that is a follow-up the user triggers explicitly once they've stopped using the TUI day-to-day.
- When this feature reaches `Implemented`, populate the Documentation Plan below (new `docs/design/` and `docs/detailed-design/` entries for the web app, registered in `docs/index.md`), then move this document to `features/completed/standalone-web-app.md` once `Completed`.

## Documentation Plan

_To be defined when the feature reaches Implemented (see Implementation Plan, Phase 7)._

## Brainstorm Notes

### 2026-11-19 — Repository separation and clean root

The repository layout is to be redesigned so future TUI and web entry points start from a much cleaner separation:

- `TimeTracker.py` remains the only Python entry module in the repository root.
- All other existing application modules move into `app/`.
- `db/` is the only shared lower-level package.
- The TUI and web application must remain separate applications and must not import from one another.
- The two applications may share data through the existing SQLite file, but they may not share TUI/web UI classes or entry-point code.

This requires a move of the following domain modules out of the root:

- `Commands.py`
- `Storage.py`
- `EpicStorage.py`
- `SettingsStorage.py`
- `Promark.py`
- `Printer.py`
- `Constants.py`
- `logger.py`
- `app_context.py`

The existing TUI modules already under `app/` remain TUI-owned. The standalone web application receives its own fresh top-level package, `webapp/`, with no dependency on the TUI package.

#### The `db/` boundary

The phrase "the only shared code should be `db/`" is important. `db/` should contain only generic SQLite mechanics:

- database connection lifecycle
- generic read/write/query helpers
- query type or result helpers
- database path configuration or path resolution, if it contains no TimeTracker domain rules
- optional generic migration infrastructure

`db/` must not contain TimeTracker domain logic or schema knowledge such as the names and columns of `sessions`, `epics`, `task_catalog`, or `settings`.

The `CREATE TABLE IF NOT EXISTS` and trigger declarations are domain/schema code, not generic SQLite infrastructure. Therefore they must not be placed in `db/` merely to make it available to both applications. A shared TimeTracker schema module outside `db/` would violate the "only shared code is `db/`" boundary unless `db/` is intentionally allowed to contain domain-specific initialization.

The cleanest interpretation is that `db/` remains generic and each standalone application owns its own initialization and schema setup. Because both applications initially use the same existing database, the web application should use the TUI-created schema rather than create a duplicate schema in its own startup path. If a future shared schema is necessary, it should become an explicitly separate shared domain package, with that boundary approved instead of silently placing domain information in `db/`.

This interpretation is the preferred baseline for the feature brainstorm. It gives both applications an independent runtime and leaves `db/` truly reusable infrastructure.

#### Proposed package shape

```text
TimeTracker.py         — TUI entry/bootstrap module only
app/
    (existing TUI Textual package contents)
    Commands.py, Storage.py, EpicStorage.py, SettingsStorage.py,
    Promark.py, Printer.py, Constants.py, logger.py, app_context.py
                       — relocated former-root domain modules, TUI-owned
webapp/                — new, independent FastAPI/Jinja2/HTMX application
 db/                   — generic SQLite infrastructure only, shared by app/ and webapp/
```

**Decision (2026-11-24):** this package shape is confirmed, not merely proposed — see the Manual Changes "Correction" entry. No decision has been made yet about internal sub-structure within `app/` or `webapp/` (e.g. whether `webapp/` further splits into `routes/`, `templates/`, `static/`, `services/`, etc.) — that remains to be refined during implementation.

#### Migration implications

- Moving root modules is a structural refactor and must not silently change application behavior.
- Existing imports and tests must be updated consistently.
- The TUI must remain runnable after the move.
- The web application must have its own entry module and must not import `app.*`.
- The existing database file and data remain unchanged.
- No database replacement or migration is needed for this structural phase.
- A schema initialization review is required before implementation so `db/` does not acquire domain-specific tables or triggers.

### 2026-11-19 — Standalone web application

The desired workflow is:

- TimeTracker runs in the background as a local web service.
- The user opens or pins a localhost URL in a browser.
- The browser provides the day-to-day interface.
- The existing TUI remains available as a separate application for the time being.
- Starting and using the web application does not require Node.js or TypeScript.

The strongest candidate architecture is:

- FastAPI for the Python HTTP application and API.
- Uvicorn for local serving.
- Jinja2 for server-rendered HTML.
- HTMX for selective partial-page updates, if the added dependency is acceptable.
- Plain browser JavaScript for behaviours that are not better handled through normal HTML and server rendering.
- No frontend build tool, package manager, Node.js runtime, or TypeScript toolchain.

The web application should be structurally independent:

- A dedicated top-level package, `webapp/`, will own routes, templates, static files, application startup, and web-specific view models.
- `webapp/` must not import from `app/`.
- `app/` must not import from `webapp/`.
- Both applications may share only the `db/` package.
- The browser application must not issue SQL or contain schema knowledge outside the existing storage layer.

The web application could call existing command and storage functions, but this requires careful design. `Commands.py` is TUI-oriented in part because it accepts an `AppContext` for feedback and UI refreshes. A web-specific context or web command service may be needed. Directly rendering TUI classes or reusing TuiAppContext is not intended.

The first database model should remain the existing SQLite database:

- Location: `%APPDATA%\TimeTracker\timetracker.db`
- Existing `sessions`, `epics`, `task_catalog`, `settings`, and `_h` tables remain authoritative.
- The web application does not create a parallel database for the same application data.
- The TUI and web application should be treated as shared-state local processes.

No database migration is proposed as part of this feature's first implementation. SQLite is already suitable for a single-user, local application. A migration script should only become necessary if a replacement database is later approved.

If a replacement database is approved in the future, migration requirements should include:

- A separate, explicit migration command or script.
- Importing sessions, epics, task catalog mappings, settings, and audit history.
- Preserving existing identifiers where practical.
- A dry-run or validation phase.
- A rollback or backup strategy.
- Verification counts and data checks after migration.
- No automatic replacement or deletion of the existing SQLite database.

### Runtime and deployment ideas

- Bind FastAPI to `127.0.0.1`, not `0.0.0.0` or an externally reachable interface.
- Use a fixed localhost port.
- Start Uvicorn automatically at Windows login using the Startup folder or Task Scheduler.
- Consider a small Windows wrapper or shortcut that starts the service without showing a terminal.
- Provide a health/status page or endpoint to help diagnose startup problems.
- Pin the application URL in the browser rather than creating an installed desktop application.
- Keep all browser assets local; do not rely on CDNs.
- The application may open the browser automatically on startup, but the browser need not be kept open for the service to run.

### 2026-11-20 — Server availability indication

The browser UI should tell the user when FastAPI is unavailable:

- `/health` is the preferred lightweight availability endpoint.
- `/alivecheck` may be used only if it fits an existing project convention.
- FastAPI's default documentation route is not an availability endpoint.
- The browser should check `/health` immediately on page load and approximately every 5 minutes afterward.
- Checks should use a short timeout and show a clear persistent status or notification when the server is down.
- The browser should not attempt to start a process or execute a Windows script.
- Subprocess execution remains separate future ProjectOrganizer functionality.

### UI ideas

The initial web view should cover the core current TUI behaviours:

- Active session and running timer.
- Today's timeline.
- Quick work-hour statistics.
- Start, lunch, pause, resume, stop, and restart actions.
- Task/Epic assignment.
- Epic creation and Task/Epic linking.
- Weekly overview.
- Promark-style output.
- Configuration settings.
- Command history is likely not necessary unless it maps cleanly to web navigation.

Visual style may initially mirror the dashboard concept or be a simpler responsive page. A full UX redesign should not be assumed without a dedicated approval stage.

### Concurrency and process behaviour ideas

- The FastAPI process and TUI may run at the same time because they share one database.
- SQLite should be tested under concurrent reads and writes from both processes.
- Mutating operations should use the existing write transaction behaviour.
- Web requests should refresh state from SQLite rather than keep a stale copy in memory.
- The web process should not cache sessions indefinitely.
- The service should stop cleanly and log startup, shutdown, and request/application failures.

### Security and workplace constraints ideas

- Localhost-only binding is a strong baseline, but controlled corporate laptops may restrict:
  - Installing Python packages.
  - Running Python from Startup.
  - Task Scheduler or Startup-folder execution.
  - Pinned browser behaviour.
  - Loopback HTTP access through endpoint filtering or browser policy.
- The browser-facing application should not expose external data APIs.
- Authentication is probably unnecessary while strictly bound to loopback, but this assumption must be tested against workplace policy.
- Cross-origin browser requests should be prevented or deliberately constrained.
- A cross-site request forgery defence should be considered before mutating HTML forms are exposed.
- Localhost security policy and browser exception management may require review before implementation.

### Alternatives considered

#### Jinja2 plus HTMX

Pros:

- Uses no Node.js or TypeScript.
- Server-rendered HTML is simple to maintain.
- FastAPI integration is conventional.
- HTMX can reduce repeated JavaScript while preserving partial updates.

Risks:

- HTMX is a new frontend dependency.
- It may not be desirable if workplace browser policy blocks JavaScript libraries or CDNs.
- Vendored assets and CSP compatibility need validation.

#### Jinja2 with plain JavaScript

Pros:

- Fewer dependencies.
- JavaScript can be reviewed and kept minimal.
- No frontend build process.

Risks:

- Partial-page update code becomes custom JavaScript.
- Timer and response handling need explicit implementation.

#### Pure HTML with form POST navigation

Pros:

- Maximum simplicity.
- No JavaScript dependency.
- Easiest to inspect and maintain.

Risks:

- Live timer and partial refreshes are inconvenient.
- Navigation may feel less responsive than the TUI.

#### Electron or a Tauri-style desktop wrapper

Rejected for this feature:

- Electron is incompatible with the preference to avoid Node.js.
- Tauri introduces a desktop wrapper and native toolchain beyond the browser-tab goal.
- It does not solve the requirement to run a pinned browser application.

#### Browser-only PWA with a different database

Rejected for now:

- Ordinary browsers cannot access the existing Windows SQLite file directly.
- OPFS or IndexedDB would require a different persistence model.
- Initial duplication or migration would complicate the standalone application.
- A PWA is a future interface option, not the initial architecture.

> **Update 2026-11-23:** The TUI is intended to be transitional and deleted once the web application is complete (see Manual Changes). This removes the "forever" framing of the duplication risk above — there would be no long-lived second interface to keep in sync, only a finite migration window. That weakens, but does not eliminate, the Spring Boot objection: the web app would still need a full from-scratch reimplementation effort during that window, with no shared test suite to prove behavioural equivalence with the TUI before it is retired. The FastAPI path remains preferable mainly because it can import the existing Python modules directly and avoid re-implementing the domain at all, not merely because it avoids indefinite duplication.

## Open Questions (resolved 2026-11-24)

All items below were answered on 2026-11-24; see the Manual Changes entry for that date and the Requirements/Non-Goals sections. Retained here only as a historical record of the original question list.

1. ~~Should HTMX be used, or should the first version use Jinja2 and plain JavaScript only?~~ Resolved: HTMX + Jinja2.
2. ~~Should browser assets be vendored or loaded via a package mechanism?~~ Resolved: Bootstrap/jQuery vendored locally.
3. ~~Task Scheduler, Startup folder, or service wrapper?~~ Resolved: not important now; `.bat`/Startup-folder shortcut is enough.
4. ~~Auto-open browser or manual pin?~~ Resolved: user pins the tab manually.
5. ~~Is every mutating action required to work while the TUI runs simultaneously?~~ Resolved: No — see 2026-11-23 manual change (TUI is transitional).
6. ~~Reuse `Commands.py`, extract shared services, or independent web functions?~~ Resolved: independent web service functions; only `db/` is shared.
7. ~~One dashboard with overlays, or multiple pages?~~ Resolved: to be redefined via iterative UI prototyping — may combine modals and/or subpages.
8. ~~Workplace browser policy compatibility?~~ Resolved: standard URL-based access assumed fine.
9. ~~Is Python/pip installation permitted?~~ Resolved: yes, fully permitted.
10. ~~Is authentication required for loopback-only access?~~ Resolved: doesn't matter — fully isolated local app.
11. ~~When should SQLite be replaced?~~ Resolved: separate future feature; SQLite expected sufficient indefinitely.
12. ~~Logging/diagnostics level?~~ Resolved: not relevant for this feature.

### 2026-11-19 — Browser UI template exploration

The browser version should translate the existing feature set rather than copy the TUI visually. It should cover, in the initial scope:

- Active session and running timer
- Start, lunch, pause, resume, stop, and restart actions
- Task/Epic assignment and Epic creation/linking
- Today's timeline
- Quick work-hour statistics
- Task notes
- Command/action feedback
- Weekly Overview
- Promark-style output
- Configuration settings

The following templates are layout alternatives for the primary dashboard. They do not yet make decisions about routing, HTMX/plain JavaScript, page count, or visual styling.

##### Template 1 — Persistent cockpit

```text
┌──────────────────────────── TimeTracker ─────────────────────────────┐
│ [Today] [Week] [Epic Summary] [Promark]             [Settings]       │
├──────────────────────────────────┬─────────────────────────────────┤
│ ACTIVE SESSION                   │ QUICK STATS                     │
│ TASK-4321                         │ Today  5.8h / 7.4h              │
│ Epic: Platform Ops                │ Rem.   1.6h                     │
│ Running 02:37:14                  │ Leave  ~15:42                   │
│ [Pause] [Stop] [Restart]          │ Week   31.2h / 37.0h            │
├──────────────────────────────────┴─────────────────────────────────┤
│ TODAY'S TIMELINE                                                   │
│ 07:00–08:30  TASK-1111  1.5h                                       │
│ 08:30–09:00  TASK-2222  0.5h                                       │
│ 09:00–Now    TASK-4321  2.6h  ▶                                   │
├────────────────────────────────────────────────────────────────────┤
│ TASK NOTES                                                         │
│ [notes for the active task]                                        │
├────────────────────────────────────────────────────────────────────┤
│ FEEDBACK                                                           │
│ ✓ Session started: TASK-4321 at 09:00                              │
└────────────────────────────────────────────────────────────────────┘
```

- Closest to the existing TUI and lowest conceptual risk.
- Keeps the full day at a glance.
- May feel tall and cramped on laptop screens unless the timeline and feedback sections scroll independently.
- Best fit if the browser should act like a pinned dashboard.

##### Template 2 — Browser app shell

```text
┌ Sidebar  ────────────────┬────────────────────── Main surface ───────┐
│ TimeTracker             │  Thursday, 19 November              │
│                         │                                      │
│ ● Today                 │  ┌ Active Session ───────────────┐  │
│   Weekly                │  │ TASK-4321 · 02:37:14          │  │
│   Epic Summary          │  │ [Pause] [Stop] [Restart]       │  │
│   Promark               │  └───────────────────────────────┘  │
│                         │                                      │
│ Settings                │  [Timeline]  [Notes]  [Feedback]     │
│                         │  07:00–08:30  TASK-1111              │
│                         │  08:30–09:00  TASK-2222              │
│                         │  09:00–Now    TASK-4321  ▶           │
│                         │                                      │
│                         │  5.8h today · 1.6h left              │
└─────────────────────────────┴──────────────────────────────────────────────┘
```

- Gives normal browser navigation clearer structure than one permanent dashboard.
- Keeps the active session and primary actions close to the top.
- The Today view can still contain most of the TUI dashboard panels.
- Adds side navigation and separate route/state decisions.
- Strong general-purpose option for desktop-first use.

##### Template 3 — Timeline-first workbench

```text
┌──────────────────────────── TimeTracker ─────────────────────────────┐
│ ┌ ACTIVE TASK ─────────────────────────────┐  ┌ QUICK ────────────┐ │
│ │ TASK-4321  02:37:14                      │  │ 5.8h / 7.4h       │ │
│ │ Platform Ops                             │  │ ~15:42 leave      │ │
│ │ [Start task] [Lunch] [Pause] [Stop]      │  │ 31.2h week        │ │
│ └─────────────────────────────────────────┘  └───────────────────┘ │
├────────────────────────────────────────────────────────────────────┤
│ Timeline                                    [Add] [Edit] [Weekly] │
│                                                                     │
│ 09:00 ───────────────────────── Now                                 │
│        Platform Ops · TASK-4321                                     │
│ 08:30 ─ 08:30–09:00 · TASK-2222                                    │
│ 07:00 ─ 07:00–08:30 · TASK-1111                                    │
├────────────────────────────────────────────────────────────────────┤
│ Task notes                               │ Action feedback          │
└────────────────────────────────────────────────────────────────────┘
```

- Makes the timeline and editing actions the centre of the experience.
- Good foundation for correcting session history and Epic/task assignment.
- Session editing is an adjacent but not necessarily required initial workflow.
- Visually more modern and less terminal-like than Template 1.
- Requires careful responsive behaviour for the two-column action areas.

##### Template 4 — Card-and-modal dashboard

```text
┌──────────────────────────── TimeTracker ─────────────────────────────┐
│ [Today] [Weekly] [Epic Summary] [Promark] [Settings]                 │
├─────────────────────────────────────────────────────────────────────┤
│ ┌ Running 02:37:14 ──────┐ ┌ Today ───┐ ┌ Week ────┐ ┌ Leave ────┐ │
│ │ TASK-4321              │ │ 5.8h     │ │ 31.2h   │ │ ~15:42    │ │
│ │ Platform Ops           │ │ /7.4h    │ │ /37.0h  │ │           │ │
│ └────────────────────────┘ └──────────┘ └──────────┘ └───────────┘ │
├──────────────────────────────────┬──────────────────────────────────┤
│ Today                            │ Actions                         │
│ Timeline rows                    │ [Start] [Lunch] [Pause]         │
│                                  │ [Resume] [Stop] [Restart]       │
├──────────────────────────────────┴──────────────────────────────────┤
│ Epic assignment and configuration open as focused overlays          │
└────────────────────────────────────────────────────────────────────┘
```

- Friendly, compact, and natural for cards/forms/overlays.
- Modals work well for Epic creation/linking and configuration.
- Risk of hiding too much state if overlays are overused.
- A good candidate if the UI wants to feel less like the TUI and more like a small web application.

##### Template 5 — Focused page-per-purpose

```text
Today     | Sessions     | Week     | Epics & Tasks     | Promark     | Settings

[Today]
  Active session hero + primary actions
  Today's timeline

[Sessions]
  Search/edit/list of sessions

[Week]
  Weekly overview and totals

[Epics & Tasks]
  Epic catalog, task links, and creation

[Promark]
  Generated output and copy/export-style actions

[Settings]
  Working hours and application configuration
```

- Lowest pressure on one dashboard to display every concept.
- Strongest separation of today, reporting, catalog, output, and configuration.
- Gives each workflow more screen room and simpler navigation.
- Requires more routes/pages and risks losing at-a-glance TUI behaviour.
- Weekly Overview, Epic linking, and Promark become first-class destinations rather than overlays.

#### Cross-template patterns

- Active-session state should remain visually dominant because it is the user's main at-a-glance status.
- Primary session actions should be directly visible rather than hidden behind a command bar.
- A command bar is not required in the web UI, but it could exist as an optional convenience or keyboard-accessible command palette.
- Today, Weekly, Epics/Tasks, Promark, and Settings should exist as coherent destinations even if the final template uses a dashboard with overlays.
- Task notes and action feedback are useful supporting panels, but should not compete with active-session or timeline controls.
- Configuration and Epic/task assignment should use explicit labels and form validation, rather than TUI command parsing.
- Every template should show an explicit idle state, not just an empty card.
- On small screens, the active session should remain first, followed by primary actions, then the timeline; reports and notes can move below or into separate pages.