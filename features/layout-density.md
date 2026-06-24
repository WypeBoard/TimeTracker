# Feature: Layout Density Toggle

Status: Proposed

## Purpose

Allow the user to switch between layout density modes inside the TUI so the
dashboard is usable on terminals with small fonts or limited screen real estate.

Because Textual renders inside a terminal emulator, the app cannot directly
control font size — that is a terminal-level setting. What the app can control
is the amount of padding, margin, and fixed heights applied to each widget.
Cycling through density presets achieves a similar "zoom" feel without changing
the font.

---

## Requirements

- Three density levels:
  - **Compact** — minimal padding (0), reduced Output panel height, no top margin on
    the Output panel.
  - **Normal** — current defaults (padding `0 1`, Output height `8`, margin-top `1`).
  - **Comfortable** — extra padding (`1 2`), taller Output panel height (`12`),
    slightly larger margins.
- Keybindings `[` (decrease) and `]` (increase) cycle through the three levels.
- The current density level is shown in the footer or the Header sub-title so the
  user can see what mode is active.
- The selected density is **not** persisted across restarts (session-only preference).
- Changing density must not disrupt the currently displayed content — only CSS
  properties are updated, no data re-fetch.

---

## Non-Goals

- Does not change the terminal font size (that is a terminal emulator concern).
- Does not persist the density preference to disk.
- Does not add more than three levels.
- Does not change any widget's content or data-fetching logic.

---

## Manual Changes

_(none yet)_

---

## Brainstorm Notes

### Implementation sketch

`TimeTrackerApp` maintains a cycle index (0 = compact, 1 = normal, 2 = comfortable).
On each keypress the index advances (or retreats) and `app.stylesheet` / inline CSS
is updated by calling helper methods that apply reactive CSS classes to the `Screen`
or root container.

The cleanest Textual approach is to add CSS classes to the root `Screen` widget:

```
Screen.density-compact  { ... }
Screen.density-normal   { ... }   /* default — same as no class */
Screen.density-comfortable { ... }
```

Binding `[` to `action_density_down` and `]` to `action_density_up` in `BINDINGS`
makes the keys discoverable via the built-in Footer widget.

### Affected CSS properties

| Widget | Compact | Normal | Comfortable |
|--------|---------|--------|-------------|
| `TodayPanel`, `WeekPanel` | `padding: 0` | `padding: 0 1` | `padding: 1 2` |
| `OutputPanel` | `height: 5` | `height: 8` | `height: 12` |
| `OutputPanel` | `margin-top: 0` | `margin-top: 1` | `margin-top: 1` |

### Keybinding rationale

`[` / `]` are conventional "smaller / larger" keys (used by vim, browsers in some
contexts) and are unlikely to conflict with command syntax since no current command
uses those characters.

---

## Future Ideas

- Persist the density preference to a config file or SQLite settings table.
- Add a fourth "micro" level for very constrained terminals.
- Show a transient toast/notification confirming the new density level on change.
