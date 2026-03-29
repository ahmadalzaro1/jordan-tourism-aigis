"""
AutoResearch Loop for Jordan Tourism AI-GIS.

Inspired by karpathy/autoresearch:
- Fixed evaluation budget
- Single metric to optimize
- Agent modifies analytics config → runs → evaluates → keeps or discards
- Overnight: ~100 experiments while you sleep

Instead of training neural networks, we're doing:
- Statistical hypothesis testing on tourism data
- Correlation discovery between indicators
- Feature importance analysis
- Threshold optimization for classification
- Forecast model selection
- Assumption validation

The DATA tells us what the project should look like.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from itertools import product
from datetime import datetime
import json

SAMPLE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "sample",
)


def load_all_data():
    """Load all CSV datasets and merge into a single analysis-ready DataFrame."""
    visitors = pd.read_csv(os.path.join(SAMPLE_DIR, "visitors.csv"))
    occupancy = pd.read_csv(os.path.join(SAMPLE_DIR, "occupancy.csv"))

    # Merge on governorate + year + month
    merged = visitors.merge(
        occupancy,
        on=["governorate_code", "year", "month"],
        how="outer",
        suffixes=("_vis", "_occ"),
    )

    # Compute derived indicators
    merged["rooms_per_1000"] = (
        merged["total_rooms"] / merged["total_visitors"] * 1000
    ).replace([np.inf, -np.inf], np.nan)
    merged["beds_per_1000"] = (
        merged["total_beds"] / merged["total_visitors"] * 1000
    ).replace([np.inf, -np.inf], np.nan)
    merged["occupancy_pressure"] = (
        merged["avg_occupancy_rate"] * 0.6 + merged["avg_occupancy_rate"] * 1.3 * 0.4
    )
    merged["visitors_per_bed"] = (
        merged["total_visitors"] / merged["total_beds"]
    ).replace([np.inf, -np.inf], np.nan)
    merged["date"] = pd.to_datetime(
        merged["year"].astype(str)
        + "-"
        + merged["month"].astype(str).str.zfill(2)
        + "-01"
    )

    return merged


def experiment_correlation_analysis(df):
    """
    Experiment: Find which variables correlate most strongly with visitor demand.
    This tells us what data actually drives tourism.
    """
    numeric_cols = [
        "total_visitors",
        "international_visitors",
        "domestic_visitors",
        "avg_occupancy_rate",
        "total_rooms",
        "total_beds",
        "rooms_per_1000",
        "beds_per_1000",
        "occupancy_pressure",
        "visitors_per_bed",
    ]

    available = [c for c in numeric_cols if c in df.columns]
    corr_matrix = df[available].corr()

    # Find strongest correlations with total_visitors
    visitor_corrs = (
        corr_matrix["total_visitors"]
        .drop("total_visitors")
        .sort_values(key=abs, ascending=False)
    )

    findings = []
    for var, corr in visitor_corrs.items():
        strength = (
            "strong" if abs(corr) > 0.7 else "moderate" if abs(corr) > 0.4 else "weak"
        )
        findings.append(
            {
                "variable": var,
                "correlation": round(corr, 3),
                "strength": strength,
                "interpretation": _interpret_correlation(var, corr),
            }
        )

    return {
        "experiment": "correlation_analysis",
        "metric": "strongest_correlation",
        "value": round(abs(visitor_corrs.iloc[0]), 3),
        "findings": findings,
        "top_3": [f["variable"] for f in findings[:3]],
    }


def experiment_seasonality_analysis(df):
    """
    Experiment: Quantify seasonality patterns.
    Which months are peak? Which governorates have strongest seasonality?
    """
    monthly = (
        df.groupby("month")
        .agg(
            avg_visitors=("total_visitors", "mean"),
            avg_occupancy=("avg_occupancy_rate", "mean"),
        )
        .reset_index()
    )

    # Seasonality index = peak month / average month
    avg_all = monthly["avg_visitors"].mean()
    monthly["seasonality_index"] = monthly["avg_visitors"] / avg_all

    peak_months = monthly.nlargest(3, "seasonality_index")
    trough_months = monthly.nsmallest(3, "seasonality_index")

    # Per-governorate seasonality
    gov_seasonality = (
        df.groupby("governorate_code")
        .agg(
            cv=("total_visitors", lambda x: x.std() / x.mean() if x.mean() > 0 else 0),
        )
        .reset_index()
        .sort_values("cv", ascending=False)
    )

    return {
        "experiment": "seasonality_analysis",
        "metric": "seasonality_strength",
        "value": round(monthly["seasonality_index"].max(), 2),
        "peak_months": [
            {"month": int(r.month), "index": round(r.seasonality_index, 2)}
            for _, r in peak_months.iterrows()
        ],
        "trough_months": [
            {"month": int(r.month), "index": round(r.seasonality_index, 2)}
            for _, r in trough_months.iterrows()
        ],
        "most_seasonal_gov": gov_seasonality.head(3)["governorate_code"].tolist(),
        "least_seasonal_gov": gov_seasonality.tail(3)["governorate_code"].tolist(),
    }


def experiment_capacity_classification_sensitivity(df):
    """
    Experiment: Test different classification thresholds and see how they affect results.
    Which thresholds produce the most balanced classification?
    """
    from app.analytics.classification import classify_capacity
    from app.analytics.indicators import compute_indicators_for_period

    threshold_combos = [
        {"rooms_under": 3, "rooms_over": 15},
        {"rooms_under": 5, "rooms_over": 20},
        {"rooms_under": 8, "rooms_over": 25},
        {"rooms_under": 5, "rooms_over": 30},
    ]

    results = []
    for combo in threshold_combos:
        thresholds = {
            "rooms_per_1000": {
                "under": combo["rooms_under"],
                "over": combo["rooms_over"],
            },
            "beds_per_1000": {
                "under": combo["rooms_under"] * 1.6,
                "over": combo["rooms_over"] * 1.6,
            },
            "occupancy_pressure": {"under": 25, "over": 70},
            "capacity_adequacy": {"under": 0.7, "over": 1.5},
        }

        classifications = []
        for _, row in df[df["year"] == 2025].iterrows():
            ind = compute_indicators_for_period(
                int(row.get("total_rooms", 0)),
                int(row.get("total_beds", 0)),
                int(row.get("total_visitors", 0)),
                float(row.get("avg_occupancy_rate", 0)),
                float(row.get("avg_occupancy_rate", 0) * 1.3),
            )
            cls = classify_capacity(ind, thresholds)
            classifications.append(cls)

        counts = pd.Series(classifications).value_counts()
        balance_score = 1 - (
            counts.max() / counts.sum()
        )  # closer to 0.66 = more balanced

        results.append(
            {
                "thresholds": combo,
                "distribution": counts.to_dict(),
                "balance_score": round(balance_score, 3),
            }
        )

    best = max(results, key=lambda x: x["balance_score"])

    return {
        "experiment": "threshold_sensitivity",
        "metric": "balance_score",
        "value": best["balance_score"],
        "all_combos": results,
        "recommended": best["thresholds"],
    }


def experiment_governorate_clustering(df):
    """
    Experiment: Cluster governorates by tourism behavior.
    Which governorates behave similarly? What natural groupings exist?
    """
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    # Feature matrix per governorate
    gov_features = (
        df[df["year"] == 2025]
        .groupby("governorate_code")
        .agg(
            avg_visitors=("total_visitors", "mean"),
            avg_occupancy=("avg_occupancy_rate", "mean"),
            avg_rooms=("total_rooms", "mean"),
            avg_beds=("total_beds", "mean"),
            visitor_cv=(
                "total_visitors",
                lambda x: x.std() / x.mean() if x.mean() > 0 else 0,
            ),
        )
        .fillna(0)
    )

    scaler = StandardScaler()
    scaled = scaler.fit_transform(gov_features)

    # Try K=2 to K=5
    best_k = 3
    best_score = -1

    for k in range(2, 6):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(scaled)
        # Silhouette score
        from sklearn.metrics import silhouette_score

        score = silhouette_score(scaled, labels)
        if score > best_score:
            best_score = score
            best_k = k

    km = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    labels = km.fit_predict(scaled)

    clusters = {}
    for i, code in enumerate(gov_features.index):
        cluster_id = int(labels[i])
        if cluster_id not in clusters:
            clusters[cluster_id] = []
        clusters[cluster_id].append(code)

    return {
        "experiment": "governorate_clustering",
        "metric": "silhouette_score",
        "value": round(best_score, 3),
        "optimal_k": best_k,
        "clusters": clusters,
        "interpretation": f"Governorates naturally group into {best_k} clusters based on tourism behavior",
    }


def experiment_forecast_model_comparison(df):
    """
    Experiment: Compare ARIMA vs Prophet, different horizons, different orders.
    Which model+config gives lowest MAPE?
    """
    national = df.groupby(["year", "month"])["total_visitors"].sum().reset_index()

    configs = [
        {"model": "arima", "order": (1, 1, 1), "horizon": 12},
        {"model": "arima", "order": (2, 1, 2), "horizon": 12},
        {"model": "arima", "order": (1, 1, 1), "horizon": 6},
    ]

    results = []
    for config in configs:
        try:
            from app.analytics.forecasting import prepare_monthly_series, forecast_arima

            train = national[national["year"] <= 2024]
            test = national[national["year"] == 2025]

            train_df = prepare_monthly_series(
                [
                    {"year": r.year, "month": r.month, "total": r.total_visitors}
                    for _, r in train.iterrows()
                ]
            )

            forecast = forecast_arima(
                train_df, config["horizon"], order=tuple(config["order"])
            )

            actual = test["total_visitors"].values[: config["horizon"]]
            predicted = [f["predicted"] for f in forecast["forecast"][: len(actual)]]

            mape = np.mean(np.abs((actual - predicted) / actual)) * 100

            results.append(
                {
                    "config": config,
                    "mape": round(mape, 2),
                    "method": forecast.get("method"),
                }
            )
        except Exception as e:
            results.append({"config": config, "error": str(e)})

    # Also try Prophet
    try:
        from app.analytics.forecasting import forecast_best

        train = national[national["year"] <= 2024]
        test = national[national["year"] == 2025]

        train_df = prepare_monthly_series(
            [
                {"year": r.year, "month": r.month, "total": r.total_visitors}
                for _, r in train.iterrows()
            ]
        )

        forecast = forecast_best(train_df, 12)
        actual = test["total_visitors"].values
        predicted = [f["predicted"] for f in forecast["forecast"][: len(actual)]]
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100

        results.append(
            {
                "config": {"model": "prophet", "horizon": 12},
                "mape": round(mape, 2),
                "method": "prophet",
            }
        )
    except Exception as e:
        results.append({"config": {"model": "prophet"}, "error": str(e)})

    best = min(results, key=lambda x: x.get("mape", 999))

    return {
        "experiment": "forecast_model_comparison",
        "metric": "lowest_mape",
        "value": best.get("mape"),
        "all_results": results,
        "recommended": best,
    }


def experiment_data_quality(df):
    """
    Experiment: Assess data quality. What issues exist?
    Missing values, outliers, inconsistencies.
    """
    issues = []

    # Missing values
    missing = df.isnull().sum()
    for col, count in missing[missing > 0].items():
        issues.append(
            {
                "type": "missing_values",
                "column": col,
                "count": int(count),
                "pct": round(count / len(df) * 100, 1),
            }
        )

    # Outliers (values > 3 std from mean)
    for col in ["total_visitors", "avg_occupancy_rate", "total_rooms"]:
        if col in df.columns:
            mean = df[col].mean()
            std = df[col].std()
            outliers = df[abs(df[col] - mean) > 3 * std]
            if len(outliers) > 0:
                issues.append(
                    {
                        "type": "outliers",
                        "column": col,
                        "count": len(outliers),
                        "pct": round(len(outliers) / len(df) * 100, 1),
                    }
                )

    # Zero values where unexpected
    for col in ["total_visitors", "total_rooms", "total_beds"]:
        if col in df.columns:
            zeros = (df[col] == 0).sum()
            if zeros > 0:
                issues.append(
                    {
                        "type": "zero_values",
                        "column": col,
                        "count": int(zeros),
                        "pct": round(zeros / len(df) * 100, 1),
                    }
                )

    return {
        "experiment": "data_quality",
        "metric": "issue_count",
        "value": len(issues),
        "issues": issues,
        "quality_score": round(1 - (len(issues) / (len(df.columns) * 3)), 2),
    }


def run_all_experiments():
    """Run the full experiment suite."""
    print("Loading data...")
    df = load_all_data()
    print(f"  {len(df)} records, {df['governorate_code'].nunique()} governorates")

    experiments = [
        ("Correlation Analysis", experiment_correlation_analysis),
        ("Seasonality Analysis", experiment_seasonality_analysis),
        ("Threshold Sensitivity", experiment_capacity_classification_sensitivity),
        ("Governorate Clustering", experiment_governorate_clustering),
        ("Forecast Model Comparison", experiment_forecast_model_comparison),
        ("Data Quality", experiment_data_quality),
    ]

    all_results = []
    start = datetime.utcnow()

    for name, fn in experiments:
        print(f"\n--- Running: {name} ---")
        try:
            result = fn(df)
            all_results.append(result)
            print(f"  Metric: {result['metric']} = {result['value']}")
        except Exception as e:
            print(f"  ERROR: {e}")
            all_results.append({"experiment": name, "error": str(e)})

    elapsed = (datetime.utcnow() - start).total_seconds()

    # Summary
    print(f"\n{'=' * 50}")
    print(f"AUTORESEARCH COMPLETE — {len(all_results)} experiments in {elapsed:.1f}s")
    print(f"{'=' * 50}")

    for r in all_results:
        if "error" not in r:
            print(f"  {r['experiment']}: {r['metric']} = {r['value']}")

    # Save full results
    report_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs",
        "autoresearch_results.json",
    )
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nFull results saved to {report_path}")

    return all_results


def _interpret_correlation(var, corr):
    """Human-readable interpretation of a correlation."""
    direction = "positive" if corr > 0 else "negative"
    strength = (
        "strong" if abs(corr) > 0.7 else "moderate" if abs(corr) > 0.4 else "weak"
    )

    interpretations = {
        "avg_occupancy_rate": f"{strength} {direction}: Higher visitor demand {'increases' if corr > 0 else 'decreases'} hotel occupancy",
        "total_rooms": f"{strength} {direction}: More rooms available {'correlates with' if corr > 0 else 'inversely related to'} higher visitor numbers",
        "total_beds": f"{strength} {direction}: Bed capacity {'supports' if corr > 0 else 'limits'} visitor growth",
        "rooms_per_1000": f"{strength} {direction}: Higher rooms-per-visitor ratio {'indicates excess capacity' if corr < 0 else 'attracts more visitors'}",
        "occupancy_pressure": f"{strength} {direction}: Occupancy pressure {'rises' if corr > 0 else 'falls'} with visitor demand",
    }

    return interpretations.get(
        var, f"{strength} {direction} correlation with visitor demand"
    )


if __name__ == "__main__":
    run_all_experiments()
