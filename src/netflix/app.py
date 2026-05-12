# ---------------------------
# app.py
# Syfte: Appens startpunkt
# ---------------------------

import streamlit as st
from netflix.utils.constants import STYLES_PATH, IMAGE_PATH
from netflix.utils.helpers import read_css

st.set_page_config(
    page_title="Streamly Film Statistics",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

read_css(STYLES_PATH / "main.css")

# Detta är om man vill ha en sidebar
# with st.sidebar:
# st.image(str(IMAGE_PATH / "Logga_Streamly.png"), width = "stretch")

pages = [
    st.Page("pages/country_insights.py", title="🏠Home"),
    st.Page("pages/success_profile.py", title="⭐ Success Profile"),
    st.Page("pages/insights.py", title="⭐Movies and Series Comparison"),
]

pg = st.navigation(pages)
pg.run()