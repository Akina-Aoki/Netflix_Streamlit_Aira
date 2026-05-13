"""Country Insights title analytics sections."""

from __future__ import annotations

import calendar
import html

import pandas as pd
import streamlit as st

from netflix.components.country_charts import (
    build_popularity_month_figure,
    build_popularity_week_figure,
    build_popularity_year_figure,
)
from netflix.components.html_templates import load_html_template
from netflix.components.theme import NORDIC_COUNTRIES, NORDIC_FLAGS
from netflix.components.visuals import render_single_title_market_reach
from netflix.utils.country_insights import (
    build_title_monthly_popularity_df,
    build_title_weekly_popularity_df,
    build_title_yearly_popularity_df,
    prepare_title_time_df,
    resolve_title_metric,
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
            zip(
                best_rank_by_country["country_name"],
                best_rank_by_country["best_rank"],
                strict=False,
            )
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

        st.html("".join(rows))


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

        available_years = sorted(
            metric_df["year"].dropna().astype(int).unique().tolist()
        )
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
        st.markdown("#### Popularity By Week")

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