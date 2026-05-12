"""Data preparation helpers for the Country Insights page."""

from __future__ import annotations

import calendar

import pandas as pd
import streamlit as st

from netflix.utils.helpers import get_weekly_df

MONTH_ORDER = list(calendar.month_name)[1:]
CATEGORY_MAP = {
    "Movie": "Films",
    "Movies": "Films",
    "Film": "Films",
    "Films": "Films",
    "Serie": "TV",
    "Series": "TV",
    "TV": "TV",
}


@st.cache_data
def prepare_country_insights_data() -> pd.DataFrame:
    """Load and prepare weekly country-level Top 10 data for this page."""
    df = get_weekly_df().copy()
    df["week"] = pd.to_datetime(df["week"], errors="coerce")
    df["weekly_rank"] = pd.to_numeric(df["weekly_rank"], errors="coerce")

    required_columns = ["week", "weekly_rank", "show_title", "category", "country_name"]
    df = df.dropna(subset=required_columns).copy()

    df["year"] = df["week"].dt.year
    df["month_num"] = df["week"].dt.month
    df["month_name"] = pd.Categorical(
        df["week"].dt.month_name(), categories=MONTH_ORDER, ordered=True
    )
    df["category"] = df["category"].map(CATEGORY_MAP).fillna(df["category"])
    df["score"] = 11 - df["weekly_rank"]
    return df[df["score"].notna() & (df["score"] > 0)].copy()


def available_filter_options(
    weekly_df: pd.DataFrame,
    selected_country: str | None = None,
    selected_year: int | None = None,
) -> tuple[list[str], list[int], list[str], list[str]]:
    """Return valid Country Insights filter options for Streamlit widgets."""
    countries = sorted(weekly_df["country_name"].dropna().unique().tolist())
    years = sorted(weekly_df["year"].dropna().astype(int).unique().tolist())

    if selected_country is None and countries:
        selected_country = countries[0]
    if selected_year is None and years:
        selected_year = years[-1]

    months_in_data = weekly_df.loc[
        (weekly_df["country_name"] == selected_country)
        & (weekly_df["year"] == selected_year),
        "month_name",
    ].dropna()
    months = [month for month in MONTH_ORDER if month in set(months_in_data.astype(str))]
    return countries, years, months, ["All", "Films", "TV"]


def build_country_top10_chart_df(
    df: pd.DataFrame,
    selected_country: str,
    selected_year: int,
    selected_month: str,
    selected_category: str,
) -> pd.DataFrame:
    """Return the selected country's top 10 title performance dataframe."""
    filtered = df[
        (df["country_name"] == selected_country)
        & (df["year"] == selected_year)
        & (df["month_name"].astype(str) == selected_month)
    ].copy()

    agg = (
        filtered.groupby(["show_title", "category"], as_index=False)["score"]
        .sum()
        .rename(columns={"score": "performance_score"})
    )
    if selected_category != "All":
        agg = agg[agg["category"] == selected_category].copy()

    return (
        agg.sort_values("performance_score", ascending=False)
        .head(10)
        .sort_values("performance_score", ascending=True)
    )


def build_films_tv_counts(chart_df: pd.DataFrame) -> pd.DataFrame:
    """Count Films and TV titles from the top 10 dataframe for the donut chart."""
    return pd.DataFrame(
        {
            "category": ["Films", "TV"],
            "title_count": [
                int((chart_df["category"] == "Films").sum()),
                int((chart_df["category"] == "TV").sum()),
            ],
        }
    )


def build_period_df(
    df: pd.DataFrame,
    selected_year: int,
    selected_month: str,
    selected_category: str,
) -> pd.DataFrame:
    """Filter by time and category, intentionally leaving all countries present."""
    period_df = df[
        (df["year"] == selected_year) & (df["month_name"].astype(str) == selected_month)
    ].copy()
    if selected_category != "All":
        period_df = period_df[period_df["category"] == selected_category].copy()
    return period_df


def build_heatmap_df(
    period_df: pd.DataFrame,
    selected_country: str,
    top_n_titles: int = 10,
    max_countries: int = 20,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build a Country × Title pivot using the selected country's top titles."""
    selected_country_titles = period_df[period_df["country_name"] == selected_country].copy()
    title_df = (
        selected_country_titles.groupby(["show_title", "category"], as_index=False)["score"]
        .sum()
        .rename(columns={"score": "performance_score"})
        .sort_values("performance_score", ascending=False)
        .head(top_n_titles)
    )

    top_titles = title_df["show_title"].tolist()
    if not top_titles:
        return pd.DataFrame(), title_df

    title_scores_by_country = (
        period_df[period_df["show_title"].isin(top_titles)]
        .groupby(["country_name", "show_title"], as_index=False)["score"]
        .sum()
        .rename(columns={"score": "performance_score"})
    )
    pivot_df = title_scores_by_country.pivot_table(
        index="country_name",
        columns="show_title",
        values="performance_score",
        aggfunc="sum",
        fill_value=0,
    )
    pivot_df = pivot_df.reindex(columns=top_titles, fill_value=0)
    pivot_df["__total__"] = pivot_df[top_titles].sum(axis=1)

    countries_to_keep = (
        pivot_df.sort_values("__total__", ascending=False).head(max_countries).index.tolist()
    )
    if selected_country in pivot_df.index and selected_country not in countries_to_keep:
        countries_to_keep.append(selected_country)

    pivot_df = pivot_df.loc[countries_to_keep].sort_values("__total__", ascending=False)
    if selected_country in pivot_df.index:
        row_order = [selected_country] + [c for c in pivot_df.index if c != selected_country]
        pivot_df = pivot_df.loc[row_order]

    return pivot_df.drop(columns="__total__"), title_df


def build_filter_context_title(
    selected_country: str,
    selected_year: int,
    selected_month: str,
    selected_category: str,
) -> str:
    """Build the main chart title from the active filter context."""
    title_parts = [selected_country, f"{selected_month} {selected_year}"]
    if selected_category != "All":
        title_parts.append(selected_category)
    return " · ".join(str(part) for part in title_parts if part)


def normalize_title_for_match(value: object) -> str:
    """Normalize title text for case-insensitive title analytics matching."""
    if pd.isna(value):
        return ""
    return str(value).strip().casefold()


def filter_title_rows(title_name: str, country_df: pd.DataFrame | None) -> pd.DataFrame:
    """Return country-level rows for the selected title without UI dependencies."""
    if country_df is None or country_df.empty or not title_name:
        return pd.DataFrame()
    if "show_title" not in country_df.columns:
        return pd.DataFrame()

    normalized_title = normalize_title_for_match(title_name)
    return country_df[
        country_df["show_title"].apply(normalize_title_for_match) == normalized_title
    ].copy()


def prepare_title_time_df(title_name: str, country_df: pd.DataFrame | None) -> pd.DataFrame:
    """Filter title rows and add parsed week/year/month columns when possible."""
    title_df = filter_title_rows(title_name, country_df)
    if title_df.empty or "week" not in title_df.columns:
        return pd.DataFrame()

    title_df["week"] = pd.to_datetime(title_df["week"], errors="coerce")
    title_df = title_df.dropna(subset=["week"]).copy()
    if title_df.empty:
        return pd.DataFrame()

    title_df["year"] = title_df["week"].dt.year
    title_df["month_num"] = title_df["week"].dt.month
    title_df["month_name"] = title_df["week"].dt.month_name()
    return title_df


def resolve_title_metric(df: pd.DataFrame) -> tuple[pd.DataFrame, str, str]:
    """Add a numeric metric_value column using the best available real metric."""
    if df is None or df.empty:
        return pd.DataFrame(), "Performance score", "number"

    metric_candidates = [
        ("weekly_hours_viewed", "Hours viewed", "compact"),
        ("hours_viewed", "Hours viewed", "compact"),
        ("views", "Number of views", "compact"),
    ]
    metric_df = df.copy()
    for column, label, format_type in metric_candidates:
        if column in metric_df.columns:
            metric_df["metric_value"] = pd.to_numeric(metric_df[column], errors="coerce")
            metric_df = metric_df.dropna(subset=["metric_value"]).copy()
            return metric_df, label, format_type

    if "weekly_rank" not in metric_df.columns:
        return pd.DataFrame(), "Performance score", "number"

    metric_df["weekly_rank"] = pd.to_numeric(metric_df["weekly_rank"], errors="coerce")
    metric_df["metric_value"] = 11 - metric_df["weekly_rank"]
    metric_df = metric_df[
        metric_df["metric_value"].notna() & (metric_df["metric_value"] > 0)
    ].copy()
    return metric_df, "Performance score", "number"


def build_title_yearly_popularity_df(metric_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate title popularity by year and flag the highest year."""
    yearly_df = (
        metric_df.groupby("year", as_index=False)["metric_value"]
        .sum()
        .sort_values("year")
    )
    yearly_df = yearly_df[yearly_df["year"].between(2021, 2025)].copy()
    if yearly_df.empty:
        return yearly_df

    highlight_year = int(yearly_df.loc[yearly_df["metric_value"].idxmax(), "year"])
    yearly_df["bar_color"] = yearly_df["year"].apply(
        lambda year: "highlight" if int(year) == highlight_year else "standard"
    )
    return yearly_df


def build_title_monthly_popularity_df(
    metric_df: pd.DataFrame, selected_year: int
) -> pd.DataFrame:
    """Aggregate title popularity by month for a selected year."""
    month_lookup = pd.DataFrame(
        {"month_num": list(range(1, 13)), "month_name": MONTH_ORDER}
    )
    monthly_df = (
        metric_df[metric_df["year"] == selected_year]
        .groupby("month_num", as_index=False)["metric_value"]
        .sum()
    )
    monthly_df = month_lookup.merge(monthly_df, on="month_num", how="left")
    monthly_df["metric_value"] = monthly_df["metric_value"].fillna(0)
    return monthly_df


def build_title_weekly_popularity_df(metric_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate title popularity by week."""
    return (
        metric_df.groupby("week", as_index=False)["metric_value"]
        .sum()
        .sort_values("week")
    )