"""Shared Streamly branding components."""

import streamlit as st

from netflix.utils.constants import IMAGE_PATH


STREAMLY_LOGO_FILENAME = "Logga_Streamly.png"


def render_streamly_banner(width: int = 200) -> None:
    """Render the Streamly logo, caption, and divider used across pages."""
    logo_path = IMAGE_PATH / STREAMLY_LOGO_FILENAME

    # Fall back to text branding if the image file is not available.
    st.markdown('<div class="streamly-banner">', unsafe_allow_html=True)
    if logo_path.exists():
        st.image(str(logo_path), width=width)
    else:
        st.markdown(
            '<div class="streamly-logo-fallback">Streamly</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="streamly-brand-caption">Global Netflix viewing statistics</div>
        <div class="streamly-divider"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str | None = None) -> None:
    """Render a branded Streamly page title and optional subtitle."""
    subtitle_html = (
        f'<div class="streamly-page-subtitle">{subtitle}</div>' if subtitle else ""
    )
    st.markdown(
        f"""
        <div class="streamly-page-header">
            <div class="streamly-page-title">{title}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )