# 🌍 Global Economy Dashboard

An interactive, multi-dashboard analytics application built with **Python, Streamlit, and Plotly**, using **World Bank World Development Indicators (WDI)** to explore global economic trends, country comparisons, and composite economic health.

This project demonstrates end-to-end skills in **data engineering, analytics, and visualization**, packaged as a deployable, portfolio-grade web application.

---

## 🚀 Live Demo
The dashboard is deployed as a **Streamlit app on Hugging Face Spaces** (free hosting).

🔗 **Live Demo:**  
https://huggingface.co/spaces/<your-username>/global-economy-dashboard


---

## 📊 What This Project Does

The Global Economy Dashboard allows users to:

- Explore **macroeconomic trends** by country and year
- Analyze **cost-of-living and affordability proxies**
- Rank countries globally and visualize results on **interactive world maps**
- Build a **composite economic health index** from multiple indicators
- Download filtered datasets directly from the UI

The application is designed to resemble real-world analytics tools used by:
- policy analysts  
- economists  
- international organizations  
- data science teams  

---

## 🧭 Dashboards Overview

### 🏠 Home
Landing page explaining the project scope, data source, and how to navigate the dashboards.

---

### 📈 Macro Dashboard (Option A)
**Country-level macroeconomic analysis**
- Inflation (CPI, %)
- GDP growth (%)
- Unemployment (%)
- KPI snapshots (latest year)
- Interactive time-series plots
- Indicator comparison tables

---

### 🧺 Cost of Living & Affordability (Option B)
**Inflation impact and affordability-focused views**
- Inflation trends
- GDP per capita
- Exchange rate indicators
- Inflation vs GDP-per-capita scatter (global affordability proxy)
- Country highlights and comparisons
- CSV export of filtered data

---

### 🗺️ Global Rankings & Map
**Cross-country comparison for any indicator**
- Top / Bottom country rankings
- Horizontal bar charts
- Full-width interactive choropleth world map
- Log-scale toggle for skewed indicators
- Data coverage statistics
- Indicator-year CSV downloads

---

### 🧠 Global Economic Health Index (Option C)
**Composite economic “health” view**
- Built from GDP growth, inflation, and unemployment
- Z-score normalization
- Adjustable weights (if enabled)
- Global rankings and world map
- Country-level component breakdown

---

## 📚 Data Source

**World Bank – World Development Indicators (WDI)**  
https://databank.worldbank.org/source/world-development-indicators

Data is retrieved using the **World Bank Indicators API**, processed via a custom ETL pipeline, and stored locally in Parquet format for fast loading.

---

## 🏗️ Project Structure

