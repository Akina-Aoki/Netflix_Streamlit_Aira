# ---------------------------------------------------------
# helpers.py
# Syfte: Hjälpfunktioner för fil-läsning och datainsamling
# ---------------------------------------------------------

from netflix.utils.constants import DATA_PATH  # sökvägen till data-mappen
import pandas as pd
import streamlit as st


def read_textfile(path):
    """Funktion för att läsa in vilken fil som helst"""
    with open(path) as file:

        return file.read()


def read_css(path):
    """Funktionen läser in CSS och injicerar i streamlit"""
    css = read_textfile(path)

    st.write(
        f"<style>{css}</style>",  # slår in CSS i HTML style-tagg
        unsafe_allow_html=True,  # Krävs - Streamlit blockerar annars HTML
    )


@st.cache_data
def get_weekly_df():
    """Läser in global_weekly Excel-data"""
    return pd.read_excel(DATA_PATH / "global_weekly.xlsx")


@st.cache_data
def get_alltime_df():
    """Läser in global_alltime Excel-data"""
    return pd.read_excel(DATA_PATH / "global_alltime.xlsx")


@st.cache_data
def get_global_df():
    """Läser in normaliserad global data"""
    return pd.read_csv(DATA_PATH / "FactGlobal_Final.csv")


@st.cache_data
def get_country_df():
    """Läser in normaliserad country-data"""
    return pd.read_csv(DATA_PATH / "FactCountry_Final.csv")


def _normalize_title(value: object) -> str:
    """Normalize title text so country reach matching is case-insensitive."""
    if pd.isna(value):
        return ""

    return str(value).strip().casefold()


def prepare_country_reach_data(
    country_df: pd.DataFrame,
    selected_title: str,
) -> tuple[pd.DataFrame, int, list[str]]:
    """Prepare total country-level reach data for a selected title.

    Market Reach uses the selected Success Profile title only. It does not reuse
    the page-level country, year, month, or category filters because the goal is
    to measure total reach across all available country-level Top 10 data.
    """
    required_columns = {"country_name", "show_title"}

    if (
        country_df.empty
        or not selected_title
        or not required_columns.issubset(country_df.columns)
    ):
        return pd.DataFrame(), 0, []

    normalized_selected_title = _normalize_title(selected_title)
    filtered_df = country_df[
        country_df["show_title"].apply(_normalize_title) == normalized_selected_title
    ].copy()

    if "weekly_rank" in filtered_df.columns:
        weekly_rank = pd.to_numeric(filtered_df["weekly_rank"], errors="coerce")
        filtered_df = filtered_df[weekly_rank.between(1, 10)].copy()

    filtered_df = filtered_df.dropna(subset=["country_name"]).copy()

    country_names = sorted(filtered_df["country_name"].astype(str).unique().tolist())

    return filtered_df, len(country_names), country_names


@st.cache_data
def get_metadata_df():
    """Läser in metadata med posters, trailers o beskrivningar"""
    return pd.read_csv(DATA_PATH / "DimMetaData_Final.csv")


def _clean_title_option(value: object) -> str:
    """Return a display-ready title option or an empty string for null values."""
    if pd.isna(value):
        return ""

    return str(value).strip()


def get_independent_title_profile_options(
    global_df: pd.DataFrame | None = None,
    metadata_df: pd.DataFrame | None = None,
) -> list[str]:
    """Build the full title list for the independent profile explorer.

    The Country Insights title profile must not depend on the page-level
    country/year/month/category filters, so this helper only reads full global
    title data and optional metadata title data.
    """
    title_lookup: dict[str, str] = {}

    for source_df in (global_df, metadata_df):
        if source_df is None or source_df.empty or "show_title" not in source_df.columns:
            continue

        for raw_title in source_df["show_title"].dropna().tolist():
            title = _clean_title_option(raw_title)
            if not title:
                continue
            title_lookup.setdefault(title.casefold(), title)

    return sorted(title_lookup.values(), key=lambda title: title.casefold())


