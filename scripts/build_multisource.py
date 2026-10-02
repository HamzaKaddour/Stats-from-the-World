from __future__ import annotations

from pathlib import Path
import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parents[1]
WB_PATH = BASE_DIR / "data" / "processed" / "econ_option_a.parquet"
OUT_PATH = BASE_DIR / "data" / "processed" / "global_economy.parquet"
IMF_API = "https://www.imf.org/external/datamapper/api/v1"

# IMF WEO/DataMapper series. Values for the current/future period are estimates/projections.
IMF_SERIES = {
    "gdp_growth": "NGDP_RPCH",
    "inflation_cpi": "PCPIPCH",
    "unemployment": "LUR",
}
YEARS = [2025, 2026, 2027, 2028, 2029, 2030]
TIMEOUT = 90


def fetch_imf_series(indicator: str) -> dict:
    periods = ",".join(map(str, YEARS))
    url = f"{IMF_API}/{indicator}?periods={periods}"
    response = requests.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    return payload.get("values", {}).get(indicator, {})


def main() -> None:
    wb = pd.read_parquet(WB_PATH)
    if "iso3_code" not in wb.columns:
        raise ValueError("World Bank dataset must include iso3_code; run etl_worldbank.py first.")

    # Explicit provenance: WDI rows are reported observations where available.
    wb["data_source"] = "World Bank WDI"
    wb["data_status"] = "reported"
    for metric in IMF_SERIES:
        wb[f"{metric}_source"] = wb[metric].notna().map({True: "World Bank WDI", False: None})
        wb[f"{metric}_status"] = wb[metric].notna().map({True: "reported", False: None})

    country_meta = (
        wb.sort_values("year")
        .drop_duplicates("iso3_code", keep="last")
        [["iso3_code", "country_code", "country_name", "region", "income_level",
          "lending_type", "capital_city", "longitude", "latitude"]]
    )

    # One future/current row per IMF country-year. Metrics remain individually sourced.
    future = []
    series = {metric: fetch_imf_series(code) for metric, code in IMF_SERIES.items()}
    for iso3 in country_meta["iso3_code"].dropna().unique():
        meta = country_meta[country_meta["iso3_code"] == iso3].iloc[0].to_dict()
        for year in YEARS:
            row = {**meta, "year": year, "data_source": "IMF WEO", "data_status": "projection"}
            has_value = False
            for metric, code in IMF_SERIES.items():
                value = series[metric].get(iso3, {}).get(str(year))
                if value is not None:
                    has_value = True
                    row[metric] = value
                    row[f"{metric}_source"] = "IMF WEO"
                    row[f"{metric}_status"] = "estimate/projection"
                else:
                    row[metric] = None
                    row[f"{metric}_source"] = None
                    row[f"{metric}_status"] = None
            if has_value:
                future.append(row)

    imf = pd.DataFrame(future)

    # For 2025+, prefer WDI reported values metric-by-metric; fill missing fields from IMF.
    historical = wb[wb["year"] < 2025].copy()
    recent_wb = wb[wb["year"] >= 2025].copy()
    if imf.empty:
        combined = wb
    else:
        keys = ["iso3_code", "year"]
        merged = imf.merge(
            recent_wb[keys + list(IMF_SERIES.keys())],
            on=keys, how="left", suffixes=("", "_wdi")
        )
        for metric in IMF_SERIES:
            reported = merged[f"{metric}_wdi"].notna()
            merged.loc[reported, metric] = merged.loc[reported, f"{metric}_wdi"]
            merged.loc[reported, f"{metric}_source"] = "World Bank WDI"
            merged.loc[reported, f"{metric}_status"] = "reported"
            merged.drop(columns=[f"{metric}_wdi"], inplace=True)
        combined = pd.concat([historical, merged], ignore_index=True, sort=False)

    combined = combined.sort_values(["country_name", "year"]).reset_index(drop=True)
    combined.to_parquet(OUT_PATH, index=False)

    print(f"Saved multi-source dataset: {OUT_PATH}")
    print(f"Rows: {len(combined):,}")
    for year in [2025, 2026]:
        part = combined[combined["year"] == year]
        print(f"{year}: {len(part):,} country rows")
        for metric in IMF_SERIES:
            print(f"  {metric}: {part[metric].notna().sum():,} values")


if __name__ == "__main__":
    main()
