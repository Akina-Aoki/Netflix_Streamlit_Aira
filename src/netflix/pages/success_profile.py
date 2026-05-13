"""Success Profile Streamlit page.

This page orchestrates Success Profile by delegating data preparation, charts,
and UI sections to reusable utilities and components.
"""

import streamlit as st

from netflix.components.author_credit import render_author_credit
from netflix.components.branding import render_page_header, render_streamly_banner
from netflix.components.footer import render_disclaimer_footer
from netflix.components.success_sections import (render_success_explanation_section, render_success_filters, render_success_kpi_cards, render_success_market_reach_section, render_success_scatter_section, render_success_story_cards,)
from netflix.utils.constants import STYLES_PATH
from netflix.utils.helpers import read_css
from netflix.utils.success_profile import (build_success_profile_data, prepare_success_profile_data,)


def _load_dashboard_css() -> None:
    """Load the shared dashboard stylesheet when it is available."""
    css_path = STYLES_PATH / "dashboard.css"
    if css_path.exists():
        read_css(css_path)


def _render_success_header() -> None:
    """Render the Success Profile banner and page header."""
    render_streamly_banner(width=220)
    render_page_header(
        title="What does a successful show look like?",
        subtitle="Compare top shows by longevity and popularity.",
    )

def _render_missing_data_error(weekly_df) -> bool:
    """Render blocking data errors and return True when the page should stop."""
    if "_missing_columns" in weekly_df.columns:
        st.error(
            "Success Profile cannot render because these required columns are missing: "
            f"{weekly_df['_missing_columns'].iloc[0]}"
        )
        render_disclaimer_footer()
        return True


    if weekly_df.empty:
        st.warning("No weekly data available.")
        render_disclaimer_footer()
        return True
    return False

def success_profile() -> None:
    """Render the Success Profile page."""
    _load_dashboard_css()
    _render_success_header()
    render_success_story_cards()

    weekly_df = prepare_success_profile_data()
    if _render_missing_data_error(weekly_df):
        return

    country, year, month, category = render_success_filters(weekly_df)
    profile_df, mode = build_success_profile_data(
        weekly_df,
        country,
        year,
        month,
        category,
    )

    if profile_df.empty:
        st.warning("No data available for the selected filters.")
        render_disclaimer_footer()
        return

    if mode == "relaxed":
        st.info(
            f"No rows for {month} in {country} ({year}, {category}). "
            "Showing broader yearly data instead."
        )

    render_success_explanation_section()
    render_success_kpi_cards(profile_df)
    render_success_scatter_section(profile_df)
    render_success_market_reach_section(profile_df)
    render_author_credit()
    render_disclaimer_footer()


if __name__ == "__main__":
    success_profile()