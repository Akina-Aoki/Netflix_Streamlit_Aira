"""Reusable visualization helpers for Streamly pages."""
import calendar
import html
import importlib.util
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import streamlit as st
from netflix.utils.helpers import get_country_df, prepare_country_reach_data

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
            PAGE_COLORS["muted"],
            PAGE_COLORS["yellow"],
        ],
        range_color=(0, 1),
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=PAGE_COLORS["card"],
        plot_bgcolor=PAGE_COLORS["card"],
        font=dict(
            color=PAGE_COLORS["text"],
            family="Segoe UI, sans-serif",
        ),
        coloraxis_showscale=False,
        geo=dict(
            showframe=False,
            showcoastlines=False,
            bgcolor=PAGE_COLORS["card"],
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
        color_continuous_scale=[PAGE_COLORS["orange"], PAGE_COLORS["yellow"]],
        range_color=(0, 1),
    )

    fig.update_layout(
        height=430,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=PAGE_COLORS["card"],
        plot_bgcolor=PAGE_COLORS["card"],
        font=dict(
            color=PAGE_COLORS["text"],
            family="Segoe UI, sans-serif",
        ),
        coloraxis_showscale=False,
        geo=dict(
            bgcolor=PAGE_COLORS["card"],
            landcolor="#2A2118",
            lakecolor=PAGE_COLORS["card"],
            oceancolor=PAGE_COLORS["card"],
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
            safe_title = html.escape(title)
            st.markdown(
                f"""
                <div class="market-reach-tile {selected_class}">
                    <span>{safe_title}</span>
                </div>
                """,
                unsafe_allow_html=True,
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
        st.markdown(
            """
            <section class="market-reach-section">
                <div class="home-section-title">Market Reach</div>
                <div class="home-section-subtitle">
                    See how widely this title reached Netflix Top 10 markets across
                    all available country-level data.
                </div>
            </section>
            """,
            unsafe_allow_html=True,
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

    st.markdown(
        f"""
        <div class="market-reach-kpi-card">
            <div class="success-kpi-label">Countries Reached</div>
            <div class="success-kpi-value">{country_reach:,}</div>
            <div class="home-kpi-note">
                Unique markets where this title appeared in the Netflix Top 10.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if country_reach_df.empty:
        st.warning("No market reach data available for this title.")
        return

    st.markdown(
        '<div class="market-reach-map-heading">Reached markets map</div>',
        unsafe_allow_html=True,
    )
    map_fig = make_country_reach_map(country_reach_df)

    if map_fig is not None:
        st.plotly_chart(map_fig, width="stretch")
    else:
        st.info("Map data is unavailable for the selected title.")

    if show_country_table:
        st.markdown(
            '<div class="market-reach-map-heading">Reached countries</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(
            pd.DataFrame({"Country": country_names}),
            width="stretch",
            hide_index=True,
        )

def _normalize_title_for_match(value: object) -> str:
    """Normalize title text for case-insensitive title analytics matching."""
    if pd.isna(value):
        return ""

    return str(value).strip().casefold()


def _filter_title_rows(title_name: str, country_df: pd.DataFrame | None) -> pd.DataFrame:
    """Return country-level rows for the selected title without raising on bad data."""
    if country_df is None or country_df.empty or not title_name:
        return pd.DataFrame()

    if "show_title" not in country_df.columns:
        return pd.DataFrame()

    normalized_title = _normalize_title_for_match(title_name)
    return country_df[
        country_df["show_title"].apply(_normalize_title_for_match) == normalized_title
    ].copy()


def _prepare_title_time_df(title_name: str, country_df: pd.DataFrame | None) -> pd.DataFrame:
    """Filter title rows and add parsed week/year/month columns when possible."""
    title_df = _filter_title_rows(title_name, country_df)
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
    """
    Add a numeric metric_value column using the best available real metric.

    Returns the prepared dataframe, chart label, and formatting type.
    """
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
            metric_df["metric_value"] = pd.to_numeric(
                metric_df[column], errors="coerce"
            )
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


def _format_metric_value(value: float, format_type: str) -> str:
    """Format metric labels compactly for chart annotations."""
    if pd.isna(value):
        return "0"

    value = float(value)
    if format_type == "compact":
        if abs(value) >= 1_000_000_000:
            return f"{value / 1_000_000_000:.1f}B"
        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        if abs(value) >= 1_000:
            return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def _title_metric_empty_message(metric_label: str) -> None:
    """Render a consistent message when no chart data is available."""
    st.info(f"No {metric_label.lower()} data is available for this title.")


def _style_title_metric_figure(fig, yaxis_title: str | None = None):
    """Apply Streamly dark styling to title-profile metric charts."""
    fig.update_layout(
        paper_bgcolor=PAGE_COLORS["card"],
        plot_bgcolor=PAGE_COLORS["card"],
        font=dict(color=PAGE_COLORS["text"], family="Segoe UI, sans-serif"),
        margin=dict(l=10, r=20, t=20, b=35),
        showlegend=False,
    )
    fig.update_xaxes(gridcolor="rgba(158, 150, 137, 0.14)", title_text=None)
    fig.update_yaxes(
        gridcolor="rgba(158, 150, 137, 0.14)",
        title_text=yaxis_title,
    )
    return fig


def render_nordic_ranking_for_title(
    title_name: str,
    country_df: pd.DataFrame,
    selected_year: int | None = None,
) -> None:
    """Show the selected title's best weekly rank across Nordic countries."""
    with st.container(border=True):
        st.markdown("#### Ranking across the Nordic countries")

        required_columns = {"country_name", "weekly_rank"}
        title_df = _prepare_title_time_df(title_name, country_df)
        if title_df.empty or not required_columns.issubset(title_df.columns):
            st.info("No Nordic ranking data is available for this title.")
            return

        nordic_flags = {
            "Sweden": "🇸🇪",
            "Norway": "🇳🇴",
            "Denmark": "🇩🇰",
            "Finland": "🇫🇮",
            "Iceland": "🇮🇸",
        }
        title_df["weekly_rank"] = pd.to_numeric(title_df["weekly_rank"], errors="coerce")
        title_df = title_df[title_df["country_name"].isin(nordic_flags)].copy()
        title_df = title_df.dropna(subset=["weekly_rank", "year"])

        if title_df.empty:
            st.info("No Nordic ranking data is available for this title.")
            return

        if selected_year is None or selected_year not in set(title_df["year"].astype(int)):
            selected_year = int(title_df["year"].max())

        year_df = title_df[title_df["year"] == selected_year].copy()
        if year_df.empty:
            st.info(f"No Nordic ranking data is available for {selected_year}.")
            return

        best_rank_by_country = (
            year_df.groupby("country_name", as_index=False)["weekly_rank"]
            .min()
            .rename(columns={"weekly_rank": "best_rank"})
        )

        lookup = dict(
            zip(best_rank_by_country["country_name"], best_rank_by_country["best_rank"], strict=False)
        )
        st.caption(f"Best weekly Top 10 rank in {selected_year} (1 is best).")

        rows = []
        for country, flag in nordic_flags.items():
            best_rank = lookup.get(country)
            rank_label = f"#{int(best_rank)}" if pd.notna(best_rank) else "No data"
            muted_class = " market-rank-row-muted" if pd.isna(best_rank) else ""
            rows.append(
                f"""
                <div class="market-rank-row{muted_class}">
                    <div class="market-rank-country"><span>{flag}</span><strong>{country}</strong></div>
                    <div class="market-rank-value">{rank_label}</div>
                </div>
                """
            )

        st.markdown(
            f"""
            <style>
                .market-rank-row {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 0.7rem 0.85rem;
                    margin: 0.45rem 0;
                    border: 1px solid rgba(247, 185, 82, 0.18);
                    border-radius: 0.8rem;
                    background: rgba(42, 33, 24, 0.45);
                }}
                .market-rank-row-muted {{ opacity: 0.62; }}
                .market-rank-country {{
                    display: flex;
                    gap: 0.55rem;
                    align-items: center;
                    color: {PAGE_COLORS["text"]};
                }}
                .market-rank-value {{
                    color: {PAGE_COLORS["yellow"]};
                    font-weight: 800;
                }}
            </style>
            {''.join(rows)}
            """,
            unsafe_allow_html=True,
        )


def render_title_yearly_views_chart(title_name: str, country_df: pd.DataFrame) -> None:
    """Render yearly viewing/performance totals for the selected title."""
    with st.container(border=True):
        title_df = _prepare_title_time_df(title_name, country_df)
        metric_df, metric_label, format_type = resolve_title_metric(title_df)
        st.markdown(f"#### {metric_label} per year")

        if metric_df.empty:
            _title_metric_empty_message(metric_label)
            return

        yearly_df = (
            metric_df.groupby("year", as_index=False)["metric_value"]
            .sum()
            .sort_values("year")
        )
        yearly_df = yearly_df[yearly_df["year"].between(2021, 2025)].copy()
        if yearly_df.empty:
            _title_metric_empty_message(metric_label)
            return

        highlight_year = int(yearly_df.loc[yearly_df["metric_value"].idxmax(), "year"])
        yearly_df["bar_color"] = yearly_df["year"].apply(
            lambda year: "highlight" if int(year) == highlight_year else "standard"
        )
        yearly_df["label"] = yearly_df["metric_value"].apply(
            lambda value: _format_metric_value(value, format_type)
        )

        fig = px.bar(
            yearly_df,
            x="year",
            y="metric_value",
            text="label",
            color="bar_color",
            color_discrete_map={
                "standard": PAGE_COLORS["yellow"],
                "highlight": PAGE_COLORS["orange"],
            },
            hover_data={"year": True, "metric_value": ":,.0f", "bar_color": False, "label": False},
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_layout(height=360)
        fig.update_xaxes(type="category")
        st.plotly_chart(_style_title_metric_figure(fig, metric_label), width="stretch")


def _get_title_available_years(title_name: str, country_df: pd.DataFrame) -> list[int]:
    """Return sorted years with title rows that can feed time-series charts."""
    title_df = _prepare_title_time_df(title_name, country_df)
    if title_df.empty or "year" not in title_df.columns:
        return []
    return sorted(title_df["year"].dropna().astype(int).unique().tolist())


def render_title_monthly_views_chart(
    title_name: str,
    country_df: pd.DataFrame,
) -> int | None:
    """Render monthly viewing/performance totals and return the selected year."""
    with st.container(border=True):
        title_df = _prepare_title_time_df(title_name, country_df)
        metric_df, metric_label, format_type = resolve_title_metric(title_df)
        st.markdown(f"#### {metric_label} per month")

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

        month_lookup = pd.DataFrame(
            {
                "month_num": list(range(1, 13)),
                "month_name": list(calendar.month_name)[1:],
            }
        )
        monthly_df = (
            metric_df[metric_df["year"] == selected_year]
            .groupby("month_num", as_index=False)["metric_value"]
            .sum()
        )
        monthly_df = month_lookup.merge(monthly_df, on="month_num", how="left")
        monthly_df["metric_value"] = monthly_df["metric_value"].fillna(0)
        monthly_df["label"] = monthly_df["metric_value"].apply(
            lambda value: _format_metric_value(value, format_type)
        )

        fig = px.bar(
            monthly_df,
            x="month_name",
            y="metric_value",
            text="label",
            color_discrete_sequence=[PAGE_COLORS["yellow"]],
            hover_data={"month_name": True, "metric_value": ":,.0f", "month_num": False, "label": False},
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_layout(height=390)
        fig.update_xaxes(categoryorder="array", categoryarray=list(calendar.month_name)[1:])
        st.plotly_chart(_style_title_metric_figure(fig, metric_label), width="stretch")
        return int(selected_year)


def render_title_weekly_views_chart(
    title_name: str,
    country_df: pd.DataFrame,
    selected_year: int,
) -> None:
    """Render weekly viewing/performance totals for the selected year/month."""
    with st.container(border=True):
        title_df = _prepare_title_time_df(title_name, country_df)
        metric_df, metric_label, _format_type = resolve_title_metric(title_df)
        st.markdown(f"#### {metric_label} per week")

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

        weekly_df = (
            year_df.groupby("week", as_index=False)["metric_value"]
            .sum()
            .sort_values("week")
        )

        fig = px.line(
            weekly_df,
            x="week",
            y="metric_value",
            markers=True,
            color_discrete_sequence=[PAGE_COLORS["orange"]],
            hover_data={"week": "|%Y-%m-%d", "metric_value": ":,.0f"},
        )
        fig.update_traces(line=dict(width=3), marker=dict(size=7))
        fig.update_layout(height=390)
        st.plotly_chart(_style_title_metric_figure(fig, metric_label), width="stretch")


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
    st.markdown(
        """
        <section class="market-reach-section">
            <div class="home-section-title">Market Reach</div>
            <div class="home-section-subtitle">
                See how widely the selected Success Profile title reached
                Netflix Top 10 markets across all available country-level data.
            </div>
        </section>
        """,        
        unsafe_allow_html=True,
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
