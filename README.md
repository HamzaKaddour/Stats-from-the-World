# Stats from the World

An interactive global economic data project built around the **World Bank World Development Indicators (WDI)**. It demonstrates an end-to-end workflow from API ingestion and data preparation to exploratory analytics, geospatial visualization, and static web deployment.

## Live dashboard

After GitHub Pages is enabled for the repository, the static dashboard is available at:

**https://hamzakaddour.github.io/Stats-from-the-World/**

The Pages dashboard is intentionally **static and serverless**. It uses Plotly.js in the browser and retrieves public World Bank data directly, so no paid hosting, database, or backend service is required.

## What the project demonstrates

- **Data engineering:** World Bank API ingestion, country metadata filtering, cleaning, joins, and Parquet output.
- **Data analysis:** country-level trends, cross-country comparisons, descriptive insights, and coverage-aware snapshots.
- **Data visualization:** interactive time series, ranked bar charts, choropleth maps, scatter plots, and KPI cards.
- **Geospatial analytics:** global country-level mapping with interactive indicator selection.
- **Web delivery:** a responsive GitHub Pages dashboard with zero backend infrastructure.
- **Python analytics:** a separate Streamlit implementation remains in the repository for richer Python-driven exploration.

## Indicators

| Indicator | World Bank code | Interpretation |
| --- | --- | --- |
| Inflation, consumer prices | `FP.CPI.TOTL.ZG` | Annual % change in CPI |
| GDP growth | `NY.GDP.MKTP.KD.ZG` | Annual % growth |
| Unemployment | `SL.UEM.TOTL.ZS` | % of total labor force |

## Repository structure

```
Stats-from-the-World/
├── index.html                  # Static GitHub Pages dashboard
├── Home.py                     # Streamlit landing page
├── pages/                      # Streamlit analytical views
├── scripts/
│   └── etl_worldbank.py       # Python ETL pipeline
├── data/processed/
│   └── econ_option_a.parquet  # Processed country-year dataset
└── requirements.txt
```

## Run the Python version locally

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python scripts/etl_worldbank.py
streamlit run Home.py
```

## GitHub Pages deployment

In the repository, open **Settings → Pages**, choose **Deploy from a branch**, select **main** and **/(root)**, then save. GitHub will serve `index.html` as the project site.

## Methodology and limitations

The dashboard uses publicly reported World Bank WDI observations. Coverage varies by country, indicator, and year, so comparisons use the countries with available observations for the selected snapshot.

The repository's **Cost Pressure Score** and **Economic Health Index** are exploratory composite metrics created for analytical demonstration. They are **not official World Bank indicators**, and they should not be interpreted as definitive rankings of welfare, economic performance, or policy quality. Their formulas are documented in the corresponding Streamlit pages.

## Data source

Data source: **World Bank — World Development Indicators (WDI)**, accessed through the World Bank API.

## Tech stack

Python · Pandas · Streamlit · Plotly · Plotly.js · Parquet · World Bank API · GitHub Pages

## Author

**Hamza Kaddour** — Machine Learning / AI Engineer

This project is intended as a portfolio demonstration of data engineering, analytics, visualization, and lightweight web deployment.
