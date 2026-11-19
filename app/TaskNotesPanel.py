"""TaskNotesPanel — placeholder for future Obsidian note integration.

Renders two static dimmed lines. The panel exists now so that the cockpit
layout does not need to reshuffle when the Obsidian feature ships
(feature `ui-layout-redesign.md` §12–13).
"""
from __future__ import annotations

from rich.console import Group
from rich.text import Text
from textual.widgets import Static


class TaskNotesPanel(Static):
    """Static placeholder — no data source wired yet."""

    DEFAULT_CSS = """
    TaskNotesPanel {
        border: solid $accent;
        padding: 0 1;
        height: 1fr;
    }
    """

    def on_mount(self) -> None:
        self.border_title = "Task Notes"
        self.update(Group(
            Text("Notes for the active task will appear here.", style="dim"),
            Text("(Obsidian integration — not yet implemented)", style="dim"),
        ))
