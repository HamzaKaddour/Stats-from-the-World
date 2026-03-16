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


st.title("🗺️ Global Rankings + World Map")

if not DATA_PATH.exists():
    st.warning("Dataset not found. Run `python scripts/etl_worldbank.py` first.")
    st.stop()

df = load_data(DATA_PATH)
latest_year = int(df["year"].max())
latest_df = df[df["year"] == latest_year].copy()

metric_options = {
    "Inflation CPI (%)": "inflation_cpi",
    "GDP Growth (%)": "gdp_growth",
    "Unemployment (%)": "unemployment",
}

selected_metric_label = st.selectbox("Select metric", list(metric_options.keys()))
selected_metric = metric_options[selected_metric_label]

col1, col2 = st.columns([1.4, 1])

with col1:
    map_df = latest_df.dropna(subset=[selected_metric]).copy()
    fig_map = px.choropleth(
        map_df,
        locations="country_code",
        color=selected_metric,
        hover_name="country_name",
        hover_data={
            "region": True,
            "income_level": True,
            selected_metric: ":.2f",
            "country_code": False,
        },
        color_continuous_scale="Viridis",
        projection="natural earth",
        title=f"{selected_metric_label} by country ({latest_year})",
    )
    fig_map.update_layout(height=650)
    st.plotly_chart(fig_map, use_container_width=True)

with col2:
    sort_desc = True if selected_metric != "gdp_growth" else False

    ranking_df = (
        latest_df[["country_name", "region", selected_metric]]
        .dropna()
        .sort_values(selected_metric, ascending=not sort_desc if False else not False)
    )

    if selected_metric == "gdp_growth":
        ranking_df = ranking_df.sort_values(selected_metric, ascending=False)
    else:
        ranking_df = ranking_df.sort_values(selected_metric, ascending=False)

    ranking_df = ranking_df.head(20)

    fig_rank = px.bar(
        ranking_df,
        x=selected_metric,
        y="country_name",
        orientation="h",
        title=f"Top 20 countries by {selected_metric_label}",
        labels={
            selected_metric: selected_metric_label,
            "country_name": "Country",
        },
    )
    fig_rank.update_layout(height=650, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_rank, use_container_width=True)

st.divider()

st.subheader("Ranking table")
table_df = (
    latest_df[["country_name", "country_code", "region", "income_level", selected_metric]]
    .dropna()
    .sort_values(selected_metric, ascending=False)
)
st.dataframe(table_df, use_container_width=True)