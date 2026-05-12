# ---------------------------------------------------------
# helpers.py
# Syfte: Hjälpfunktioner för fil-läsning och datainsamling
# ---------------------------------------------------------

import warnings
import pandas as pd
import streamlit as st

from netflix.utils.constants import DATA_PATH 


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


def _read_excel_with_default_style_warning_suppressed(path):
    """Read Excel files while hiding openpyxl's harmless default-style warning."""
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Workbook contains no default style, apply openpyxl's default",
            category=UserWarning,
            module="openpyxl.styles.stylesheet",
        )
        return pd.read_excel(path)

@st.cache_data
def get_weekly_df():
    """Läser in global_weekly Excel-data"""
    return _read_excel_with_default_style_warning_suppressed(
        DATA_PATH / "global_weekly.xlsx"
    )

@st.cache_data
def get_alltime_df():
    """Läser in global_alltime Excel-data"""
    return _read_excel_with_default_style_warning_suppressed(
        DATA_PATH / "global_alltime.xlsx"
    )

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
    country_df: pd.DataFrame | None,
    selected_title: str,
) -> tuple[pd.DataFrame, int, list[str]]:
    """Prepare total country-level reach data for a selected title.

    Market Reach uses the selected Success Profile title only. It does not reuse
    the page-level country, year, month, or category filters because the goal is
    to measure total reach across all available country-level Top 10 data.
    """
    required_columns = {"country_name", "show_title"}

    if country_df is None or country_df.empty or not selected_title:
        return pd.DataFrame(), 0, []

    if "show_title" not in country_df.columns:
        return pd.DataFrame(), 0, []
    
    has_country_name = "country_name" in country_df.columns
    has_country_iso2 = "country_iso2" in country_df.columns
    if not has_country_name and not has_country_iso2:
        return pd.DataFrame(), 0, []

    normalized_selected_title = _normalize_title(selected_title)
    filtered_df = country_df[
        country_df["show_title"].apply(_normalize_title) == normalized_selected_title
    ].copy()

    if filtered_df.empty:
        return pd.DataFrame(), 0, []

    if "weekly_rank" in filtered_df.columns:
        weekly_rank = pd.to_numeric(filtered_df["weekly_rank"], errors="coerce")
        filtered_df = filtered_df[weekly_rank.between(1, 10)].copy()


    valid_country_mask = pd.Series(False, index=filtered_df.index)
    if has_country_name:
        valid_country_mask = valid_country_mask | filtered_df["country_name"].notna()
    if has_country_iso2:
        valid_country_mask = valid_country_mask | filtered_df["country_iso2"].notna()
    filtered_df = filtered_df[valid_country_mask].copy()

    if filtered_df.empty:
        return pd.DataFrame(), 0, []

    if has_country_name:
        filtered_df["country_name"] = filtered_df["country_name"].astype(str).str.strip()
    else:
        filtered_df["country_name"] = ""

    if has_country_iso2:
        filtered_df["country_iso2"] = (
            filtered_df["country_iso2"].astype(str).str.strip().str.upper()
        )


    country_key = "country_iso2" if has_country_iso2 else "country_name"
    grouped_columns = [country_key]
    if has_country_name and country_key != "country_name":
        grouped_columns.append("country_name")

    aggregations: dict[str, tuple[str, str]] = {
        "appearances": ("show_title", "count"),
    }
    if "weekly_rank" in filtered_df.columns:
        filtered_df["weekly_rank"] = pd.to_numeric(
            filtered_df["weekly_rank"], errors="coerce"
        )
        aggregations["best_rank"] = ("weekly_rank", "min")
    if "week" in filtered_df.columns:
        filtered_df["week"] = pd.to_datetime(filtered_df["week"], errors="coerce")
        aggregations["latest_week"] = ("week", "max")

    reach_df = (
        filtered_df.dropna(subset=[country_key])
        .groupby(grouped_columns, as_index=False)
        .agg(**aggregations)
    )

    if reach_df.empty:
        return pd.DataFrame(), 0, []

    if "country_name" not in reach_df.columns:
        reach_df["country_name"] = reach_df[country_key].astype(str)
    else:
        missing_names = reach_df["country_name"].isna() | (
            reach_df["country_name"].astype(str).str.strip() == ""
        )
        reach_df.loc[missing_names, "country_name"] = reach_df.loc[
            missing_names, country_key
        ].astype(str)

    reach_df["show_title"] = selected_title

    country_names = sorted(
        reach_df["country_name"].dropna().astype(str).unique().tolist()
    )

    return reach_df, int(reach_df[country_key].nunique()), country_names


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


