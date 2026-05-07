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
            note="Unique film titles across Netflix viewing datasets.",
        )

    with col2:
        render_kpi_card(
            label="Total Series",
            value=total_series,
            note="Unique TV titles tracked across weekly and country data.",
        )

    with col3:
        render_kpi_card(
            label="Countries",
            value=total_countries,
            note="Markets represented in the country-level Top 10 data.",
        )

    with col4:
        render_kpi_card(
            label="Weeks Tracked",
            value=weeks_tracked,
            note="Weekly snapshots available for trend exploration.",
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
            Streamly visualizes Netflix global viewing data across weekly and all-time datasets.
            Use the dashboard to explore what audiences watch, compare films and TV series,
            and understand how popularity shifts across countries and time.
            <br><br>
            The dataset is sourced from Netflix Tudum Top 10 data:
            <a href="{TUDUM_SOURCE_URL}" target="_blank">Netflix Tudum — Most Popular</a>.
        """,
        variant="orange",
    )