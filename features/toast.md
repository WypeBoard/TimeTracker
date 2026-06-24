# Feature: Toast Notifications

Status: Brainstorming

## Purpose

Remind the user when no active time tracking session is running, by periodically sending a Windows toast notification. This prevents untracked work time going unnoticed.

Additionally, surface today's Outlook calendar schedule at startup and re-notify the user whenever calendar changes are detected, so the user can make informed decisions about session labelling.

## Requirements

### Notification library

- All Windows toast notifications **must** use the `win11toast` library exclusively.
- No in-app toasts (e.g. Textual's built-in notification system) are to be used for any of the notifications described in this feature.
- No alternative notification library is to be considered or substituted.

### Application lifecycle

- The application must be running (e.g. added to Shell:startup) for notifications to work.
- On application startup, a background thread is spawned that runs on a fixed interval of **5 minutes**.
- When the application is shut down, the background thread stops and no further notifications are sent.

### Session tracking reminder

- The background thread checks whether an active session is currently registered.
- If no active session is found, a `win11toast` notification is sent to alert the user.
- Notifications repeat on each interval tick as long as no session is active.

### Outlook schedule awareness

- On each interval tick, all meetings for the current calendar day are fetched via `win32com.client`.
- "All meetings" means every calendar item returned for today — no filtering by type, category, or response status.
- The first time events are fetched a `win11toast` notification is sent summarising today's schedule (event titles and times).
- The fetched meeting list is persisted to a dedicated database table (`calendar_meetings`) and compared against the previously stored snapshot for today.
- If a new meeting is detected, or an existing meeting has changed (subject, start time, end time, or cancellation status), a new `win11toast` notification is sent describing what changed.
- Only meetings for the current calendar day are considered; past and future dates are ignored.

### Vacation period cross-check

- This check is **deferred** and depends on the separate **Vacation Periods** feature (see `features/vacation-periods.md`).
- The Vacation Periods feature will piggyback on this feature once it is implemented.
- No vacation cross-check logic is part of this feature's implementation scope.

## Non-Goals

- Does not track or modify sessions itself — it only reads session state.
- Does not send notifications through any channel other than Windows toast via `win11toast`.
- Does not persist notification history across application restarts.
- Does not create, modify, or delete Outlook calendar events.
- Does not cover multi-day Outlook diffing — only today's meetings are tracked.
- Does not implement the vacation cross-check (deferred to Vacation Periods feature).

## Manual Changes

2026-06-22
- Pinned notification library to `win11toast` exclusively; Textual toast is explicitly excluded.
- Added Outlook schedule awareness requirement (today only, change detection).
- Added vacation period cross-check requirement; extracted vacation periods into a separate feature document.

2026-06-22 (revision)
- Vacation cross-check deferred; it is not required for this feature to be considered complete.
  The Vacation Periods feature will piggyback on this feature after it is implemented.
- Outlook scope clarified: fetch all meetings for the day — no filtering.
- Vacation suppression of "no active session" toasts is deferred to the Vacation Periods feature.
- Outlook meeting snapshot storage changed from in-memory to a dedicated DB table.
- `pywin32` dependency formally documented.
- Identity key changed from `GlobalAppointmentID` to `EntryID`.
- Notification interval fixed at 5 minutes.

## Brainstorm Notes

**Pre-requisites identified:**
- The Textual feature must be completed before this feature is implemented (Status: Implemented ✓).
- The application should be added to `Shell:startup` so it runs automatically and can issue notifications.
- The Vacation Periods feature is **not** a prerequisite for this feature.

---

**Package decision: `win11toast` only**
- `win11toast` provides a straightforward API for sending Windows 11 native toast notifications.
- No standard library alternative exists for native Windows toast notifications.
- Textual's notification system is explicitly excluded — it produces in-app UI banners, not OS-level toasts.
- No other library (e.g. `plyer`, `winotify`) is to be introduced for this purpose.

---

**Package decision: `pywin32` for Outlook integration**

- **Why needed:** `win32com.client` (part of `pywin32`) is the standard Windows COM automation interface for reading Outlook calendar data locally, without any network API or OAuth flow.
- **Alternatives considered:**
  - Microsoft Graph API: requires OAuth registration and network access — adds significant complexity that is out of scope.
  - Custom implementation: not possible without a COM or Graph binding.
- **Benefits:** Zero network dependency, works with the local default Outlook profile, battle-tested on Windows.
- **Maintenance:** Tied to the installed Outlook version; no known breaking changes between Outlook versions for the properties used here.
- Add to `requirements.txt` when implementation begins: `pywin32>=306`

---

**Outlook AppointmentItem — available properties (probed 2026-06-22)**

The following properties are accessible on an `AppointmentItem` object returned by `win32com.client`:

| Property | Type | Notes |
|---|---|---|
| `Subject` | `str` | Meeting title |
| `Start` | `datetime` | Timezone-aware start time |
| `End` | `datetime` | Timezone-aware end time |
| `Duration` | `int` | Duration in minutes |
| `EntryID` | `str` | Unique per occurrence — identity key used for change detection |
| `GlobalAppointmentID` | `str` | Stable across occurrences of the same recurring series |
| `MeetingStatus` | `int` | 0=non-meeting, 1=organizer, 3=received, 5=canceled (organizer), 7=received+canceled |
| `ResponseStatus` | `int` | 0=none, 1=organized, 2=tentative, 3=accepted, 4=declined, 5=not responded |
| `IsRecurring` | `bool` | Whether the item is part of a recurring series |
| `AllDayEvent` | `bool` | Whether it is an all-day event |
| `BusyStatus` | `int` | 0=free, 1=tentative, 2=busy, 3=out-of-office, 4=working-elsewhere |
| `Organizer` | `str` | Display name of the organizer |
| `Location` | `str` | Meeting location string |
| `Categories` | `str` | Comma-separated category string (may be empty) |

**Cancellation detection:** `MeetingStatus` values 5 (`olMeetingCanceled`) and 7 (`olMeetingReceivedAndCanceled`) indicate a canceled meeting.

---

**Outlook snapshot — database table approach**

Instead of keeping the meeting snapshot purely in memory, it is persisted to a dedicated `calendar_meetings` table in the existing SQLite database. This gives a clear, inspectable record of the last-known state of today's meetings.

Proposed schema:

```sql
CREATE TABLE calendar_meetings (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    fetch_date            TEXT NOT NULL,   -- ISO date, e.g. "2026-06-22" (always today)
    entry_id              TEXT NOT NULL,   -- identity key; unique per occurrence
    subject               TEXT NOT NULL,
    start_time            TEXT NOT NULL,   -- ISO 8601 datetime string (UTC)
    end_time              TEXT NOT NULL,   -- ISO 8601 datetime string (UTC)
    meeting_status        INTEGER NOT NULL,
    response_status       INTEGER NOT NULL,
    is_all_day            INTEGER NOT NULL DEFAULT 0
);
```

**Change detection logic per tick:**

1. Fetch all meetings for today from Outlook via `win32com.client`.
2. Load today's stored rows from `calendar_meetings`.
3. Compare by `entry_id`:
   - Row absent in DB → **new meeting** → notify + insert row.
   - Row present in DB but `subject`, `start_time`, `end_time`, or `meeting_status` differs → **changed meeting** → notify + update row.
   - `meeting_status` in `(5, 7)` and was previously not canceled → **cancellation** → notify + update row.
   - Row present in DB but absent from today's Outlook fetch → **meeting removed** → notify + delete row.
4. On the very first fetch for the day (no rows for `fetch_date`), send a summary notification of all meetings, then insert all rows.

---

**Threading approach:**
- A single background thread handles both notification checks (session reminder + Outlook schedule).
- The thread polls at a fixed interval of **5 minutes**.
- The thread is tied to the application lifecycle — shutting down the app stops the thread and all notifications.
- The vacation cross-check will be added to this thread once the Vacation Periods feature is implemented.

---

**Notification behavior:**
- Session reminder: triggered on every tick where no active session is detected.
- Schedule summary: triggered once on the first fetch of the day.
- Meeting change: triggered whenever a new, changed, canceled, or removed meeting is detected.

## Future Ideas

- Make the notification interval configurable by the user (currently fixed at 5 minutes).
- Add system idle detection to suppress notifications when the user is away.
- Allow the user to start a session directly from the toast notification (action button).
- Support multi-day vacation cross-checking (part of Vacation Periods feature, not this feature).
- Vacation cross-check: once Vacation Periods feature is implemented, add a check here that warns when a local vacation period has no corresponding Outlook entry.
- Suppress "no active session" toasts during an active vacation period (Vacation Periods feature).
