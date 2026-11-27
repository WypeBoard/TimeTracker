"""Shared Jinja2Templates instance for webapp/ routers.

Centralised here (rather than created inside main.py) so route modules can
import it directly without importing from webapp/main.py, which would
otherwise risk a circular import (main.py includes the routers).
"""
import json
import os

from fastapi.templating import Jinja2Templates
from markupsafe import Markup

_TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

templates = Jinja2Templates(directory=_TEMPLATES_DIR)


def _tojson(value) -> Markup:
    """Render a Python value as JSON, safe for embedding in an HTML
    attribute (e.g. ``data-foo='{{ value | tojson }}'``).

    Starlette's Jinja2Templates does not register Flask's ``tojson`` filter,
    so it is added here. HTML-significant characters are escaped the same
    way Flask's implementation does, so the result is safe inside both
    single- and double-quoted attributes.
    """
    dumped = json.dumps(value)
    dumped = (
        dumped.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("'", "\\u0027")
    )
    return Markup(dumped)


templates.env.filters["tojson"] = _tojson
