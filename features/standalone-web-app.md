# Feature: Standalone Browser Application

Status: Refinement

## Purpose

Provide a browser-based interface for TimeTracker that runs locally in a pinned browser tab, so normal daily use does not require keeping the Textual TUI open.

The browser application will be a fully standalone application in relation to the existing TUI. It will use the same SQLite database, but it will not depend on `app/`, Textual widgets, TUI contexts, or TUI-only entry points.

## Next Step

> **Current status:** Refinement
> **To reach Proposed:** Settle on a concrete UI layout (dashboard/subpages/modals) and translate the requirements below into a specific page/route inventory and component list.

## Requirements

- Web stack: FastAPI + Uvicorn, server-rendered with Jinja2 templates, enhanced with HTMX for partial-page updates. (Jinja2 is required regardless of HTMX, since it is how FastAPI response data is injected into HTML.)
- Frontend assets: Bootstrap and jQuery. Referencing them via CDN is acceptable during active development, but before this feature is considered complete and merged via pull request, they must be converted to static files vendored locally in the repo. No Node.js, no TypeScript, no frontend build tooling, no package manager for JS at any stage.
- The web application is an independent process from the TUI:
  - New independent web service functions are written for the web app instead of reusing `Commands.py`/`*Storage.py`/`AppContext`.
  - The only code shared between the TUI and the web app is the `db/` package (generic SQLite infrastructure).
  - `web/` (or equivalent package) must not import from `app/`, and `app/` must not import from `web/`.
- The web app and TUI may run concurrently against the same SQLite database; no in-memory caching of session/epic state across requests — each request reads fresh from SQLite.
- Access model: plain `http://127.0.0.1:<port>/` URL, bound to loopback only. No authentication. Standard browser same-origin navigation (no special CORS handling needed since there is no cross-origin caller).
- Startup: manual for now. Acceptable minimal options are a `.bat` file or a Startup-folder shortcut; no Task Scheduler/service wrapper design needed at this stage.
- The user opens/pins the browser tab manually; the app does not need to auto-launch a browser.
- UI shape is not yet finalized: expect to prototype one layout, get it in front of the user, and refactor the UI more than once before settling. The final shape may combine a dashboard with modals and/or dedicated subpages — this will be decided in a follow-up UI design pass before moving to Proposed.
- Logging/diagnostics: not a concern for this feature; use whatever baseline logging the rest of the app already has.

## Non-Goals

- No database replacement or migration; SQLite remains the store for the web app. Any future replacement of SQLite (and the associated transition plan) is explicitly a separate feature.
- No authentication/authorization layer.
- No CDN-hosted or npm/yarn-managed frontend dependencies in the merged/completed feature; a CDN reference is an acceptable temporary convenience during active development but must be replaced with vendored static assets before the feature is considered done and merged via pull request. No frontend build pipeline regardless.
- No automatic process supervision (Task Scheduler/Windows service) design as part of this feature.
- No automatic browser launching.
- No reuse of `Commands.py`, `*Storage.py`, or `AppContext`/`TuiAppContext` by the web app; no shared UI code between TUI and web app beyond `db/`.
- Command-history-style interaction is not an explicit goal for the web UI.

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


## Documentation Plan

_To be defined when the feature reaches Proposed._

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

The existing TUI modules already under `app/` remain TUI-owned. The standalone web application will receive its own package beneath or alongside `app/`, with no dependency on the TUI package.

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
TimeTracker.py         — local entry/bootstrap module only
app/
    tui/               — existing Textual application and TUI presentation
    web/               — standalone FastAPI/Jinja application
    domain/            — if required, shared command/storage behavior
    legacy root modules? — none, after the migration
 db/                   — generic SQLite infrastructure only
```

The exact names and package shape remain to be refined. In particular, no decision has been made about whether existing `Commands.py` and `*Storage.py` modules should be moved unchanged, wrapped into shared domain services, or rewritten to serve only the web application.

#### Migration implications

- Moving root modules is a structural refactor and must not silently change application behavior.
- Existing imports and tests must be updated consistently.
- The TUI must remain runnable after the move.
- The web application must have its own entry module and must not import `app.tui.*`.
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

- A dedicated top-level package, such as `web/`, will own routes, templates, static files, application startup, and web-specific view models.
- `web/` must not import from `app/`.
- `app/` must not import from `web/`.
- Both applications may share lower-level domain and storage modules.
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