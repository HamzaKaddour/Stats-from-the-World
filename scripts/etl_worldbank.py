from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "data" / "processed"
OUTPUT_PATH = OUTPUT_DIR / "econ_option_a.parquet"

WORLD_BANK_API = "https://api.worldbank.org/v2"

# A compact development-data layer spanning the domains shown in the web app.
# All series are official World Bank World Development Indicators (WDI).
INDICATORS: Dict[str, str] = {
    # Economy
    "inflation_cpi": "FP.CPI.TOTL.ZG",
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",
    "unemployment": "SL.UEM.TOTL.ZS",
    "gdp_per_capita": "NY.GDP.PCAP.CD",
    # People
    "population": "SP.POP.TOTL",
    "life_expectancy": "SP.DYN.LE00.IN",
    "youth_unemployment": "SL.UEM.1524.ZS",
    "secondary_enrollment": "SE.SEC.ENRR",
    # Poverty & shared prosperity
    "gini": "SI.POV.GINI",
    "poverty_national": "SI.POV.NAHC",
    # Climate & environment
    "co2_per_capita": "EN.GHG.CO2.PC.CE.AR5",
    "renewable_energy": "EG.FEC.RNEW.ZS",
    "forest_area": "AG.LND.FRST.ZS",
    # Infrastructure & basic services
    "electricity_access": "EG.ELC.ACCS.ZS",
    "drinking_water_basic": "SH.H2O.BASW.ZS",
    "sanitation_basic": "SH.STA.BASS.ZS",
    # Digital connectivity
    "internet_users": "IT.NET.USER.ZS",
    "mobile_subscriptions": "IT.CEL.SETS.P2",
    "fixed_broadband": "IT.NET.BBND.P2",
}

START_YEAR = 2000
END_YEAR = datetime.now(timezone.utc).year
PER_PAGE = 20000
TIMEOUT = 90


def fetch_json(url: str, params: dict | None = None) -> list:
    response = requests.get(url, params=params, timeout=TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError(f"Unexpected World Bank API response from {url}")
    return payload


def fetch_country_metadata() -> pd.DataFrame:
    all_rows: List[dict] = []
    page = 1

    while True:
        data = fetch_json(
            f"{WORLD_BANK_API}/country",
            params={"format": "json", "per_page": 400, "page": page},
        )
        meta, rows = data[0], data[1]
        all_rows.extend(rows)

        if page >= int(meta["pages"]):
            break
        page += 1

    records = []
    for row in all_rows:
        records.append(
            {
                "country_code": row.get("iso2Code"),
                "iso3_code": row.get("id"),
                "country_name": row.get("name"),
                "region": (row.get("region") or {}).get("value"),
                "income_level": (row.get("incomeLevel") or {}).get("value"),
                "lending_type": (row.get("lendingType") or {}).get("value"),
                "capital_city": row.get("capitalCity"),
                "longitude": row.get("longitude"),
                "latitude": row.get("latitude"),
            }
        )

    df = pd.DataFrame(records)
    df = df[df["region"].notna() & (df["region"] != "Aggregates")].copy()
    df = df[df["country_code"].notna() & (df["country_code"] != "")].copy()
    return df


def fetch_indicator(indicator_code: str, metric_name: str) -> pd.DataFrame:
    all_rows: List[dict] = []
    page = 1

    while True:
        data = fetch_json(
            f"{WORLD_BANK_API}/country/all/indicator/{indicator_code}",
            params={
                "format": "json",
                "per_page": PER_PAGE,
                "page": page,
                "date": f"{START_YEAR}:{END_YEAR}",
            },
        )
        meta, rows = data[0], data[1]
        all_rows.extend(rows)

        if page >= int(meta["pages"]):
            break
        page += 1

    records = []
    for row in all_rows:
        country = row.get("country", {}) or {}
        try:
            year = int(row.get("date"))
        except (TypeError, ValueError):
            continue

        records.append(
            {
                "country_code": country.get("id"),
                "year": year,
                metric_name: row.get("value"),
            }
        )

    return pd.DataFrame(records)


def build_dataset() -> pd.DataFrame:
    countries = fetch_country_metadata()
    print(f"Country metadata rows: {len(countries):,}")

    # Begin with a complete country/year frame. This preserves years even when a
    # particular indicator is missing and makes coverage analysis deterministic.
    years = pd.DataFrame({"year": range(START_YEAR, END_YEAR + 1)})
    countries["_join_key"] = 1
    years["_join_key"] = 1
    df = countries.merge(years, on="_join_key", how="outer").drop(columns="_join_key")

    for metric_name, indicator_code in INDICATORS.items():
        print(f"Fetching {metric_name} ({indicator_code}) ...")
        metric_df = fetch_indicator(indicator_code, metric_name)
        print(f"  -> rows: {len(metric_df):,}; non-null: {metric_df[metric_name].notna().sum():,}")
        df = df.merge(metric_df, on=["country_code", "year"], how="left")

    numeric_cols = list(INDICATORS) + ["longitude", "latitude"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df = df[df["year"].notna()].copy()
    df["year"] = df["year"].astype(int)

    # Drop country-years with no analytical observation at all. Country metadata
    # remains available through every retained observation.
    df = df[df[list(INDICATORS)].notna().any(axis=1)].copy()
    df = df.sort_values(["country_name", "year"]).reset_index(drop=True)
    return df


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = build_dataset()
    df.to_parquet(OUTPUT_PATH, index=False)

    required = {"country_code", "iso3_code", "country_name", "year", *INDICATORS.keys()}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if df.empty or df["country_code"].nunique() < 150:
        raise ValueError("Dataset validation failed: unexpectedly low country coverage")
    if df["year"].max() < datetime.now(timezone.utc).year - 2:
        raise ValueError("Dataset validation failed: data appears stale")

    print(f"Saved validated dataset to: {OUTPUT_PATH}")
    print(f"Rows: {len(df):,}")
    print(f"Countries/economies: {df['country_code'].nunique():,}")
    print(f"Year range: {df['year'].min()} - {df['year'].max()}")
    for metric in INDICATORS:
        print(f"{metric}: {df[metric].notna().sum():,} observations")


if __name__ == "__main__":
    main()
