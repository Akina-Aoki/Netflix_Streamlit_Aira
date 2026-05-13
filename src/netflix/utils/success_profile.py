"""Data preparation utilities for the Success Profile page."""

from __future__ import annotations

import calendar

import pandas as pd


MONTH_ORDER = list(calendar.month_name)[1:]
REQUIRED_COLUMNS = {
    "country_name",
    "week",
    "weekly_rank",
    "show_title",
    "category",
}
SEGMENT_ORDER = ["Balanced", "High Retention", "Hype"]


def get_global_weekly_df() -> pd.DataFrame:
    """Compatibility wrapper for the older Success Profile page naming."""
    from netflix.utils.helpers import get_weekly_df

    return get_weekly_df()


def prepare_success_profile_data() -> pd.DataFrame:
    """Load and clean weekly data for the Success Profile page."""
    df = get_global_weekly_df().copy()

    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        return pd.DataFrame({"_missing_columns": [", ".join(sorted(missing_columns))]})

    df["week"] = pd.to_datetime(df["week"], errors="coerce")
    df["weekly_rank"] = pd.to_numeric(df["weekly_rank"], errors="coerce")

    df = df.dropna(
        subset=["country_name", "week", "weekly_rank", "show_title", "category"]
    ).copy()

    df["year"] = df["week"].dt.year
    df["month_name"] = pd.Categorical(
        df["week"].dt.month_name(),
        categories=MONTH_ORDER,
        ordered=True,
    )

    return df


def add_performance_score(df: pd.DataFrame) -> pd.DataFrame:
    """Add the rank-based popularity score used by Success Profile."""
    scored_df = df.copy()
    scored_df["performance_score"] = 11 - scored_df["weekly_rank"]
    return scored_df


def calculate_title_longevity(filtered_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate weekly rows so each title has longevity and popularity metrics."""
    if filtered_df.empty:
        return pd.DataFrame()

    scored_df = add_performance_score(filtered_df)
    profile_df = (
        scored_df.groupby(["show_title", "category"], as_index=False)
        .agg(
            longevity=("week", "count"),
            performance_score=("performance_score", "sum"),
        )
        .copy()
    )

    if profile_df.empty:
        return pd.DataFrame()

    profile_df["longevity"] = pd.to_numeric(profile_df["longevity"], errors="coerce")
    profile_df["performance_score"] = pd.to_numeric(
        profile_df["performance_score"],
        errors="coerce",
    )

    return profile_df.dropna(
        subset=["show_title", "category", "longevity", "performance_score"]
    ).copy()


def _pick_first_available(
    candidate_df: pd.DataFrame,
    segment_name: str,
    selected_rows: list[pd.Series],
    used_titles: set[str],
) -> None:
    """Pick the first candidate that has not already been assigned a segment."""
    for _, row in candidate_df.iterrows():
        title = row["show_title"]
        if title not in used_titles:
            selected = row.copy()
            selected["segment"] = segment_name
            selected_rows.append(selected)
            used_titles.add(title)
            return


def build_success_profile_segments(profile_df: pd.DataFrame) -> pd.DataFrame:
    """Select Hype, High Retention, and Balanced titles from aggregated metrics."""
    if profile_df.empty:
        return pd.DataFrame()

    selected_rows: list[pd.Series] = []
    used_titles: set[str] = set()

    hype_candidates = profile_df.sort_values(
        ["performance_score", "longevity"],
        ascending=[False, False],
    )
    _pick_first_available(hype_candidates, "Hype", selected_rows, used_titles)

    retention_candidates = profile_df.sort_values(
        ["longevity", "performance_score"],
        ascending=[False, False],
    )
    _pick_first_available(
        retention_candidates, "High Retention", selected_rows, used_titles
    )

    longevity_max = profile_df["longevity"].max()
    performance_max = profile_df["performance_score"].max()
    scored_df = profile_df.copy()
    scored_df["longevity_norm"] = (
        scored_df["longevity"] / longevity_max if longevity_max > 0 else 0
    )
    scored_df["performance_norm"] = (
        scored_df["performance_score"] / performance_max if performance_max > 0 else 0
    )
    scored_df["balance_score"] = (
        scored_df["longevity_norm"] + scored_df["performance_norm"]
    )

    balanced_candidates = scored_df.sort_values(
        ["balance_score", "performance_score", "longevity"],
        ascending=[False, False, False],
    )
    _pick_first_available(balanced_candidates, "Balanced", selected_rows, used_titles)

    return pd.DataFrame(selected_rows)


def classify_success_titles(filtered_df: pd.DataFrame) -> pd.DataFrame:
    """Classify filtered weekly rows into the three Success Profile segments."""
    profile_df = calculate_title_longevity(filtered_df)
    result_df = build_success_profile_segments(profile_df)

    if result_df.empty:
        return pd.DataFrame()

    result_df["point_label"] = (
        result_df["show_title"].astype(str)
        + "<br>"
        + result_df["longevity"].astype(int).astype(str)
        + "w | "
        + result_df["performance_score"].astype(int).astype(str)
    )
    result_df["segment"] = pd.Categorical(
        result_df["segment"],
        categories=SEGMENT_ORDER,
        ordered=True,
    )

    return result_df.sort_values("segment").reset_index(drop=True)


def build_success_profile_data(
    df: pd.DataFrame,
    country: str,
    year: int,
    month: str,
    category: str,
) -> tuple[pd.DataFrame, str]:
    """Build profile data using strict monthly filters, then yearly fallback."""
    strict_df = filter_success_profile_rows(df, country, year, month, category)
    if not strict_df.empty:
        return classify_success_titles(strict_df), "strict"

    relaxed_df = filter_success_profile_rows(
        df,
        country,
        year,
        month=None,
        category=category,
    )
    return classify_success_titles(relaxed_df), "relaxed"


def filter_success_profile_rows(
    df: pd.DataFrame,
    country: str,
    year: int,
    month: str | None,
    category: str,
) -> pd.DataFrame:
    """Return rows matching the selected Success Profile filters."""
    filter_mask = (
        (df["country_name"] == country)
        & (df["year"] == year)
        & (df["category"] == category)
    )
    if month is not None:
        filter_mask = filter_mask & (df["month_name"].astype(str) == month)

    return df[filter_mask].copy()


def get_success_filter_options(
    df: pd.DataFrame,
) -> tuple[list[str], list[int], list[str], list[str]]:
    """Build sorted filter options for Success Profile selectors."""
    countries = sorted(df["country_name"].dropna().unique().tolist())
    years = sorted(df["year"].dropna().unique().tolist(), reverse=True)
    months_in_data = set(df["month_name"].dropna().astype(str).unique().tolist())
    months = [month for month in MONTH_ORDER if month in months_in_data]
    categories = sorted(df["category"].dropna().unique().tolist())
    return countries, years, months, categories


def build_success_scatter_df(profile_df: pd.DataFrame) -> pd.DataFrame:
    """Prepare Success Profile data for scatter labels and chart rendering."""
    if profile_df.empty:
        return pd.DataFrame()

    scatter_df = profile_df.copy()
    scatter_df["same_x_count"] = scatter_df.groupby("longevity")["show_title"].transform(
        "count"
    )
    scatter_df = scatter_df.sort_values(
        ["longevity", "performance_score"],
        ascending=[True, False],
    ).copy()
    scatter_df["same_x_rank"] = scatter_df.groupby("longevity").cumcount()
    return scatter_df


def build_success_kpi_df(profile_df: pd.DataFrame) -> pd.DataFrame:
    """Return compact KPI rows for the selected Success Profile titles."""
    if profile_df.empty:
        return pd.DataFrame(columns=["label", "value", "note"])

    return pd.DataFrame(
        [
            {
                "label": "Titles shown",
                "value": str(len(profile_df)),
                "note": "Selected success archetypes",
            },
            {
                "label": "Max longevity",
                "value": f"{int(profile_df['longevity'].max())}w",
                "note": "Weeks in Top 10",
            },
            {
                "label": "Max popularity",
                "value": str(int(profile_df["performance_score"].max())),
                "note": "Sum of 11 - weekly rank",
            },
        ]
    )