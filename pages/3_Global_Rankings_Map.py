from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Global Rankings + Map", page_icon="🗺️", layout="wide")

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "processed" / "econ_option_a.parquet"


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["year"] = df["year"].astype(int)
    return df


def latest_year_with_data(df: pd.DataFrame, metric: str, min_countries: int = 20) -> int:
    coverage = df.groupby("year")[metric].apply(lambda s: s.notna().sum())
    valid = coverage[coverage >= min_countries]
    if not valid.empty:
        return int(valid.index.max())
    return int(df["year"].max())


st.title("🗺️ Global Rankings + World Map")

if not DATA_PATH.exists():
    st.warning("Dataset not found. Run `python scripts/etl_worldbank.py` first.")
    st.stop()

df = load_data(DATA_PATH)

metric_options = {
    "Inflation CPI (%)": "inflation_cpi",
    "GDP Growth (%)": "gdp_growth",
    "Unemployment (%)": "unemployment",
}

selected_metric_label = st.selectbox("Select metric", list(metric_options.keys()))
selected_metric = metric_options[selected_metric_label]

available_years = (
    df.groupby("year")[selected_metric]
    .apply(lambda s: s.notna().sum())
    .reset_index(name="count")
)
available_years = available_years[available_years["count"] > 0]["year"].tolist()
default_year = latest_year_with_data(df, selected_metric)

top_controls = st.columns([1, 1, 1])
with top_controls[0]:
    selected_year = st.selectbox(
        "Select year",
        sorted(available_years, reverse=True),
        index=sorted(available_years, reverse=True).index(default_year) if default_year in available_years else 0,
    )

with top_controls[1]:
    region_options = ["All"] + sorted(df["region"].dropna().unique().tolist())
    selected_region = st.selectbox("Filter by region", region_options)

with top_controls[2]:
    top_n = st.slider("Top countries to rank", min_value=10, max_value=30, value=20, step=5)

year_df = df[df["year"] == selected_year].copy()
year_df = year_df.dropna(subset=[selected_metric, "country_name"])

if selected_region != "All":
    year_df = year_df[year_df["region"] == selected_region].copy()

col1, col2 = st.columns([1.5, 1])

with col1:
    fig_map = px.choropleth(
        year_df,
        locations="country_name",
        locationmode="country names",
        color=selected_metric,
        hover_name="country_name",
        hover_data={
            "region": True,
            "income_level": True,
            selected_metric: ":.2f",
        },
        color_continuous_scale="Viridis",
        projection="natural earth",
        title=f"{selected_metric_label} by country ({selected_year})",
    )
    fig_map.update_geos(showcoastlines=True, showcountries=True, showframe=False)
    fig_map.update_layout(
        height=650,
        margin=dict(l=0, r=0, t=50, b=0),
        coloraxis_colorbar_title=selected_metric_label,
    )
    st.plotly_chart(fig_map, use_container_width=True)

with col2:
    ranking_df = (
        year_df[["country_name", "region", selected_metric]]
        .dropna()
        .sort_values(selected_metric, ascending=False)
        .head(top_n)
    )

    fig_rank = px.bar(
        ranking_df,
        x=selected_metric,
        y="country_name",
        orientation="h",
        title=f"Top {top_n} countries by {selected_metric_label}",
        labels={
            selected_metric: selected_metric_label,
            "country_name": "Country",
        },
    )
    fig_rank.update_layout(height=650, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_rank, use_container_width=True)

st.divider()

st.subheader("Quick insight")
if not ranking_df.empty:
    top_country = ranking_df.iloc[0]
    st.info(
        f"In {selected_year}, {top_country['country_name']} ranks highest in the current filtered view for "
        f"{selected_metric_label.lower()} with a value of {top_country[selected_metric]:.2f}."
    )

st.subheader("Ranking table")
table_df = (
    year_df[["country_name", "country_code", "region", "income_level", selected_metric]]
    .dropna()
    .sort_values(selected_metric, ascending=False)
)
st.dataframe(table_df, use_container_width=True)