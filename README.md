# Stats from the World

[![CI](https://github.com/HamzaKaddour/Stats-from-the-World/actions/workflows/ci.yml/badge.svg)](https://github.com/HamzaKaddour/Stats-from-the-World/actions/workflows/ci.yml)
[![Data Refresh](https://github.com/HamzaKaddour/Stats-from-the-World/actions/workflows/refresh-worldbank.yml/badge.svg)](https://github.com/HamzaKaddour/Stats-from-the-World/actions/workflows/refresh-worldbank.yml)
[![Release](https://img.shields.io/github/v/release/HamzaKaddour/Stats-from-the-World?label=release)](https://github.com/HamzaKaddour/Stats-from-the-World/releases/latest)
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/HamzaKaddour/Stats-from-the-World?quickstart=1)

[**Portfolio case study → https://hamzakaddour.github.io/case-studies/global-development.html**](https://hamzakaddour.github.io/case-studies/global-development.html)

**A source-aware global development intelligence platform built entirely on free public data and serverless infrastructure.**

[Live Dashboard](https://hamzakaddour.github.io/Stats-from-the-World/) · [Source Code](https://github.com/HamzaKaddour/Stats-from-the-World)

Stats from the World turns authoritative international development data into an interactive decision-support experience. It combines reported World Bank World Development Indicators with clearly labeled IMF World Economic Outlook estimates and projections, harmonizes countries through ISO identifiers, preserves metric-level provenance, and serves the resulting analytical layer directly through GitHub Pages.

The project is designed to demonstrate data engineering, public-sector analytics, data governance, visualization, reproducibility, and lightweight production deployment rather than simply presenting charts.

## Product capabilities

- Large interactive global choropleth that doubles as the primary country-navigation surface
- Map and auditable table views for every supported indicator
- Six development domains: Economy, People, Poverty & Equity, Climate, Infrastructure, and Digital
- Nineteen curated development indicators
- Historical observations from 2000 onward plus selected IMF macroeconomic outlook values through 2030
- Explicit Reported vs Estimate/Projection status for every displayed metric
- Country intelligence briefs with selected-year KPIs and source labels
- Regional, income-group, and global median benchmarking
- Progress-since-2015 views using reported observations only
- Representative development-domain cards for each selected country
- Shareable URL state for country / domain / indicator / year
- Print / PDF-friendly country brief
- Machine-readable data provenance manifest
- Automated monthly data refresh and validation

## Data sources and provenance

| Source | Role | Status in the dashboard |
| --- | --- | --- |
| World Bank World Development Indicators (WDI) | Historical and recently reported development observations | `reported` |
| IMF World Economic Outlook / DataMapper | Selected current-year estimates and future macroeconomic outlook values | `estimate/projection` |

For overlapping macroeconomic observations, a reported WDI value takes precedence. IMF WEO is used only where the relevant current/future World Bank observation is absent.

Every analytical metric can carry:

```text
value
year
source
status
```

This prevents future-year projections from being visually indistinguishable from realized historical observations.

## Development domains

### Economy
- Inflation, consumer prices — `FP.CPI.TOTL.ZG`
- GDP growth — `NY.GDP.MKTP.KD.ZG`
- Unemployment — `SL.UEM.TOTL.ZS`
- GDP per capita — `NY.GDP.PCAP.CD`

### People
- Population — `SP.POP.TOTL`
- Life expectancy at birth — `SP.DYN.LE00.IN`
- Youth unemployment — `SL.UEM.1524.ZS`
- Secondary school enrollment — `SE.SEC.ENRR`

### Poverty & Equity
- Gini index — `SI.POV.GINI`
- Poverty headcount at national poverty lines — `SI.POV.NAHC`

### Climate
- CO₂ emissions per capita — `EN.ATM.CO2E.PC`
- Renewable energy consumption — `EG.FEC.RNEW.ZS`
- Forest area — `AG.LND.FRST.ZS`

### Infrastructure
- Access to electricity — `EG.ELC.ACCS.ZS`
- At least basic drinking water services — `SH.H2O.BASW.ZS`
- At least basic sanitation services — `SH.STA.BASS.ZS`

### Digital
- Individuals using the Internet — `IT.NET.USER.ZS`
- Mobile cellular subscriptions — `IT.CEL.SETS.P2`
- Fixed broadband subscriptions — `IT.NET.BBND.P2`

## Architecture

```text
World Bank WDI API                 IMF WEO / DataMapper
(reported observations)           (estimates + projections)
          |                                  |
          +---------------+------------------+
                          |
                          v
                  Python ingestion layer
                  requests + pandas
                          |
          +---------------+------------------+
          |                                  |
   schema / coverage                   ISO country
      validation                       harmonization
          |                                  |
          +---------------+------------------+
                          |
                          v
                metric-level provenance
                source + status + year
                          |
                          v
                  Parquet analytical layer
                          |
                          v
                     GitHub repository
                          |
                          v
                GitHub Pages + Plotly.js
                          |
       +------------------+------------------+
       |                  |                  |
      Maps              Tables        Country intelligence
                                             |
                                  benchmarks / progress /
                                      printable brief
```

No paid database or backend is required. The public application is read-heavy, so the data is preprocessed into compact Parquet artifacts and analytical work is performed in the browser.

## Data pipeline

`scripts/etl_worldbank.py`

1. Retrieves World Bank country metadata.
2. Excludes aggregate entities.
3. Retrieves the curated WDI indicator set over a dynamic year range.
4. Harmonizes country / year observations.
5. Coerces analytical fields to numeric types.
6. Validates schema, country coverage, and freshness.
7. Writes `data/processed/econ_option_a.parquet`.

`scripts/build_multisource.py`

1. Loads the validated WDI analytical layer.
2. Adds metric-level WDI source / status metadata.
3. Retrieves IMF WEO / DataMapper values for selected macroeconomic indicators.
4. Preserves all WDI development indicators while overlaying only missing macroeconomic values.
5. Gives reported WDI observations precedence over IMF estimates/projections.
6. Writes `data/processed/global_economy.parquet`.
7. Writes `data/processed/data_manifest.json` with refresh and source metadata.

## Automated refresh

`.github/workflows/refresh-worldbank.yml` runs monthly and can also be started manually.

The workflow:

- installs Python ETL dependencies
- refreshes WDI data
- builds the multi-source layer
- creates the provenance manifest
- commits data artifacts only when they changed
- rebases on the latest `main` before pushing, avoiding non-fast-forward races

## Repository structure

```text
.
├── index.html
├── data/
│   ├── indicator_catalog.json
│   └── processed/
│       ├── econ_option_a.parquet
│       ├── global_economy.parquet
│       └── data_manifest.json
├── scripts/
│   ├── etl_worldbank.py
│   └── build_multisource.py
├── .github/workflows/
│   └── refresh-worldbank.yml
├── Home.py
├── pages/
└── requirements.txt
```

The Streamlit application is retained as an alternate exploratory interface. GitHub Pages is the primary production-facing deployment.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python scripts/etl_worldbank.py
python scripts/build_multisource.py
python -m http.server 8000
```

Then open `http://localhost:8000`.

## Interpretation principles

The dashboard does not treat projections as realized outcomes.

- **Reported** means the displayed metric comes from a World Bank WDI observation.
- **Estimate/projection** means the displayed macroeconomic metric comes from IMF WEO / DataMapper.
- Missing observations remain missing rather than being statistically imputed.
- Peer medians are descriptive comparisons only; they do not imply policy quality, causality, or institutional performance.
- Progress views use reported observations only.
- Coverage varies substantially across indicators, especially poverty and inequality measures.

## Cost

The production design intentionally uses a zero-cost public architecture:

| Component | Cost |
| --- | ---: |
| GitHub repository | $0 |
| GitHub Pages | $0 |
| GitHub Actions within applicable free usage | $0 |
| World Bank public API | $0 |
| IMF public DataMapper API | $0 |
| Python / pandas / PyArrow | $0 |
| Plotly.js | $0 |
| Database server | $0 |
| Application server | $0 |

## Tech stack

**Data:** World Bank WDI, IMF WEO / DataMapper  
**ETL:** Python, pandas, requests, PyArrow  
**Data model:** ISO country harmonization, metric-level source/status provenance  
**Storage:** Parquet + JSON metadata  
**Analytics:** client-side JavaScript filtering, medians, benchmarking, trend analysis  
**Visualization:** Plotly.js choropleths and time series  
**Automation:** GitHub Actions  
**Deployment:** GitHub Pages

## Author

**Hamza Kaddour** — Machine Learning / AI Engineer

Built as a portfolio project demonstrating production-minded public-data engineering, transparent analytical design, data visualization, automation, and serverless deployment.
