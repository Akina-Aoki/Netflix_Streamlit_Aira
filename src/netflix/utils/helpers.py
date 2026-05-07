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


@st.cache_data
def get_metadata_df():
    """Läser in metadata med posters, trailers o beskrivningar"""
    return pd.read_csv(DATA_PATH / "DimMetaData_Final.csv")



