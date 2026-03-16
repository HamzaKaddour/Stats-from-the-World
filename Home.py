from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Global Economy Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------
# Paths + Data loading
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "processed" / "econ_option_a.parquet"


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_parquet(path)
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
    return df


df = load_data(DATA_PATH)

# ------------------------------------------------------------
# Header / Hero section
# ------------------------------------------------------------
st.markdown(
    """
    <div style="padding: 0.6rem 0 0.2rem 0;">
        <h1 style="margin-bottom: 0.2rem;">🌍 Global Economy Dashboard</h1>
        <p style="margin-top: 0; font-size: 1.05rem; color: #666;">
            An interactive analytics suite built with <b>Python + Streamlit + Plotly</b> using
            <b>World Bank World Development Indicators (WDI)</b>.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# If no data, show a clean onboarding message
if df.empty:
    st.warning(
        f"Dataset not found at: {DATA_PATH}\n\n"
        "To generate it locally, run:\n"
        "• `python scripts/etl_worldbank.py`\n\n"
        "Then re-run the app."
    )
    st.stop()

# ------------------------------------------------------------
# Quick stats
# ------------------------------------------------------------
countries = df["country_code"].nunique() if "country_code" in df.columns else 0
year_min = int(df["year"].min()) if "year" in df.columns and df["year"].notna().any() else None
year_max = int(df["year"].max()) if "year" in df.columns and df["year"].notna().any() else None
rows = len(df)

available_indicators = [
    col for col in ["inflation_cpi", "gdp_growth", "unemployment"] if col in df.columns
]
indicator_labels = {
    "inflation_cpi": "Inflation CPI",
    "gdp_growth": "GDP Growth",
    "unemployment": "Unemployment",
}
indicator_names = [indicator_labels[c] for c in available_indicators]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Countries", f"{countries:,}")
k2.metric("Indicators", f"{len(indicator_names):,}")
k3.metric("Years", "—" if year_min is None else f"{year_min} → {year_max}")
k4.metric("Rows", f"{rows:,}")

st.divider()

# ------------------------------------------------------------
# What this project demonstrates
# ------------------------------------------------------------
left, right = st.columns([1.25, 1])

with left:
    st.subheader("What this project is about")
    st.write(
        """
This project is designed as a **portfolio-grade data product** that demonstrates:
- **ETL pipeline** (API ingestion → cleaning → parquet)
- **Exploratory analytics** (country trends, rankings, cross-indicator analysis)
- **Interactive dashboards** (filters, KPIs, maps, downloads)
- **Deployment readiness** (designed for Streamlit hosting)

The goal is to make global macroeconomic data easy to explore using modern, interactive visualization.
"""
    )

with right:
    st.subheader("How to use the app")
    st.markdown(
        """
1. Use the **sidebar Pages** menu to switch dashboards.
2. Apply filters such as **country** and **year**.
3. Use page-level visualizations to compare trends and rankings.
4. Start with **Macro**, then explore **Rankings & Map** and the **Economic Health Index**.
"""
    )
    st.info("Tip: Start with **Macro** for country trends, then use **Rankings & Map** for global context.")

st.divider()

# ------------------------------------------------------------
# Dashboard cards (explain what each page does)
# ------------------------------------------------------------
st.subheader("Dashboards inside this project")

c1, c2 = st.columns(2)

with c1:
    st.markdown("### 📈 Macro Dashboard")
    st.write(
        """
**Purpose:** Explore a single country over time and compare macroeconomic indicators.

**What you can do:**
- Select a country
- View KPI snapshots for the latest year
- Plot trends over time
- Compare inflation, growth, and unemployment
"""
    )

    st.markdown("### 🧺 Cost of Living & Affordability")
    st.write(
        """
**Purpose:** Analyze inflation-related cost pressure using available macro variables.

**What you can do:**
- Track inflation as a cost pressure signal
- Compare countries on inflation, unemployment, and growth context
- View a proxy affordability / pressure ranking
- Explore relative country positioning
"""
    )

with c2:
    st.markdown("### 🗺️ Global Rankings & Map")
    st.write(
        """
**Purpose:** Compare countries globally for a selected indicator in a selected year.

**What you can do:**
- Rank countries by inflation, GDP growth, or unemployment
- Visualize results on a **world choropleth map**
- Compare global patterns quickly
- Inspect country-level values interactively
"""
    )

    st.markdown("### 🧠 Global Health Index")
    st.write(
        """
**Purpose:** Build a composite economic “health” view.

**What you can do:**
- Combine growth, inflation, and unemployment into one score
- Compare countries on a normalized basis
- Rank countries using a composite index
- Visualize economic strength on a world map
"""
    )

st.divider()

# ------------------------------------------------------------
# Data source + transparency section
# ------------------------------------------------------------
st.subheader("Data source & transparency")

st.write(
    """
- **Source:** World Bank – World Development Indicators (WDI)
- **Access method:** World Bank API via ETL script
- **Stored format:** country-year parquet dataset
- **Indicators included:** Inflation CPI, GDP Growth, Unemployment
- **Limitations:** coverage varies by country and year; some values may be missing
"""
)

with st.expander("Show dataset preview"):
    preview_cols = [
        c
        for c in [
            "country_name",
            "country_code",
            "region",
            "income_level",
            "year",
            "inflation_cpi",
            "gdp_growth",
            "unemployment",
        ]
        if c in df.columns
    ]
    st.dataframe(df[preview_cols].head(50), use_container_width=True)

st.caption(
    "This dashboard is for informational purposes. Reported values depend on public datasets coverage and may be missing for some country-year combinations."
)