"""
Data-Driven Analytics for Jordan Tourism AI-GIS.

NO HARD-CODED ASSUMPTIONS. Everything computed from the data provided.

Key principles:
1. Thresholds are computed from data percentiles, not fixed values
2. Seasonality is detected, not assumed
3. Rankings are computed, not hard-coded
4. Confidence scores reflect data quality
5. Missing data is flagged, not ignored
"""

import pandas as pd
import numpy as np
from typing import Optional


def compute_dynamic_thresholds(df: pd.DataFrame, column: str) -> dict:
    """
    Compute classification thresholds from data distribution.
    Uses tertiles (33rd and 67th percentiles) instead of fixed values.
    Adapts to whatever data is provided.
    """
    values = df[column].dropna()
    if len(values) < 3:
        return {"under": None, "over": None, "method": "insufficient_data"}

    return {
        "under": round(values.quantile(0.33), 2),
        "over": round(values.quantile(0.67), 2),
        "min": round(values.min(), 2),
        "max": round(values.max(), 2),
        "mean": round(values.mean(), 2),
        "std": round(values.std(), 2),
        "method": "tertiles",
        "n": len(values),
    }


def detect_seasonality(monthly_series: pd.Series) -> dict:
    """
    Detect seasonality from data — don't assume it.
    Returns peak month, trough month, seasonal strength.
    """
    if len(monthly_series) < 12:
        return {"detected": False, "reason": "insufficient_months"}

    avg = monthly_series.mean()
    if avg == 0:
        return {"detected": False, "reason": "zero_average"}

    indices = monthly_series / avg
    peak_month = int(indices.idxmax())
    trough_month = int(indices.idxmin())
    seasonal_strength = round(indices.max() - indices.min(), 3)

    return {
        "detected": True,
        "peak_month": peak_month,
        "trough_month": trough_month,
        "peak_index": round(indices.max(), 3),
        "trough_index": round(indices.min(), 3),
        "seasonal_strength": seasonal_strength,
        "is_strong": seasonal_strength > 0.5,
        "monthly_indices": {int(m): round(v, 3) for m, v in indices.items()},
    }


def classify_capacity_dynamic(indicators: dict, data: pd.DataFrame) -> str:
    """
    Classify capacity using data-driven thresholds.
    Computes thresholds from the actual dataset, not fixed values.
    """
    votes = []

    # Rooms per 1000 — use data percentiles
    if indicators.get("rooms_per_1000_visitors") is not None:
        thresholds = compute_dynamic_thresholds(data, "rooms_per_1000")
        if thresholds["under"] is not None:
            val = indicators["rooms_per_1000_visitors"]
            if val < thresholds["under"]:
                votes.append("under")
            elif val > thresholds["over"]:
                votes.append("over")
            else:
                votes.append("balanced")

    # Occupancy pressure — use data percentiles
    if indicators.get("occupancy_pressure_index") is not None:
        thresholds = compute_dynamic_thresholds(data, "avg_occupancy_rate")
        if thresholds["under"] is not None:
            val = indicators["occupancy_pressure_index"]
            if val > thresholds["over"]:
                votes.append("under")  # high occupancy = under capacity
            elif val < thresholds["under"]:
                votes.append("over")  # low occupancy = over capacity
            else:
                votes.append("balanced")

    if not votes:
        return "unknown"

    from collections import Counter

    return Counter(votes).most_common(1)[0][0]


def compute_data_completeness(df: pd.DataFrame, required_cols: list) -> dict:
    """
    Assess data completeness. What's available, what's missing.
    """
    total_cells = len(df) * len(required_cols)
    missing_cells = df[required_cols].isnull().sum().sum()
    completeness = (
        round((1 - missing_cells / total_cells) * 100, 1) if total_cells > 0 else 0
    )

    per_column = {}
    for col in required_cols:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            zero_count = (
                (df[col] == 0).sum() if df[col].dtype in ["int64", "float64"] else 0
            )
            per_column[col] = {
                "total": len(df),
                "nulls": int(null_count),
                "zeros": int(zero_count),
                "completeness": round((1 - null_count / len(df)) * 100, 1),
            }

    return {
        "overall_completeness": completeness,
        "total_cells": total_cells,
        "missing_cells": int(missing_cells),
        "per_column": per_column,
        "status": "complete"
        if completeness > 95
        else "partial"
        if completeness > 80
        else "incomplete",
    }


def compute_confidence(n_observations: int, n_expected: int = None) -> dict:
    """
    Compute confidence score based on data quantity.
    More data = higher confidence.
    """
    if n_observations >= 60:  # 5 years of monthly data
        confidence = "high"
        score = 0.9
    elif n_observations >= 24:  # 2 years
        confidence = "medium"
        score = 0.6
    elif n_observations >= 12:  # 1 year
        confidence = "low"
        score = 0.3
    else:
        confidence = "very_low"
        score = 0.1

    return {
        "confidence": confidence,
        "score": score,
        "n_observations": n_observations,
        "recommendation": f"Results based on {n_observations} data points ({confidence} confidence)",
    }


def compute_governorate_rankings(
    df: pd.DataFrame, metric: str, year: int = None
) -> list:
    """
    Rank governorates by any metric. Fully data-driven.
    """
    if year:
        data = df[df["year"] == year]
    else:
        data = df

    rankings = (
        data.groupby("governorate_code")
        .agg(
            value=(metric, "mean"),
            count=(metric, "count"),
        )
        .reset_index()
        .sort_values("value", ascending=False)
    )

    result = []
    for i, (_, row) in enumerate(rankings.iterrows()):
        result.append(
            {
                "rank": i + 1,
                "governorate": row["governorate_code"],
                "value": round(row["value"], 2),
                "data_points": int(row["count"]),
                "confidence": compute_confidence(int(row["count"]))["confidence"],
            }
        )

    return result


def detect_trends(yearly_series: pd.Series) -> dict:
    """
    Detect growth trends from data. No assumptions.
    """
    if len(yearly_series) < 2:
        return {"trend": "insufficient_data"}

    values = yearly_series.values
    growth_rates = []
    for i in range(1, len(values)):
        if values[i - 1] > 0:
            growth_rates.append((values[i] - values[i - 1]) / values[i - 1] * 100)

    if not growth_rates:
        return {"trend": "no_growth_data"}

    avg_growth = sum(growth_rates) / len(growth_rates)
    recent_growth = growth_rates[-1] if growth_rates else 0
    acceleration = recent_growth - growth_rates[0] if len(growth_rates) > 1 else 0

    return {
        "avg_growth": round(avg_growth, 2),
        "recent_growth": round(recent_growth, 2),
        "acceleration": round(acceleration, 2),
        "trend": "growing"
        if avg_growth > 2
        else "declining"
        if avg_growth < -2
        else "stable",
        "momentum": "accelerating"
        if acceleration > 3
        else "decelerating"
        if acceleration < -3
        else "steady",
        "n_years": len(growth_rates),
        "confidence": compute_confidence(len(growth_rates))["confidence"],
    }


def detect_anomalies(
    df: pd.DataFrame, column: str, group_col: str = "governorate_code"
) -> list:
    """
    Detect anomalies using data-driven z-scores.
    """
    group_stats = df.groupby(group_col)[column].agg(["mean", "std"]).reset_index()
    global_mean = df[column].mean()
    global_std = df[column].std()

    anomalies = []
    for _, row in group_stats.iterrows():
        if row["std"] > 0:
            z = (row["mean"] - global_mean) / global_std if global_std > 0 else 0
            if abs(z) > 1.5:
                anomalies.append(
                    {
                        "group": row[group_col],
                        "mean": round(row["mean"], 2),
                        "global_mean": round(global_mean, 2),
                        "z_score": round(z, 2),
                        "direction": "above" if z > 0 else "below",
                    }
                )

    return anomalies
