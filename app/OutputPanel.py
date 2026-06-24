"""OutputPanel — scrollable read-only log of command feedback.

Displays info/warning/error messages produced by Commands.py via
TuiAppContext. Also accepts Rich renderables for structured output
such as the Promark table.
"""
from textual.widgets import RichLog


class OutputPanel(RichLog):
    """A scrollable log that receives command feedback from TuiAppContext."""

    DEFAULT_CSS = """
    OutputPanel {
        height: 7;
        border: solid $panel;
        padding: 0 1;
    }
    """

    def on_mount(self) -> None:
        # RichLog wraps long lines by default; enable markup so Rich tags work.
        self.markup = True
        self.auto_scroll = True

    def add_message(self, text: str, level: str = "info") -> None:
        """Write a feedback message to the log.

        Args:
            text:  The message string. May contain Rich markup tags.
            level: One of "info", "warning", or "error".  Controls the style
                   applied when the text itself carries no colour markup.
        """
        from rich.text import Text

        style_map = {
            "warning": "bold yellow",
            "error": "bold red",
            "info": "",
        }
        style = style_map.get(level, "")
        if style:
            self.write(Text(text, style=style))
        else:
            # Let Rich parse any inline markup the message already contains.
            self.write(Text.from_markup(text))
