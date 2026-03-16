from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "data" / "processed"
OUTPUT_PATH = OUTPUT_DIR / "econ_option_a.parquet"

WORLD_BANK_API = "https://api.worldbank.org/v2"

INDICATORS: Dict[str, str] = {
    "inflation_cpi": "FP.CPI.TOTL.ZG",
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",
    "unemployment": "SL.UEM.TOTL.ZS",
}

START_YEAR = 2000
END_YEAR = 2025
PER_PAGE = 20000
TIMEOUT = 60


def fetch_json(url: str, params: dict | None = None) -> list:
    response = requests.get(url, params=params, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def fetch_country_metadata() -> pd.DataFrame:
    all_rows: List[dict] = []
    page = 1

    while True:
        data = fetch_json(
            f"{WORLD_BANK_API}/country",
            params={
                "format": "json",
                "per_page": 400,
                "page": page,
            },
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
                # IMPORTANT: use iso2Code here
                "country_code": row.get("iso2Code"),
                "country_name_meta": row.get("name"),
                "region": (row.get("region") or {}).get("value"),
                "income_level": (row.get("incomeLevel") or {}).get("value"),
                "lending_type": (row.get("lendingType") or {}).get("value"),
                "capital_city": row.get("capitalCity"),
                "longitude": row.get("longitude"),
                "latitude": row.get("latitude"),
            }
        )

    df = pd.DataFrame(records)

    # Keep only real countries, not aggregates
    df = df[df["region"].notna()].copy()
    df = df[df["region"] != "Aggregates"].copy()

    # Remove weird blanks if any
    df = df[df["country_code"].notna()].copy()
    df = df[df["country_code"] != ""].copy()

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
            },
        )

        meta, rows = data[0], data[1]
        all_rows.extend(rows)

        if page >= int(meta["pages"]):
            break
        page += 1

    records = []
    for row in all_rows:
        date_str = row.get("date")
        value = row.get("value")
        country = row.get("country", {}) or {}

        if date_str is None:
            continue

        try:
            year = int(date_str)
        except (TypeError, ValueError):
            continue

        if year < START_YEAR or year > END_YEAR:
            continue

        records.append(
            {
                # indicator endpoint country.id aligns with iso2Code
                "country_code": country.get("id"),
                "country_name": country.get("value"),
                "year": year,
                metric_name: value,
            }
        )

    return pd.DataFrame(records)


def build_dataset() -> pd.DataFrame:
    countries = fetch_country_metadata()
    print(f"Country metadata rows: {len(countries):,}")
    print("Country metadata sample codes:", countries["country_code"].dropna().unique()[:10])

    metric_frames = []
    for metric_name, indicator_code in INDICATORS.items():
        print(f"Fetching {metric_name} ({indicator_code}) ...")
        metric_df = fetch_indicator(indicator_code, metric_name)
        print(f"  -> rows fetched for {metric_name}: {len(metric_df):,}")
        metric_frames.append(metric_df)

    # Merge indicators together
    df = metric_frames[0]
    for other in metric_frames[1:]:
        df = df.merge(
            other,
            on=["country_code", "country_name", "year"],
            how="outer",
        )

    print(f"Rows after combining indicators: {len(df):,}")
    print("Indicator sample codes:", df["country_code"].dropna().unique()[:10])

    # Merge metadata only on country_code
    df = df.merge(countries, on="country_code", how="left")

    print(f"Rows after metadata merge: {len(df):,}")
    print(f"Rows with non-null region: {df['region'].notna().sum():,}")

    # Prefer indicator-side name, fallback to metadata
    df["country_name"] = df["country_name"].fillna(df["country_name_meta"])
    df = df.drop(columns=["country_name_meta"], errors="ignore")

    # Keep only real countries
    df = df[df["region"].notna()].copy()

    numeric_cols = ["inflation_cpi", "gdp_growth", "unemployment", "longitude", "latitude"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df[df["year"].notna()].copy()
    df["year"] = df["year"].astype(int)

    df = df.sort_values(["country_name", "year"]).reset_index(drop=True)

    return df


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = build_dataset()
    df.to_parquet(OUTPUT_PATH, index=False)

    print(f"Saved dataset to: {OUTPUT_PATH}")
    print(f"Rows: {len(df):,}")
    print(f"Countries: {df['country_code'].nunique():,}")
    if len(df) > 0:
        print(f"Year range: {df['year'].min()} - {df['year'].max()}")
    else:
        print("Year range: no data")


if __name__ == "__main__":
    main()