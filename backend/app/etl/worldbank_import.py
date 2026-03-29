"""
World Bank Data Connector for Jordan Tourism AI-GIS.

Source: World Bank Open Data API (free, no key needed)
https://data.worldbank.org

Fetches economic indicators for Jordan:
- GDP (current US$)
- GDP growth (%)
- Tourism receipts (% of total exports)
- International arrivals
- Inflation (CPI)
- Unemployment rate
- Exchange rate (USD)
"""

import requests
import pandas as pd
import os

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "economic",
)

# World Bank indicator codes
INDICATORS = {
    "NY.GDP.MKTP.CD": "gdp_usd",
    "NY.GDP.MKTP.KD.ZG": "gdp_growth_pct",
    "ST.INT.RCPT.XP.ZS": "tourism_receipts_pct_exports",
    "ST.INT.ARVL": "international_arrivals",
    "FP.CPI.TOTL.ZG": "inflation_pct",
    "SL.UEM.TOTL.ZS": "unemployment_pct",
    "PA.NUS.FCRF": "exchange_rate_usd",
}


def fetch_world_bank_data(country_code="JO", start_year=2010, end_year=2025):
    """
    Fetch World Bank indicators for Jordan.
    Free API, no key needed.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_data = {}

    for indicator_code, indicator_name in INDICATORS.items():
        url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator_code}"
        params = {
            "date": f"{start_year}:{end_year}",
            "format": "json",
            "per_page": 100,
        }

        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            if len(data) > 1 and data[1]:
                records = []
                for entry in data[1]:
                    if entry["value"] is not None:
                        records.append(
                            {
                                "year": int(entry["date"]),
                                "indicator": indicator_name,
                                "value": entry["value"],
                            }
                        )
                all_data[indicator_name] = records
                print(f"  {indicator_name}: {len(records)} years")

        except Exception as e:
            print(f"  Error fetching {indicator_name}: {e}")

    # Combine into single DataFrame
    if all_data:
        frames = []
        for indicator, records in all_data.items():
            frames.append(pd.DataFrame(records))

        combined = pd.concat(frames, ignore_index=True)
        pivot = combined.pivot_table(
            index="year", columns="indicator", values="value", aggfunc="first"
        )
        pivot = pivot.reset_index()

        output_path = os.path.join(OUTPUT_DIR, "jordan_economic_indicators.csv")
        pivot.to_csv(output_path, index=False)
        print(f"\nSaved to {output_path}")

        return pivot

    return None


def load_cached_economic():
    """Load cached economic data."""
    csv_path = os.path.join(OUTPUT_DIR, "jordan_economic_indicators.csv")
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return None


if __name__ == "__main__":
    print("Fetching World Bank data for Jordan...")
    df = fetch_world_bank_data()
    if df is not None:
        print(f"\nIndicators available:")
        for col in df.columns:
            non_null = df[col].notna().sum()
            print(f"  {col}: {non_null} years of data")
