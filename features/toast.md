# Feature: Toast Notifications

Status: Brainstorming

## Purpose

Remind the user when no active time tracking session is running, by periodically sending a Windows toast notification. This prevents untracked work time going unnoticed.

## Requirements

- The application must be running (e.g. added to Shell:startup) for notifications to work.
- On application startup, a background thread is spawned that runs on a configurable interval (every 5–10 minutes).
- The background thread checks whether an active session is currently registered.
- If no active session is found, a Windows toast notification is sent to alert the user.
- Notifications repeat on each interval tick as long as no session is active.
- When the application is shut down, the background thread stops and no further notifications are sent.

## Non-Goals

- Does not track or modify sessions itself — it only reads session state.
- Does not send notifications through any channel other than Windows toast.
- Does not persist notification history.

## Manual Changes

_None yet._

## Brainstorm Notes

**Pre-requisites identified:**
- The Textual feature must be completed before this feature is implemented.
- The application should be added to `Shell:startup` so it runs automatically and can issue notifications.

**Package considered:** `win11toast`
- Provides a straightforward API for sending Windows 11 toast notifications.
- No standard library alternative exists for native Windows toast notifications.

**Threading approach:**
- A scheduled background thread is started at application startup.
- The thread polls for an active session at a fixed interval (proposed: every 5–10 minutes).
- The thread is tied to the application lifecycle — shutting down the app stops the thread and all notifications.

**Notification behavior:**
- Only triggered when no active session is detected.
- Should indicate clearly to the user that no session is registered.
- Optional: check if the system is active (e.g. not idle/locked) before sending, to avoid unnecessary notifications.

## Future Ideas

- Make the notification interval configurable by the user.
- Add system idle detection to suppress notifications when the user is away.
- Allow the user to start a session directly from the toast notification (action button).