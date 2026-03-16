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


st.title("🩺 Composite Economic Health Index")

if not DATA_PATH.exists():
    st.warning("Dataset not found. Run `python scripts/etl_worldbank.py` first.")
    st.stop()

df = load_data(DATA_PATH)
latest_year = int(df["year"].max())
latest_df = df[df["year"] == latest_year].copy()

# Normalize components to 0-100
# GDP growth: higher is better
# Inflation / unemployment: lower is better, so invert after min-max
latest_df["gdp_score"] = minmax(latest_df["gdp_growth"])
latest_df["inflation_score"] = 100 - minmax(latest_df["inflation_cpi"])
latest_df["unemployment_score"] = 100 - minmax(latest_df["unemployment"])

# Composite index
latest_df["economic_health_index"] = (
    0.45 * latest_df["gdp_score"].fillna(50)
    + 0.30 * latest_df["inflation_score"].fillna(50)
    + 0.25 * latest_df["unemployment_score"].fillna(50)
)

countries = sorted(latest_df["country_name"].dropna().unique().tolist())
default_country = "United States" if "United States" in countries else countries[0]
selected_country = st.selectbox("Select country", countries, index=countries.index(default_country))

country_row = latest_df[latest_df["country_name"] == selected_country].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Latest Year", latest_year)
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

col1, col2 = st.columns([1.4, 1])

with col1:
    map_df = latest_df.dropna(subset=["economic_health_index"]).copy()
    fig_map = px.choropleth(
        map_df,
        locations="country_code",
        color="economic_health_index",
        hover_name="country_name",
        hover_data={
            "gdp_growth": ":.2f",
            "inflation_cpi": ":.2f",
            "unemployment": ":.2f",
            "economic_health_index": ":.1f",
            "country_code": False,
        },
        color_continuous_scale="RdYlGn",
        projection="natural earth",
        title=f"Composite Economic Health Index ({latest_year})",
    )
    fig_map.update_layout(height=650)
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

Each component is min-max scaled to a 0-100 range using the latest available year.
"""
)