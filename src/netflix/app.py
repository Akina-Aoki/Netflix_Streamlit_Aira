# ---------------------------
# Application Entry Point
# ---------------------------

import streamlit as st
from netflix.utils.constants import STYLES_PATH
from netflix.utils.helpers import read_css

st.set_page_config(
    page_title="Streamly Film Statistics",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

read_css(STYLES_PATH / "main.css")

pages = [
    st.Page("pages/country_insights.py", title="🏠Home"),
    st.Page("pages/success_profile.py", title="⭐ Success Profile"),
]

pg = st.navigation(pages)
pg.run()