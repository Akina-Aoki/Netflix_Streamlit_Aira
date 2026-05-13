"""Streamlit UI sections for the Success Profile page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from netflix.components.filters import render_labeled_selectbox
from netflix.components.html_templates import render_html_template
from netflix.components.success_charts import build_success_profile_figure
from netflix.components.visuals import render_country_reach_section
from netflix.utils.success_profile import (
    build_success_kpi_df,
    get_success_filter_options,
)

_SUCCESS_CARD_VARIANTS = {"default", "amber", "orange", "green", "red"}


def _variant_class(prefix: str, variant: str) -> str:
    """Return a safe CSS class for a supported Success Profile card variant."""
    safe_variant = variant if variant in _SUCCESS_CARD_VARIANTS else "default"
    return f"{prefix}-{safe_variant}"


def _render_success_story_card(
    title: str,
    body_html: str,
    variant: str = "default",
) -> None:
    """Render one Success Profile storytelling card from an HTML template."""
    render_html_template(
        "success_story_card.html",
        title=title,
        body_html=body_html,
        card_class=_variant_class("sp-card", variant),
        title_class=_variant_class("sp-card-title", variant),
    )


def render_success_profile_intro() -> None:
    """Render the Success Profile educational story cards."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        _render_success_story_card(
            title="How to read this chart",
            body_html=(
                "<strong>Weeks</strong> = time in Top 10.<br>"
                "<strong>Score</strong> = how popular the show was."
            ),
        )
    with col2:
        _render_success_story_card(
            title="High Retention",
            body_html=(
                "People keep watching again and again.<br><br>"
                "These titles stay in the Top 10 longer and show stronger staying power."
            ),
            variant="green",
        )
    with col3:
        _render_success_story_card(
            title="Balanced Success",
            body_html=(
                "Strong popularity and strong retention.<br><br>"
                "These titles combine momentum with consistency."
            ),
            variant="amber",
        )
    with col4:
        _render_success_story_card(
            title="Hype",
            body_html=(
                "Strongest popularity spike.<br><br>"
                "These titles rise fast and stand out through high popularity score."
            ),
            variant="red",
        )


def render_success_filters(df: pd.DataFrame) -> tuple[str, int, str, str]:
    """Render the Success Profile filter row."""
    countries, years, months, categories = get_success_filter_options(df)
    st.markdown(
        '<div class="streamly-filter-section streamly-filter-section-sp">',
        unsafe_allow_html=True,
    )
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        country = render_labeled_selectbox("Country", countries, index=0)
    with col2:
        year = render_labeled_selectbox("Year", years, index=0)
    with col3:
        month = render_labeled_selectbox("Month", months, index=0)
    with col4:
        category = render_labeled_selectbox("Category", categories, index=0)

    st.markdown("</div>", unsafe_allow_html=True)
    return country, int(year), month, category


def render_success_kpi_cards(profile_df: pd.DataFrame) -> None:
    """Render compact KPI cards for the selected Success Profile titles."""
    kpi_df = build_success_kpi_df(profile_df)
    if kpi_df.empty:
        return

    columns = st.columns(len(kpi_df))
    for column, row in zip(columns, kpi_df.to_dict("records"), strict=False):
        with column:
            render_html_template(
                "success_kpi_card.html",
                label=row["label"],
                value=row["value"],
                note=row["note"],
            )


def render_success_scatter_section(profile_df: pd.DataFrame) -> None:
    """Render the Success Profile scatter chart."""
    fig = build_success_profile_figure(profile_df)
    st.plotly_chart(fig, width="stretch")


def render_success_story_cards() -> None:
    """Render explanatory cards that define the three success archetypes."""
    render_success_profile_intro()


def render_success_explanation_section() -> None:
    """Render a short explanation of the metric formulas."""
    render_html_template(
        "success_section_heading.html",
        title="How Success Profile scores titles",
        subtitle=(
            "Popularity uses the weekly rank score 11 - weekly rank. Longevity counts "
            "weekly Top 10 appearances. Balanced combines normalized popularity and longevity."
        ),
    )


def render_success_market_reach_section(profile_df: pd.DataFrame) -> None:
    """Render Market Reach for titles visible in the Success Profile scatter chart."""
    scatter_titles = profile_df["show_title"].dropna().astype(str).tolist()
    render_country_reach_section(visible_titles=scatter_titles)