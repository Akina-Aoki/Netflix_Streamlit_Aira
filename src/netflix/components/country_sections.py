"""Streamlit UI sections for the Country Insights page."""

from __future__ import annotations
from html import escape

import pandas as pd
import streamlit as st

from netflix.components.country_charts import build_donut_figure, build_top10_bar_figure
from netflix.components.filters import render_labeled_selectbox
from netflix.components.html_templates import render_html_template
from netflix.components.title_profile import (
    get_all_title_profile_options,
    render_title_profile_section,
)
from netflix.components.visuals import render_selected_title_market_analytics
from netflix.utils.country_insights import (
    available_filter_options,
    build_country_top10_chart_df,
    build_films_tv_counts,
    build_filter_context_title,
)
from netflix.utils.helpers import get_country_df, get_global_df, get_metadata_df


def render_card_header(title: str, subtitle: str | None = None) -> None:
    """Render a reusable card title block above Streamlit chart containers."""
    subtitle_html = (
        f'<div class="country-card-subtitle">{escape(subtitle)}</div>' if subtitle else ""      
    )
    render_html_template("card_header.html", title=title, subtitle_html=subtitle_html)


def render_section_heading(title: str, subtitle: str) -> None:
    """Render a larger section title for Country Insights feature sections."""
    render_html_template("section_heading.html", title=title, subtitle=subtitle)


def render_section_divider() -> None:
    """Render a visual separator before Country Insights sections."""
    render_html_template("section_divider.html")


def render_title_selectbox(
    label: str,
    options: list[str],
    key: str,
    index: int = 0,
) -> str:
    """Render a searchable title selector with Country Insights card-title styling."""
    render_html_template("title_selector_label.html", label=label)
    return st.selectbox(
        label,
        options,
        index=index,
        key=key,
        label_visibility="collapsed",
    )


def render_empty_state(message: str) -> None:
    """Render a consistent Streamlit-native empty state."""
    st.info(message)


def render_country_filters(weekly_df: pd.DataFrame) -> tuple[str, int, str, str]:
    """Render the Country Insights filter row."""
    st.markdown('<div class="streamly-filter-section">', unsafe_allow_html=True)
    country_col, year_col, month_col, category_col = st.columns(4)

    countries, years, _months, categories = available_filter_options(weekly_df)
    latest_year_idx = len(years) - 1 if years else 0

    with country_col:
        selected_country = render_labeled_selectbox(
            "Country", countries, key="country_insights_country"
        )
    with year_col:
        selected_year = render_labeled_selectbox(
            "Year", years, index=latest_year_idx, key="country_insights_year"
        )

    _countries, _years, available_months, _categories = available_filter_options(
        weekly_df, selected_country, selected_year
    )
    with month_col:
        selected_month = render_labeled_selectbox(
            "Month", available_months, key="country_insights_month"
        )
    with category_col:
        selected_category = render_labeled_selectbox(
            "Category", categories, key="country_insights_category"
        )

    st.markdown("</div>", unsafe_allow_html=True)
    return selected_country, int(selected_year), selected_month, selected_category


def _render_donut_stats(counts_df: pd.DataFrame) -> None:
    """Render Films and TV counts beside the donut chart."""
    counts = counts_df.set_index("category")["title_count"].to_dict()
    render_html_template(
        "donut_stats.html",
        films_count=int(counts.get("Films", 0)),
        tv_count=int(counts.get("TV", 0)),
    )


def render_top10_snapshot_section(
    weekly_df: pd.DataFrame,
    selected_country: str,
    selected_year: int,
    selected_month: str,
    selected_category: str,
) -> None:
    """Render the Top 10 bar chart and Films vs TV donut section."""
    top10_df = build_country_top10_chart_df(
        weekly_df, selected_country, selected_year, selected_month, selected_category
    )
    if top10_df.empty:
        st.warning("No titles found for the selected filters.")
        return

    title_context = build_filter_context_title(
        selected_country, selected_year, selected_month, selected_category
    )
    bar_col, donut_col = st.columns([1.25, 1], gap="large")

    with bar_col:
        with st.container(border=True):
            render_card_header(title_context)
            st.plotly_chart(build_top10_bar_figure(top10_df), width="stretch")

    with donut_col:
        with st.container(border=True):
            render_card_header("Films vs TV", "Share of titles in the Top 10 chart")
            counts_df = build_films_tv_counts(top10_df)
            chart_col, stat_col = st.columns([1.2, 1])
            with chart_col:
                st.plotly_chart(build_donut_figure(counts_df), width="stretch")
            with stat_col:
                _render_donut_stats(counts_df)


def render_title_profile_explorer_section() -> str | None:
    """Render the independent title profile selector and metadata profile."""
    render_section_heading(
        "Title Profile Explorer",
        "Search for any Netflix title in the dataset and view its metadata and global Top 10 performance. This section is independent from the country, year, month, and category filters above.",
    )

    metadata_df = get_metadata_df()
    global_history_df = get_global_df()
    all_titles = get_all_title_profile_options(metadata_df, global_df=global_history_df)
    if not all_titles:
        st.warning("No titles available for profiling.")
        return None

    default_index = next(
        (i for i, title in enumerate(all_titles) if title.casefold() == "stranger things"),
        0,
    )
    with st.container(border=True):
        selected_title = render_title_selectbox(
            "CHOOSE ONE TITLE TO PROFILE",
            all_titles,
            key="independent_title_profile_selector",
            index=default_index,
        )
        render_title_profile_section(
            selected_title,
            metadata_df=metadata_df,
            kpi_records_df=global_history_df,
            genre_records_df=global_history_df,
        )
    return selected_title


def render_market_reach_analytics_section(selected_title: str | None) -> None:
    """Render Market Reach and popularity analytics for the selected title."""
    if not selected_title:
        render_empty_state("Select a title to view market reach analytics.")
        return
    render_selected_title_market_analytics(
        title_name=selected_title,
        country_df=get_country_df(),
    )