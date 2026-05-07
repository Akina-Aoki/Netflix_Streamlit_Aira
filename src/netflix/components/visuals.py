"""Reusable visualization helpers for Streamly pages."""
import importlib.util
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import streamlit as st
from netflix.utils.helpers import get_country_df

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


# ---- Russia line chart ----
RED_1 = "#E50914"
GRAY_3 = "#888888"


def russia_line_chart():
    """Render the Russia data drop-off line chart in Streamlit."""
    df = get_country_df()
    df["week"] = pd.to_datetime(df["week"])

    russia_rows = (
        df[df["country_name"] == "Russia"]
        .groupby(df[df["country_name"] == "Russia"]["week"].dt.year)["country_name"]
        .count()
        .reindex([2021, 2022, 2023, 2024, 2025], fill_value=0)
    )
    russia_2022 = russia_rows[russia_rows > 0]

    world_df = df[df["country_name"] != "Russia"]
    world_yearly = (
        world_df.groupby(world_df["week"].dt.year)["country_name"].count()
        / world_df["country_name"].nunique()
    )
    world_continue = world_yearly[world_yearly.index <= 2025]
    
    # Matplotlib is used here because this is a custom annotated story chart.
    fig, ax = plt.subplots(figsize=(8, 5))

    fig.patch.set_facecolor("#1A1612")
    ax.set_facecolor("#1A1612")

    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#9E9689")
    ax.tick_params(colors="#9E9689")
    ax.yaxis.label.set_color("#9E9689")
    ax.xaxis.label.set_color("#9E9689")  


    ax.set_xlabel("YEAR")
    ax.set_ylabel("# of rows")

    ax.plot(range(len(russia_2022)), russia_2022.values, linewidth=2, linestyle="--", zorder=2)
    ax.plot(range(len(world_continue)), world_continue.values, linewidth=2, linestyle="--", zorder=2, color=GRAY_3)

    ax.scatter(range(len(russia_2022)), russia_2022.values, s=80, zorder=3)
    ax.scatter([1], [russia_2022.iloc[1]], s=120, zorder=4, color=RED_1)

    ax.set_xticks(range(len(russia_rows)))
    ax.set_xticklabels(russia_rows.index, rotation=0)

    ax.set_title(
        "Netflix data for Russia ends abruptly in March 2022"
        "\nfollowing the invasion of Ukraine",
        pad=22, loc="left",
        fontfamily="Segoe UI",
        fontweight="normal",
        color="#F5F0E8",
    )

    ax.annotate(
        "Start of Russian aggression\nin Ukraine",
        xy=(1, russia_2022.iloc[1]),
        xytext=(1.8, russia_2022.iloc[1] * 2.5),
        arrowprops=dict(arrowstyle="->", color=RED_1, shrinkB=8),
        fontsize=10, ha="center", color=RED_1
    )

    ax.text(4.1, world_continue.iloc[-1], "Rest of world (avg)", fontsize=9, va="center", color="#F5F0E8")
    ax.text(1.1, russia_2022.iloc[-1], "Russia", fontsize=9, va="center", color="#F5F0E8")

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
