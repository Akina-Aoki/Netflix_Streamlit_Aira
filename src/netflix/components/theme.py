"""Shared Streamly theme values for component styling and Plotly charts."""

STREAMLY_COLORS = {
    "bg": "#0F0D0B",
    "card": "#1A1612",
    "surface": "#2A2118",
    "border": "#2A2118",
    "yellow": "#F7B952",
    "orange": "#E8622A",
    "amber": "#FFB84D",
    "text": "#F5F0E8",
    "muted": "#9E9689",
    "green": "#2A9D8F",
    "red": "#E63946",
}

CATEGORY_COLORS = {
    "Films": STREAMLY_COLORS["yellow"],
    "TV": STREAMLY_COLORS["orange"],
}

CHART_FONT = {
    "color": STREAMLY_COLORS["text"],
    "family": "Segoe UI, sans-serif",
}

NORDIC_COUNTRIES = ["Sweden", "Norway", "Denmark", "Finland", "Iceland"]

NORDIC_FLAGS = {
    "Sweden": "🇸🇪",
    "Norway": "🇳🇴",
    "Denmark": "🇩🇰",
    "Finland": "🇫🇮",
    "Iceland": "🇮🇸",

}
SUCCESS_SEGMENT_COLORS = {
    "Hype": STREAMLY_COLORS["red"],
    "Balanced": "#F4A261",
    "High Retention": STREAMLY_COLORS["green"],
}

SUCCESS_PROFILE_CHART_COLORS = {
    "background": STREAMLY_COLORS["text"],
    "text": "#111111",
    "muted_text": "#4A4A4A",
    "axis": "#222222",
    "vertical_guide": "#E8C87E",
}