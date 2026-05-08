# Netflix Streamlit App - Charts Page

import pandas as pd
import plotly.express as px
import streamlit as st
from netflix.utils.constants import IMAGE_PATH, STYLES_PATH
from netflix.utils.helpers import get_global_df, read_css
from netflix.components.footer import render_disclaimer_footer

read_css(STYLES_PATH / "charts.css")

st.image(str(IMAGE_PATH / "Logga_Streamly.png"), width=200)
st.caption("Global Netflix viewing statistics")
st.divider()

CUSTOM_COLORS = [
    "#E50914",  
    "#E74C3C",  
    "#F39C12",  
    "#F7B952",  
    "#F9A03F",  
    "#FAB060",  
    "#FCC08D",  
    "#FDD1A8",  
    "#FEE2C4",  
    "#FFF0E0",  
]

# ========== READ DATA ==========
df_global = get_global_df()

# ========== EXTRACT YEARS ==========
df_global["year"] = df_global["year_week"].str[:4].astype(int)
available_years = sorted(df_global["year"].unique().tolist())

# ========== FILTERS ==========
st.subheader("The top global titles over time, by views")
st.markdown(
    "<span style='color: #9E9689;'>"
    "Compare how the most watched titles performed week by week. "
    "Use Line for trend comparison, Bar for exact weekly volumes.",
    unsafe_allow_html=True
)

st.write("")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        '<div class="streamly-filter-label">Filter by category</div>',
        unsafe_allow_html=True,
    )
    category = st.selectbox(
        "Filter by category",
        options=["Movie", "Serie"],
        index=0,
        label_visibility="collapsed",
    )

with col2:
    st.markdown(
        '<div class="streamly-filter-label">Number of titles</div>',
        unsafe_allow_html=True,
    )
    top_n = st.selectbox(
        "Number of titles",
        options=[5, 10],
        index=1,
        label_visibility="collapsed",
    )

with col3:
    st.markdown(
        '<div class="streamly-filter-label">Filter by year</div>',
        unsafe_allow_html=True,
    )
    selected_year = st.selectbox(
        "Filter by year",
        options=available_years,
        index=len(available_years) - 1,
        label_visibility="collapsed",
    )

with col4:
    st.markdown(
        '<div class="streamly-filter-label">Chart type</div>',
        unsafe_allow_html=True,
    )
    chart_type = st.selectbox(
        "Chart type",
        options=["Line", "Bar"],
        index=0,
        label_visibility="collapsed",
    )

st.divider()

# ========== FILTER DATA ==========
if category == "All":
    df_filtered = df_global.copy()
else:
    df_filtered = df_global[df_global["category"] == category]

df_filtered = df_filtered[df_filtered["year"] == selected_year]

# Skapa en "Week"-kolumn med enbart veckonumret
df_filtered["week_number"] = df_filtered["year_week"].str[-2:]
df_filtered["week_label"] = "W." + df_filtered["week_number"]

# ========== COMPUTE TOP N ==========
top_titles = (
    df_filtered.groupby("show_title")["weekly_hours_viewed"]
    .max()
    .nlargest(top_n)
    .index.tolist()
)

df_topn = df_filtered[df_filtered["show_title"].isin(top_titles)].sort_values("week_number")
df_topn["week_sort"] = df_topn["week_number"].astype(int)
df_topn = df_topn.sort_values("week_sort")

# ========== KPIs ==========
total_hours = df_topn["weekly_hours_viewed"].sum()

if chart_type == "Line":
    # Använd rolling average för Line
    df_topn_smooth = df_topn.copy()
    df_topn_smooth["weekly_hours_smooth"] = (
        df_topn_smooth.groupby("show_title")["weekly_hours_viewed"]
        .transform(lambda x: x.rolling(window=4, min_periods=1).mean())
    )
    df_kpi = df_topn_smooth
    value_col = "weekly_hours_smooth"
else:
    # Använd originalvärden för Bar
    df_kpi = df_topn
    value_col = "weekly_hours_viewed"

df_sorted = df_kpi.sort_values(value_col, ascending=False)
peak_row = df_sorted.iloc[0]
peak_week_label = peak_row["week_label"]
peak_hours = peak_row[value_col]
peak_title = peak_row["show_title"]

best_title = df_kpi.groupby("show_title")[value_col].sum().idxmax()
avg_weekly = df_topn["weekly_hours_viewed"].mean()

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Hours Viewed", f"{total_hours/1e9:.2f}B")
kpi2.metric("Peak", f"{peak_week_label}")
kpi3.metric("Most Watched Title", best_title)
kpi4.metric("Avg Weekly Hours", f"{avg_weekly/1e6:.1f}M")

st.write("")
st.divider()

# ========== PIVOT ==========
df_pivot = df_topn.pivot_table(
    index="week_label",
    columns="show_title",
    values="weekly_hours_viewed",
    aggfunc="sum"
)[top_titles]

df_pivot_smooth = df_pivot.rolling(window=4, min_periods=1).mean()

# Sortera veckorna numeriskt (W.01 → W.52)
sorted_weeks = sorted(df_pivot.index.tolist(), key=lambda x: int(x.replace("W.", "")))
df_pivot = df_pivot.reindex(sorted_weeks)
df_pivot_smooth = df_pivot_smooth.reindex(sorted_weeks)

# ========== BUILD CHART ==========
category_label = category 

if chart_type == "Line":
    fig = px.line(
        df_pivot_smooth,
        x=df_pivot_smooth.index,
        y=top_titles,
        title=f"Top {top_n} {category_label} titles - {selected_year}",
        labels={"value": "Hours Viewed", "week_label": "Week", "variable": "Title"},
        color_discrete_sequence=CUSTOM_COLORS[:top_n],
    )
else:
    fig = px.bar(
        df_topn,
        x="week_label",
        y="weekly_hours_viewed",
        color="show_title",
        barmode="group",
        title=f"Top {top_n} {category_label} titles - {selected_year}",
        labels={
            "weekly_hours_viewed": "Hours Viewed",
            "week_label": "Week",
            "show_title": "Title"
        },
        color_discrete_sequence=CUSTOM_COLORS[:top_n],
    )
    fig.update_xaxes(categoryorder="array", categoryarray=sorted(df_topn["week_label"].unique(), 
    key=lambda x: int(x.replace("W.", ""))))

# ========== LAYOUT ==========
fig.update_layout(
    plot_bgcolor="#1A1612",
    paper_bgcolor="#0F0D0B",
    title={
        "font": {"color": "#F5F0E8", "size": 20},
        "x": 0.01,
    },

    legend={
        "font": {"color": "#9E9689", "size": 12},
        "title": {"text": "Title", "font": {"color": "#F5F0E8"}},
        "bgcolor": "#1A1612",
        "bordercolor": "#f7b952",
        "borderwidth": 1,
        "x": 1.05,
        "yanchor": "top",
        "y": 1.02,
    },
    hovermode="x unified",
    hoverlabel={"bgcolor": "#1A1612", "font_size": 12, "font_color": "#F5F0E8"},
    xaxis={
        "tickfont": {"color": "#9E9689", "size": 10},
        "gridcolor": "rgba(158, 150, 137, 0.1)",
    },
    yaxis={
        "tickfont": {"color": "#9E9689", "size": 10},
        "gridcolor": "rgba(158, 150, 137, 0.1)",
    },
    height=580,
    margin={"l": 90, "r": 60, "t": 80, "b": 100},
)

fig.update_traces(
    hovertemplate="<b>%{fullData.name}</b><br>Hours: %{y:,.0f}<extra></extra>"
)

# ========== SUBTITLE + CHART ==========
st.caption(
    f"Peak: ≈ {peak_hours/1e6:.0f}M hours - {peak_title}"
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

render_disclaimer_footer()