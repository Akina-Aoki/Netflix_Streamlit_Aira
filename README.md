# Netflix Streamlit Dashboard
- [Streamlit Project Link](https://netflixappgit-ww5sfjcnptv9s8ge6ruqia.streamlit.app/)

This project is a collaborative Data Engineering and UX project built with Streamlit.  
The dashboard uses Netflix Top 10 data from Tudum by Netflix and turns it into an interactive web app called **Streamly**.

The goal of the project is to make Netflix viewing patterns easier to explore. Users can look at country-level trends, compare titles, inspect successful shows and movies, and understand how different content performs across time.

The project is built with a clear structure so the code is easier to maintain, reuse, and deploy. that follows DRY.


## The dashboard includes these main pages:

- **🏠Country Insights Home**  
  Shows Netflix Top 10 patterns by country, year, month, and category.

- **⭐Best Movie and Serie**  
  Allows users to compare two selected titles side by side.

- **⭐Success Profile**  
  Explores what successful Netflix titles have in common based on ranking, category, and time period.

- **📊Russia: Data Story**  
  Contains a focused datastory telling analysis of Russia compared with the rest of the world.

The project follows a `src` folder structure and separates pages, components, helper functions, assets, and styling into different folders.


## Data Engineering Workflow

                    ┌──────────────────────────────────────────────┐
                    │        Netflix Top 10 Data Assets            │
                    │ src/netflix/assets/data/                     │
                    │ - global_weekly.xlsx                         │
                    │ - global_alltime.xlsx                        │
                    │ - FactGlobal_Final.csv                       │
                    │ - FactCountry_Final.csv                      │
                    │ - DimMetaData_Final.csv                      │
                    └─────────────────────┬────────────────────────┘
                                          │
                                          ▼
                    ┌──────────────────────────────────────────────┐
                    │         Data Loading & Helpers               │
                    │ src/netflix/utils/helpers.py                 │
                    │ - reads CSV / Excel files                    │
                    │ - caches data                                │
                    │ - shared helper functions                    │
                    └─────────────────────┬────────────────────────┘
                                          │
                                          ▼
                    ┌──────────────────────────────────────────────┐
                    │         Constants & Asset Paths              │
                    │ src/netflix/utils/constants.py               │
                    │ - data paths                                 │
                    │ - image paths                                │
                    │ - style paths                                │
                    └─────────────────────┬────────────────────────┘
                                          │
                                          ▼
       ┌─────────────────────────────────────────────────────────────────────┐
       │                    Streamlit Application Layer                      │
       │                     src/netflix/app.py                              │
       │             - defines navigation between pages                      │
       └───────────────┬───────────────────────┬────────────────────────────┘
                       │                       │
                       │                       │
                       ▼                       ▼
    ┌──────────────────────────┐   ┌──────────────────────────┐
    │     Reusable Components  │   │      Dashboard Pages     │
    │ src/netflix/components/  │   │   src/netflix/pages/     │
    │ - branding               │   │ - country_insights.py    │
    │ - filters                │   │ - insights.py            │
    │ - cards                  │   │ - success_profile.py     │
    │ - footer                 │   │ - dashboard.py           │
    │ - visuals                │   │                          │
    └──────────────┬───────────┘   └──────────────┬───────────┘
                   │                              │
                   └──────────────┬───────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────────────────────────┐
                    │           Visual Output Layer                │
                    │ - KPI cards                                  │
                    │ - filters                                    │
                    │ - Plotly charts                              │
                    │ - Matplotlib visuals                         │
                    │ - insight sections                           │
                    └─────────────────────┬────────────────────────┘
                                          │
                                          ▼
                    ┌──────────────────────────────────────────────┐
                    │     User Interface / Deployment Layer        │
                    │ - Local host via Streamlit                   │
                    │ - Streamlit Cloud deployment                 │
                    │ - End users explore Netflix insights         │
                    └──────────────────────────────────────────────┘


## Repository Structure

```text
Netflix_Streamlit/
├── src/
│   └── netflix/
│       ├── app.py                  # Main Streamlit entry point and page navigation
│       ├── pages/                  
│       │   ├── country_insights.py # Country-level Netflix Top 10 insights with weekly view
│       │   ├── dashboard.py        # Dashboard page for focused datastorytelling analysis abour Russia
│       │   ├── insights.py         # Best Movie and Serie comparison page
│       │   └── success_profile.py  # Success pattern analysis for Netflix titles
│ 
│       ├── components/             # Reusable UI and visual building blocks
│       │   ├── author_credit.py    # Creator credit section used in selected pages (Aira's)
│       │   ├── branding.py         # Streamly branding and shared header elements
│       │   ├── cards.py            # Reusable KPI and story card layouts
│       │   ├── filters.py          # Shared filter logic for dashboard controls
│       │   ├── footer.py           # Reusable disclaimer/footer component
│       │   ├── home_summary.py     # Summary KPI section for the home page
│       │   └── visuals.py          # Shared chart and visualization functions
│ 
│       ├── utils/                  # Shared helper logic
│       │   ├── constants.py        # Central paths for data, images, styles, and assets
│       │   └── helpers.py          # Cached data loading and CSS helper functions
│       └── assets/                 # Project assets used by the Streamlit app
│           ├── data/               # Netflix CSV and Excel data files
│           ├── image/              # Logo and image assets
│           ├── markdown/           # Optional markdown content
│           └── style/              # CSS files for the Streamly design
└── 
```