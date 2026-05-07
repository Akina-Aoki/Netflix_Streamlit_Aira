import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from netflix.components.visuals import russia_line_chart
from netflix.utils.constants import STYLES_PATH
from netflix.utils.helpers import get_country_df, read_css
from netflix.components.branding import render_streamly_banner


# --- For Russias KPIs using unique "shows" (film and series) --
# --- Adding filters with 3 options ---
def get_russia_kpi(category="All"):

# --- Loading the data and filtering only Russia ---
    df = get_country_df()
    df["week"] = pd.to_datetime(df["week"])
    russia = df[df["country_name"] == "Russia"]

# --- Filter by category ---
    if category != "All":
        russia = russia[russia["category"] == category]

# --- Counting unique shows at beginning and ends of 2021 and 2022 (march) ---
# --- Filtering now month (July) and extracting unique value ---
    start_2021 = russia[russia["month"] == 7]["show_title"].nunique()
    end_2021   = russia[russia["month"] == 12]["show_title"].nunique()
    start_2022 = russia[(russia["year"] == 2022) & (russia["month"] == 1)]["show_title"].nunique()
    end_2022   = russia[(russia["year"] == 2022) & (russia["month"] == 2)]["show_title"].nunique()

# --- Calculating the difference | function only used here ---
    def cal_diff(start, end):
        return end - start, ((end - start) / start) * 100

    diff_2021, prct_2021 = cal_diff(start_2021, end_2021)
    diff_2022, prct_2022 = cal_diff(start_2022, end_2022)
    both_years, both_years_prct  = cal_diff(start_2021, end_2022)

# --- returning a dict ---
    return {
    "start_2021":  start_2021,
    "end_2021":    end_2021,
    "diff_2021":   diff_2021,
    "pct_2021":    prct_2021,
    "start_2022":  start_2022,
    "end_2022":    end_2022,
    "diff_2022":   diff_2022,
    "pct_2022":    prct_2022,
    "both_years":     both_years_prct,
    "both_years_pct": both_years_prct,
}


# --- separation band between sections ---
def separation_band(title):
    st.markdown(f"## {title}")


# --- Loaded css was needed here ---
read_css(STYLES_PATH / "dashboard.css")

render_streamly_banner()



st.subheader("A data anomaly that reveals a geopolitical event.")

st.markdown("""
    <p class='disclaimer'>
        This dashboard explores Netflix viewing data up to February 2022 only visible after exploratory data analysis (EDA). <br>
        The chart line and metrics below show what Netflix looked like in Russia until the events.
    </p>
""", unsafe_allow_html=True)

st.divider()


st.markdown(
    "<h1 style='text-align: center; font-family: Segoe UI, sans-serif;font-weight: bold;color= #F5F0E8'>Russia data against rest of the world's data since 2021</h1>",
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    russia_line_chart()

# --- Insights band ---
st.divider()
separation_band("Unique Shows — Russia in Numbers")


# --- Filters ---
category = st.radio(
    "Filter by category",
    ["All", "Movie", "Serie"],
    horizontal=True
)


# --- Values in the center of the cards ---
st.markdown("""
    <style>
        [data-testid="stMetric"] {
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        [data-testid="stMetricValue"] {
            justify-content: center;
            text-align: center;
        }
        [data-testid="stMetricLabel"] {
            text-align: center;
            width: 100%;
        }
        [data-testid="stMetricDelta"] {
            justify-content: center;
        }
    </style>
""", unsafe_allow_html=True)


# --- Getting all the calculated numbers ---
kpi = get_russia_kpi(category)
 
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Unique shows at the start (Jul 2021)", value=kpi["start_2021"])

with col2:
    st.metric(label="Unique shows end 2021", value=kpi["end_2021"],
        delta=f"{kpi['diff_2021']:+d} ({kpi['pct_2021']:+.1f}%)")

with col3:
    st.metric(label="Peak in Jan 2022", value=kpi["start_2022"])

with col4:
    st.metric(label="Last data from Feb 2022", value=kpi["end_2022"],
        delta=f"{kpi['both_years']:+.0f} ({kpi['both_years_pct']:+.1f}%) vs Jul 2021")


# --- Word of caution about the numbers and interpretation ---
st.markdown("""
    <p class='disclaimer'>
        Note: the low numbers (11 to 14 unique series) mean percentages should be interpreted with caution. 
        Series were the growth driver in Russia — up +27.3% from July 2021 to February 2022. Films declined with -5%.
    </p>
""", unsafe_allow_html=True)

st.divider()

# --- Top 10 series in Russia ---
separation_band("Top 10 Series in Russia")

col_left, col_mid, col_right = st.columns([1, 2, 1])
with col_mid:
    df = get_country_df()
    russia = df[df["country_name"] == "Russia"]
    series = russia[russia["category"] == "Serie"]

    top10 = (
        series.groupby("show_title")["cumulative_weeks_in_top_10"]
        .max()
        .sort_values(ascending=True)  # ascending so longest bar is on top
        .tail(10)
        .reset_index()
    )
    top10.columns = ["show_title", "weeks_in_top_10"]
    top10["show_title"] = top10["show_title"].str.title()

    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor("#1A1612")
    ax.set_facecolor("#1A1612")

    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#9E9689")
    ax.tick_params(colors="#9E9689")
    ax.xaxis.label.set_color("#9E9689")
    ax.yaxis.label.set_color("#9E9689")

    bars = ax.barh(
        top10["show_title"],
        top10["weeks_in_top_10"],
        color="#FFB84D",  
        edgecolor="none",
    )

# --- Highlight the top bar in yellow ---
    bars[-1].set_color("#F7B952")

# --- Add value labels at end of each bar ---
    for bar in bars:
        ax.text(
            bar.get_width() + 0.3,
            bar.get_y() + bar.get_height() / 2,
            f"{int(bar.get_width())} weeks",
            va="center",
            color="#9E9689",
            fontsize=9,
        )

    ax.set_xlabel("Weeks in Top 10", color="#9E9689")
    ax.set_title(
        "Top 10 Series in Russia before February 2022",
        pad=22, loc="left",
        fontfamily="Segoe UI",
        fontweight="normal",
        color="#F5F0E8",
    )

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

# --- closing comment ---
st.markdown("""
    <p class='disclaimer'>
        Money Heist dominated Russia's top 10 for 35 weeks — more than double any other series.
    </p>
""", unsafe_allow_html=True)