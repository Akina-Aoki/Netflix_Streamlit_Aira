"""Reusable author credit component for Streamlit pages."""

import streamlit as st

from netflix.components.html_templates import render_html_template

def render_author_credit() -> None:
    """Render a compact creator attribution card aligned under page charts."""
    credit_col, _ = st.columns([1, 2])
    with credit_col:
        render_html_template("author_credit.html")