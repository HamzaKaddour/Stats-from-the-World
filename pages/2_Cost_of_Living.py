from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Cost of Living", page_icon="💸", layout="wide")

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "processed" / "econ_option_a.parquet"


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df = df[df["year"].notna()].copy()
    df["year"] = df["year"].astype(int)
    return df


def zscore(series: pd.Series) -> pd.Series:
    valid = series.dropna()
    if valid.empty:
        return pd.Series([0.0] * len(series), index=series.index)

    std = valid.std(ddof=0)
    if std == 0 or pd.isna(std):
        return pd.Series([0.0] * len(series), index=series.index)

    return (series - valid.mean()) / std


def latest_year_with_scatter_data(df: pd.DataFrame, min_countries: int = 20) -> int:
    coverage = (
        df.dropna(subset=["inflation_cpi", "unemployment"])
        .groupby("year")
        .size()
        .sort_index()
    )
    valid = coverage[coverage >= min_countries]
    if not valid.empty:
        return int(valid.index.max())

    # fallback: latest year with at least one valid pair
    if not coverage.empty:
        return int(coverage.index.max())

    # last fallback
    return int(df["year"].max())


st.title("💸 Cost of Living Dashboard")
st.caption(
    "This page uses a proxy view. Since the ETL only includes inflation, GDP growth, and unemployment, "
    "the analysis approximates cost pressure rather than true household basket cost-of-living data."
)

if not DATA_PATH.exists():
    st.warning("Dataset not found. Run `python scripts/etl_worldbank.py` first.")
    st.stop()

df = load_data(DATA_PATH)

# ------------------------------------------------------------
# Year + filters
# ------------------------------------------------------------
default_year = latest_year_with_scatter_data(df)

year_coverage = (
    df.groupby("year")[["inflation_cpi", "unemployment", "gdp_growth"]]
    .apply(lambda x: pd.Series({
        "infl_unemp_pairs": x.dropna(subset=["inflation_cpi", "unemployment"]).shape[0],
        "complete_cases": x.dropna(subset=["inflation_cpi", "unemployment", "gdp_growth"]).shape[0],
    }))
    .reset_index()
)

available_years = sorted(df["year"].dropna().unique().tolist(), reverse=True)

top_controls = st.columns([1, 1])
with top_controls[0]:
    selected_year = st.selectbox(
        "Select year",
        available_years,
        index=available_years.index(default_year) if default_year in available_years else 0,
    )

with top_controls[1]:
    region_options = ["All"] + sorted(df["region"].dropna().unique().tolist())
    selected_region = st.selectbox("Filter by region", region_options)

year_df = df[df["year"] == selected_year].copy()

if selected_region != "All":
    year_df = year_df[year_df["region"] == selected_region].copy()

# ------------------------------------------------------------
# Proxy metrics
# ------------------------------------------------------------
year_df["inflation_z"] = zscore(year_df["inflation_cpi"])
year_df["unemployment_z"] = zscore(year_df["unemployment"])
year_df["gdp_growth_z"] = zscore(year_df["gdp_growth"])

# Higher = more cost pressure
year_df["cost_pressure_score"] = (
    0.60 * year_df["inflation_z"].fillna(0)
    + 0.25 * year_df["unemployment_z"].fillna(0)
    - 0.15 * year_df["gdp_growth_z"].fillna(0)
)

countries = sorted(year_df["country_name"].dropna().unique().tolist())
if not countries:
    st.warning("No data is available for the selected filters.")
    st.stop()

default_country = "United States" if "United States" in countries else countries[0]
selected_country = st.selectbox(
    "Select country",
    countries,
    index=countries.index(default_country) if default_country in countries else 0,
)

row = year_df[year_df["country_name"] == selected_country].iloc[0]

# ------------------------------------------------------------
# KPIs
# ------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Year", selected_year)
c2.metric("Inflation CPI", f"{row['inflation_cpi']:.2f}%" if pd.notna(row["inflation_cpi"]) else "N/A")
c3.metric("Unemployment", f"{row['unemployment']:.2f}%" if pd.notna(row["unemployment"]) else "N/A")
c4.metric(
    "Cost Pressure Score",
    f"{row['cost_pressure_score']:.2f}" if pd.notna(row["cost_pressure_score"]) else "N/A"
)

st.divider()

# ------------------------------------------------------------
# Charts
# ------------------------------------------------------------
col1, col2 = st.columns([1.2, 1])

with col1:
    scatter_df = year_df.dropna(subset=["inflation_cpi", "unemployment"]).copy()

    if scatter_df.empty:
        st.info(f"No countries have both inflation and unemployment data for {selected_year}.")
    else:
        fig = px.scatter(
            scatter_df,
            x="inflation_cpi",
            y="unemployment",
            hover_name="country_name",
            color="region" if "region" in scatter_df.columns else None,
            title=f"Inflation vs Unemployment ({selected_year})",
            labels={
                "inflation_cpi": "Inflation CPI (%)",
                "unemployment": "Unemployment (%)",
            },
        )

        # highlight selected country if present
        selected_point = scatter_df[scatter_df["country_name"] == selected_country]
        if not selected_point.empty:
            fig.add_scatter(
                x=selected_point["inflation_cpi"],
                y=selected_point["unemployment"],
                mode="markers+text",
                text=selected_point["country_name"],
                textposition="top center",
                marker=dict(size=14, symbol="diamond"),
                name="Selected country",
            )

        fig.update_layout(height=550)
        st.plotly_chart(fig, use_container_width=True)

with col2:
    top_pressure = (
        year_df[["country_name", "cost_pressure_score"]]
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

# ------------------------------------------------------------
# Quick insight
# ------------------------------------------------------------
st.subheader("Quick insight")
if not year_df.dropna(subset=["cost_pressure_score"]).empty:
    top_country = (
        year_df[["country_name", "cost_pressure_score"]]
        .dropna()
        .sort_values("cost_pressure_score", ascending=False)
        .iloc[0]
    )
    st.info(
        f"In {selected_year}, {top_country['country_name']} shows the highest cost pressure score "
        f"in the current view at {top_country['cost_pressure_score']:.2f}."
    )

# ------------------------------------------------------------
# Methodology
# ------------------------------------------------------------
st.subheader("Methodology")
st.markdown(
    """
**Cost Pressure Score (proxy)** is computed within the selected year using:
- higher inflation → higher pressure
- higher unemployment → higher pressure
- higher GDP growth → lower pressure

This is useful for a portfolio dashboard, but it should not be interpreted as an official cost-of-living index.
"""
)

# ------------------------------------------------------------
# Ranking table + download
# ------------------------------------------------------------
st.subheader("Country ranking")
rank_df = year_df[
    ["country_name", "region", "inflation_cpi", "unemployment", "gdp_growth", "cost_pressure_score"]
].sort_values("cost_pressure_score", ascending=False)

st.dataframe(rank_df, use_container_width=True)

st.download_button(
    "Download ranking as CSV",
    data=rank_df.to_csv(index=False),
    file_name=f"cost_of_living_proxy_{selected_year}.csv",
    mime="text/csv",
)