from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Macro Dashboard", page_icon="📈", layout="wide")

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "processed" / "econ_option_a.parquet"


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["year"] = df["year"].astype(int)
    return df


st.title("📈 Macro Dashboard")

if not DATA_PATH.exists():
    st.warning("Dataset not found. Run `python scripts/etl_worldbank.py` first.")
    st.stop()

df = load_data(DATA_PATH)

countries = sorted(df["country_name"].dropna().unique().tolist())
default_country = "United States" if "United States" in countries else countries[0]

selected_country = st.selectbox("Select country", countries, index=countries.index(default_country))

country_df = df[df["country_name"] == selected_country].sort_values("year").copy()
latest_row = country_df.loc[country_df["year"].idxmax()]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Latest Year", int(latest_row["year"]))
c2.metric(
    "Inflation CPI",
    f"{latest_row['inflation_cpi']:.2f}%" if pd.notna(latest_row["inflation_cpi"]) else "N/A",
)
c3.metric(
    "GDP Growth",
    f"{latest_row['gdp_growth']:.2f}%" if pd.notna(latest_row["gdp_growth"]) else "N/A",
)
c4.metric(
    "Unemployment",
    f"{latest_row['unemployment']:.2f}%" if pd.notna(latest_row["unemployment"]) else "N/A",
)

st.divider()

metric_map = {
    "Inflation CPI (%)": "inflation_cpi",
    "GDP Growth (%)": "gdp_growth",
    "Unemployment (%)": "unemployment",
}

selected_metrics = st.multiselect(
    "Select metrics to plot",
    list(metric_map.keys()),
    default=["Inflation CPI (%)", "GDP Growth (%)", "Unemployment (%)"],
)

if selected_metrics:
    plot_df = country_df[["year"]].copy()

    for label in selected_metrics:
        col = metric_map[label]
        plot_df[label] = country_df[col].values

    long_df = plot_df.melt(
        id_vars="year",
        var_name="Metric",
        value_name="Value",
    )

    fig = px.line(
        long_df,
        x="year",
        y="Value",
        color="Metric",
        markers=True,
        title=f"Macro trends for {selected_country}",
    )
    fig.update_layout(height=550)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Raw time series")
st.dataframe(
    country_df[
        ["country_name", "region", "income_level", "year", "inflation_cpi", "gdp_growth", "unemployment"]
    ].sort_values("year", ascending=False),
    use_container_width=True,
)