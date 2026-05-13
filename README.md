# Streamly — Netflix Top 10 Data Visualization App

[Open the Streamlit app](https://netflix-top10-tudum-analysis.streamlit.app/)

## Demo Video
[Netflix_Streamlit_Aira.webm](https://github.com/user-attachments/assets/3cab68be-c002-4193-b723-66efc442b02b)


Streamly is a Streamlit dashboard that explores Netflix Top 10 / Tudum data. It helps users see which films and TV series perform well globally, how titles trend in different countries, and what kind of success pattern a title has.

I built this project from a Data Engineering and DRY (Don't Repeat Yourself) perspective: prepare the data, create reusable transformations, and present the results in a dashboard that is simple to use and easy to explain.

## Main features

- Country Insights page with Netflix Top 10 title performance
- Filters for country, year, month, and category
- Films vs TV comparison
- Title Profile Explorer with metadata, poster, and performance history
- Market Reach view showing how many countries a title appeared in
- Nordic country ranking for selected titles
- Popularity views by year, month, and week
- Success Profile page with title types such as Hype, High Retention, and Balanced

## Dataset

The data comes from Netflix Tudum Top 10 data and prepared project files in `src/netflix/assets/data/`.

The app uses:

- global weekly Top 10 data
- global all-time Top 10 data
- country-level Top 10 data
- metadata for title details, posters, descriptions, genres, and trailers where available

Important fields include `show_title`, `category`, `week`, `country_name`, `weekly_rank`, and `weekly_hours_viewed` where available.

## Metrics explained

### Performance Score

Netflix ranks titles from 1 to 10 each week. To make rankings easier to compare and aggregate, the app converts weekly rank into a score:

```text
performance_score = 11 - weekly_rank
```

So rank 1 gets 10 points, rank 10 gets 1 point, and higher scores mean stronger performance.

### Longevity

Longevity counts how many weeks a title stays in the Top 10. A title with high longevity may not always have the biggest launch, but it stays relevant for longer.

### Market Reach

Market Reach counts how many countries a title appeared in. This helps show whether a title was popular in one market or reached many Netflix markets.

## Code structure and DRY principles

The project follows DRY principles, which means **“Don’t Repeat Yourself.”** Instead of repeating the same chart code, HTML, colors, and styling in every page, I moved reusable logic into components. This makes the app easier to maintain because changes only need to be made in one place.

| Part | Responsibility |
| --- | --- |
| `country_insights.py` | Controls the page flow |
| `country_sections.py` | Renders Streamlit page sections |
| `country_charts.py` | Builds Plotly charts |
| `utils/country_insights.py` | Prepares and transforms data |
| `theme.py` | Stores shared colors/constants |
| `html/` | Stores reusable HTML templates |
| `dashboard.css` | Stores styling |

## How Streamlit is used

Streamly uses Streamlit for the app layout, filters, navigation, and chart rendering.

The app uses:

- `st.Page` and `st.navigation` for multi-page navigation
- `st.columns` for layout
- `st.container` for grouped sections and cards
- `st.selectbox` for filters and title selectors
- `st.plotly_chart` for interactive charts
- `st.image` for logos and poster images
- `st.dataframe` for table views when needed
- `.streamlit/config.toml` for theme settings

Charts use `width="stretch"` for responsive rendering.

## Folder structure
```
src/netflix/
├── app.py
├── pages/
│   ├── country_insights.py
│   └── success_profile.py
│
├── components/
│   ├── country_sections.py
│   ├── country_charts.py
│   ├── success_sections.py
│   ├── success_charts.py
│   ├── cards.py
│   ├── branding.py
│   ├── footer.py
│   ├── theme.py
│   └── html/
│
├── utils/
│   ├── helpers.py
│   ├── constants.py
│   ├── country_insights.py
│   └── success_profile.py
│
└── assets/
    ├── data/
    ├── image/
    └── style/
        ├── dashboard.css
        └── main.css
```

## How to run locally

```bash
git clone <repository-url>
cd Netflix_Streamlit_Aira
uv sync
uv run streamlit run src/netflix/app.py
```

If you are not using `uv`, install the project with pip and run Streamlit directly:

```bash
python -m pip install -e .
streamlit run src/netflix/app.py
```

## Disclaimer / notes

This project is for learning, portfolio, and data storytelling purposes. It uses Netflix Top 10 / Tudum data to explore viewing trends, but it should not be treated as a complete picture of all Netflix viewing behavior.
