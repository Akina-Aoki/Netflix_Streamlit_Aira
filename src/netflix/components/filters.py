"""Reusable Streamly filter controls."""

from html import escape

import streamlit as st


def render_labeled_selectbox(
    label: str,
    options: list,
    index: int = 0,
    key: str | None = None,
):
    """Render a Streamly-styled label and collapsed Streamlit selectbox."""
    st.html(f'<div class="streamly-filter-label">{escape(label)}</div>')
    return st.selectbox(
        label,
        options,
        index=index,
        key=key,
        label_visibility="collapsed",
    )