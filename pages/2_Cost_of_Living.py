from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Cost of Living", page_icon="💸", layout="wide")

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "processed" / "econ_option_a.parquet"


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["year"] = df["year"].astype(int)
    return df


def zscore(series: pd.Series) -> pd.Series:
    std = series.std(ddof=0)
    if std == 0 or pd.isna(std):
        return pd.Series([0] * len(series), index=series.index)
    return (series - series.mean()) / std


st.title("💸 Cost of Living Dashboard")
st.caption(
    "This page uses a proxy view. Since the ETL only includes inflation, GDP growth, and unemployment, "
    "the analysis approximates cost pressure rather than true household basket cost-of-living data."
)

if not DATA_PATH.exists():
    st.warning("Dataset not found. Run `python scripts/etl_worldbank.py` first.")
    st.stop()

df = load_data(DATA_PATH)
latest_year = int(df["year"].max())
latest_df = df[df["year"] == latest_year].copy()

# Proxy metrics
latest_df["inflation_z"] = zscore(latest_df["inflation_cpi"])
latest_df["unemployment_z"] = zscore(latest_df["unemployment"])
latest_df["gdp_growth_z"] = zscore(latest_df["gdp_growth"])

# Higher = more cost pressure
latest_df["cost_pressure_score"] = (
    0.60 * latest_df["inflation_z"].fillna(0)
    + 0.25 * latest_df["unemployment_z"].fillna(0)
    - 0.15 * latest_df["gdp_growth_z"].fillna(0)
)

countries = sorted(latest_df["country_name"].dropna().unique().tolist())
default_country = "United States" if "United States" in countries else countries[0]
selected_country = st.selectbox("Select country", countries, index=countries.index(default_country))

row = latest_df[latest_df["country_name"] == selected_country].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Year", latest_year)
c2.metric("Inflation CPI", f"{row['inflation_cpi']:.2f}%" if pd.notna(row["inflation_cpi"]) else "N/A")
c3.metric("Unemployment", f"{row['unemployment']:.2f}%" if pd.notna(row["unemployment"]) else "N/A")
c4.metric(
    "Cost Pressure Score",
    f"{row['cost_pressure_score']:.2f}" if pd.notna(row["cost_pressure_score"]) else "N/A"
)

st.divider()

col1, col2 = st.columns([1.2, 1])

with col1:
    scatter_df = latest_df.dropna(subset=["inflation_cpi", "unemployment"]).copy()
    fig = px.scatter(
        scatter_df,
        x="inflation_cpi",
        y="unemployment",
        hover_name="country_name",
        color="region",
        title=f"Inflation vs Unemployment ({latest_year})",
        labels={
            "inflation_cpi": "Inflation CPI (%)",
            "unemployment": "Unemployment (%)",
        },
    )
    fig.update_layout(height=550)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    top_pressure = (
        latest_df[["country_name", "cost_pressure_score"]]
        .dropna()
        .sort_values("cost_pressure_score", ascending=False)
        .head(15)
    )

    fig_bar = px.bar(
        top_pressure,
        x="cost_pressure_score",
        y="country_name",
        orientation="h",
        title="Highest cost pressure (proxy)",
        labels={
            "cost_pressure_score": "Cost Pressure Score",
            "country_name": "Country",
        },
    )
    fig_bar.update_layout(height=550, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

st.subheader("Methodology")
st.markdown(
    """
**Cost Pressure Score (proxy)** is computed from the latest available year using:
- higher inflation → higher pressure
- higher unemployment → higher pressure
- higher GDP growth → lower pressure

This is useful for a portfolio dashboard, but it should not be interpreted as an official cost-of-living index.
"""
)

st.subheader("Latest country ranking")
rank_df = latest_df[
    ["country_name", "region", "inflation_cpi", "unemployment", "gdp_growth", "cost_pressure_score"]
].sort_values("cost_pressure_score", ascending=False)

st.dataframe(rank_df, use_container_width=True)
