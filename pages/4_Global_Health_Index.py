from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Economic Health Index", page_icon="🩺", layout="wide")

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "processed" / "econ_option_a.parquet"


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["year"] = df["year"].astype(int)
    return df


def minmax(series: pd.Series) -> pd.Series:
    s = series.copy()
    valid = s.dropna()
    if valid.empty:
        return pd.Series([None] * len(s), index=s.index)
    min_v = valid.min()
    max_v = valid.max()
    if max_v == min_v:
        return pd.Series([50.0] * len(s), index=s.index)
    return ((s - min_v) / (max_v - min_v)) * 100


def latest_complete_year(df: pd.DataFrame, min_complete: int = 30) -> int:
    coverage = df.groupby("year")[["inflation_cpi", "gdp_growth", "unemployment"]].apply(
        lambda x: x.dropna().shape[0]
    )
    valid = coverage[coverage >= min_complete]
    if not valid.empty:
        return int(valid.index.max())
    return int(df["year"].max())


st.title("🩺 Composite Economic Health Index")

if not DATA_PATH.exists():
    st.warning("Dataset not found. Run `python scripts/etl_worldbank.py` first.")
    st.stop()

df = load_data(DATA_PATH)

valid_years = (
    df.groupby("year")[["inflation_cpi", "gdp_growth", "unemployment"]]
    .apply(lambda x: x.dropna().shape[0])
    .reset_index(name="complete_cases")
)
valid_years = valid_years[valid_years["complete_cases"] > 0]["year"].tolist()

default_year = latest_complete_year(df)

top_controls = st.columns([1, 1])
with top_controls[0]:
    selected_year = st.selectbox(
        "Select year",
        sorted(valid_years, reverse=True),
        index=sorted(valid_years, reverse=True).index(default_year) if default_year in valid_years else 0,
    )

with top_controls[1]:
    region_options = ["All"] + sorted(df["region"].dropna().unique().tolist())
    selected_region = st.selectbox("Filter by region", region_options)

latest_df = df[df["year"] == selected_year].copy()
latest_df = latest_df.dropna(subset=["inflation_cpi", "gdp_growth", "unemployment", "country_name"])

if selected_region != "All":
    latest_df = latest_df[latest_df["region"] == selected_region].copy()

# Normalize components to 0-100
latest_df["gdp_score"] = minmax(latest_df["gdp_growth"])
latest_df["inflation_score"] = 100 - minmax(latest_df["inflation_cpi"])
latest_df["unemployment_score"] = 100 - minmax(latest_df["unemployment"])

latest_df["economic_health_index"] = (
    0.45 * latest_df["gdp_score"].fillna(50)
    + 0.30 * latest_df["inflation_score"].fillna(50)
    + 0.25 * latest_df["unemployment_score"].fillna(50)
)

countries = sorted(latest_df["country_name"].dropna().unique().tolist())
default_country = "United States" if "United States" in countries else (countries[0] if countries else None)

selected_country = None
if countries:
    selected_country = st.selectbox(
        "Select country",
        countries,
        index=countries.index(default_country) if default_country in countries else 0,
    )

if selected_country:
    country_row = latest_df[latest_df["country_name"] == selected_country].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Selected Year", selected_year)
    c2.metric("GDP Score", f"{country_row['gdp_score']:.1f}" if pd.notna(country_row["gdp_score"]) else "N/A")
    c3.metric(
        "Inflation Score",
        f"{country_row['inflation_score']:.1f}" if pd.notna(country_row["inflation_score"]) else "N/A",
    )
    c4.metric(
        "Economic Health Index",
        f"{country_row['economic_health_index']:.1f}" if pd.notna(country_row["economic_health_index"]) else "N/A",
    )

st.divider()

col1, col2 = st.columns([1.5, 1])

with col1:
    fig_map = px.choropleth(
        latest_df,
        locations="country_name",
        locationmode="country names",
        color="economic_health_index",
        hover_name="country_name",
        hover_data={
            "gdp_growth": ":.2f",
            "inflation_cpi": ":.2f",
            "unemployment": ":.2f",
            "economic_health_index": ":.1f",
        },
        color_continuous_scale="RdYlGn",
        projection="natural earth",
        title=f"Composite Economic Health Index ({selected_year})",
    )
    fig_map.update_geos(showcoastlines=True, showcountries=True, showframe=False)
    fig_map.update_layout(
        height=650,
        margin=dict(l=0, r=0, t=50, b=0),
    )
    st.plotly_chart(fig_map, use_container_width=True)

with col2:
    top_df = (
        latest_df[["country_name", "economic_health_index"]]
        .dropna()
        .sort_values("economic_health_index", ascending=False)
        .head(20)
    )

    fig_bar = px.bar(
        top_df,
        x="economic_health_index",
        y="country_name",
        orientation="h",
        title="Top 20 countries by Economic Health Index",
        labels={
            "economic_health_index": "Index",
            "country_name": "Country",
        },
    )
    fig_bar.update_layout(height=650, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

if selected_country:
    st.subheader("Component breakdown")
    components_df = pd.DataFrame(
        {
            "Component": ["GDP Growth Score", "Inflation Score", "Unemployment Score"],
            "Score": [
                country_row["gdp_score"],
                country_row["inflation_score"],
                country_row["unemployment_score"],
            ],
        }
    )

    fig_components = px.bar(
        components_df,
        x="Component",
        y="Score",
        title=f"Index component scores for {selected_country}",
    )
    fig_components.update_layout(height=450)
    st.plotly_chart(fig_components, use_container_width=True)

st.subheader("Methodology")
st.markdown(
    """
The **Economic Health Index** is a simple composite portfolio metric:

- **45% GDP growth score**
- **30% inflation score** (lower inflation = better)
- **25% unemployment score** (lower unemployment = better)

Each component is min-max scaled to a 0-100 range within the selected year.
"""
)