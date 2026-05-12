import streamlit as st
from netflix.utils.helpers import get_global_df, get_metadata_df
from netflix.utils.helpers import read_css
from netflix.utils.constants import STYLES_PATH, IMAGE_PATH
from netflix.components.footer import render_disclaimer_footer
from netflix.components.title_profile import (calculate_title_kpis, get_title_profile_data, render_title_hero, render_title_kpi_cards,)
import plotly.graph_objects as go

import pandas as pd

st.image(str(IMAGE_PATH / "Logga_Streamly.png"), width=200)
st.caption("Global Netflix viewing statistics")
st.divider()

read_css(STYLES_PATH / "dashboard.css")
read_css(STYLES_PATH / "insights.css")


df_global = get_global_df()
df_metadata = get_metadata_df()

st.title("Compare titles")
st.caption("Select two titles to compare side by side")
st.divider()

# Dropdowns
all_titles = sorted(df_global["show_title"].unique())
col_left, col_right = st.columns(2, gap="large", vertical_alignment="top")

with col_left:
    title_left = st.selectbox(
        label="Select first title",
        options=all_titles,
        index=None,
        placeholder="Choose a title",
        key="left",
    )

with col_right:
    title_right = st.selectbox(
        label="Select second title",
        options=all_titles,
        index=None,
        placeholder="Choose a title",
        key="right",
    )


def get_stats(title):
    """Fetch reusable statistics and chart data for a comparison title."""
    data = df_global[df_global["show_title"] == title].copy()
    if data.empty:
        return None
    
    kpis = calculate_title_kpis(df_global, title)
    chart_columns = ["week", "weekly_views", "weekly_rank"]
    available_chart_columns = [col for col in chart_columns if col in data.columns]
    chart_data = data[available_chart_columns].sort_values("week")
    return {
        **kpis,
        "chart_data": chart_data,
    }

def show_title_card(col, title, stats):
    """Render one selected title using the shared profile components."""
    with col:
        profile = get_title_profile_data(title, df_metadata, records_df=df_global)
        render_title_hero(profile)
        if stats is not None:
            render_title_kpi_cards(stats)
        else:
            st.warning("Data is missing")

def show_views_chart(stats_left, stats_right, title_left, title_right):
    """Visar line chart med weekly views över tid för båda titlarna"""
    stats_left["chart_data"]["week"] = pd.to_datetime(stats_left["chart_data"]["week"])
    stats_right["chart_data"]["week"] = pd.to_datetime(
        stats_right["chart_data"]["week"]
    )

    x_min = max(
        stats_left["chart_data"]["week"].min(), stats_right["chart_data"]["week"].min()
    )
    x_max = max(
        stats_left["chart_data"]["week"].max(), stats_right["chart_data"]["week"].max()
    )

    fig_views = go.Figure()

    if stats_left is not None:
        fig_views.add_trace(
            go.Scatter(
                x=stats_left["chart_data"]["week"],
                y=stats_left["chart_data"]["weekly_views"],
                name=title_left.title(),
                line=dict(color="#F7B952", width=2),
            )
        )

    if stats_right is not None:
        fig_views.add_trace(
            go.Scatter(
                x=stats_right["chart_data"]["week"],
                y=stats_right["chart_data"]["weekly_views"],
                name=title_right.title(),
                line=dict(color="#E8622A", width=2),
            )
        )

    fig_views.update_layout(
        title="Views over time",
        paper_bgcolor="#0F0D08",
        plot_bgcolor="#1A1612",
        font=dict(color="#F5F0E8"),
        xaxis=dict(
            title="", range=[x_min.strftime("%Y-%m-%d"), x_max.strftime("%Y-%m-%d")]
        ),
        yaxis=dict(title=""),
        legend=dict(bgcolor="#2A2118"),
    )
    st.plotly_chart(fig_views, width="stretch")


if title_left:
    stats_left = get_stats(title_left)
    show_title_card(col_left, title_left, stats_left)

if title_right:
    stats_right = get_stats(title_right)
    show_title_card(col_right, title_right, stats_right)


if title_left and title_right and stats_left is not None and stats_right is not None:
    show_views_chart(stats_left, stats_right, title_left, title_right)


render_disclaimer_footer()
