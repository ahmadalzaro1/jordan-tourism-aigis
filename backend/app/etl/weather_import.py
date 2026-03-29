"""
Weather Data Connector for Jordan Tourism AI-GIS.

Source: Open-Meteo (free, no API key needed)
https://open-meteo.com

Fetches monthly historical weather for each Jordan governorate:
- Temperature (avg, max, min)
- Rainfall
- Sunshine hours

This data is used to correlate weather with tourism demand patterns.
"""

import requests
import pandas as pd
import os
import json
from datetime import datetime

# Governorate coordinates for weather API
GOVERNORATE_COORDS = {
    "AMM": {"lat": 31.9454, "lng": 35.9284, "name": "Amman"},
    "IRB": {"lat": 32.5556, "lng": 35.8500, "name": "Irbid"},
    "ZAR": {"lat": 32.0728, "lng": 36.0880, "name": "Zarqa"},
    "MAF": {"lat": 32.3428, "lng": 36.2080, "name": "Mafraq"},
    "JER": {"lat": 32.2806, "lng": 35.8994, "name": "Jerash"},
    "AJL": {"lat": 32.3325, "lng": 35.7517, "name": "Ajloun"},
    "BAL": {"lat": 31.7500, "lng": 35.5500, "name": "Dead Sea"},
    "MAD": {"lat": 31.7167, "lng": 35.8000, "name": "Madaba"},
    "KAR": {"lat": 31.1853, "lng": 35.7047, "name": "Karak"},
    "TAF": {"lat": 30.8400, "lng": 35.6000, "name": "Tafilah"},
    "MAA": {"lat": 30.3285, "lng": 35.4444, "name": "Petra"},
    "AQAB": {"lat": 29.5321, "lng": 35.0063, "name": "Aqaba"},
}

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "weather",
)


def fetch_weather(gov_code, start_date="2020-01-01", end_date=None):
    """
    Fetch monthly historical weather for a governorate from Open-Meteo.
    Free API, no key needed.
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    coords = GOVERNORATE_COORDS.get(gov_code)
    if not coords:
        return None

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": coords["lat"],
        "longitude": coords["lng"],
        "start_date": start_date,
        "end_date": end_date,
        "monthly": "temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum,sunshine_duration",
        "timezone": "Asia/Amman",
    }

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if "monthly" not in data:
            return None

        df = pd.DataFrame(
            {
                "date": data["monthly"]["time"],
                "temp_mean": data["monthly"].get("temperature_2m_mean", []),
                "temp_max": data["monthly"].get("temperature_2m_max", []),
                "temp_min": data["monthly"].get("temperature_2m_min", []),
                "precipitation_mm": data["monthly"].get("precipitation_sum", []),
                "sunshine_hours": [
                    s / 3600 if s else 0
                    for s in data["monthly"].get("sunshine_duration", [])
                ],
            }
        )

        df["governorate_code"] = gov_code
        df["year"] = pd.to_datetime(df["date"]).dt.year
        df["month"] = pd.to_datetime(df["date"]).dt.month

        return df

    except Exception as e:
        print(f"  Error fetching weather for {gov_code}: {e}")
        return None


def fetch_all_governorates(start_date="2020-01-01", end_date=None):
    """Fetch weather for all 12 governorates."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_data = []
    for gov_code in GOVERNORATE_COORDS:
        print(
            f"  Fetching weather for {gov_code} ({GOVERNORATE_COORDS[gov_code]['name']})..."
        )
        df = fetch_weather(gov_code, start_date, end_date)
        if df is not None:
            all_data.append(df)
            print(f"    Got {len(df)} months")

    if all_data:
        combined = pd.concat(all_data, ignore_index=True)

        # Save to CSV
        output_path = os.path.join(OUTPUT_DIR, "jordan_weather_monthly.csv")
        combined.to_csv(output_path, index=False)
        print(f"\nSaved {len(combined)} records to {output_path}")

        return combined

    return None


def get_weather_for_governorate(gov_code):
    """Load cached weather data for a governorate."""
    csv_path = os.path.join(OUTPUT_DIR, "jordan_weather_monthly.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        return df[df["governorate_code"] == gov_code]
    return None


if __name__ == "__main__":
    print("Fetching Jordan weather data from Open-Meteo...")
    df = fetch_all_governorates()
    if df is not None:
        print(f"\nSummary:")
        print(f"  Records: {len(df)}")
        print(f"  Governorates: {df['governorate_code'].nunique()}")
        print(f"  Date range: {df['year'].min()}-{df['year'].max()}")
        print(
            f"  Avg temp range: {df['temp_min'].mean():.1f}°C to {df['temp_max'].mean():.1f}°C"
        )
