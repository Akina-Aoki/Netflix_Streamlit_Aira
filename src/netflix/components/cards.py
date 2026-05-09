"""Reusable Streamly card components."""

import streamlit as st

CARD_VARIANTS = {"default", "amber", "orange", "green", "red"}


def _variant_class(prefix: str, variant: str) -> str:
    """Return a CSS class suffix for supported card variants."""
    # Validate the variant so unexpected names do not create missing CSS classes.
    safe_variant = variant if variant in CARD_VARIANTS else "default"
    return f"{prefix}-{safe_variant}"


def render_kpi_card(label: str, value: str, note: str | None = None) -> None:
    """Render one Streamly KPI card with an optional explanatory note."""
    note_html = note or "&nbsp;"
    empty_note_class = " home-kpi-note-empty" if not note else ""

    st.markdown(
        f"""
        <div class="home-kpi-card">
            <div class="home-kpi-label">{label}</div>
            <div class="home-kpi-value">{value}</div>
            <div class="home-kpi-note{empty_note_class}">{note_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_info_card(title: str, body: str, variant: str = "default") -> None:
    """Render an informational Streamly card."""
    st.markdown(
        f"""
        <div class="home-about-card {_variant_class('home-about-card', variant)}">
            <div class="home-about-eyebrow">About this app</div>
            <div class="home-about-title">{title}</div>
            <div class="home-about-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_story_card(title: str, body: str, variant: str = "default") -> None:
    """Render one Success Profile storytelling card."""
    st.markdown(
        f"""
        <div class="sp-card {_variant_class('sp-card', variant)}">
            <div class="sp-card-title {_variant_class('sp-card-title', variant)}">{title}</div>
            <div class="sp-card-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )