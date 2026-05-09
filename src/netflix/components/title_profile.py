"""Reusable title profile components for Streamly pages."""

from __future__ import annotations

import html
import math
from typing import Any

import pandas as pd
import streamlit as st


MISSING_POSTER_URL = "https://placehold.co/500x750/1A1612/F7B952?text=No+Poster"


def _is_missing(value: Any) -> bool:
    """Return True when a value should be treated as missing display data."""
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return str(value).strip().lower() in {"", "nan", "none", "null", "n/a"}


def _clean_text(value: Any, fallback: str = "") -> str:
    """Return clean text with a fallback for null-like values."""
    if _is_missing(value):
        return fallback
    return str(value).strip()


def _normalize_title(value: Any) -> str:
    """Normalize title text for case-insensitive matching across datasets."""
    return _clean_text(value).casefold()


def format_title(value: Any) -> str:
    """Format dataset title text for display."""
    text = _clean_text(value, "Selected title")
    return text.title() if text.islower() else text


def format_genres(value: Any) -> list[str]:
    """Return safe genre/category pill labels from one or many source values."""
    if isinstance(value, (list, tuple, set)):
        raw_parts = list(value)
    elif _is_missing(value):
        raw_parts = []
    else:
        text = str(value)
        for separator in ["|", ";", "/"]:
            text = text.replace(separator, ",")
        raw_parts = text.split(",")

    genres = []
    for part in raw_parts:
        cleaned = _clean_text(part)
        if cleaned and cleaned not in genres:
            genres.append(cleaned)

    return genres


def format_rating_stars(rating: Any) -> tuple[str, str]:
    """Convert a 10-point rating to a 5-star label and numeric display."""
    if _is_missing(rating):
        return "", "Rating unavailable"

    numeric_rating = pd.to_numeric(rating, errors="coerce")
    if pd.isna(numeric_rating):
        return "", "Rating unavailable"

    numeric_rating = float(numeric_rating)
    clamped_rating = max(0.0, min(10.0, numeric_rating))
    filled_stars = max(1, math.ceil(clamped_rating / 2)) if clamped_rating > 0 else 0
    filled_stars = min(5, filled_stars)
    stars = "★" * filled_stars + "☆" * (5 - filled_stars)
    return stars, f"{numeric_rating:.1f} / 10"


def get_title_profile_data(
    title: str,
    metadata_df: pd.DataFrame | None,
    records_df: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Collect metadata and category fallback values for a selected title."""
    normalized_title = _normalize_title(title)
    profile: dict[str, Any] = {
        "title": title,
        "display_title": format_title(title),
        "image": "",
        "trailer": "",
        "description": "No description available for this title.",
        "rating": None,
        "genres": [],
        "cast_members": "",
        "metadata_found": False,
    }

    if metadata_df is not None and not metadata_df.empty and "show_title" in metadata_df.columns:
        metadata_titles = metadata_df["show_title"].apply(_normalize_title)
        match = metadata_df[metadata_titles == normalized_title]
        if not match.empty:
            meta = match.iloc[0]
            profile.update(
                {
                    "image": _clean_text(meta.get("image", "")),
                    "trailer": _clean_text(meta.get("trailer", "")),
                    "description": _clean_text(
                        meta.get("description", ""),
                        "No description available for this title.",
                    ),
                    "rating": meta.get("rating"),
                    "genres": format_genres(meta.get("genre", meta.get("genres", ""))),
                    "cast_members": _clean_text(meta.get("cast_members", "")),
                    "metadata_found": True,
                }
            )

    if not profile["genres"] and records_df is not None and not records_df.empty:
        if {"show_title", "category"}.issubset(records_df.columns):
            title_records = records_df[
                records_df["show_title"].apply(_normalize_title) == normalized_title
            ]
            if not title_records.empty:
                profile["genres"] = format_genres(
                    title_records["category"].dropna().astype(str).unique().tolist()
                )

    return profile


def calculate_title_kpis(records_df: pd.DataFrame | None, title: str) -> dict[str, str]:
    """Calculate reusable Top 10/rank KPI values for a selected title."""
    empty_kpis = {
        "weeks_in_top_10": "N/A",
        "last_global_rank": "N/A",
        "average_global_rank": "N/A",
        "best_global_rank": "N/A",
    }
    if records_df is None or records_df.empty or "show_title" not in records_df.columns:
        return empty_kpis

    normalized_title = _normalize_title(title)
    title_df = records_df[
        records_df["show_title"].apply(_normalize_title) == normalized_title
    ].copy()
    if title_df.empty:
        return empty_kpis

    if "weekly_rank" in title_df.columns:
        title_df["weekly_rank"] = pd.to_numeric(title_df["weekly_rank"], errors="coerce")

    if "week" in title_df.columns:
        title_df["week"] = pd.to_datetime(title_df["week"], errors="coerce")
        title_df = title_df.sort_values("week")

    weeks_value = "N/A"
    if "cumulative_weeks_in_top_10" in title_df.columns:
        weeks = pd.to_numeric(title_df["cumulative_weeks_in_top_10"], errors="coerce")
        if weeks.notna().any():
            weeks_value = str(int(weeks.max()))
    elif "week" in title_df.columns:
        weeks_value = str(int(title_df["week"].dropna().nunique()))
    else:
        weeks_value = str(len(title_df))

    last_rank = "N/A"
    if {"week", "weekly_rank"}.issubset(title_df.columns):
        ranked = title_df.dropna(subset=["week", "weekly_rank"]).sort_values("week")
        if not ranked.empty:
            last_rank = f"#{int(ranked.iloc[-1]['weekly_rank'])}"
    elif "weekly_rank" in title_df.columns and title_df["weekly_rank"].notna().any():
        last_rank = f"#{int(title_df['weekly_rank'].dropna().iloc[-1])}"

    avg_rank = "N/A"
    best_rank = "N/A"
    if "weekly_rank" in title_df.columns and title_df["weekly_rank"].notna().any():
        avg_rank = f"{title_df['weekly_rank'].mean():.1f}"
        best_rank = f"#{int(title_df['weekly_rank'].min())}"

    return {
        "weeks_in_top_10": weeks_value,
        "last_global_rank": last_rank,
        "average_global_rank": avg_rank,
        "best_global_rank": best_rank,
    }


def render_title_hero(profile: dict[str, Any]) -> None:
    """Render the poster/title/metadata hero block for one title."""
    display_title = html.escape(profile.get("display_title", "Selected title"))
    poster_url = html.escape(profile.get("image") or MISSING_POSTER_URL)
    description = html.escape(
        profile.get("description") or "No description available for this title."
    )
    genres = format_genres(profile.get("genres"))
    genre_html = "".join(
        f'<span class="title-profile-genre-pill">{html.escape(genre)}</span>'
        for genre in genres
    ) or '<span class="title-profile-genre-pill muted">Genre unavailable</span>'
    stars, rating_label = format_rating_stars(profile.get("rating"))
    rating_html = (
        f'<span class="title-profile-stars">{stars}</span>' if stars else ""
    )
    trailer_url = _clean_text(profile.get("trailer"))
    if trailer_url:
        trailer_html = (
            f'<a class="title-profile-trailer-button" href="{html.escape(trailer_url)}" '
            'target="_blank" rel="noopener noreferrer">▶ Play Trailer</a>'
        )
    else:
        trailer_html = '<span class="title-profile-trailer-button disabled">Trailer unavailable</span>'

    st.markdown(
        f"""
        <div class="title-profile-hero">
            <div class="title-profile-poster-card">
                <img class="title-profile-poster" src="{poster_url}" alt="Poster for {display_title}">
            </div>
            <div class="title-profile-content">
                <div class="title-profile-eyebrow">Selected Title Profile</div>
                <h2>{display_title}</h2>
                <div class="title-profile-genres">{genre_html}</div>
                <div class="title-profile-rating">
                    {rating_html}<span>{html.escape(rating_label)}</span>
                </div>
                <p class="title-profile-description">{description}</p>
                <div class="title-profile-actions">{trailer_html}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_title_kpi_cards(kpis: dict[str, str]) -> None:
    """Render equal-height KPI cards for one title."""
    cards = [
        ("Weeks in Top 10", kpis.get("weeks_in_top_10", "N/A")),
        ("Last Global Rank", kpis.get("last_global_rank", "N/A")),
        ("Average Global Rank", kpis.get("average_global_rank", "N/A")),
        ("Best Global Rank", kpis.get("best_global_rank", "N/A")),
    ]
    cards_html = "".join(
        f"""
        <div class="title-profile-kpi-card">
            <div class="title-profile-kpi-label">{html.escape(label)}</div>
            <div class="title-profile-kpi-value">{html.escape(str(value))}</div>
        </div>
        """
        for label, value in cards
    )
    st.markdown(
        f'<div class="title-profile-kpi-grid">{cards_html}</div>',
        unsafe_allow_html=True,
    )


def render_title_profile_section(
    title: str,
    metadata_df: pd.DataFrame | None,
    kpi_records_df: pd.DataFrame | None,
    genre_records_df: pd.DataFrame | None = None,
) -> None:
    """Render the complete selected-title profile section."""
    if not title:
        st.info("Choose a title to view its profile.")
        return

    profile = get_title_profile_data(
        title,
        metadata_df,
        records_df=genre_records_df if genre_records_df is not None else kpi_records_df,
    )
    kpis = calculate_title_kpis(kpi_records_df, title)
    render_title_hero(profile)
    render_title_kpi_cards(kpis)