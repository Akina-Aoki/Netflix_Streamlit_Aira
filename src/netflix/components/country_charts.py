"""Plotly chart builders for Country Insights."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from netflix.components.theme import CATEGORY_COLORS, CHART_FONT, STREAMLY_COLORS


def apply_streamly_chart_theme(fig: go.Figure, *, height: int | None = None) -> go.Figure:
    """Apply shared Streamly colors, fonts, and margins to a Plotly figure."""
    layout = {
        "paper_bgcolor": STREAMLY_COLORS["card"],
        "plot_bgcolor": STREAMLY_COLORS["card"],
        "font": CHART_FONT,
        "margin": dict(l=10, r=20, t=20, b=35),
    }
    if height is not None:
        layout["height"] = height
    fig.update_layout(**layout)
    return fig


def apply_clean_axis_style(fig: go.Figure) -> go.Figure:
    """Remove noisy gridlines and axis titles while keeping useful tick labels."""
    fig.update_xaxes(title_text=None, showgrid=False)
    fig.update_yaxes(title_text=None, showgrid=False, zeroline=False)
    return fig


def apply_hidden_y_axis_style(fig: go.Figure) -> go.Figure:
    """Hide y-axis labels for compact popularity charts."""
    fig.update_yaxes(title_text=None, showticklabels=False, showgrid=False, zeroline=False)
    return fig


def build_top10_bar_figure(chart_df: pd.DataFrame) -> go.Figure:
    """Build the selected country's Top 10 horizontal bar chart."""
    fig = px.bar(
        chart_df,
        x="performance_score",
        y="show_title",
        color="category",
        orientation="h",
        color_discrete_map=CATEGORY_COLORS,
        hover_data={"show_title": True, "category": True, "performance_score": True},
    )
    fig.update_traces(textposition="none", cliponaxis=False)
    apply_streamly_chart_theme(fig, height=430)
    fig.update_layout(
        margin=dict(l=10, r=30, t=20, b=35),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(title_text=None, gridcolor="rgba(158, 150, 137, 0.18)")
    fig.update_yaxes(title_text=None, tickfont=dict(size=12))
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
    fig.update_traces(textinfo="percent+label", textfont_color=STREAMLY_COLORS["text"])
    apply_streamly_chart_theme(fig, height=360)
    fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=5, b=5))
    return fig


def build_heatmap_figure(heatmap_df: pd.DataFrame, selected_country: str) -> go.Figure:
    """Build a dark Streamly-styled Country × Title heatmap figure."""
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
                [0.45, STREAMLY_COLORS["amber"]],
                [1.0, STREAMLY_COLORS["orange"]],
            ],
            colorbar=dict(title="Score", tickfont=dict(color=STREAMLY_COLORS["text"])),
            hovertemplate=(
                "Country: %{y}<br>Title: %{x}<br>Performance Score: %{z}<extra></extra>"
            ),
        )
    )
    apply_streamly_chart_theme(fig, height=max(520, 30 * len(heatmap_df.index) + 180))
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=130), xaxis_title="Titles", yaxis_title="Countries")
    fig.update_xaxes(tickangle=-35, tickfont=dict(size=11), side="bottom")
    fig.update_yaxes(tickfont=dict(size=12), autorange="reversed")
    return fig


def build_popularity_year_figure(yearly_df: pd.DataFrame) -> go.Figure:
    """Build the Title Profile yearly popularity bar chart."""
    fig = px.bar(
        yearly_df,
        x="year",
        y="metric_value",
        color="bar_color",
        color_discrete_map={
            "standard": STREAMLY_COLORS["yellow"],
            "highlight": STREAMLY_COLORS["orange"],
        },
        hover_data={"year": True, "metric_value": ":,.0f", "bar_color": False},
    )
    fig.update_traces(text=None, texttemplate=None, cliponaxis=False)
    fig.update_layout(height=360, showlegend=False)
    fig.update_xaxes(type="category")
    return apply_hidden_y_axis_style(apply_clean_axis_style(apply_streamly_chart_theme(fig)))


def build_popularity_month_figure(monthly_df: pd.DataFrame, month_order: list[str]) -> go.Figure:
    """Build the Title Profile monthly popularity bar chart."""
    fig = px.bar(
        monthly_df,
        x="month_name",
        y="metric_value",
        color_discrete_sequence=[STREAMLY_COLORS["yellow"]],
        hover_data={"month_name": True, "metric_value": ":,.0f", "month_num": False},
    )
    fig.update_traces(text=None, texttemplate=None, cliponaxis=False)
    fig.update_layout(height=390, showlegend=False)
    fig.update_xaxes(categoryorder="array", categoryarray=month_order)
    return apply_hidden_y_axis_style(apply_clean_axis_style(apply_streamly_chart_theme(fig)))


def build_popularity_week_figure(weekly_df: pd.DataFrame, *, show_all_months: bool) -> go.Figure:
    """Build the Title Profile weekly popularity line chart."""
    fig = px.line(
        weekly_df,
        x="week",
        y="metric_value",
        markers=True,
        color_discrete_sequence=[STREAMLY_COLORS["orange"]],
        hover_data={"week": "|%Y-%m-%d", "metric_value": ":,.0f"},
    )
    fig.update_traces(
        line=dict(width=3), marker=dict(size=7), text=None, texttemplate=None
    )
    fig.update_layout(height=390, showlegend=False)
    if show_all_months:
        fig.update_xaxes(dtick="M1", tickformat="%b")
    else:
        fig.update_xaxes(nticks=6, tickformat="%b %-d")
    return apply_hidden_y_axis_style(apply_clean_axis_style(apply_streamly_chart_theme(fig)))