from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parents[1]
WB_PATH = BASE_DIR / "data" / "processed" / "econ_option_a.parquet"
OUT_PATH = BASE_DIR / "data" / "processed" / "global_economy.parquet"
MANIFEST_PATH = BASE_DIR / "data" / "processed" / "data_manifest.json"
IMF_API = "https://www.imf.org/external/datamapper/api/v1"

# IMF World Economic Outlook / DataMapper series used for current-year estimates
# and future projections. World Bank reported observations always take precedence.
IMF_SERIES = {
    "gdp_growth": "NGDP_RPCH",
    "inflation_cpi": "PCPIPCH",
    "unemployment": "LUR",
}

FORECAST_YEARS = list(range(2025, 2031))
TIMEOUT = 90
META_COLUMNS = [
    "iso3_code",
    "country_code",
    "country_name",
    "region",
    "income_level",
    "lending_type",
    "capital_city",
    "longitude",
    "latitude",
]


def fetch_imf_series(indicator: str) -> dict:
    periods = ",".join(map(str, FORECAST_YEARS))
    url = f"{IMF_API}/{indicator}?periods={periods}"
    response = requests.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    return payload.get("values", {}).get(indicator, {})


def annotate_world_bank(wb: pd.DataFrame) -> pd.DataFrame:
    wb = wb.copy()
    analytical = [
        c
        for c in wb.columns
        if c not in META_COLUMNS + ["year"] and pd.api.types.is_numeric_dtype(wb[c])
    ]

    wb["data_source"] = "World Bank WDI"
    wb["data_status"] = "reported"
    for metric in analytical:
        wb[f"{metric}_source"] = wb[metric].notna().map(
            {True: "World Bank WDI", False: None}
        )
        wb[f"{metric}_status"] = wb[metric].notna().map(
            {True: "reported", False: None}
        )
    return wb


def main() -> None:
    wb = pd.read_parquet(WB_PATH)
    if "iso3_code" not in wb.columns:
        raise ValueError("World Bank dataset must include iso3_code; run etl_worldbank.py first.")

    wb = annotate_world_bank(wb)

    country_meta = (
        wb.sort_values("year")
        .drop_duplicates("iso3_code", keep="last")[META_COLUMNS]
        .dropna(subset=["iso3_code"])
    )

    imf_series = {metric: fetch_imf_series(code) for metric, code in IMF_SERIES.items()}
    print("Fetched IMF WEO/DataMapper series.")

    # Index existing WDI country-year rows. The row is kept intact so all
    # development-domain indicators survive the IMF overlay.
    existing = {
        (row["iso3_code"], int(row["year"])): row.to_dict()
        for _, row in wb.iterrows()
        if pd.notna(row.get("iso3_code")) and pd.notna(row.get("year"))
    }

    for _, meta_row in country_meta.iterrows():
        iso3 = meta_row["iso3_code"]
        meta = meta_row.to_dict()

        for year in FORECAST_YEARS:
            key = (iso3, year)
            row = existing.get(key, {**meta, "year": year})

            for metric in IMF_SERIES:
                # Prefer official WDI reported values whenever they already exist.
                current = row.get(metric)
                if pd.notna(current):
                    row[f"{metric}_source"] = "World Bank WDI"
                    row[f"{metric}_status"] = "reported"
                    continue

                value = imf_series[metric].get(iso3, {}).get(str(year))
                if value is not None:
                    row[metric] = value
                    row[f"{metric}_source"] = "IMF WEO"
                    row[f"{metric}_status"] = "estimate/projection"

            # Summary row-level provenance is informational only; the web app uses
            # metric-level source/status for every displayed value.
            statuses = [
                row.get(f"{metric}_status")
                for metric in IMF_SERIES
                if row.get(metric) is not None
            ]
            sources = [
                row.get(f"{metric}_source")
                for metric in IMF_SERIES
                if row.get(metric) is not None
            ]
            if any(s == "estimate/projection" for s in statuses):
                row["data_status"] = "mixed/reported+projection" if "reported" in statuses else "projection"
            else:
                row["data_status"] = "reported"
            row["data_source"] = " + ".join(sorted(set(s for s in sources if s))) or "World Bank WDI"

            existing[key] = row

    combined = pd.DataFrame(existing.values())

    # Ensure every non-macro WDI metric still carries explicit provenance.
    base_cols = set(pd.read_parquet(WB_PATH).columns)
    analytical = [
        c
        for c in base_cols
        if c not in META_COLUMNS + ["year"] and c in combined.columns
    ]
    for metric in analytical:
        source_col = f"{metric}_source"
        status_col = f"{metric}_status"
        if source_col not in combined.columns:
            combined[source_col] = None
        if status_col not in combined.columns:
            combined[status_col] = None
        mask = combined[metric].notna() & combined[source_col].isna()
        combined.loc[mask, source_col] = "World Bank WDI"
        combined.loc[mask, status_col] = "reported"

    # Remove future placeholder rows for which no metric is available.
    metric_cols = [c for c in base_cols if c not in META_COLUMNS + ["year"] and c in combined.columns]
    metric_cols = [c for c in metric_cols if not c.endswith("_source") and not c.endswith("_status")]
    combined = combined[combined[metric_cols].notna().any(axis=1)].copy()

    combined["year"] = pd.to_numeric(combined["year"], errors="coerce").astype(int)
    combined = combined.sort_values(["country_name", "year"]).reset_index(drop=True)
    combined.to_parquet(OUT_PATH, index=False)

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "row_count": int(len(combined)),
        "country_count": int(combined["iso3_code"].nunique()),
        "year_min": int(combined["year"].min()),
        "year_max": int(combined["year"].max()),
        "sources": [
            {
                "name": "World Bank World Development Indicators",
                "short": "World Bank WDI",
                "role": "reported observations",
                "url": "https://api.worldbank.org/v2/",
            },
            {
                "name": "IMF World Economic Outlook / DataMapper",
                "short": "IMF WEO",
                "role": "estimates and projections for selected macroeconomic series",
                "url": "https://www.imf.org/external/datamapper/api/v1/",
            },
        ],
        "forecast_years": FORECAST_YEARS,
        "provenance_rule": "Metric-level source/status fields are authoritative. WDI reported observations take precedence; IMF WEO fills missing current/future macro values.",
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Saved multi-source dataset: {OUT_PATH}")
    print(f"Saved data manifest: {MANIFEST_PATH}")
    print(f"Rows: {len(combined):,}")
    for year in [2025, 2026, 2030]:
        part = combined[combined["year"] == year]
        print(f"{year}: {len(part):,} country/economy rows")
        for metric in IMF_SERIES:
            if metric in part.columns:
                n = part[metric].notna().sum()
                projected = (
                    part[f"{metric}_status"].astype(str).str.contains("projection", case=False).sum()
                    if f"{metric}_status" in part.columns
                    else 0
                )
                print(f"  {metric}: {n:,} values ({projected:,} estimates/projections)")


if __name__ == "__main__":
    main()
