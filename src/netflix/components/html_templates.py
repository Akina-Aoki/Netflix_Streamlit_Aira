"""Lightweight HTML template helpers for reusable Streamlit components."""

from __future__ import annotations

from html import escape
from pathlib import Path
from string import Formatter
from typing import Any

import streamlit as st

_TEMPLATE_DIR = Path(__file__).parent / "html"


def load_html_template(template_name: str) -> str:
    """Load an HTML template from the component template directory."""
    template_path = _TEMPLATE_DIR / template_name
    return template_path.read_text(encoding="utf-8")


def _escape_context(template: str, context: dict[str, Any]) -> dict[str, str]:
    """Escape provided values while preserving explicitly marked safe fields."""
    field_names = {
        field_name
        for _, field_name, _, _ in Formatter().parse(template)
        if field_name
    }
    escaped: dict[str, str] = {}
    for field_name in field_names:
        value = context.get(field_name, "")
        if field_name.endswith("_html"):
            escaped[field_name] = str(value)
        else:
            escaped[field_name] = escape(str(value))
    return escaped


def render_html_template(template_name: str, **context: Any) -> None:
    """Render an HTML template with escaped context through Streamlit markdown."""
    template = load_html_template(template_name)
    st.markdown(
        template.format(**_escape_context(template, context)),
        unsafe_allow_html=True,
    )