"""Country Insights Streamlit page.
The page orchestrates Country Insights by loading shared assets/data and delegating
UI, chart, and data preparation work to reusable components and utilities.
"""


import streamlit as st

from netflix.components.author_credit import render_author_credit
from netflix.components.branding import render_page_header, render_streamly_banner
from netflix.components.country_sections import (render_country_filters, render_market_reach_analytics_section, render_section_divider, render_title_profile_explorer_section, render_top10_snapshot_section,)
from netflix.components.footer import render_disclaimer_footer
from netflix.components.home_summary import render_home_summary
from netflix.utils.constants import STYLES_PATH
from netflix.utils.country_insights import prepare_country_insights_data
from netflix.utils.helpers import read_css

def _load_dashboard_css() -> None:
    """Load the shared dashboard stylesheet when it is available."""
    dashboard_css = STYLES_PATH / "dashboard.css"
    if dashboard_css.exists():
        read_css(dashboard_css)


def _render_page_intro() -> None:
    """Render the Streamly banner, summary, divider, and Country Insights header."""
    render_streamly_banner(width=200)
    render_home_summary(show_banner=False)
    render_section_divider()
    render_page_header(
        title="Top 10 Films and Movies Worldwide",
        subtitle="Explore what each country prefers and compare viewing patterns across markets.",
    )

def country_insights() -> None:
    """Render the Country Insights page."""
    _load_dashboard_css()
    _render_page_intro()
    weekly_df = prepare_country_insights_data()
    if weekly_df.empty:
        st.warning("No weekly country data is available for Country Insights.")
        render_disclaimer_footer()
        return

    selected_country, selected_year, selected_month, selected_category = (
        render_country_filters(weekly_df)
    )
    if not selected_month:
        st.warning("No month is available for the selected country and year.")
        render_disclaimer_footer()
        return

    render_top10_snapshot_section(
        weekly_df=weekly_df,
        selected_country=selected_country,
        selected_year=selected_year,
        selected_month=selected_month,
        selected_category=selected_category,
    )

    render_section_divider()
    selected_profile_title = render_title_profile_explorer_section()
    render_market_reach_analytics_section(selected_profile_title)
    render_author_credit()
    render_disclaimer_footer()

if __name__ == "__main__":
    country_insights()