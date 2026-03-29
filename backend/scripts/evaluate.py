"""
Evaluate the current analytics system quality.

Composite score (0-100) based on:
- Data coverage (20%)
- Insight depth (20%)
- Forecast accuracy (20%)
- Correlation discovery (15%)
- Actionability (15%)
- Reproducibility (10%)

Run: python3 scripts/evaluate.py
"""

import sys, os, json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime

SAMPLE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample"
)
DOCS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs"
)


def load_data():
    visitors = pd.read_csv(os.path.join(SAMPLE_DIR, "visitors.csv"))
    occupancy = pd.read_csv(os.path.join(SAMPLE_DIR, "occupancy.csv"))
    sites = pd.read_csv(os.path.join(SAMPLE_DIR, "sites.csv"))
    hotels = pd.read_csv(os.path.join(SAMPLE_DIR, "hotels.csv"))
    site_visits = pd.read_csv(os.path.join(SAMPLE_DIR, "site_visits.csv"))
    return visitors, occupancy, sites, hotels, site_visits


def score_data_coverage(visitors, occupancy, sites, hotels, site_visits):
    """How much of the available data is used by the analytics?"""
    available = 5  # visitors, occupancy, sites, hotels, site_visits
    used = 0
    try:
        from app.analytics.indicators import compute_indicators_for_period

        compute_indicators_for_period(
            100, 200, 10000, 50, 70
        )  # uses visitors + occupancy
        used += 2  # visitors, occupancy
    except:
        pass
    try:
        from app.analytics.scoring import compute_priority_score

        compute_priority_score(10000, 500, 60, 10, False, 50)  # uses derived indicators
        used += 1
    except:
        pass
    try:
        from app.analytics.clusters import TOURISM_CLUSTERS

        if len(TOURISM_CLUSTERS) >= 6:
            used += 1  # clusters use site data
    except:
        pass
    # Site visits and hotels data used in API endpoints
    used += 1  # counted via GeoJSON endpoints

    return min(100, (used / available) * 100)


def score_insight_depth():
    """How many distinct analytical insights can the system produce?"""
    insights = 0

    # Indicators
    try:
        from app.analytics.indicators import compute_indicators_for_period

        result = compute_indicators_for_period(100, 200, 10000, 50, 70, 9000)
        insights += len([v for v in result.values() if v is not None])
    except:
        pass

    # Classification
    try:
        from app.analytics.classification import classify_capacity

        cls = classify_capacity(
            {
                "rooms_per_1000_visitors": 5,
                "beds_per_1000_visitors": 10,
                "occupancy_pressure_index": 50,
                "capacity_adequacy_index": 1.0,
            }
        )
        insights += 1
    except:
        pass

    # Forecast
    try:
        from app.analytics.forecasting import prepare_monthly_series, forecast_best

        data = [
            {"year": 2020 + i // 12, "month": (i % 12) + 1, "total": 10000 + i * 100}
            for i in range(48)
        ]
        df = prepare_monthly_series(data)
        result = forecast_best(df, 12)
        insights += len(result.get("forecast", []))
    except:
        pass

    # Simulation types
    insights += 2  # accommodation + demand scenarios

    # Scoring components
    try:
        from app.analytics.scoring import compute_priority_score

        result = compute_priority_score(10000, 500, 60, 10, False, 50)
        insights += len(result.get("components", {}))
    except:
        pass

    # Clusters
    try:
        from app.analytics.clusters import TOURISM_CLUSTERS

        insights += len(TOURISM_CLUSTERS)
    except:
        pass

    # Normalize: 30+ insights = 100
    return min(100, (insights / 30) * 100)


def score_forecast_accuracy():
    """Based on back-test results."""
    report_path = os.path.join(DOCS_DIR, "forecast_backtest_report.json")
    if os.path.exists(report_path):
        with open(report_path) as f:
            report = json.load(f)
        mape = report.get("national", {}).get("mape", 100)
        # MAPE 0% = 100, MAPE 20% = 50, MAPE 40% = 0
        return max(0, min(100, 100 - (mape * 2.5)))
    return 50  # default if no backtest run


def score_correlation_discovery():
    """How many significant correlations discovered?"""
    report_path = os.path.join(DOCS_DIR, "forecast_backtest_report.json")
    if os.path.exists(report_path):
        # Count governorate-level metrics as correlation proxies
        with open(report_path) as f:
            report = json.load(f)
        gov_count = len(report.get("governorates", {}))
        return min(100, (gov_count / 12) * 100)
    return 0


def score_actionability():
    """Can a policymaker use the outputs to make a decision?"""
    score = 0

    # Has classification? (+25)
    try:
        from app.analytics.classification import classify_capacity

        score += 25
    except:
        pass

    # Has investment ranking? (+25)
    try:
        from app.analytics.scoring import compute_priority_score

        result = compute_priority_score(10000, 500, 60, 10, False, 50)
        if result.get("recommended_investment_type"):
            score += 25
    except:
        pass

    # Has simulation comparison? (+25)
    try:
        from app.analytics.simulation import accommodation_scenario

        baseline = {
            "total_rooms": 100,
            "total_beds": 200,
            "total_visitors": 50000,
            "avg_occupancy": 60,
            "peak_occupancy": 80,
            "visitors_prev_year": 45000,
        }
        result = accommodation_scenario(baseline, "Test", 500)
        if "difference" in result:
            score += 25
    except:
        pass

    # Has clusters? (+25)
    try:
        from app.analytics.clusters import TOURISM_CLUSTERS

        if len(TOURISM_CLUSTERS) >= 3:
            score += 25
    except:
        pass

    return score


def score_reproducibility():
    """Same input = same output?"""
    try:
        from app.analytics.indicators import compute_indicators_for_period

        results = set()
        for _ in range(100):
            r = compute_indicators_for_period(100, 200, 10000, 50, 70, 9000)
            results.add(str(r))
        return 100 if len(results) == 1 else 0
    except:
        return 0


def evaluate():
    """Run full evaluation and return composite score."""
    visitors, occupancy, sites, hotels, site_visits = load_data()

    scores = {
        "data_coverage": score_data_coverage(
            visitors, occupancy, sites, hotels, site_visits
        ),
        "insight_depth": score_insight_depth(),
        "forecast_accuracy": score_forecast_accuracy(),
        "correlation_discovery": score_correlation_discovery(),
        "actionability": score_actionability(),
        "reproducibility": score_reproducibility(),
    }

    weights = {
        "data_coverage": 0.20,
        "insight_depth": 0.20,
        "forecast_accuracy": 0.20,
        "correlation_discovery": 0.15,
        "actionability": 0.15,
        "reproducibility": 0.10,
    }

    composite = sum(scores[k] * weights[k] for k in scores)

    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "scores": {k: round(v, 1) for k, v in scores.items()},
        "composite": round(composite, 1),
        "weights": weights,
    }

    return result


if __name__ == "__main__":
    result = evaluate()

    print(f"\n{'=' * 50}")
    print(f"  ANALYTICS QUALITY SCORE: {result['composite']}/100")
    print(f"{'=' * 50}")
    for k, v in result["scores"].items():
        bar = "█" * int(v / 5)
        print(f"  {k:<25} {v:>5.1f}/100 {bar}")

    # Save
    report_path = os.path.join(DOCS_DIR, "quality_score.json")
    with open(report_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved to {report_path}")
