"""Shared Streamly branding components."""

from html import escape
import streamlit as st

from netflix.components.html_templates import render_html_template
from netflix.utils.constants import IMAGE_PATH


STREAMLY_LOGO_FILENAME = "Logga_Streamly.png"


def render_streamly_banner(width: int = 200) -> None:
    """Render the Streamly logo, caption, and divider used across pages."""
    logo_path = IMAGE_PATH / STREAMLY_LOGO_FILENAME

    if logo_path.exists():
        st.image(str(logo_path), width=width)
    else:
        render_html_template("streamly_logo_fallback.html")
    render_html_template("streamly_banner_close.html")


def render_page_header(title: str, subtitle: str | None = None) -> None:
    """Render a branded Streamly page title and optional subtitle."""
    subtitle_html = (
        f'<div class="streamly-page-subtitle">{escape(subtitle)}</div>'
        if subtitle
        else ""
    )
    render_html_template(
        "streamly_page_header.html",
        title=title,
        subtitle_html=subtitle_html,
    )