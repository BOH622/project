"""Jinja-rendered email templates."""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATE_DIR = Path(__file__).parent / "email_templates"
_env = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(["html"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def render(name: str, **ctx: object) -> tuple[str, str]:
    """Returns (html, text) for a named template. Expects {name}.html and {name}.txt."""
    html = _env.get_template(f"{name}.html").render(**ctx)
    text = _env.get_template(f"{name}.txt").render(**ctx)
    return html, text
