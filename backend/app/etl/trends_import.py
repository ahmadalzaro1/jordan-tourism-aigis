"""
Google Trends Data Connector for Jordan Tourism AI-GIS.

Fetches search interest for tourism-related keywords in Jordan.
Free API via pytrends (unofficial Google Trends API).

Keywords tracked:
- "travel Jordan"
- "visit Petra"
- "Jordan tourism"
- "Wadi Rum"
- "Aqaba"
- "Dead Sea Jordan"
"""

import os
import pandas as pd
from datetime import datetime

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "trends",
)

KEYWORDS = [
    "travel Jordan",
    "visit Petra",
    "Jordan tourism",
    "Wadi Rum",
    "Aqaba Jordan",
    "Dead Sea Jordan",
]


def fetch_trends(keywords=None, geo="JO", timeframe="2020-01-01 2025-12-31"):
    """
    Fetch Google Trends data for Jordan tourism keywords.
    Requires: pip install pytrends
    """
    try:
        from pytrends.request import TrendReq
    except ImportError:
        print("pytrends not installed. Run: pip install pytrends")
        return None

    if keywords is None:
        keywords = KEYWORDS

    pytrends = TrendReq(hl="en-US", tz=360)

    all_data = []
    # Google Trends limits to 5 keywords per request
    for i in range(0, len(keywords), 5):
        batch = keywords[i : i + 5]
        try:
            pytrends.build_payload(batch, cat=0, timeframe=timeframe, geo=geo)
            df = pytrends.interest_over_time()
            if not df.empty:
                df = df.reset_index()
                df = df.drop(columns=["isPartial"], errors="ignore")
                all_data.append(df)
        except Exception as e:
            print(f"  Error fetching trends for {batch}: {e}")

    if all_data:
        # Merge all batches
        combined = all_data[0]
        for df in all_data[1:]:
            combined = combined.merge(df, on="date", how="outer")

        # Save
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, "google_trends_jordan.csv")
        combined.to_csv(output_path, index=False)
        print(f"Saved {len(combined)} records to {output_path}")
        return combined

    return None


def load_cached_trends():
    """Load cached Google Trends data."""
    csv_path = os.path.join(OUTPUT_DIR, "google_trends_jordan.csv")
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return None


def compute_search_interest_correlation(trends_df, visitor_df):
    """
    Correlate Google search interest with actual visitor data.
    Returns correlation coefficients for each keyword.
    """
    if trends_df is None or visitor_df is None:
        return None

    # Merge on date
    trends_df["date"] = pd.to_datetime(trends_df["date"])
    trends_df["year"] = trends_df["date"].dt.year
    trends_df["month"] = trends_df["date"].dt.month

    monthly_visitors = (
        visitor_df.groupby(["year", "month"])["total_visitors"].sum().reset_index()
    )

    merged = trends_df.merge(monthly_visitors, on=["year", "month"], how="inner")

    # Correlate each keyword with visitors
    correlations = {}
    for col in trends_df.columns:
        if col not in ["date", "year", "month"] and col in merged.columns:
            corr = merged[col].corr(merged["total_visitors"])
            correlations[col] = round(corr, 3) if not pd.isna(corr) else 0

    return correlations


if __name__ == "__main__":
    print("Fetching Google Trends data for Jordan tourism...")
    df = fetch_trends()
    if df is not None:
        print(f"\nColumns: {list(df.columns)}")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    else:
        print("No data fetched. Install pytrends: pip install pytrends")
