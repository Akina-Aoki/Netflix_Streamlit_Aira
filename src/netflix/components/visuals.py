"""Reusable visualization helpers for Streamly pages."""

import importlib.util

import pandas as pd
import plotly.express as px
import streamlit as st

from netflix.components.html_templates import render_html_template
from netflix.components.theme import STREAMLY_COLORS
from netflix.utils.helpers import get_country_df, prepare_country_reach_data


def _iso2_to_iso3(iso2_code: str) -> str | None:
    """Convert a two-letter country code to ISO-3 for Plotly maps."""
    if importlib.util.find_spec("pycountry") is None:
        return None
    

    import pycountry

    country = pycountry.countries.get(alpha_2=str(iso2_code).upper())
    return country.alpha_3 if country else None


def make_country_reach_map(country_reach_df: pd.DataFrame):
    """Create a dark themed world map highlighting reached Top 10 markets."""
    if country_reach_df.empty:
        return None

    has_country_name = "country_name" in country_reach_df.columns
    has_country_iso2 = "country_iso2" in country_reach_df.columns
    if not has_country_name and not has_country_iso2:
        return None

    columns = []
    for column in [
        "country_name",
        "country_iso2",
        "show_title",
        "best_rank",
        "appearances",
        "latest_week",
    ]:
        if column in country_reach_df.columns:
            columns.append(column)

    drop_subset = ["country_iso2"] if has_country_iso2 else ["country_name"]

    countries = (
        country_reach_df[columns]
        .dropna(subset=drop_subset)
        .drop_duplicates(subset=drop_subset)
        .copy()
    )

    if countries.empty:
        return None
    
    if "country_name" not in countries.columns:
        countries["country_name"] = countries["country_iso2"].astype(str)
    else:
        missing_names = countries["country_name"].isna() | (
            countries["country_name"].astype(str).str.strip() == ""
        )
        if has_country_iso2:
            countries.loc[missing_names, "country_name"] = countries.loc[
                missing_names, "country_iso2"
            ].astype(str)

    location_column = "country_name"
    location_mode = "country names"

    if has_country_iso2:
        countries["iso3"] = countries["country_iso2"].apply(_iso2_to_iso3)

        if countries["iso3"].notna().any():
            countries = countries.dropna(subset=["iso3"]).copy()
            location_column = "iso3"
            location_mode = "ISO-3"
    if countries.empty:
        return None
    
    countries["reached"] = 1

    hover_parts = ["<b>%{customdata[0]}</b>"]
    custom_data = ["country_name"]

    if "show_title" in countries.columns:
        hover_parts.append("Title: %{customdata[1]}")
        custom_data.append("show_title")
    if "best_rank" in countries.columns:
        countries["best_rank_label"] = countries["best_rank"].apply(
            lambda value: f"#{int(value)}" if pd.notna(value) else "N/A"
        )
        hover_parts.append(f"Best rank: %{{customdata[{len(custom_data)}]}}")
        custom_data.append("best_rank_label")
    if "appearances" in countries.columns:
        hover_parts.append(f"Top 10 appearances: %{{customdata[{len(custom_data)}]}}")
        custom_data.append("appearances")
    if "latest_week" in countries.columns:
        countries["latest_week_label"] = pd.to_datetime(
            countries["latest_week"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")

        countries["latest_week_label"] = countries["latest_week_label"].fillna("N/A")
        hover_parts.append(f"Latest week: %{{customdata[{len(custom_data)}]}}")
        custom_data.append("latest_week_label")

    fig = px.choropleth(
        countries,
        locations=location_column,
        locationmode=location_mode,
        hover_name="country_name",
        custom_data=custom_data,
        color="reached",
        color_continuous_scale=[STREAMLY_COLORS["orange"], STREAMLY_COLORS["yellow"]],
        range_color=(0, 1),
    )

    fig.update_layout(
        height=430,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=STREAMLY_COLORS["card"],
        plot_bgcolor=STREAMLY_COLORS["card"],
        font=dict(
            color=STREAMLY_COLORS["text"],
            family="Segoe UI, sans-serif",
        ),
        coloraxis_showscale=False,
        geo=dict(
            bgcolor=STREAMLY_COLORS["card"],
            landcolor="#2A2118",
            lakecolor=STREAMLY_COLORS["card"],
            oceancolor=STREAMLY_COLORS["card"],
            projection_type="natural earth",
            showcoastlines=False,
            showcountries=True,
            countrycolor="rgba(245, 240, 232, 0.18)",
            showframe=False,
            showland=True,
            showlakes=False,
            showocean=True,
        ),
    )

    fig.update_traces(
        marker_line_color="rgba(15, 13, 11, 0.75)",
        marker_line_width=0.6,
        hovertemplate="<br>".join(hover_parts) + "<extra></extra>",
    )
    return fig


def render_title_selector_tiles(
    visible_titles: list[str],
    key: str = "market_reach_title",
) -> str | None:
    """Render tile-style buttons for the visible scatter plot titles."""
    titles = [str(title) for title in visible_titles if pd.notna(title) and str(title)]

    if not titles:
        return None

    if st.session_state.get(key) not in titles:
        st.session_state[key] = titles[0]

    columns = st.columns(len(titles))

    for column, title in zip(columns, titles, strict=False):
        is_selected = st.session_state[key] == title
        with column:
            selected_class = "market-reach-tile-selected" if is_selected else ""
            render_html_template(
                "market_reach_tile.html",
                selected_class=selected_class,
                title=title,
            )
            if st.button(
                "Selected" if is_selected else "View reach",
                key=f"{key}_{title}",
                type="primary" if is_selected else "secondary",
                width="stretch",
            ):
                st.session_state[key] = title
                st.rerun()

    return st.session_state[key]


def render_single_title_market_reach(
    title_name: str,
    country_df: pd.DataFrame | None,
    *,
    show_country_table: bool = False,
    show_header: bool = True,
) -> None:
    """Render Market Reach for one selected title across all country data."""
    if show_header:
        render_html_template(
            "market_reach_section.html",
            title="Market Reach",
            subtitle=(
                "See how widely this title reached Netflix Top 10 markets across "
                "all available country-level data."
            ),
        )

    if not title_name:
        st.info("Select a title to view market reach.")
        return
    
    if country_df is None or country_df.empty:
        st.warning("Country-level data is not available for market reach.")
        return

    if "show_title" not in country_df.columns:
        st.warning("Country-level data is not available for market reach.")
        return

    if (
        "country_name" not in country_df.columns
        and "country_iso2" not in country_df.columns
    ):
        st.warning(
            "Country-level data is missing country identifiers for market reach."
        )
        return

    country_reach_df, country_reach, country_names = prepare_country_reach_data(
        country_df=country_df,
        selected_title=title_name,
    )

    render_html_template(
        "kpi_card.html",
        label="Countries Reached",
        value=f"{country_reach:,}",
        note="Unique markets where this title appeared in the Netflix Top 10.",
    )

    if country_reach_df.empty:
        st.warning("No market reach data available for this title.")
        return

    render_html_template("market_map_heading.html", title="Reached markets map")
    map_fig = make_country_reach_map(country_reach_df)

    if map_fig is not None:
        st.plotly_chart(map_fig, width="stretch")
    else:
        st.info("Map data is unavailable for the selected title.")

    if show_country_table:
        render_html_template("market_map_heading.html", title="Reached countries")
        st.dataframe(
            pd.DataFrame({"Country": country_names}),
            width="stretch",
            hide_index=True,
        )


def render_country_reach_section(visible_titles: list[str]) -> None:
    """Render Market Reach for the titles visible in Success Profile."""
    render_html_template(
        "market_reach_section.html",
        title="Market Reach",
        subtitle=(
            "See how widely the selected Success Profile title reached Netflix Top 10 "
            "markets across all available country-level data."
        ),
    )
    selected_title = render_title_selector_tiles(visible_titles)

    if not selected_title:
        st.info("No Success Profile titles are available for Market Reach.")
        return

    render_single_title_market_reach(
        title_name=selected_title,
        country_df=get_country_df(),
        show_country_table=True,
        show_header=False,
    )
