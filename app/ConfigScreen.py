"""ConfigScreen — TUI configuration screen.

Allows the user to edit application settings without touching code:

  - Daily work target (37h / 40h / Custom)
  - Lunch handling (included/excluded worktime, lunch duration)
  - Excluded tasks (not counted toward the daily target)
  - Always-separate tasks (standalone Promark rows)

Interaction model:
  - All edits are held in memory while the screen is open.
  - [Save]: validates all fields; if valid, writes to the database and closes.
             If invalid, shows an inline error and stays open. Text left in an
             open "add task" input is committed before saving rather than
             being discarded.
  - [Close] / Escape: discards all unsaved changes and closes.

Access:
  - Type 'config' in the command bar.
  - Press Ctrl+, (the VS Code convention for settings).
"""
from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, RadioButton, RadioSet, Static

from SettingsStorage import SettingsRepository


class ConfigScreen(ModalScreen):
    """Configuration screen for application settings.

    Edits are held in memory. Nothing is written to the database until the
    user presses [Save]. Escape / [Close] discards all changes.
    """

    BINDINGS = [
        Binding("escape", "handle_escape", "Close"),
    ]

    DEFAULT_CSS = """
    ConfigScreen {
        align: center middle;
    }

    #config-container {
        width: 74;
        max-height: 92vh;
        background: $surface;
        border: double $accent;
        padding: 1 2;
    }

    #config-title {
        text-style: bold;
        margin-bottom: 1;
        text-align: center;
    }

    .section-heading {
        text-style: bold;
        color: $accent;
        margin-top: 1;
        margin-bottom: 0;
    }

    .section-hint {
        color: $text-muted;
        margin-bottom: 0;
    }

    .error-text {
        color: $warning;
    }

    #custom-target-row {
        height: auto;
        margin-top: 0;
    }

    #custom-target-row Label {
        padding: 0 1;
        height: 3;
        content-align: left middle;
    }

    #custom-hours-input {
        width: 10;
    }

    #lunch-duration-row {
        height: auto;
        margin-top: 0;
    }

    #lunch-duration-row Label {
        padding: 0 1;
        height: 3;
        content-align: left middle;
    }

    #lunch-duration-input {
        width: 8;
    }

    #excluded-list, #separate-list {
        height: auto;
        min-height: 1;
        margin-top: 0;
        margin-bottom: 0;
    }

    .task-row {
        height: 3;
        align: left middle;
    }

    .task-row Label {
        padding: 0 1;
        height: 3;
        content-align: left middle;
        width: 1fr;
    }

    .add-input-row {
        height: auto;
        display: none;
        margin-bottom: 1;
    }

    .add-input-row Input {
        width: 1fr;
    }

    #button-row {
        margin-top: 2;
        height: auto;
        align: right middle;
    }

    #button-row Button {
        margin-left: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        # In-memory task lists — only written to DB on Save.
        self._excluded_tasks: list[str] = []
        self._separate_tasks: list[str] = []
        # Set in on_mount: True when a stored task list could not be parsed.
        self._task_lists_corrupt: bool = False

    # ------------------------------------------------------------------ #
    # Widget composition
    # ------------------------------------------------------------------ #

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="config-container"):
            yield Static("⚙  Configuration", id="config-title")

            # ── Daily work target ────────────────────────────────────────
            yield Static("Daily work target", classes="section-heading")
            with RadioSet(id="target-radio"):
                yield RadioButton("37-hour week  (7h 24m)", id="target-37")
                yield RadioButton("40-hour week  (8h 00m)", id="target-40")
                yield RadioButton("Custom", id="target-custom")
            with Horizontal(id="custom-target-row"):
                yield Label("Hours: ")
                yield Input("", placeholder="e.g. 7.5", id="custom-hours-input")
            yield Static("", id="target-error", classes="error-text")

            # ── Lunch ─────────────────────────────────────────────────────
            yield Static("Lunch", classes="section-heading")
            with RadioSet(id="lunch-radio"):
                yield RadioButton("Included in working hours", id="lunch-incl")
                yield RadioButton("Excluded from working hours", id="lunch-excl")
            yield Static(
                "Excluded = the break is your own time: it does not count "
                "toward the daily target and is always reserved in the "
                "registered day span.",
                classes="section-hint",
            )
            with Horizontal(id="lunch-duration-row"):
                yield Label("Lunch duration: ")
                yield Input("", placeholder="30", id="lunch-duration-input")
                yield Label(" minutes")
            yield Static("", id="lunch-error", classes="error-text")

            # ── Excluded tasks ─────────────────────────────────────────────
            yield Static("Excluded from working hours", classes="section-heading")
            yield Static(
                "Tracked but not counted toward the daily target.",
                classes="section-hint",
            )
            with Vertical(id="excluded-list"):
                pass  # populated dynamically in on_mount
            with Horizontal(id="excluded-add-btn-row"):
                yield Button("Add exclusion…", id="btn-add-excluded")
            with Horizontal(id="excluded-input-row", classes="add-input-row"):
                yield Input(placeholder="Task name…", id="excluded-add-input")
            yield Static("", id="excluded-error", classes="error-text")

            # ── Always-separate tasks ─────────────────────────────────────
            yield Static("Always separate  (Promark only)", classes="section-heading")
            yield Static(
                "Counted as hours but reported as standalone rows in the Promark view.",
                classes="section-hint",
            )
            with Vertical(id="separate-list"):
                pass  # populated dynamically in on_mount
            with Horizontal(id="separate-add-btn-row"):
                yield Button("Add always-separate…", id="btn-add-separate")
            with Horizontal(id="separate-input-row", classes="add-input-row"):
                yield Input(placeholder="Task name…", id="separate-add-input")
            yield Static("", id="separate-error", classes="error-text")

            # ── Action buttons ─────────────────────────────────────────────
            with Horizontal(id="button-row"):
                yield Button("Save", id="btn-save", variant="primary")
                yield Button("Close", id="btn-close")

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def on_mount(self) -> None:
        """Load current settings from the database and populate the UI."""
        settings = SettingsRepository()

        # ── Daily work target ────────────────────────────────────────────
        target = settings.get_daily_work_target()
        custom_input = self.query_one("#custom-hours-input", Input)

        if target == 7.4:
            self._select_radio("target-radio", 0)
            custom_input.disabled = True
            custom_input.value = "7.4"
        elif target == 8.0:
            self._select_radio("target-radio", 1)
            custom_input.disabled = True
            custom_input.value = "8.0"
        else:
            self._select_radio("target-radio", 2)
            custom_input.disabled = False
            custom_input.value = str(target)

        # ── Lunch ────────────────────────────────────────────────────────
        # Radio index 0 = Included, index 1 = Excluded (default).
        self._select_radio("lunch-radio", 1 if settings.get_lunch_excluded() else 0)

        self.query_one("#lunch-duration-input", Input).value = str(
            settings.get_lunch_duration_minutes()
        )

        # ── Task lists ───────────────────────────────────────────────────
        # If a stored list is unreadable the screen must not pretend it is
        # empty — Save would then overwrite the real data with [].
        self._task_lists_corrupt = settings.has_corrupt_task_lists()

        self._excluded_tasks = list(settings.get_excluded_tasks())
        self._rebuild_excluded_list()

        self._separate_tasks = list(settings.get_always_separate_tasks())
        self._rebuild_separate_list()

        if self._task_lists_corrupt:
            self.query_one("#excluded-error", Static).update(
                "⚠  A stored task list could not be read — saving is blocked "
                "to avoid overwriting it. See the log for the raw value."
            )

    def _select_radio(self, radio_set_id: str, index: int) -> None:
        """Programmatically select a RadioButton by its 0-based index.

        RadioSet does not expose a simple press-by-index API, so we set
        value=True on the desired RadioButton, which triggers RadioSet's
        internal mutual-exclusion logic to deselect all others.
        """
        radio_set = self.query_one(f"#{radio_set_id}", RadioSet)
        buttons = list(radio_set.query(RadioButton))
        if 0 <= index < len(buttons):
            buttons[index].value = True

    # ------------------------------------------------------------------ #
    # RadioSet events
    # ------------------------------------------------------------------ #

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle radio button selection changes in the target-radio group."""
        if event.radio_set.id != "target-radio":
            return  # Only act on the work-target group.

        custom_input = self.query_one("#custom-hours-input", Input)
        pressed_id = event.pressed.id if event.pressed else None

        if pressed_id == "target-37":
            custom_input.disabled = True
            custom_input.value = "7.4"
        elif pressed_id == "target-40":
            custom_input.disabled = True
            custom_input.value = "8.0"
        elif pressed_id == "target-custom":
            custom_input.disabled = False
            custom_input.focus()

    # ------------------------------------------------------------------ #
    # Button events
    # ------------------------------------------------------------------ #

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Dispatch all button presses to the appropriate handler."""
        btn_id = event.button.id

        if btn_id == "btn-save":
            self._handle_save()
        elif btn_id == "btn-close":
            self.dismiss()
        elif btn_id == "btn-add-excluded":
            self._show_add_input("excluded")
        elif btn_id == "btn-add-separate":
            self._show_add_input("separate")
        elif btn_id and btn_id.startswith("rm-ex-"):
            # Remove button for an excluded task — parse index from ID.
            idx = int(btn_id[len("rm-ex-"):])
            if 0 <= idx < len(self._excluded_tasks):
                self._excluded_tasks.pop(idx)
                self._rebuild_excluded_list()
        elif btn_id and btn_id.startswith("rm-sp-"):
            # Remove button for an always-separate task — parse index from ID.
            idx = int(btn_id[len("rm-sp-"):])
            if 0 <= idx < len(self._separate_tasks):
                self._separate_tasks.pop(idx)
                self._rebuild_separate_list()

        # Stop propagation so the parent screen doesn't receive the event.
        event.stop()

    # ------------------------------------------------------------------ #
    # Input submitted events (Enter in add-item inputs)
    # ------------------------------------------------------------------ #

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in add-item inputs."""
        input_id = event.input.id

        if input_id == "excluded-add-input":
            self._add_task_to_list("excluded", event.value)
        elif input_id == "separate-add-input":
            self._add_task_to_list("separate", event.value)

    # ------------------------------------------------------------------ #
    # Escape handling
    # ------------------------------------------------------------------ #

    def action_handle_escape(self) -> None:
        """Escape: cancel the active add-input, or close the screen.

        If an add-input row is visible, Escape hides it (cancels the add).
        If no add-input is active, Escape closes the screen without saving.
        """
        if self.query_one("#excluded-input-row").display:
            self._hide_add_input("excluded")
        elif self.query_one("#separate-input-row").display:
            self._hide_add_input("separate")
        else:
            self.dismiss()

    # ------------------------------------------------------------------ #
    # Add-item helpers
    # ------------------------------------------------------------------ #

    def _show_add_input(self, which: str) -> None:
        """Show the inline add-input for the given list (excluded or separate)."""
        input_row = self.query_one(f"#{which}-input-row")
        input_widget = self.query_one(f"#{which}-add-input", Input)
        input_row.display = True
        input_widget.value = ""
        input_widget.focus()

    def _hide_add_input(self, which: str) -> None:
        """Hide and clear the inline add-input."""
        self.query_one(f"#{which}-input-row").display = False
        self.query_one(f"#{which}-add-input", Input).value = ""
        self.query_one(f"#{which}-error", Static).update("")

    def _add_task_to_list(self, which: str, raw_value: str) -> None:
        """Validate and add a task to the in-memory list, or show an error.

        Validation rules (per feature spec):
        - Must be a non-empty string after trimming whitespace.
        - 'Lunch' is explicitly rejected — it is handled in the Lunch section.
        - Duplicates are silently ignored (no duplicate added).
        """
        task = raw_value.strip()
        error_widget = self.query_one(f"#{which}-error", Static)

        if not task:
            # Empty input — do nothing, keep the input open.
            return

        if task == "Lunch":
            error_widget.update(
                '⚠  "Lunch" is configured in the Lunch section above.'
            )
            return

        target_list = self._excluded_tasks if which == "excluded" else self._separate_tasks

        if task in target_list:
            # Duplicate — silently ignore, close the input.
            self._hide_add_input(which)
            return

        target_list.append(task)
        error_widget.update("")
        self._hide_add_input(which)

        if which == "excluded":
            self._rebuild_excluded_list()
        else:
            self._rebuild_separate_list()

    # ------------------------------------------------------------------ #
    # List rebuild helpers
    # ------------------------------------------------------------------ #

    def _rebuild_excluded_list(self) -> None:
        """Clear and repopulate the excluded-tasks list widget."""
        container = self.query_one("#excluded-list", Vertical)
        container.remove_children()
        for i, task in enumerate(self._excluded_tasks):
            container.mount(
                Horizontal(
                    Label(task),
                    Button("Remove", id=f"rm-ex-{i}", variant="error"),
                    classes="task-row",
                )
            )

    def _rebuild_separate_list(self) -> None:
        """Clear and repopulate the always-separate tasks list widget."""
        container = self.query_one("#separate-list", Vertical)
        container.remove_children()
        for i, task in enumerate(self._separate_tasks):
            container.mount(
                Horizontal(
                    Label(task),
                    Button("Remove", id=f"rm-sp-{i}", variant="error"),
                    classes="task-row",
                )
            )

    # ------------------------------------------------------------------ #
    # Save logic
    # ------------------------------------------------------------------ #

    def _handle_save(self) -> None:
        """Validate all fields; write to the database if valid, stay open if not."""
        # Clear previous error messages.
        self.query_one("#target-error", Static).update("")
        self.query_one("#lunch-error", Static).update("")
        self.query_one("#excluded-error", Static).update("")
        self.query_one("#separate-error", Static).update("")

        # ── Refuse to overwrite data we could not read ────────────────────
        if self._task_lists_corrupt:
            self.query_one("#excluded-error", Static).update(
                "⚠  Saving is blocked: a stored task list is unreadable. "
                "Repair or clear the setting before saving."
            )
            return

        # ── Commit text still sitting in an open add-input ────────────────
        # Clicking [Save] straight after typing a task name used to discard
        # it silently, which looked exactly like "my settings disappeared".
        self._commit_pending_add_input("excluded")
        self._commit_pending_add_input("separate")

        # ── Validate daily work target ────────────────────────────────────
        custom_hours_input = self.query_one("#custom-hours-input", Input)
        raw_hours = custom_hours_input.value.strip()
        try:
            target_hours = float(raw_hours)
            if target_hours <= 0 or target_hours > 24:
                raise ValueError("out of range")
        except ValueError:
            self.query_one("#target-error", Static).update(
                "⚠  Hours must be a positive number no greater than 24."
            )
            return

        # ── Validate lunch duration ───────────────────────────────────────
        duration_raw = self.query_one("#lunch-duration-input", Input).value.strip()
        if duration_raw == "":
            lunch_duration = SettingsRepository.DEFAULT_LUNCH_DURATION_MINUTES
        else:
            try:
                lunch_duration = int(duration_raw)
                if lunch_duration < 0 or lunch_duration > 240:
                    raise ValueError("out of range")
            except ValueError:
                self.query_one("#lunch-error", Static).update(
                    "⚠  Lunch duration must be a whole number of minutes (0–240)."
                )
                return

        # ── Determine lunch exclusion from radio ──────────────────────────
        # RadioSet.pressed_index is the 0-based index of the currently selected
        # button. Index 0 = "Included", index 1 = "Excluded".
        lunch_radio = self.query_one("#lunch-radio", RadioSet)
        lunch_excluded = (lunch_radio.pressed_index == 1)

        # ── All valid — write to database ─────────────────────────────────
        settings = SettingsRepository()
        settings.set_daily_work_target(target_hours)
        settings.set_lunch_excluded(lunch_excluded)
        settings.set_lunch_duration_minutes(lunch_duration)
        settings.set_excluded_tasks(self._excluded_tasks)
        settings.set_always_separate_tasks(self._separate_tasks)

        self.dismiss()

    def _commit_pending_add_input(self, which: str) -> None:
        """Add any text left in the visible add-input before saving."""
        if not self.query_one(f"#{which}-input-row").display:
            return
        pending = self.query_one(f"#{which}-add-input", Input).value
        if pending.strip():
            self._add_task_to_list(which, pending)
