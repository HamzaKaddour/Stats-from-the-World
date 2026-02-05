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
BASE_DIR = Path(__file__).resolve().parent  # Home.py is at project root
DATA_PATH = BASE_DIR / "data" / "processed" / "econ_option_a.parquet"

@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_parquet(path)
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
indicators = sorted(df["indicator_name"].dropna().unique().tolist()) if "indicator_name" in df.columns else []
year_min = int(df["year"].min()) if "year" in df.columns else None
year_max = int(df["year"].max()) if "year" in df.columns else None
rows = len(df)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Countries", f"{countries:,}")
k2.metric("Indicators", f"{len(indicators):,}")
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
- **Exploratory analytics** (country trends, ranking, cross-indicator analysis)
- **Interactive dashboards** (filters, KPIs, maps, downloads)
- **Deployment readiness** (designed for Hugging Face Spaces or Streamlit hosting)

The goal is to make global macroeconomic data easy to explore using modern, interactive visualization.
"""
    )

with right:
    st.subheader("How to use the app")
    st.markdown(
        """
1. Use the **sidebar Pages** menu to switch dashboards.
2. Apply filters (country, indicator, year).
3. Use **Download CSV** when available to export slices.
4. Compare countries via **rankings + maps** for fast insights.
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
**Purpose:** Explore a single country over time and compare indicators.

**What you can do:**
- Select a country + multiple indicators
- View KPI snapshots (latest year)
- Plot trends over time (line chart)
- Compare indicators in a pivot table
"""
    )

    st.markdown("### 🧺 Cost of Living & Affordability")
    st.write(
        """
**Purpose:** Analyze inflation impact and affordability proxies.

**What you can do:**
- Track inflation + related cost-of-living indicators
- View affordability-style plots (e.g., inflation vs GDP per capita)
- Highlight a country relative to others
- Export filtered data
"""
    )

with c2:
    st.markdown("### 🗺️ Global Rankings & Map")
    st.write(
        """
**Purpose:** Compare countries globally for any indicator in a selected year.

**What you can do:**
- Rank **Top / Bottom** countries by indicator and year
- Visualize results on a full-width **world choropleth map**
- Switch to log-scale for skewed indicators
- Download indicator-year slices
"""
    )

    st.markdown("### 🧠 Global Health Index")
    st.write(
        """
**Purpose:** Build a composite economic “health” view.

**What you can do:**
- Compute an index from growth, inflation, unemployment
- Normalize indicators (z-scores)
- Adjust weights (if your page supports it)
- Rank countries + visualize index on a world map
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
- **Access method:** World Bank Indicators API (via ETL script)
- **Processing:** unified long-format table saved as a parquet file
- **Limitations:** coverage varies by country/year; some indicators may be missing for specific years
"""
)

with st.expander("Show dataset preview"):
    show_cols = [c for c in ["country", "country_code", "year", "indicator_name", "value", "source"] if c in df.columns]
    st.dataframe(df[show_cols].head(50), width="stretch")

st.caption(
    "This dashboard is for informational purposes. Reported values depend on World Bank coverage and may be missing for some country-year combinations."
)
