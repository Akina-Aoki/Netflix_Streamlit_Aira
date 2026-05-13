"""Plotly chart builders for the Success Profile page."""

from __future__ import annotations

import pandas as pd
import plotly.express as px

from netflix.components.theme import (
    SUCCESS_PROFILE_CHART_COLORS,
    SUCCESS_SEGMENT_COLORS,
)
from netflix.utils.success_profile import SEGMENT_ORDER, build_success_scatter_df


def _success_chart_axis_max(profile_df: pd.DataFrame) -> tuple[float, float]:
    """Return padded x/y limits so markers and labels are not clipped."""
    y_max = profile_df["performance_score"].max()
    x_max = profile_df["longevity"].max()
    return x_max + 1.2, y_max * 1.55 if y_max > 0 else 1


def _apply_success_chart_layout(fig, x_axis_max: float, y_axis_max: float):
    """Apply the Success Profile cream chart theme and axis styling."""
    chart_colors = SUCCESS_PROFILE_CHART_COLORS
    fig.update_layout(
        height=700,
        paper_bgcolor=chart_colors["background"],
        plot_bgcolor=chart_colors["background"],
        font=dict(color=chart_colors["text"], size=16),
        legend=dict(
            title=dict(text="Segment", font=dict(color=chart_colors["text"], size=15)),
            font=dict(color=chart_colors["text"], size=14),
            bgcolor="rgba(255, 253, 248, 0.92)",
            bordercolor=chart_colors["axis"],
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
    fig.update_xaxes(
        showgrid=True,
        gridcolor=chart_colors["vertical_guide"],
        showline=False,
        zeroline=False,
        range=[0, x_axis_max],
        title_font=dict(size=20, color=chart_colors["text"]),
        tickfont=dict(size=15, color=chart_colors["text"]),
        tickcolor=chart_colors["axis"],
        title_standoff=22,
    )
    fig.update_yaxes(
        showgrid=False,
        showline=False,
        zeroline=False,
        range=[0, y_axis_max],
        showticklabels=False,
        title_font=dict(size=20, color=chart_colors["text"]),
        title_standoff=24,
    )
    return fig


def _add_axis_arrows(fig, x_axis_max: float, y_axis_max: float) -> None:
    """Add arrowheads to the x and y axes."""
    arrow_style = dict(
        showarrow=True,
        arrowhead=3,
        arrowwidth=2,
        arrowcolor=SUCCESS_PROFILE_CHART_COLORS["text"],
        text="",
    )
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


def _label_offset_for_segment(segment: str) -> dict[str, object]:
    """Return the default annotation offset for a Success Profile segment."""
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
    return label_offsets.get(
        segment,
        {
            "ax": 0,
            "ay": -38,
            "xanchor": "center",
            "yanchor": "bottom",
            "align": "center",
        },
    ).copy()


def _stagger_shared_x_label(
    row: pd.Series,
    offset: dict[str, object],
) -> dict[str, object]:
    """Stagger labels when multiple points share the same longevity value."""
    if int(row["same_x_count"]) <= 1:
        return offset

    rank = int(row["same_x_rank"])
    offset["ay"] = int(offset["ay"]) - (rank * 24)

    if rank % 2 == 0:
        offset["ax"] = int(offset["ax"]) - 28
        offset["xanchor"] = "right"
        offset["align"] = "right"
    else:
        offset["ax"] = int(offset["ax"]) + 28
        offset["xanchor"] = "left"
        offset["align"] = "left"

    return offset


def _add_success_point_labels(fig, profile_df: pd.DataFrame) -> None:
    """Add custom title labels around scatter markers."""
    for _, row in build_success_scatter_df(profile_df).iterrows():
        offset = _label_offset_for_segment(str(row["segment"]))
        offset = _stagger_shared_x_label(row, offset)
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
            font=dict(color=SUCCESS_PROFILE_CHART_COLORS["text"], size=13),
            align=offset["align"],
            xanchor=offset["xanchor"],
            yanchor=offset["yanchor"],
            bgcolor="rgba(245, 240, 232, 0)",
            borderpad=2,
        )


def build_success_profile_figure(profile_df: pd.DataFrame):
    """Create the storytelling-style Success Profile scatter chart."""
    x_axis_max, y_axis_max = _success_chart_axis_max(profile_df)
    fig = px.scatter(
        profile_df,
        x="longevity",
        y="performance_score",
        color="segment",
        color_discrete_map=SUCCESS_SEGMENT_COLORS,
        category_orders={"segment": SEGMENT_ORDER},
        hover_name="show_title",
    )
    fig.update_traces(
        mode="markers",
        marker=dict(size=26, line=dict(width=2, color="#FFFFFF")),
        cliponaxis=False,
    )
    _apply_success_chart_layout(fig, x_axis_max, y_axis_max)
    _add_axis_arrows(fig, x_axis_max, y_axis_max)
    _add_success_point_labels(fig, profile_df)
    return fig