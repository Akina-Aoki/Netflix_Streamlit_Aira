"""Reusable author credit component for Streamlit pages."""

import streamlit as st


def render_author_credit() -> None:
    """Render a compact creator attribution card aligned under page charts."""
    # Use a narrow column so the credit reads like a small card under content.
    credit_col, _ = st.columns([1, 2])
    with credit_col:
        st.markdown(
            """
            <div style="
                margin-top: 0.75rem;
                padding: 0.9rem 1rem;
                max-width: 460px;
                border: 1px solid #5A3B18;
                border-left: 4px solid #F7B952;
                border-radius: 10px;
                background: linear-gradient(90deg, rgba(247,185,82,0.10) 0%, rgba(232,98,42,0.08) 100%);
                color: #F5F0E8;
                font-size: 0.95rem;
                line-height: 1.5;
            ">
                <div style="font-weight: 700; margin-bottom: 0.35rem;">
                    This page was created by Aira Franco
                </div>
                <div>
                    <strong>GitHub Profile:</strong>
                    <a href="https://github.com/Akina-Aoki" target="_blank" rel="noopener noreferrer" style="color:#F7B952; text-decoration:none;">
                        https://github.com/Akina-Aoki
                    </a>
                </div>
                <div>
                    <strong>LinkedIn:</strong>
                    <a href="https://www.linkedin.com/in/aira-franco0965/" target="_blank" rel="noopener noreferrer" style="color:#F7B952; text-decoration:none;">
                        https://www.linkedin.com/in/aira-franco0965/
                    </a>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )