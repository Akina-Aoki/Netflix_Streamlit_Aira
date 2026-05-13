"""Reusable visualization helpers for Streamly pages."""
import calendar
import html
import importlib.util
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import streamlit as st
from netflix.components.country_charts import (build_popularity_month_figure, build_popularity_week_figure, build_popularity_year_figure,)
from netflix.components.html_templates import load_html_template, render_html_template
from netflix.components.theme import NORDIC_COUNTRIES, NORDIC_FLAGS, STREAMLY_COLORS
from netflix.utils.country_insights import (build_title_monthly_popularity_df, build_title_weekly_popularity_df, build_title_yearly_popularity_df, prepare_title_time_df, resolve_title_metric,)
from netflix.utils.helpers import get_country_df, prepare_country_reach_data


def _iso2_to_iso3(iso2_code: str) -> str | None:
    """Convert a two-letter country code to ISO-3 for Plotly maps."""
    if importlib.util.find_spec("pycountry") is None:
        return None
    
    import pycountry

    country = pycountry.countries.get(alpha_2=str(iso2_code).upper())
    return country.alpha_3 if country else None


def make_country_choropleth(df: pd.DataFrame, selected_country: str):
    """Create a world map that highlights the selected country."""
    columns = ["country_name"]

    if "country_iso2" in df.columns:
        columns.append("country_iso2")

    countries = (
        df[columns]
        .dropna(subset=["country_name"])
        .drop_duplicates()
        .copy()
    )

    if countries.empty:
        return None

    location_column = "country_name"
    location_mode = "country names"
    custom_data = ["country_name"]

    if "country_iso2" in countries.columns:
        countries["iso3"] = countries["country_iso2"].apply(_iso2_to_iso3)

        if countries["iso3"].notna().any():
            countries = countries.dropna(subset=["iso3"]).copy()
            location_column = "iso3"
            location_mode = "ISO-3"
            custom_data = ["country_name", "country_iso2"]
    # Use a simple 0/1 value so the selected country receives the bright color.
    countries["is_selected"] = (
        countries["country_name"] == selected_country
    ).astype(int)

    fig = px.choropleth(
        countries,
        locations=location_column,
        locationmode=location_mode,
        hover_name="country_name",
        custom_data=custom_data,
        color="is_selected",
        color_continuous_scale=[
            STREAMLY_COLORS["muted"],
            STREAMLY_COLORS["yellow"],
        ],
        range_color=(0, 1),
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=STREAMLY_COLORS["card"],
        plot_bgcolor=STREAMLY_COLORS["card"],
        font=dict(
            color=STREAMLY_COLORS["text"],
            family="Segoe UI, sans-serif",
        ),
        coloraxis_showscale=False,
        geo=dict(
            showframe=False,
            showcoastlines=False,
            bgcolor=STREAMLY_COLORS["card"],
            projection_type="natural earth",
        ),
        height=360,
    )

    return fig


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
        hovertemplate="<br>".join(hover_parts) + "<extra></extra>",)

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

def _title_metric_empty_message(metric_label: str) -> None:
    """Render a consistent message when no chart data is available."""
    st.info(f"No {metric_label.lower()} data is available for this title.")


def render_nordic_ranking_for_title(
    title_name: str,
    country_df: pd.DataFrame | None,
    selected_year: int | None = None,
) -> None:
    """Show the selected title's best weekly rank across Nordic countries."""
    no_data_message = "No Nordic ranking data is available for this title and year."
    with st.container(border=True):
        st.markdown("#### Ranking across the Nordic countries")
        st.caption("Best weekly Top 10 rank in selected/latest year")

        source_columns = {"show_title", "country_name", "weekly_rank"}
        if (
            country_df is None
            or country_df.empty
            or not source_columns.issubset(country_df.columns)
        ):
            st.info(no_data_message)
            return

        required_columns = {"country_name", "weekly_rank", "year"}
        title_df = prepare_title_time_df(title_name, country_df)
        if title_df.empty or not required_columns.issubset(title_df.columns):
            st.info(no_data_message)
            return
        
        title_df["weekly_rank"] = pd.to_numeric(title_df["weekly_rank"], errors="coerce")
        title_df = title_df[title_df["country_name"].isin(NORDIC_COUNTRIES)].copy()
        title_df = title_df.dropna(subset=["weekly_rank", "year"])

        if title_df.empty:
            st.info(no_data_message)
            return

        title_df["year"] = title_df["year"].astype(int)
        available_years = set(title_df["year"].unique())
        if selected_year is None:
            selected_year = int(title_df["year"].max())
        elif selected_year not in available_years:
            st.info(no_data_message)
            return

        year_df = title_df[title_df["year"] == selected_year].copy()
        if year_df.empty:
            st.info(no_data_message)
            return

        best_rank_by_country = (
            year_df.groupby("country_name", as_index=False)["weekly_rank"]
            .min()
            .rename(columns={"weekly_rank": "best_rank"})
        )

        lookup = dict(
            zip(best_rank_by_country["country_name"], best_rank_by_country["best_rank"], strict=False)
        )

        rows = []
        row_template = load_html_template("nordic_rank_row.html")
        for country_name in NORDIC_COUNTRIES:
            flag = NORDIC_FLAGS.get(country_name, "")
            best_rank = lookup.get(country_name)
            rank_label = f"#{int(best_rank)}" if pd.notna(best_rank) else "No data"
            muted_class = " market-rank-row-muted" if pd.isna(best_rank) else ""
            rows.append(
                row_template.format(
                    muted_class=html.escape(muted_class),
                    flag=html.escape(flag),
                    country_name=html.escape(country_name),
                    rank_label=html.escape(rank_label),
                )
            )

        st.markdown("".join(rows), unsafe_allow_html=True)

def render_title_yearly_views_chart(title_name: str, country_df: pd.DataFrame) -> None:
    """Render yearly viewing/performance totals for the selected title."""
    with st.container(border=True):
        title_df = prepare_title_time_df(title_name, country_df)
        metric_df, metric_label, _format_type = resolve_title_metric(title_df)
        st.markdown("#### Popularity Per Year")

        if metric_df.empty:
            _title_metric_empty_message(metric_label)
            return

        yearly_df = build_title_yearly_popularity_df(metric_df)
        if yearly_df.empty:
            _title_metric_empty_message(metric_label)
            return

        st.plotly_chart(build_popularity_year_figure(yearly_df), width="stretch")

def _get_title_available_years(title_name: str, country_df: pd.DataFrame) -> list[int]:
    """Return sorted years with title rows that can feed time-series charts."""
    title_df = prepare_title_time_df(title_name, country_df)
    if title_df.empty or "year" not in title_df.columns:
        return []
    return sorted(title_df["year"].dropna().astype(int).unique().tolist())


def render_title_monthly_views_chart(
    title_name: str,
    country_df: pd.DataFrame,
) -> int | None:
    """Render monthly viewing/performance totals and return the selected year."""
    with st.container(border=True):
        title_df = prepare_title_time_df(title_name, country_df)
        metric_df, metric_label, _format_type = resolve_title_metric(title_df)
        st.markdown("#### Popularity By Month")

        if metric_df.empty:
            _title_metric_empty_message(metric_label)
            return None

        available_years = sorted(metric_df["year"].dropna().astype(int).unique().tolist())
        if not available_years:
            _title_metric_empty_message(metric_label)
            return None

        default_year = max(available_years)
        selected_year = st.selectbox(
            "Select year",
            available_years,
            index=available_years.index(default_year),
            key="title_profile_monthly_year_filter",
            width="stretch",
        )

        monthly_df = build_title_monthly_popularity_df(metric_df, selected_year)


        st.plotly_chart(
            build_popularity_month_figure(monthly_df, list(calendar.month_name)[1:]),
            width="stretch",
        )

        return int(selected_year)


def render_title_weekly_views_chart(
    title_name: str,
    country_df: pd.DataFrame,
    selected_year: int,
) -> None:
    """Render weekly viewing/performance totals for the selected year/month."""
    with st.container(border=True):
        title_df = prepare_title_time_df(title_name, country_df)
        metric_df, metric_label, _format_type = resolve_title_metric(title_df)
        st.markdown(f"#### Popularity By Week")

        if metric_df.empty or selected_year is None:
            _title_metric_empty_message(metric_label)
            return

        year_df = metric_df[metric_df["year"] == selected_year].copy()
        if year_df.empty:
            st.info(f"No {metric_label.lower()} data is available for {selected_year}.")
            return

        month_options = ["All months"] + list(calendar.month_name)[1:]
        selected_month = st.selectbox(
            "Select month",
            month_options,
            key="title_profile_weekly_month_filter",
            width="stretch",
        )

        if selected_month != "All months":
            year_df = year_df[year_df["month_name"] == selected_month].copy()

        if year_df.empty:
            st.info("No weekly data is available for the selected month.")
            return

        weekly_df = build_title_weekly_popularity_df(year_df)

        st.plotly_chart(
            build_popularity_week_figure(
                weekly_df, show_all_months=selected_month == "All months"
            ),
            width="stretch",
        )

def render_selected_title_market_analytics(
    title_name: str,
    country_df: pd.DataFrame | None,
) -> None:
    """Render Market Reach plus extended title analytics for Country Insights."""
    render_single_title_market_reach(title_name=title_name, country_df=country_df)

    if country_df is None or country_df.empty:
        return

    selected_year = st.session_state.get("title_profile_monthly_year_filter")
    if not isinstance(selected_year, int):
        selected_year = None

    nordic_col, yearly_col = st.columns(2, gap="large")
    with nordic_col:
        render_nordic_ranking_for_title(title_name, country_df, selected_year)
    with yearly_col:
        render_title_yearly_views_chart(title_name, country_df)

    monthly_year = render_title_monthly_views_chart(title_name, country_df)
    if monthly_year is not None:
        render_title_weekly_views_chart(title_name, country_df, monthly_year)


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
