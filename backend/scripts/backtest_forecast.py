"""
Forecast Back-Testing for Jordan Tourism AI-GIS.

Per RFP ToR Section 4.4.1:
- Reserve last 12 months for testing
- Train on earlier data
- Evaluate using MAPE, MAE, RMSE
- Report national-level and governorate-level accuracy

This script works with the sample data CSVs directly (no database needed).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from app.analytics.forecasting import prepare_monthly_series, forecast_best

SAMPLE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "sample",
)


def load_visitor_data():
    """Load visitor CSV and return DataFrame."""
    filepath = os.path.join(SAMPLE_DIR, "visitors.csv")
    df = pd.read_csv(filepath)
    return df


def run_backtest(visitors_df, train_end_year=2024, test_year=2025):
    """
    Run back-testing: train on data up to train_end_year, predict test_year.

    Returns dict with national and per-governorate metrics.
    """
    results = {
        "national": {},
        "governorates": {},
        "summary": {},
    }

    # National-level back-test
    national_train = (
        visitors_df[visitors_df["year"] <= train_end_year]
        .groupby(["year", "month"])["total_visitors"]
        .sum()
        .reset_index()
    )

    national_test = (
        visitors_df[visitors_df["year"] == test_year]
        .groupby(["year", "month"])["total_visitors"]
        .sum()
        .reset_index()
    )

    train_df = prepare_monthly_series(
        [
            {"year": r.year, "month": r.month, "total": r.total_visitors}
            for _, r in national_train.iterrows()
        ]
    )

    forecast = forecast_best(train_df, 12)

    # Compare against actual
    actual_values = national_test["total_visitors"].values
    predicted_values = [
        f["predicted"] for f in forecast["forecast"][: len(actual_values)]
    ]

    mape = _mape(actual_values, predicted_values)
    mae = _mae(actual_values, predicted_values)
    rmse = _rmse(actual_values, predicted_values)

    results["national"] = {
        "mape": round(mape, 2),
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "method": forecast.get("method", "unknown"),
        "train_months": len(train_df),
        "test_months": len(actual_values),
        "actual": actual_values.tolist(),
        "predicted": predicted_values,
        "monthly_comparison": [
            {
                "month": i + 1,
                "actual": int(actual_values[i]) if i < len(actual_values) else None,
                "predicted": int(predicted_values[i])
                if i < len(predicted_values)
                else None,
                "error_pct": round(
                    abs(actual_values[i] - predicted_values[i])
                    / actual_values[i]
                    * 100,
                    1,
                )
                if i < len(actual_values) and actual_values[i] > 0
                else None,
            }
            for i in range(min(len(actual_values), len(predicted_values)))
        ],
    }

    # Per-governorate back-test
    gov_names = (
        visitors_df[["governorate_code"]].drop_duplicates()["governorate_code"].tolist()
    )

    for gov_code in gov_names:
        gov_data = visitors_df[visitors_df["governorate_code"] == gov_code]

        gov_train = gov_data[gov_data["year"] <= train_end_year]
        gov_test = gov_data[gov_data["year"] == test_year]

        if len(gov_train) < 12 or len(gov_test) < 1:
            continue

        train_df_gov = prepare_monthly_series(
            [
                {"year": r.year, "month": r.month, "total": r.total_visitors}
                for _, r in gov_train.iterrows()
            ]
        )

        try:
            gov_forecast = forecast_best(train_df_gov, 12)
            gov_actual = gov_test["total_visitors"].values
            gov_predicted = [
                f["predicted"] for f in gov_forecast["forecast"][: len(gov_actual)]
            ]

            gov_mape = _mape(gov_actual, gov_predicted)
            gov_mae = _mae(gov_actual, gov_predicted)
            gov_rmse = _rmse(gov_actual, gov_predicted)

            results["governorates"][gov_code] = {
                "mape": round(gov_mape, 2),
                "mae": round(gov_mae, 2),
                "rmse": round(gov_rmse, 2),
                "test_months": len(gov_actual),
            }
        except Exception as e:
            results["governorates"][gov_code] = {"error": str(e)}

    # Summary
    gov_mapes = [v["mape"] for v in results["governorates"].values() if "mape" in v]
    results["summary"] = {
        "national_mape": results["national"]["mape"],
        "national_mape_pass": results["national"]["mape"] <= 20.0,
        "governorate_avg_mape": round(np.mean(gov_mapes), 2) if gov_mapes else None,
        "governorate_max_mape": round(max(gov_mapes), 2) if gov_mapes else None,
        "governorate_min_mape": round(min(gov_mapes), 2) if gov_mapes else None,
        "method": results["national"]["method"],
        "train_period": f"2020-01 to {train_end_year}-12",
        "test_period": f"{test_year}-01 to {test_year}-12",
    }

    return results


def _mape(actual, predicted):
    actual, predicted = np.array(actual, dtype=float), np.array(predicted, dtype=float)
    mask = actual != 0
    return (
        np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100
        if mask.sum() > 0
        else 0
    )


def _mae(actual, predicted):
    return np.mean(
        np.abs(np.array(actual, dtype=float) - np.array(predicted, dtype=float))
    )


def _rmse(actual, predicted):
    return np.sqrt(
        np.mean((np.array(actual, dtype=float) - np.array(predicted, dtype=float)) ** 2)
    )


if __name__ == "__main__":
    import json

    print("Loading visitor data...")
    df = load_visitor_data()
    print(f"  {len(df)} records, {df['governorate_code'].nunique()} governorates")
    print(f"  Date range: {df['year'].min()}-{df['year'].max()}")

    print("\nRunning back-test (train 2020-2024, predict 2025)...")
    results = run_backtest(df)

    print(f"\n=== NATIONAL RESULTS ===")
    print(f"  Method: {results['national']['method']}")
    print(
        f"  MAPE: {results['national']['mape']}% {'✓ PASS' if results['summary']['national_mape_pass'] else '✗ FAIL'} (target: ≤20%)"
    )
    print(f"  MAE: {results['national']['mae']:.0f}")
    print(f"  RMSE: {results['national']['rmse']:.0f}")

    print(f"\n=== MONTHLY COMPARISON ===")
    print(f"  {'Month':<8} {'Actual':>10} {'Predicted':>10} {'Error %':>8}")
    for m in results["national"]["monthly_comparison"]:
        print(
            f"  {m['month']:<8} {m['actual']:>10,} {m['predicted']:>10,} {m['error_pct']:>7.1f}%"
        )

    print(f"\n=== GOVERNORATE RESULTS ===")
    print(f"  {'Code':<6} {'MAPE':>6} {'MAE':>8} {'RMSE':>8}")
    for code, metrics in sorted(results["governorates"].items()):
        if "mape" in metrics:
            print(
                f"  {code:<6} {metrics['mape']:>5.1f}% {metrics['mae']:>8.0f} {metrics['rmse']:>8.0f}"
            )

    print(f"\n=== SUMMARY ===")
    print(
        f"  National MAPE: {results['summary']['national_mape']}% {'✓' if results['summary']['national_mape_pass'] else '✗'}"
    )
    print(f"  Gov avg MAPE: {results['summary']['governorate_avg_mape']}%")
    print(f"  Gov max MAPE: {results['summary']['governorate_max_mape']}%")
    print(f"  Gov min MAPE: {results['summary']['governorate_min_mape']}%")

    # Save report
    report_path = os.path.join(
        SAMPLE_DIR, "..", "..", "docs", "forecast_backtest_report.json"
    )
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nReport saved to {report_path}")
