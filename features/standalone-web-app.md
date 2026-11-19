# Feature: Standalone Browser Application

Status: Brainstorming

## Purpose

Provide a browser-based interface for TimeTracker that runs locally in a pinned browser tab, so normal daily use does not require keeping the Textual TUI open.

The browser application will be a fully standalone application in relation to the existing TUI. It will use the same SQLite database, but it will not depend on `app/`, Textual widgets, TUI contexts, or TUI-only entry points.

## Next Step

> **Current status:** Brainstorming
> **To reach Refinement:** Decide the initial web technology, browser interaction model, process startup method, and migration boundary.

## Requirements

_Not yet defined — brainstorm only._

## Non-Goals

_Not yet defined._

## Manual Changes

_(none yet)_

## Documentation Plan

_To be defined when the feature reaches Proposed._

## Brainstorm Notes

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

## Open Questions

1. Should HTMX be used, or should the first version use Jinja2 and plain JavaScript only?
2. Should browser assets be vendored with the application or loaded through an approved package mechanism?
3. Should FastAPI and Uvicorn be launched through Task Scheduler, the Startup folder, or a dedicated Windows service wrapper?
4. Should the browser open automatically at login, or should the user open/pin the URL manually?
5. Is every mutating action required to work while the TUI is running simultaneously?
6. Should the web application reuse `Commands.py` through a web context, extract shared command services, or create independent web service functions?
7. Should the web UI expose one dashboard page and overlays/modals, or begin with multiple normal pages?
8. Is workplace browser policy compatible with a local HTTP URL and client-side JavaScript?
9. Is Python package installation already permitted, or does startup need to use an existing virtual environment or installed runtime?
10. Is authentication required even for loopback-only access, or is OS-process isolation considered sufficient?
11. When, if ever, should the SQLite database be replaced, and should that decision be handled as a separate feature?
12. What level of logging and on-screen diagnostics is expected for a background service?

## Future Ideas

- Add a browser notification or in-page toast for reminders.
- Add a live timer that updates without a full page request.
- Add keyboard shortcuts mirroring the TUI command bar.
- Add a responsive mobile layout for a local phone browser, but not before the Windows workflow is stable.
- Add a migration script for a future database replacement.
- Add service health reporting in Windows or an application tray icon.
- Add an optional local API if it is useful outside the Jinja-rendered interface.

## Next Step

> **Current status:** Brainstorming
> **To reach Refinement:** Review the open questions, select the smallest feasible initial architecture, and remove ideas that are not required for the first browser workflow.
