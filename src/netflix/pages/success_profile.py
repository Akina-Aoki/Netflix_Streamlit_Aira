"""Success Profile Streamlit page.

This page explains success with simple segments based on popularity and
longevity in the Netflix country-level Top 10 data.
"""

import calendar

import pandas as pd
import plotly.express as px
import streamlit as st

from netflix.components.author_credit import render_author_credit
from netflix.components.branding import render_page_header, render_streamly_banner
from netflix.components.cards import render_story_card
from netflix.components.filters import render_labeled_selectbox
from netflix.components.footer import render_disclaimer_footer
from netflix.utils.constants import STYLES_PATH
from netflix.utils.helpers import get_weekly_df, read_css


SEGMENT_COLORS = {
    "Hype": "#E63946",
    "Balanced": "#F4A261",
    "High Retention": "#2A9D8F",
}

CHART_COLORS = {
    "background": "#F5F0E8",
    "text": "#111111",
    "muted_text": "#4A4A4A",
    "axis": "#222222",
    "vertical_guide": "#E8C87E",
}

MONTH_ORDER = list(calendar.month_name)[1:]

REQUIRED_COLUMNS = {
    "country_name",
    "week",
    "weekly_rank",
    "show_title",
    "category",
}


def get_global_weekly_df() -> pd.DataFrame:
    """Compatibility wrapper for the older Success Profile page naming."""
    return get_weekly_df()


@st.cache_data
def prepare_success_profile_data() -> pd.DataFrame:
    """Load and clean weekly data for the Success Profile page."""
    df = get_global_weekly_df().copy()

    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        return pd.DataFrame({"_missing_columns": [", ".join(sorted(missing_columns))]})

    # Convert source columns to reliable types before filtering and grouping.
    df["week"] = pd.to_datetime(df["week"], errors="coerce")
    df["weekly_rank"] = pd.to_numeric(df["weekly_rank"], errors="coerce")

    df = df.dropna(
        subset=[
            "country_name",
            "week",
            "weekly_rank",
            "show_title",
            "category",
        ]
    ).copy()

    df["year"] = df["week"].dt.year
    df["month_name"] = df["week"].dt.month_name()

    df["month_name"] = pd.Categorical(
        df["month_name"],
        categories=MONTH_ORDER,
        ordered=True,
    )

    return df


@st.cache_data
def _aggregate_success_profile(filtered_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate filtered weekly rows into robust storytelling segments.

    This version tries to pick three archetypes:
    - Hype = strongest popularity score
    - High Retention = strongest longevity
    - Balanced = strongest combined longevity + popularity
    """
    if filtered_df.empty:
        return pd.DataFrame()

    # Aggregate weekly rows so each title becomes one point on the chart.
    profile_df = (
        filtered_df.groupby(["show_title", "category"], as_index=False)
        .agg(
            longevity=("week", "count"),
            performance_score=("weekly_rank", lambda ranks: (11 - ranks).sum()),
        )
        .copy()
    )

    if profile_df.empty:
        return pd.DataFrame()

    profile_df["longevity"] = pd.to_numeric(profile_df["longevity"], errors="coerce")
    profile_df["performance_score"] = pd.to_numeric(
        profile_df["performance_score"],
        errors="coerce",
    )

    profile_df = profile_df.dropna(
        subset=[
            "show_title",
            "category",
            "longevity",
            "performance_score",
        ]
    ).copy()

    if profile_df.empty:
        return pd.DataFrame()

    selected_rows = []
    used_titles = set()

    def pick_first_available(candidate_df: pd.DataFrame, segment_name: str) -> None:
        """Pick the first candidate that has not already been used."""
        for _, row in candidate_df.iterrows():
            title = row["show_title"]
            if title not in used_titles:
                selected = row.copy()
                selected["segment"] = segment_name
                selected_rows.append(selected)
                used_titles.add(title)
                return

    # 1. Hype = strongest popularity / highest performance score
    hype_candidates = profile_df.sort_values(
        ["performance_score", "longevity"],
        ascending=[False, False],
    )
    pick_first_available(
        candidate_df=hype_candidates,
        segment_name="Hype",
    )

    # 2. High Retention = strongest longevity
    retention_candidates = profile_df.sort_values(
        ["longevity", "performance_score"],
        ascending=[False, False],
    )
    pick_first_available(
        candidate_df=retention_candidates,
        segment_name="High Retention",
    )

    # 3. Balanced = best combined normalized longevity + popularity
    longevity_max = profile_df["longevity"].max()
    performance_max = profile_df["performance_score"].max()

    profile_df["longevity_norm"] = (
        profile_df["longevity"] / longevity_max if longevity_max > 0 else 0
    )
    profile_df["performance_norm"] = (
        profile_df["performance_score"] / performance_max if performance_max > 0 else 0
    )
    profile_df["balance_score"] = (
        profile_df["longevity_norm"] + profile_df["performance_norm"]
    )

    balanced_candidates = profile_df.sort_values(
        ["balance_score", "performance_score", "longevity"],
        ascending=[False, False, False],
    )
    pick_first_available(
        candidate_df=balanced_candidates,
        segment_name="Balanced",
    )

    result_df = pd.DataFrame(selected_rows)

    if result_df.empty:
        return pd.DataFrame()

    # Build a compact label that can be shown next to each selected title.
    result_df["point_label"] = (
        result_df["show_title"].astype(str)
        + "<br>"
        + result_df["longevity"].astype(int).astype(str)
        + "w | "
        + result_df["performance_score"].astype(int).astype(str)
    )

    segment_order = ["Balanced", "High Retention", "Hype"]
    result_df["segment"] = pd.Categorical(
        result_df["segment"],
        categories=segment_order,
        ordered=True,
    )

    return result_df.sort_values("segment").reset_index(drop=True)


@st.cache_data
def build_success_profile_data(
    df: pd.DataFrame,
    country: str,
    year: int,
    month: str,
    category: str,
) -> tuple[pd.DataFrame, str]:
    """Build profile data using strict monthly filters, then yearly fallback."""
    strict_df = df[
        (df["country_name"] == country)
        & (df["year"] == year)
        & (df["month_name"].astype(str) == month)
        & (df["category"] == category)
    ].copy()

    if not strict_df.empty:
        return _aggregate_success_profile(strict_df), "strict"

    # If a month has no rows, keep the page useful by falling back to the year.
    relaxed_df = df[
        (df["country_name"] == country)
        & (df["year"] == year)
        & (df["category"] == category)
    ].copy()

    return _aggregate_success_profile(relaxed_df), "relaxed"


def build_success_profile_figure(profile_df: pd.DataFrame):
    """Create the cream storytelling-style Success Profile scatter chart with safer label spacing."""
    y_max = profile_df["performance_score"].max()
    x_max = profile_df["longevity"].max()

    # Extra space so labels do not get clipped at the top or right side.
    x_axis_max = x_max + 1.2
    y_axis_max = y_max * 1.55 if y_max > 0 else 1

    # Plotly creates the base scatter; later code adds custom labels and arrows.
    fig = px.scatter(
        profile_df,
        x="longevity",
        y="performance_score",
        color="segment",
        color_discrete_map=SEGMENT_COLORS,
        category_orders={"segment": ["Balanced", "High Retention", "Hype"]},
        hover_name="show_title",
    )

    # Markers only. Labels are added manually below as annotations.
    fig.update_traces(
        mode="markers",
        marker=dict(size=26, line=dict(width=2, color="#FFFFFF")),
        cliponaxis=False,
    )

    fig.update_layout(
        height=700,
        paper_bgcolor=CHART_COLORS["background"],
        plot_bgcolor=CHART_COLORS["background"],
        font=dict(color=CHART_COLORS["text"], size=16),
        legend=dict(
            title=dict(
                text="Segment",
                font=dict(color=CHART_COLORS["text"], size=15),
            ),
            font=dict(color=CHART_COLORS["text"], size=14),
            bgcolor="rgba(255, 253, 248, 0.92)",
            bordercolor=CHART_COLORS["axis"],
            borderwidth=1,
            orientation="h",
            x=0.98,
            xanchor="right",
            y=0.98,
            yanchor="top",
        ),
        xaxis_title="Longevity (weeks in Top 10)",
        yaxis_title="Popularity",
        margin=dict(l=80, r=110, t=60, b=80),
    )

    # Vertical grid lines ON
    fig.update_xaxes(
        showgrid=True,
        gridcolor=CHART_COLORS["vertical_guide"],
        showline=False,
        zeroline=False,
        range=[0, x_axis_max],
        title_font=dict(size=20, color=CHART_COLORS["text"]),
        tickfont=dict(size=15, color=CHART_COLORS["text"]),
        tickcolor=CHART_COLORS["axis"],
        title_standoff=22,
    )

    # Horizontal grid lines OFF
    fig.update_yaxes(
        showgrid=False,
        showline=False,
        zeroline=False,
        range=[0, y_axis_max],
        showticklabels=False,
        title_font=dict(size=20, color=CHART_COLORS["text"]),
        title_standoff=24,
    )

    arrow_style = dict(
        showarrow=True,
        arrowhead=3,
        arrowwidth=2,
        arrowcolor=CHART_COLORS["text"],
        text="",
    )

    # X-axis arrow
    fig.add_annotation(
        x=x_axis_max,
        y=0,
        ax=0,
        ay=0,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        **arrow_style,
    )

    # Y-axis arrow
    fig.add_annotation(
        x=0,
        y=y_axis_max,
        ax=0,
        ay=0,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        **arrow_style,
    )

    # Custom label offsets per segment.
    label_offsets = {
        "Balanced": {
            "ax": -26,
            "ay": -38,
            "xanchor": "right",
            "yanchor": "bottom",
            "align": "right",
        },
        "High Retention": {
            "ax": 42,
            "ay": -12,
            "xanchor": "left",
            "yanchor": "middle",
            "align": "left",
        },
        "Hype": {
            "ax": 0,
            "ay": -54,
            "xanchor": "center",
            "yanchor": "bottom",
            "align": "center",
        },
    }

    label_df = profile_df.copy()

    # Count points that share the same x value.
    label_df["same_x_count"] = label_df.groupby("longevity")["show_title"].transform(
        "count"
    )

    # Rank labels within the same x value so we can stagger them.
    label_df = label_df.sort_values(
        ["longevity", "performance_score"],
        ascending=[True, False],
    ).copy()

    label_df["same_x_rank"] = label_df.groupby("longevity").cumcount()

    for _, row in label_df.iterrows():
        segment = str(row["segment"])

        offset = label_offsets.get(
            segment,
            {
                "ax": 0,
                "ay": -38,
                "xanchor": "center",
                "yanchor": "bottom",
                "align": "center",
            },
        ).copy()

        # If labels share the same longevity position, stagger them more.
        if int(row["same_x_count"]) > 1:
            rank = int(row["same_x_rank"])

            offset["ay"] = offset["ay"] - (rank * 24)

            if rank % 2 == 0:
                offset["ax"] = offset["ax"] - 28
                offset["xanchor"] = "right"
                offset["align"] = "right"
            else:
                offset["ax"] = offset["ax"] + 28
                offset["xanchor"] = "left"
                offset["align"] = "left"

        label = (
            f"{row['show_title']}<br>"
            f"{int(row['longevity'])}w | {int(row['performance_score'])}"
        )

        fig.add_annotation(
            x=row["longevity"],
            y=row["performance_score"],
            xref="x",
            yref="y",
            text=label,
            showarrow=True,
            arrowhead=0,
            arrowsize=1,
            arrowwidth=1.1,
            arrowcolor="rgba(60, 60, 60, 0.55)",
            ax=offset["ax"],
            ay=offset["ay"],
            font=dict(
                color=CHART_COLORS["text"],
                size=13,
            ),
            align=offset["align"],
            xanchor=offset["xanchor"],
            yanchor=offset["yanchor"],
            bgcolor="rgba(245, 240, 232, 0)",
            borderpad=2,
        )

    return fig


def _render_success_story_cards() -> None:
    """Render 4 branded storytelling cards above the filters."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_story_card(
            title="How to read this chart",
            body="""
                <strong>Weeks</strong> = time in Top 10.<br>
                <strong>Score</strong> = how popular the show was.
            """,
        )

    with col2:
        render_story_card(
            title="High Retention",
            body="""
                People keep watching again and again.<br><br>
                These titles stay in the Top 10 longer and show stronger staying power.
            """,
            variant="green",
        )

    with col3:
        render_story_card(
            title="Balanced Success",
            body="""
                Strong popularity and strong retention.<br><br>
                These titles combine momentum with consistency.
            """,
            variant="amber",
        )

    with col4:
        render_story_card(
            title="Hype",
            body="""
                Strongest popularity spike.<br><br>
                These titles rise fast and stand out through high popularity score.
            """,
            variant="red",
        )
        


def _render_success_filters(df: pd.DataFrame) -> tuple[str, int, str, str]:
    """Render branded filters local to this page so shared filters stay unchanged."""
    countries = sorted(df["country_name"].dropna().unique().tolist())
    years = sorted(df["year"].dropna().unique().tolist(), reverse=True)
    months_in_data = set(df["month_name"].dropna().astype(str).unique().tolist())
    months = [month for month in MONTH_ORDER if month in months_in_data]
    categories = sorted(df["category"].dropna().unique().tolist())

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

    return country, year, month, category


def success_profile() -> None:
    """Render the Success Profile page."""
    css_path = STYLES_PATH / "dashboard.css"
    if css_path.exists():
        read_css(css_path)

    render_streamly_banner(width=220)
    render_page_header(
        title="What does a successful show look like?",
        subtitle="Compare top shows by longevity and popularity.",
    )

    # Story cards teach the viewer how to interpret the dashboard before filtering.
    _render_success_story_cards()

    weekly_df = prepare_success_profile_data()

    if "_missing_columns" in weekly_df.columns:
        st.error(
            "Success Profile cannot render because these required columns are missing: "
            f"{weekly_df['_missing_columns'].iloc[0]}"
        )
        render_disclaimer_footer()
        return

    if weekly_df.empty:
        st.warning("No weekly data available.")
        render_disclaimer_footer()
        return

    country, year, month, category = _render_success_filters(weekly_df)

    profile_df, mode = build_success_profile_data(
        weekly_df,
        country,
        year,
        month,
        category,
    )

    # Tell users when the dashboard uses the broader yearly fallback.
    if profile_df.empty:
        st.warning("No data available for the selected filters.")
        render_disclaimer_footer()
        return

    if mode == "relaxed":
        st.info(
            f"No rows for {month} in {country} ({year}, {category}). "
            "Showing broader yearly data instead."
        )

    fig = build_success_profile_figure(profile_df)
    st.plotly_chart(fig, use_container_width=True)

    render_author_credit()
    render_disclaimer_footer()


if __name__ == "__main__":
    success_profile()