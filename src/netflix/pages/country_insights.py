"""Country Insights Streamlit page.

This page highlights a selected market's Top 10 snapshot and lets users
inspect weekly title performance trends within that country.
"""

import calendar

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from netflix.components.author_credit import render_author_credit
from netflix.components.branding import render_page_header, render_streamly_banner
from netflix.components.home_summary import render_home_summary
from netflix.components.filters import render_labeled_selectbox
from netflix.components.footer import render_disclaimer_footer
from netflix.components.title_profile import (get_all_title_profile_options, render_title_profile_section,)
from netflix.components.visuals import render_single_title_market_reach
from netflix.utils.constants import STYLES_PATH
from netflix.utils.helpers import (get_country_df, get_global_df, get_metadata_df, get_weekly_df, read_css,)

PAGE_COLORS = {
    "bg": "#0F0D0B",
    "card": "#1A1612",
    "border": "#2A2118",
    "yellow": "#F7B952",
    "orange": "#E8622A",
    "amber": "#FFB84D",
    "text": "#F5F0E8",
    "muted": "#9E9689",
}

CATEGORY_COLORS = {
    "Films": PAGE_COLORS["yellow"],
    "TV": PAGE_COLORS["orange"],
}

MONTH_ORDER = list(calendar.month_name)[1:]


@st.cache_data
def prepare_country_insights_data() -> pd.DataFrame:
    """Load and prepare weekly country-level Top 10 data for this page."""
    df = get_weekly_df().copy()
    
    # Convert dates and ranks first so later filtering and scoring are reliable.
    df["week"] = pd.to_datetime(df["week"], errors="coerce")
    df["weekly_rank"] = pd.to_numeric(df["weekly_rank"], errors="coerce")

    required_columns = [
        "week",
        "weekly_rank",
        "show_title",
        "category",
        "country_name",
    ]
    df = df.dropna(subset=required_columns).copy()

    df["year"] = df["week"].dt.year
    df["month_num"] = df["week"].dt.month
    df["month_name"] = pd.Categorical(
        df["week"].dt.month_name(),
        categories=MONTH_ORDER,
        ordered=True,
    )

    category_map = {
        "Movie": "Films",
        "Movies": "Films",
        "Film": "Films",
        "Films": "Films",
        "Serie": "TV",
        "Series": "TV",
        "TV": "TV",
    }
    # Standardize category names so charts can consistently compare Films and TV.
    df["category"] = df["category"].map(category_map).fillna(df["category"])

    # A rank of 1 earns 10 points, rank 10 earns 1 point.
    df["score"] = 11 - df["weekly_rank"]
    df = df[df["score"].notna() & (df["score"] > 0)].copy()

    return df


def build_country_top10_chart_df(
    df: pd.DataFrame,
    selected_country: str,
    selected_year: int,
    selected_month: str,
    selected_category: str,
) -> pd.DataFrame:
    """Return the selected country's top 10 title performance dataframe."""
    # Apply the snapshot filters before aggregating title scores.
    filtered = df[
        (df["country_name"] == selected_country)
        & (df["year"] == selected_year)
        & (df["month_name"].astype(str) == selected_month)
    ].copy()

    # Sum weekly scores because a title can appear multiple times in one month.
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
    """Build a Country × Title pivot using the selected country's top titles.

    The selected country is only used to choose the title columns. The pivot
    values are then calculated from all countries in the same period/category.
    """
    selected_country_titles = period_df[
        period_df["country_name"] == selected_country
    ].copy()

    title_df = (
        selected_country_titles.groupby(["show_title", "category"], as_index=False)[
            "score"
        ]
        .sum()
        .rename(columns={"score": "performance_score"})
        .sort_values("performance_score", ascending=False)
        .head(top_n_titles)
    )

    top_titles = title_df["show_title"].tolist()
    if not top_titles:
        return pd.DataFrame(), title_df

    # Recalculate those selected titles across every country for comparison.
    title_scores_by_country = (
        period_df[period_df["show_title"].isin(top_titles)]
        .groupby(["country_name", "show_title"], as_index=False)["score"]
        .sum()
        .rename(columns={"score": "performance_score"})
    )

    # Pivot creates the Country × Title matrix used by the heatmap visualization.
    pivot_df = title_scores_by_country.pivot_table(
        index="country_name",
        columns="show_title",
        values="performance_score",
        aggfunc="sum",
        fill_value=0,
    )

    pivot_df = pivot_df.reindex(columns=top_titles, fill_value=0)
    pivot_df["__total__"] = pivot_df[top_titles].sum(axis=1)

    # Limit rows for readability, but always include the selected country.
    countries_to_keep = (
        pivot_df.sort_values("__total__", ascending=False)
        .head(max_countries)
        .index.tolist()
    )
    if selected_country in pivot_df.index and selected_country not in countries_to_keep:
        countries_to_keep.append(selected_country)

    pivot_df = pivot_df.loc[countries_to_keep].copy()
    pivot_df = pivot_df.sort_values("__total__", ascending=False)

    if selected_country in pivot_df.index:
        row_order = [selected_country] + [
            country for country in pivot_df.index if country != selected_country
        ]
        pivot_df = pivot_df.loc[row_order]

    pivot_df = pivot_df.drop(columns="__total__")
    return pivot_df, title_df


def build_top10_bar_figure(chart_df: pd.DataFrame) -> go.Figure:
    """Build the selected country's Top 10 horizontal bar chart."""
    fig = px.bar(
        chart_df,
        x="performance_score",
        y="show_title",
        color="category",
        orientation="h",
        color_discrete_map=CATEGORY_COLORS,
        hover_data={
            "show_title": True,
            "category": True,
            "performance_score": True,
        },
    )
    fig.update_traces(textposition="none", cliponaxis=False)
    fig.update_layout(
        height=430,
        paper_bgcolor=PAGE_COLORS["card"],
        plot_bgcolor=PAGE_COLORS["card"],
        font=dict(color=PAGE_COLORS["text"], family="Segoe UI, sans-serif"),
        xaxis_title="None",
        yaxis_title="",
        margin=dict(l=10, r=30, t=20, b=35),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(title_text=None, gridcolor="rgba(158, 150, 137, 0.18)")
    fig.update_yaxes(tickfont=dict(size=12))
    return fig


def build_donut_figure(counts_df: pd.DataFrame) -> go.Figure:
    """Build a Films vs TV donut chart for the titles in the Top 10 chart."""
    fig = px.pie(
        counts_df,
        names="category",
        values="title_count",
        hole=0.62,
        color="category",
        color_discrete_map=CATEGORY_COLORS,
    )
    fig.update_traces(textinfo="percent+label", textfont_color=PAGE_COLORS["text"])
    fig.update_layout(
        showlegend=False,
        height=360,
        paper_bgcolor=PAGE_COLORS["card"],
        plot_bgcolor=PAGE_COLORS["card"],
        font=dict(color=PAGE_COLORS["text"], family="Segoe UI, sans-serif"),
        margin=dict(l=10, r=10, t=5, b=5),
    )
    return fig


def build_heatmap_figure(heatmap_df: pd.DataFrame, selected_country: str) -> go.Figure:
    """Render a dark Streamly-styled heatmap figure."""
    y_labels = [
        f"★ {country}" if country == selected_country else country
        for country in heatmap_df.index.tolist()
    ]

    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_df.values,
            x=heatmap_df.columns.tolist(),
            y=y_labels,
            colorscale=[
                [0.0, "#17120E"],
                [0.45, PAGE_COLORS["amber"]],
                [1.0, PAGE_COLORS["orange"]],
            ],
            colorbar=dict(title="Score", tickfont=dict(color=PAGE_COLORS["text"])),
            hovertemplate=(
                "Country: %{y}<br>Title: %{x}<br>Performance Score: %{z}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        height=max(520, 30 * len(heatmap_df.index) + 180),
        paper_bgcolor=PAGE_COLORS["card"],
        plot_bgcolor=PAGE_COLORS["card"],
        font=dict(color=PAGE_COLORS["text"], family="Segoe UI, sans-serif"),
        margin=dict(l=20, r=20, t=20, b=130),
        xaxis_title="Titles",
        yaxis_title="Countries",
    )
    fig.update_xaxes(tickangle=-35, tickfont=dict(size=11), side="bottom")
    fig.update_yaxes(tickfont=dict(size=12), autorange="reversed")
    return fig


def render_card_header(title: str, subtitle: str | None = None) -> None:
    """Render a reusable card title block above Streamlit chart containers."""
    subtitle_html = (
        f'<div class="country-card-subtitle">{subtitle}</div>' if subtitle else ""
    )
    st.markdown(
        f"""
        <div class="country-card-heading">
            <div class="country-card-title">{title}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_title_selectbox(
    label: str,
    options: list[str],
    key: str,
    index: int = 0,
) -> str:
    """Render a searchable title selector with Country Insights card-title styling."""
    st.markdown(
        f'<div class="country-card-title country-selector-title">{label}</div>',
        unsafe_allow_html=True,
    )
    return st.selectbox(
        label,
        options,
        index=index,
        key=key,
        label_visibility="collapsed",
    )


def render_section_heading(title: str, subtitle: str) -> None:
    """Render a larger section title for Country Insights feature sections."""
    st.markdown(
        f"""
        <div class="country-section-heading">
            <div class="country-section-title">{title}</div>
            <div class="country-section-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_divider() -> None:
    """Render a visual separator before the Country Insights chart section."""
    st.markdown(
        '<div class="country-home-section-divider" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )


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


def render_filters(weekly_df: pd.DataFrame) -> tuple[str, int, str, str]:
    """Render the Country Insights filter row."""
    st.markdown('<div class="streamly-filter-section">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)

    countries = sorted(weekly_df["country_name"].dropna().unique().tolist())
    years = sorted(weekly_df["year"].dropna().unique().tolist())
    latest_year_idx = len(years) - 1 if years else 0

    with c1:
        selected_country = render_labeled_selectbox(
            "Country", countries, key="country_insights_country"
        )

    with c2:
        selected_year = render_labeled_selectbox(
            "Year", years, index=latest_year_idx, key="country_insights_year"
        )

    months_in_data = weekly_df.loc[
        (weekly_df["country_name"] == selected_country)
        & (weekly_df["year"] == selected_year),
        "month_name",
    ].dropna()
    # Month choices depend on the selected country and year to avoid empty views.
    available_months = [m for m in MONTH_ORDER if m in set(months_in_data.astype(str))]

    with c3:
        selected_month = render_labeled_selectbox(
            "Month", available_months, key="country_insights_month"
        )

    with c4:
        selected_category = render_labeled_selectbox(
            "Category", ["All", "Films", "TV"], key="country_insights_category"
        )

    st.markdown("</div>", unsafe_allow_html=True)
    return selected_country, selected_year, selected_month, selected_category


def country_insights() -> None:
    """Render the Country Insights page."""
    if (STYLES_PATH / "dashboard.css").exists():
        read_css(STYLES_PATH / "dashboard.css")

    render_streamly_banner(width=200)
    render_home_summary(show_banner=False)
    render_section_divider()
    render_page_header(
        title="Top 10 Films and Movies Worldwide",
        subtitle="Explore what each country prefers and compare viewing patterns across markets.",
    )
    
    # Load cached, cleaned data before building filters and charts.
    weekly_df = prepare_country_insights_data()
    if weekly_df.empty:
        st.warning("No weekly country data is available for Country Insights.")
        render_disclaimer_footer()
        return

    selected_country, selected_year, selected_month, selected_category = render_filters(
        weekly_df
    )

    if not selected_month:
        st.warning("No month is available for the selected country and year.")
        render_disclaimer_footer()
        return

    top10_df = build_country_top10_chart_df(
        weekly_df,
        selected_country,
        selected_year,
        selected_month,
        selected_category,
    )

    if top10_df.empty:
        st.warning("No titles found for the selected filters.")
        
    else:
        title_context = build_filter_context_title(
            selected_country,
            selected_year,
            selected_month,
            selected_category,
        )
        bar_col, donut_col = st.columns([1.25, 1], gap="large")


        with bar_col:
            with st.container(border=True):
                render_card_header(title_context)
                st.plotly_chart(
                    build_top10_bar_figure(top10_df), use_container_width=True
                )

        with donut_col:
            with st.container(border=True):
                render_card_header("Films vs TV", "Share of titles in the Top 10 chart")
                counts_df = build_films_tv_counts(top10_df)
                chart_col, stat_col = st.columns([1.2, 1])
                with chart_col:
                    st.plotly_chart(
                        build_donut_figure(counts_df), use_container_width=True
                    )
                with stat_col:
                    films_count = int(
                        counts_df.loc[
                            counts_df["category"] == "Films", "title_count"
                        ].iloc[0]
                    )
                    tv_count = int(
                        counts_df.loc[
                            counts_df["category"] == "TV", "title_count"
                        ].iloc[0]
                    )
                    st.markdown(
                        f"""
                        <div class="country-donut-stat">
                            <span>Films</span><strong>{films_count}</strong>
                        </div>
                        <div class="country-donut-stat">
                            <span>TV</span><strong>{tv_count}</strong>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    render_section_divider()

    render_section_heading(
        "Title Profile Explorer",
        "Search for any Netflix title in the dataset and view its metadata and global Top 10 performance. This section is independent from the country, year, month, and category filters above."
    )

    profile_source_df = get_metadata_df()
    profile_global_history_df = get_global_df()
    all_profile_titles = get_all_title_profile_options(
        profile_source_df,
        global_df=profile_global_history_df,
    )

    if not all_profile_titles:
        st.warning("No titles available for profiling.")
    else:
        default_profile_index = next(
            (
                index
                for index, title in enumerate(all_profile_titles)
                if title.casefold() == "stranger things"
            ),
            0,
        )
        with st.container(border=True):
            selected_profile_title = render_title_selectbox(
                "CHOOSE ONE TITLE TO PROFILE",
                all_profile_titles,
                key="independent_title_profile_selector",
                index=default_profile_index,
            )
            render_title_profile_section(
                selected_profile_title,
                metadata_df=profile_source_df,
                kpi_records_df=profile_global_history_df,
                genre_records_df=profile_global_history_df,
            )

            render_single_title_market_reach(
                title_name=selected_profile_title,
                country_df=get_country_df(),
            )
            
    render_author_credit()
    render_disclaimer_footer()

if __name__ == "__main__":
    country_insights()