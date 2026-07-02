"""EpicModal — two-state modal for linking a new task to an Epic.

Shown when a task identifier is used (via start, resume, or task) and
has no existing entry in task_catalog.

State 1 — Epic selection:
    Shows a ListView with all known Epics plus a "[ + New epic… ]" option.
    ↑/↓ navigate, Enter selects, Esc dismisses (task saved as Misc).

State 2 — Inline Epic creation:
    Shows an Input for a new Epic name.
    Enter creates the Epic and links the task, Esc goes back to State 1.
"""
from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Label, ListItem, ListView, Static


class EpicModal(ModalScreen):
    """Two-state modal for linking a task to an Epic.

    Writes to task_catalog (and optionally epics) when the user selects or
    creates an Epic. Dismisses without writing anything when the user presses
    Esc from State 1 — the task remains in sessions but is treated as (Misc)
    in epic summary.
    """

    BINDINGS = [
        Binding("escape", "handle_escape", "Cancel / Back"),
    ]

    DEFAULT_CSS = """
    EpicModal {
        align: center middle;
    }
    #modal-container {
        width: 64;
        background: $surface;
        border: double $accent;
        padding: 1 2;
    }
    #modal-title {
        text-style: bold;
        margin-bottom: 1;
    }
    #select-hint {
        color: $text-muted;
        margin-bottom: 1;
    }
    #epic-list {
        height: auto;
        max-height: 12;
        border: solid $accent-darken-2;
    }
    #select-footer {
        color: $text-muted;
        margin-top: 1;
    }
    #state-create {
        display: none;
    }
    #create-label {
        margin-bottom: 1;
    }
    #create-error {
        color: $warning;
        margin-top: 1;
    }
    #create-footer {
        color: $text-muted;
        margin-top: 1;
    }
    """

    def __init__(self, task_id: str) -> None:
        super().__init__()
        self._task_id = task_id

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Static(f"New task: {self._task_id}", id="modal-title")
            # State 1 — Epic selection list
            with Vertical(id="state-select"):
                yield Static(
                    "Select an Epic to link this task, or press Esc to skip.",
                    id="select-hint",
                )
                yield ListView(id="epic-list")
                yield Static(
                    "[↑↓] navigate   [Enter] select   [Esc] save as (Misc)",
                    id="select-footer",
                )
            # State 2 — Inline Epic creation (hidden until user picks "New epic…")
            with Vertical(id="state-create"):
                yield Static("New Epic name:", id="create-label")
                yield Input(id="epic-name-input", placeholder="Epic name…")
                yield Static("", id="create-error")
                yield Static(
                    "[Enter] create & link   [Esc] back to list",
                    id="create-footer",
                )

    def on_mount(self) -> None:
        self._populate_list()

    # ------------------------------------------------------------------ #
    # State 1 helpers
    # ------------------------------------------------------------------ #

    def _populate_list(self) -> None:
        """Fill the ListView with existing Epics plus the creation option."""
        from EpicStorage import list_epics

        list_view = self.query_one("#epic-list", ListView)
        list_view.clear()

        for epic_id, epic_name in list_epics():
            # Store epic_id as the ListItem's name so we can retrieve it on
            # selection without parsing widget content.
            list_view.append(ListItem(Label(epic_name), name=str(epic_id)))

        # Always show the creation option at the bottom.
        list_view.append(ListItem(Label("[ + New epic… ]"), name="new"))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle Epic selection or transition to State 2."""
        item_name = event.item.name

        if item_name == "new":
            self._enter_creation_state()
            return

        # An existing Epic was selected — write the task_catalog entry.
        epic_id = int(item_name)
        from EpicStorage import link_task_to_epic
        link_task_to_epic(self._task_id, epic_id)
        self.dismiss()

    def _enter_creation_state(self) -> None:
        """Switch from State 1 (list) to State 2 (creation input)."""
        self.query_one("#state-select").display = False
        self.query_one("#state-create").display = True
        self.query_one("#epic-name-input", Input).focus()

    # ------------------------------------------------------------------ #
    # State 2 helpers
    # ------------------------------------------------------------------ #

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter in the new-Epic name field."""
        name = event.value.strip()

        # Empty name is a no-op — keep the input open.
        if not name:
            return

        from EpicStorage import add_epic, link_task_to_epic

        epic_id = add_epic(name)
        if epic_id is None:
            # Duplicate name — show inline error and stay in State 2.
            self.query_one("#create-error", Static).update(
                "⚠  An Epic with that name already exists."
            )
            return

        link_task_to_epic(self._task_id, epic_id)
        self.dismiss()

    def _enter_selection_state(self) -> None:
        """Return from State 2 (creation) back to State 1 (list).

        Clears the input and the error message, then re-shows the list.
        The list is re-populated in case a new Epic was partially created
        during another interaction.
        """
        self.query_one("#state-create").display = False
        self.query_one("#create-error", Static).update("")
        name_input = self.query_one("#epic-name-input", Input)
        name_input.value = ""
        self._populate_list()
        self.query_one("#state-select").display = True
        self.query_one("#epic-list", ListView).focus()

    # ------------------------------------------------------------------ #
    # Escape handling
    # ------------------------------------------------------------------ #

    def action_handle_escape(self) -> None:
        """Esc from State 2 → back to State 1; Esc from State 1 → dismiss."""
        if self.query_one("#state-create").display:
            self._enter_selection_state()
        else:
            # No task_catalog entry is written — task will appear as (Misc).
            self.dismiss()
