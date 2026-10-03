# Stats from the World

**A source-aware global economic intelligence dashboard combining reported observations with clearly labeled estimates and forecasts.**

[Live Dashboard](https://hamzakaddour.github.io/Stats-from-the-World/) · [Source Code](https://github.com/HamzaKaddour/Stats-from-the-World)

Stats from the World is an end-to-end data engineering and visualization project for exploring macroeconomic conditions across countries and time. The pipeline combines World Bank World Development Indicators (WDI) with IMF World Economic Outlook (WEO) data, preserves metric-level provenance and status, and serves the resulting analytical dataset through an interactive GitHub Pages dashboard.

## What you can explore

- Inflation, GDP growth, and unemployment from 2000 to the latest available observations
- Country-level historical trends
- Cross-country rankings and world choropleth maps
- Inflation vs. GDP-growth relationships
- Region and World Bank income-group filtering
- Country comparison tables and coverage-aware descriptive insights

## Architecture

```text
World Bank WDI API (reported observations)     IMF WEO / DataMapper (estimates & projections)
        |                                              |
        +----------------------+-----------------------+
                               |
        v
Python ETL (requests + pandas)
        |
        +--> country/aggregate filtering
        +--> indicator joins
        +--> type and coverage validation
        |
        v
Validated Parquet dataset
        |
        v
GitHub repository
        |
        v
GitHub Pages + JavaScript + Plotly
        |
        v
Interactive browser analytics
```

A scheduled GitHub Actions workflow refreshes the World Bank and IMF datasets monthly. If the source data has not changed, the workflow creates no commit. ETL validation prevents unexpectedly incomplete or stale datasets from being published.

## Data pipeline

The pipeline in `scripts/etl_worldbank.py`:

1. Retrieves World Bank country metadata and removes aggregate entities.
2. Retrieves the three indicators over a dynamic year range.
3. Joins indicator observations by country and year.
4. Adds region, income group, lending type, capital city and geographic metadata.
5. Coerces analytical fields to numeric types and validates country/year coverage.
6. Writes `data/processed/econ_option_a.parquet` for the web application.

### Indicators

| Metric | World Bank code | Unit |
| --- | --- | --- |
| Inflation, consumer prices | `FP.CPI.TOTL.ZG` | Annual % |
| GDP growth | `NY.GDP.MKTP.KD.ZG` | Annual % |
| Unemployment | `SL.UEM.TOTL.ZS` | % of total labor force |

## Dashboard engineering

The production dashboard is a static GitHub Pages application. It loads the processed Parquet dataset from the repository and performs filtering, aggregation, ranking, and chart preparation in the browser. This keeps the public demo fast and inexpensive while preserving a reproducible Python data pipeline.

The default snapshot year is selected dynamically using data coverage rather than assuming the newest calendar year is complete.

## Repository structure

```text
.
├── index.html
├── scripts/
│   └── etl_worldbank.py
├── data/processed/
│   └── econ_option_a.parquet
├── .github/workflows/
│   └── refresh-worldbank.yml
├── Home.py
├── pages/
└── requirements.txt
```

The Streamlit files are retained as an alternate Python exploration interface, but GitHub Pages is the primary deployed application.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/etl_worldbank.py
streamlit run Home.py
```

For the production static dashboard, serve the repository root with any local HTTP server rather than opening `index.html` directly:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000`.

## Automated refresh

`.github/workflows/refresh-worldbank.yml` runs monthly and can also be triggered manually from GitHub Actions. It installs the ETL dependencies, rebuilds and validates the dataset, and commits the Parquet artifact only when World Bank data changed.

## Interpretation and limitations

World Bank indicator coverage differs by country and year. Missing observations are excluded from snapshot calculations and rankings. The dashboard's automatically generated observations are descriptive and do not imply causality. Each metric retains a source and status field. IMF WEO values for future years are estimates/projections, not realized outcomes, and the interface labels them accordingly.

The older Streamlit views include exploratory composite measures such as Cost Pressure Score and Economic Health Index. Those are portfolio analytics constructs, not official World Bank indicators.

## Tech stack

**Data:** World Bank WDI API, IMF World Economic Outlook / DataMapper  
**ETL:** Python, pandas, requests, PyArrow  
**Analytics:** JavaScript, Parquet, client-side filtering and aggregation  
**Visualization:** Plotly / Plotly.js, choropleth mapping  
**Automation:** GitHub Actions  
**Deployment:** GitHub Pages

## Author

**Hamza Kaddour** — Machine Learning / AI Engineer

Built as a portfolio project demonstrating reproducible data ingestion, analytical data modeling, visualization, automation, and lightweight production deployment.
