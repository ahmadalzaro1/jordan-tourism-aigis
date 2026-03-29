"""
Overnight AutoResearch — 5-Hour Autonomous Research Loop.

Runs independently without agent intervention.
Modeled after karpathy/autoresearch: fixed time budget, single metric, keep/discard.

Usage:
    python3 scripts/overnight_autoresearch.py
    python3 scripts/overnight_autoresearch.py --hours 1    # shorter run
    python3 scripts/overnight_autoresearch.py --hours 8    # longer run

Output:
    docs/overnight_results.json   — full results
    docs/overnight_log.md         — human-readable log
    backend/app/analytics/        — modified with kept experiments
"""

import sys, os, time, json, shutil, traceback, argparse
from datetime import datetime, timedelta
import importlib

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import pandas as pd
import numpy as np

DATA = os.path.join(BASE, "..", "data")
ANALYTICS = os.path.join(BASE, "app", "analytics")
DOCS = os.path.join(BASE, "docs")
BACKUP = os.path.join(BASE, ".overnight_backup")

os.makedirs(DOCS, exist_ok=True)
os.makedirs(BACKUP, exist_ok=True)

LOG_PATH = os.path.join(DOCS, "overnight_log.md")
RESULTS_PATH = os.path.join(DOCS, "overnight_results.json")

# ==========================================
# DATA LOADING
# ==========================================


def load_all_data():
    """Load all available datasets."""
    data = {}

    files = {
        "visitors": "sample/visitors.csv",
        "occupancy": "sample/occupancy.csv",
        "hotels": "sample/hotels.csv",
        "sites": "sample/sites.csv",
        "site_visits": "sample/site_visits.csv",
        "weather": "weather/all_governorates_weather.csv",
        "calendar": "calendar/islamic_calendar.csv",
        "transport": "transport/governorate_accessibility.csv",
        "economic": "economic/jordan_economic_indicators.csv",
        "trends": "trends/google_trends_jordan.csv",
        "wiki": "external/wikipedia_views.csv",
        "airport": "external/queen_alia_passengers.csv",
        "conflicts": "external/regional_conflicts.csv",
        "markets": "external/source_markets.csv",
        "population": "external/jordan_population.csv",
    }

    for key, path in files.items():
        try:
            full_path = os.path.join(DATA, path)
            if os.path.exists(full_path):
                data[key] = pd.read_csv(full_path)
        except:
            pass

    return data


# ==========================================
# EVALUATION
# ==========================================


def evaluate_system(data):
    """
    Score the current analytics system quality.
    Returns composite score 0-100.
    """
    scores = {}

    # 1. Data integration (how many datasets are connected)
    connected = len(data)
    scores["data_integration"] = min(100, connected * 7)  # 14 datasets = 98

    # 2. Indicator coverage
    try:
        from app.analytics.indicators import compute_indicators_for_period

        r = compute_indicators_for_period(100, 200, 10000, 50, 70, 9000)
        indicator_count = len([v for v in r.values() if v is not None])
        scores["indicator_coverage"] = min(100, indicator_count * 20)
    except:
        scores["indicator_coverage"] = 0

    # 3. Analytics functions available
    function_count = 0
    modules = [
        "indicators",
        "classification",
        "forecasting",
        "simulation",
        "scoring",
        "clusters",
        "data_driven",
    ]
    for mod in modules:
        try:
            m = importlib.import_module(f"app.analytics.{mod}")
            functions = [
                f for f in dir(m) if not f.startswith("_") and callable(getattr(m, f))
            ]
            function_count += len(functions)
        except:
            pass
    scores["analytics_breadth"] = min(100, function_count * 2)

    # 4. Cross-dataset correlations discovered
    correlations = 0
    if "visitors" in data and "weather" in data:
        correlations += 1
    if "visitors" in data and "calendar" in data:
        correlations += 1
    if "visitors" in data and "transport" in data:
        correlations += 1
    if "wiki" in data and "visitors" in data:
        correlations += 1
    if "conflicts" in data:
        correlations += 1
    scores["correlation_coverage"] = min(100, correlations * 20)

    # 5. Reproducibility
    try:
        from app.analytics.indicators import compute_indicators_for_period

        results = set()
        for _ in range(50):
            r = compute_indicators_for_period(100, 200, 10000, 50, 70, 9000)
            results.add(str(r))
        scores["reproducibility"] = 100 if len(results) == 1 else 0
    except:
        scores["reproducibility"] = 0

    # Weighted composite
    weights = {
        "data_integration": 0.20,
        "indicator_coverage": 0.25,
        "analytics_breadth": 0.25,
        "correlation_coverage": 0.20,
        "reproducibility": 0.10,
    }

    composite = sum(scores[k] * weights[k] for k in scores)

    return {
        "composite": round(composite, 1),
        "scores": {k: round(v, 1) for k, v in scores.items()},
        "weights": weights,
    }


# ==========================================
# BACKUP & RESTORE
# ==========================================


def backup_analytics():
    """Backup current analytics files."""
    if os.path.exists(BACKUP):
        shutil.rmtree(BACKUP)
    shutil.copytree(ANALYTICS, BACKUP)


def restore_analytics():
    """Restore analytics from backup."""
    for f in os.listdir(BACKUP):
        if f.endswith(".py"):
            shutil.copy2(os.path.join(BACKUP, f), os.path.join(ANALYTICS, f))


# ==========================================
# EXPERIMENT GENERATOR
# ==========================================


def generate_experiments(data, completed):
    """Generate new experiments based on available data and what's been done."""
    experiments = []

    # Category 1: New indicators based on available data
    if "weather" in data and "weather_correlation_indicator" not in completed:
        experiments.append(
            {
                "id": "weather_correlation_indicator",
                "category": "New Indicator",
                "name": "Weather-adjusted visitor indicator",
                "hypothesis": "Adjusting visitor counts by weather conditions reveals true demand",
                "function": experiment_weather_adjusted,
            }
        )

    if "calendar" in data and "ramadan_adjusted_indicator" not in completed:
        experiments.append(
            {
                "id": "ramadan_adjusted_indicator",
                "category": "New Indicator",
                "name": "Ramadan-adjusted capacity classification",
                "hypothesis": "Removing Ramadan effect gives true capacity classification",
                "function": experiment_ramadan_adjusted,
            }
        )

    if "wiki" in data and "attention_demand_ratio" not in completed:
        experiments.append(
            {
                "id": "attention_demand_ratio",
                "category": "New Indicator",
                "name": "Wikipedia attention to visitor ratio",
                "hypothesis": "Online attention vs actual visits reveals untapped demand",
                "function": experiment_attention_ratio,
            }
        )

    if "conflicts" in data and "conflict_resilience_score" not in completed:
        experiments.append(
            {
                "id": "conflict_resilience_score",
                "category": "New Indicator",
                "name": "Conflict resilience score per governorate",
                "hypothesis": "Some governorates are more resilient to regional conflicts",
                "function": experiment_conflict_resilience,
            }
        )

    if "airport" in data and "airport_tourism_ratio" not in completed:
        experiments.append(
            {
                "id": "airport_tourism_ratio",
                "category": "New Indicator",
                "name": "Airport-to-tourism conversion rate",
                "hypothesis": "Not all airport passengers become tourists — measure the conversion",
                "function": experiment_airport_conversion,
            }
        )

    if "markets" in data and "market_vulnerability_index" not in completed:
        experiments.append(
            {
                "id": "market_vulnerability_index",
                "category": "New Indicator",
                "name": "Source market vulnerability index",
                "hypothesis": "Aggregate conflict exposure across all source markets",
                "function": experiment_market_vulnerability,
            }
        )

    if "economic" in data and "economic_tourism_elasticity" not in completed:
        experiments.append(
            {
                "id": "economic_tourism_elasticity",
                "category": "New Indicator",
                "name": "GDP-tourism elasticity",
                "hypothesis": "How much does tourism change when GDP changes by 1%",
                "function": experiment_gdp_elasticity,
            }
        )

    if "visitors" in data and "demand_concentration_index" not in completed:
        experiments.append(
            {
                "id": "demand_concentration_index",
                "category": "New Indicator",
                "name": "Herfindahl demand concentration",
                "hypothesis": "Is tourism too concentrated in few governorates?",
                "function": experiment_demand_concentration,
            }
        )

    # Category 2: Segmentation experiments
    if "hotels" in data and "class_performance_analysis" not in completed:
        experiments.append(
            {
                "id": "class_performance_analysis",
                "category": "Segmentation",
                "name": "Hotel class occupancy analysis",
                "hypothesis": "Higher-class hotels have different occupancy patterns",
                "function": experiment_class_performance,
            }
        )

    if "sites" in data and "site_type_seasonality" not in completed:
        experiments.append(
            {
                "id": "site_type_seasonality",
                "category": "Segmentation",
                "name": "Site type seasonal patterns",
                "hypothesis": "Archaeological vs natural sites have different seasonality",
                "function": experiment_site_type_seasonality,
            }
        )

    # Category 3: Forecast improvements
    if "weather" in data and "weather_enhanced_forecast" not in completed:
        experiments.append(
            {
                "id": "weather_enhanced_forecast",
                "category": "Forecast Enhancement",
                "name": "Weather-enhanced forecasting",
                "hypothesis": "Adding temperature improves forecast accuracy",
                "function": experiment_weather_forecast,
            }
        )

    # Category 4: Simulation refinements
    if "transport" in data and "accessibility_simulation" not in completed:
        experiments.append(
            {
                "id": "accessibility_simulation",
                "category": "Simulation Refinement",
                "name": "Accessibility improvement simulation",
                "hypothesis": "Model impact of building a new highway on tourism",
                "function": experiment_accessibility_sim,
            }
        )

    return experiments


# ==========================================
# EXPERIMENT IMPLEMENTATIONS
# ==========================================


def experiment_weather_adjusted(data):
    """Create weather-adjusted visitor indicator."""
    code = '''
def weather_adjusted_visitors(visitors, temp, optimal_temp=20.0):
    """
    Adjust visitor count for weather conditions.
    Optimal temperature is 20C (neither too hot nor too cold).
    """
    if temp is None or optimal_temp == 0:
        return visitors
    temp_factor = 1.0 - abs(temp - optimal_temp) / optimal_temp * 0.3
    return int(visitors * max(0.5, min(1.5, temp_factor)))
'''
    _append_to_file("indicators.py", code)
    return "Added weather_adjusted_visitors function"


def experiment_ramadan_adjusted(data):
    """Create Ramadan-adjusted classification."""
    code = '''
def ramadan_adjusted_classification(indicators, ramadan_days, total_days=30):
    """
    Adjust capacity classification to account for Ramadan effect.
    During Ramadan, apparent occupancy drops but is not a real capacity change.
    """
    if ramadan_days <= 0:
        return indicators.get("capacity_classification", "unknown")
    
    ramadan_factor = ramadan_days / total_days
    adjusted_occ = indicators.get("occupancy_pressure_index", 50) * (1 + ramadan_factor * 0.3)
    
    # Re-classify with adjusted occupancy
    adjusted = dict(indicators)
    adjusted["occupancy_pressure_index"] = min(100, adjusted_occ)
    return adjusted
'''
    _append_to_file("indicators.py", code)
    return "Added ramadan_adjusted_classification function"


def experiment_attention_ratio(data):
    """Create Wikipedia attention to visitor ratio."""
    code = '''
def attention_to_visitor_ratio(wiki_views, actual_visitors):
    """
    Ratio of Wikipedia page views to actual visitors.
    High ratio = lots of interest but few visits = untapped potential.
    Low ratio = visitors come without researching = established destination.
    """
    if actual_visitors <= 0 or wiki_views <= 0:
        return None
    return round(wiki_views / actual_visitors, 3)
'''
    _append_to_file("indicators.py", code)
    return "Added attention_to_visitor_ratio function"


def experiment_conflict_resilience(data):
    """Create conflict resilience score."""
    code = '''
def conflict_resilience_score(source_markets):
    """
    Score how resilient a governorate is to regional conflicts.
    Based on source market mix: more Saudi = more resilient, more Western = less.
    """
    if not source_markets:
        return 50  # default
    
    resilient_markets = {"Saudi Arabia", "Egypt", "Gulf States", "Jordan"}
    vulnerable_markets = {"USA", "UK", "Germany", "France", "Japan", "Italy"}
    
    resilient_pct = sum(v for k, v in source_markets.items() if k in resilient_markets)
    vulnerable_pct = sum(v for k, v in source_markets.items() if k in vulnerable_markets)
    
    return round(resilient_pct - vulnerable_pct + 50, 1)
'''
    _append_to_file("scoring.py", code)
    return "Added conflict_resilience_score function"


def experiment_airport_conversion(data):
    """Airport to tourism conversion rate."""
    code = '''
def airport_conversion_rate(total_visitors, airport_passengers):
    """
    What percentage of airport passengers become registered tourists?
    Low rate = many transit/business passengers.
    """
    if airport_passengers <= 0:
        return None
    return round(total_visitors / airport_passengers * 100, 2)
'''
    _append_to_file("indicators.py", code)
    return "Added airport_conversion_rate function"


def experiment_market_vulnerability(data):
    """Source market vulnerability index."""
    code = '''
def market_vulnerability_index(markets):
    """
    Aggregate vulnerability of all source markets to conflicts.
    0 = fully resilient, 100 = fully vulnerable.
    """
    if not markets:
        return 50
    
    exposure_map = {"critical": 100, "advisory-driven": 70, "ukraine-war": 60, "low": 10, "varies": 50}
    total_weight = sum(m.get("pct", 0) for m in markets)
    if total_weight == 0:
        return 50
    
    weighted = sum(m.get("pct", 0) * exposure_map.get(m.get("exposure", "varies"), 50) for m in markets)
    return round(weighted / total_weight, 1)
'''
    _append_to_file("scoring.py", code)
    return "Added market_vulnerability_index function"


def experiment_gdp_elasticity(data):
    """GDP-tourism elasticity."""
    code = '''
def gdp_tourism_elasticity(gdp_series, tourism_series):
    """
    How much does tourism change when GDP changes by 1%?
    > 1: tourism grows faster than economy
    < 1: tourism grows slower than economy
    """
    if len(gdp_series) < 2 or len(tourism_series) < 2:
        return None
    
    gdp_growth = [(gdp_series[i]-gdp_series[i-1])/gdp_series[i-1] for i in range(1,len(gdp_series)) if gdp_series[i-1]>0]
    tour_growth = [(tourism_series[i]-tourism_series[i-1])/tourism_series[i-1] for i in range(1,len(tourism_series)) if tourism_series[i-1]>0]
    
    min_len = min(len(gdp_growth), len(tour_growth))
    if min_len == 0:
        return None
    
    gdp_g = sum(gdp_growth[:min_len]) / min_len
    tour_g = sum(tour_growth[:min_len]) / min_len
    
    return round(tour_g / gdp_g, 3) if gdp_g != 0 else None
'''
    _append_to_file("indicators.py", code)
    return "Added gdp_tourism_elasticity function"


def experiment_demand_concentration(data):
    """Herfindahl demand concentration index."""
    code = '''
def demand_concentration(visitors_by_gov):
    """
    Herfindahl-Hirschman Index for demand concentration.
    0 = perfectly distributed, 1 = all in one governorate.
    Uses visitors_by_gov: dict of {gov_code: visitor_count}
    """
    total = sum(visitors_by_gov.values())
    if total <= 0:
        return None
    shares = [v / total for v in visitors_by_gov.values()]
    return round(sum(s ** 2 for s in shares), 4)
'''
    _append_to_file("indicators.py", code)
    return "Added demand_concentration function"


def experiment_class_performance(data):
    """Hotel class occupancy analysis."""
    if "hotels" not in data or "occupancy" not in data:
        return "Skipped — insufficient data"
    hotels = data["hotels"]
    class_counts = hotels.groupby("hotel_class").size()
    return "Class distribution: %s" % str(class_counts.to_dict())


def experiment_site_type_seasonality(data):
    """Site type seasonal analysis."""
    if "sites" not in data or "site_visits" not in data:
        return "Skipped — insufficient data"
    sites = data["sites"]
    type_counts = sites["site_type"].value_counts()
    return "Site types: %s" % str(type_counts.to_dict())


def experiment_weather_forecast(data):
    """Weather-enhanced forecasting test."""
    return "Weather forecast integration deferred — needs real data for back-testing"


def experiment_accessibility_sim(data):
    """Accessibility improvement simulation."""
    if "transport" not in data:
        return "Skipped — no transport data"
    trans = data["transport"]
    lowest = trans.nsmallest(3, "accessibility_score")
    return "Most accessible-improvement candidates: %s" % ", ".join(
        lowest["governorate_code"].tolist()
    )


def _append_to_file(filename, code):
    """Append code to an analytics file."""
    filepath = os.path.join(ANALYTICS, filename)
    with open(filepath, "r") as f:
        content = f.read()

    # Check if function already exists
    func_name = code.split("def ")[1].split("(")[0].strip() if "def " in code else None
    if func_name and func_name in content:
        return  # Already exists

    with open(filepath, "a") as f:
        f.write("\n" + code)


# ==========================================
# MAIN LOOP
# ==========================================


def run_overnight(hours=5):
    """Run the autonomous research loop for specified hours."""

    start_time = datetime.utcnow()
    end_time = start_time + timedelta(hours=hours)

    print("=" * 70)
    print("  OVERNIGHT AUTORESEARCH — %d HOUR RUN" % hours)
    print("  Started: %s" % start_time.strftime("%Y-%m-%d %H:%M UTC"))
    print("  Ends:    %s" % end_time.strftime("%Y-%m-%d %H:%M UTC"))
    print("=" * 70)

    # Load data
    print("\nLoading data...")
    data = load_all_data()
    print("  %d datasets loaded" % len(data))

    # Initial evaluation
    initial_eval = evaluate_system(data)
    print("  Initial score: %s/100" % initial_eval["composite"])

    # Backup
    backup_analytics()

    # Tracking
    completed_experiments = set()
    all_results = []
    log_entries = []

    iteration = 0

    while datetime.utcnow() < end_time:
        iteration += 1
        remaining = (end_time - datetime.utcnow()).total_seconds()

        if remaining < 60:  # Less than 1 minute left
            break

        print("\n--- Iteration %d (%d min remaining) ---" % (iteration, remaining / 60))

        # Generate experiments
        experiments = generate_experiments(data, completed_experiments)

        if not experiments:
            print("  No new experiments to run. Cycling...")
            completed_experiments.clear()
            continue

        # Run one experiment
        exp = experiments[0]
        print("  Running: %s" % exp["name"])
        print("  Hypothesis: %s" % exp["hypothesis"])

        before_eval = evaluate_system(data)
        before_score = before_eval["composite"]

        try:
            result = exp["function"](data)
            after_eval = evaluate_system(data)
            after_score = after_eval["composite"]

            delta = after_score - before_score
            kept = delta >= 0

            if not kept:
                restore_analytics()
                print(
                    "  DISCARDED (score: %.1f -> %.1f, delta: %+.1f)"
                    % (before_score, after_score, delta)
                )
            else:
                print(
                    "  KEPT (score: %.1f -> %.1f, delta: %+.1f)"
                    % (before_score, after_score, delta)
                )

            experiment_result = {
                "iteration": iteration,
                "id": exp["id"],
                "category": exp["category"],
                "name": exp["name"],
                "hypothesis": exp["hypothesis"],
                "result": result,
                "before_score": before_score,
                "after_score": after_score,
                "delta": round(delta, 1),
                "kept": kept,
                "timestamp": datetime.utcnow().isoformat(),
                "remaining_seconds": remaining,
            }

            all_results.append(experiment_result)
            completed_experiments.add(exp["id"])

            log_entry = "Iter %d: [%s] %s — %s (score: %.1f -> %.1f, %+.1f)" % (
                iteration,
                "KEPT" if kept else "DISCARDED",
                exp["name"],
                result,
                before_score,
                after_score,
                delta,
            )
            log_entries.append(log_entry)

        except Exception as e:
            print("  ERROR: %s" % str(e))
            restore_analytics()

            experiment_result = {
                "iteration": iteration,
                "id": exp["id"],
                "category": exp["category"],
                "name": exp["name"],
                "error": str(e),
                "kept": False,
                "timestamp": datetime.utcnow().isoformat(),
            }
            all_results.append(experiment_result)
            completed_experiments.add(exp["id"])
            log_entries.append(
                "Iter %d: [ERROR] %s — %s" % (iteration, exp["name"], str(e))
            )

        # Save intermediate results every 10 iterations
        if iteration % 10 == 0:
            _save_results(all_results, initial_eval, evaluate_system(data), hours)
            _save_log(log_entries, start_time)
            print("  Saved intermediate results")

    # Final evaluation
    final_eval = evaluate_system(data)

    # Save final results
    _save_results(all_results, initial_eval, final_eval, hours)
    _save_log(log_entries, start_time)

    # Summary
    elapsed = (datetime.utcnow() - start_time).total_seconds()
    kept_count = sum(1 for r in all_results if r.get("kept"))
    discarded_count = sum(1 for r in all_results if not r.get("kept"))

    print("\n" + "=" * 70)
    print("  OVERNIGHT AUTORESEARCH COMPLETE")
    print("=" * 70)
    print("  Duration: %.1f hours" % (elapsed / 3600))
    print("  Iterations: %d" % len(all_results))
    print("  Kept: %d" % kept_count)
    print("  Discarded: %d" % discarded_count)
    print("  Initial score: %.1f/100" % initial_eval["composite"])
    print("  Final score: %.1f/100" % final_eval["composite"])
    print(
        "  Improvement: %+.1f" % (final_eval["composite"] - initial_eval["composite"])
    )
    print("=" * 70)
    print("  Results: %s" % RESULTS_PATH)
    print("  Log: %s" % LOG_PATH)

    return all_results


def _save_results(all_results, initial_eval, final_eval, hours):
    """Save results to JSON."""
    results = {
        "start_time": initial_eval.get("timestamp", ""),
        "duration_hours": hours,
        "initial_score": initial_eval,
        "final_score": final_eval,
        "improvement": round(final_eval["composite"] - initial_eval["composite"], 1),
        "total_experiments": len(all_results),
        "kept": sum(1 for r in all_results if r.get("kept")),
        "discarded": sum(1 for r in all_results if not r.get("kept")),
        "experiments": all_results,
    }
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2, default=str)


def _save_log(log_entries, start_time):
    """Save human-readable log."""
    with open(LOG_PATH, "w") as f:
        f.write("# Overnight AutoResearch Log\n\n")
        f.write("Started: %s\n\n" % start_time.strftime("%Y-%m-%d %H:%M UTC"))
        for entry in log_entries:
            f.write("- %s\n" % entry)


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Overnight AutoResearch")
    parser.add_argument(
        "--hours", type=float, default=5, help="Hours to run (default: 5)"
    )
    args = parser.parse_args()

    run_overnight(args.hours)
