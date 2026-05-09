"""Reusable Streamly home-summary KPI and about components."""

import pandas as pd
import streamlit as st

from netflix.components.branding import render_streamly_banner
from netflix.components.cards import render_info_card, render_kpi_card
from netflix.utils.helpers import get_country_df, get_global_df


TUDUM_SOURCE_URL = "https://www.netflix.com/tudum/top10/most-popular"


@st.cache_data
def load_home_kpis() -> dict:
    """Load and compute KPI values shown in the Streamly landing summary."""
    df_global = get_global_df().copy()
    df_country = get_country_df().copy()

    # Combine global and country datasets so unique title KPIs use both sources.
    df_combined = pd.concat(
        [
            df_global[["category", "show_title"]],
            df_country[["category", "show_title"]],
        ],
        ignore_index=True,
    )

    film_categories = {"Movie", "Movies", "Film", "Films"}
    series_categories = {"Serie", "Series", "TV"}

    # Category sets handle small naming differences in the Netflix source files.
    total_films = df_combined[df_combined["category"].isin(film_categories)][
        "show_title"
    ].nunique()
    total_series = df_combined[df_combined["category"].isin(series_categories)][
        "show_title"
    ].nunique()

    return {
        "total_films": int(total_films),
        "total_series": int(total_series),
        "total_hours": float(df_global["weekly_hours_viewed"].sum()),
        "total_countries": int(df_country["country_name"].nunique()),
        "weeks_tracked": int(df_global["week"].nunique()),
    }


def render_home_summary(show_banner: bool = True) -> None:
    """Render the Streamly KPI row and About This App card."""
    kpis = load_home_kpis()

    total_films = f"{kpis['total_films']:,}"
    total_series = f"{kpis['total_series']:,}"
    total_countries = f"{kpis['total_countries']:,}"
    weeks_tracked = f"{kpis['weeks_tracked']:,}"
    total_hours_b = f"{kpis['total_hours'] / 1_000_000_000:.1f}B"

    if show_banner:
        render_streamly_banner(width=200)

    col1, col2, col3, col4, col5 = st.columns(5, gap="small")

    with col1:
        render_kpi_card(
            label="Total Films",
            value=total_films,
            note="Number of films.",
        )

    with col2:
        render_kpi_card(
            label="Total Series",
            value=total_series,
            note="Number of Series",
        )

    with col3:
        render_kpi_card(
            label="Countries",
            value=total_countries,
            note="Number of markets represented",
        )

    with col4:
        render_kpi_card(
            label="Weeks Tracked",
            value=weeks_tracked,
            note="Netflix Tudum dataset between July 2021 and March 2026",
        )

    with col5:
        render_kpi_card(
            label="Hours Viewed",
            value=total_hours_b,
            note="Total global weekly viewing hours captured in the data.",
        )

    render_info_card(
        title="A visual pulse check on Netflix viewing behavior.",
        body=f"""
            Streamly helps users explore what people around the world watch on Netflix.
            The app shows which films and TV series appear in the Top 10, how viewing
            patterns change over time, and how audience preferences differ between
            countries. 
            <br><br>
            The dataset is sourced from Netflix Tudum Top 10 data:
            <a href="{TUDUM_SOURCE_URL}" target="_blank">Netflix Tudum — Most Popular</a>.
        """,
        variant="orange",
    )