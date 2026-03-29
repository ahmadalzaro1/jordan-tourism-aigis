"""
AutoResearch Loop for Jordan Tourism AI-GIS.

Following karpathy/autoresearch pattern:
1. Run evaluation (get current score)
2. Pick an experiment category
3. Implement the experiment
4. Run evaluation again
5. If score improved: keep. If not: revert.
6. Log the experiment
7. Repeat

Run: python3 scripts/autoresearch_loop.py [--iterations N]
"""

import sys, os, json, subprocess, shutil, argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYTICS_DIR = os.path.join(BASE_DIR, "app", "analytics")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
LOG_PATH = os.path.join(DOCS_DIR, "autoresearch_log.md")


def get_score():
    """Run evaluate.py and return composite score."""
    from scripts.evaluate import evaluate

    result = evaluate()
    return result["composite"]


def backup_analytics():
    """Backup current analytics files."""
    backup_dir = os.path.join(BASE_DIR, ".autoresearch_backup")
    os.makedirs(backup_dir, exist_ok=True)
    for f in os.listdir(ANALYTICS_DIR):
        if f.endswith(".py"):
            shutil.copy2(os.path.join(ANALYTICS_DIR, f), os.path.join(backup_dir, f))
    return backup_dir


def restore_analytics(backup_dir):
    """Restore analytics files from backup."""
    for f in os.listdir(backup_dir):
        if f.endswith(".py"):
            shutil.copy2(os.path.join(backup_dir, f), os.path.join(ANALYTICS_DIR, f))


def log_experiment(
    num, category, description, hypothesis, before, after, kept, learning
):
    """Append experiment to log."""
    os.makedirs(DOCS_DIR, exist_ok=True)
    entry = f"""
## Experiment #{num} — {category}: {description}
**Date:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M")}
**Hypothesis:** {hypothesis}
**Before score:** {before}/100
**After score:** {after}/100
**Delta:** {"+" if after > before else ""}{after - before:.1f}
**Result:** {"KEPT ✓" if kept else "DISCARDED ✗"}
**Learning:** {learning}

"""
    with open(LOG_PATH, "a") as f:
        f.write(entry)


# ==========================================
# Experiment implementations
# ==========================================


def experiment_seasonal_indicators():
    """Add seasonal capacity classification (Q1/Q2/Q3/Q4 instead of annual)."""
    new_code = '''

def classify_capacity_seasonal(indicators_by_month: list, thresholds: dict = None) -> dict:
    """
    Classify capacity by season (spring/summer/fall/winter) instead of annual.
    Spring (Mar-May): highest demand period
    Summer (Jun-Aug): moderate
    Fall (Sep-Nov): high demand
    Winter (Dec-Feb): low demand
    """
    seasons = {
        "spring": [3, 4, 5],
        "summer": [6, 7, 8],
        "fall": [9, 10, 11],
        "winter": [12, 1, 2],
    }

    results = {}
    for season_name, months in seasons.items():
        season_indicators = [ind for ind in indicators_by_month if ind.get("month") in months]
        if season_indicators:
            avg_indicators = {}
            for key in ["rooms_per_1000_visitors", "beds_per_1000_visitors", "occupancy_pressure_index", "capacity_adequacy_index"]:
                values = [ind[key] for ind in season_indicators if ind.get(key) is not None]
                avg_indicators[key] = sum(values) / len(values) if values else None
            results[season_name] = classify_capacity(avg_indicators, thresholds)

    return results
'''
    filepath = os.path.join(ANALYTICS_DIR, "classification.py")
    with open(filepath, "a") as f:
        f.write(new_code)
    return "Added seasonal capacity classification"


def experiment_demand_elasticity():
    """Add demand elasticity indicator (how responsive is demand to capacity changes)."""
    new_code = '''

def demand_elasticity(visitors_series: list, beds_series: list) -> float:
    """
    Calculate demand elasticity: % change in visitors / % change in beds.
    > 1: elastic (demand responds strongly to capacity)
    < 1: inelastic (demand is insensitive to capacity)
    """
    if len(visitors_series) < 2 or len(beds_series) < 2:
        return None

    v_pct_change = [(visitors_series[i] - visitors_series[i-1]) / visitors_series[i-1]
                     for i in range(1, len(visitors_series)) if visitors_series[i-1] > 0]
    b_pct_change = [(beds_series[i] - beds_series[i-1]) / beds_series[i-1]
                     for i in range(1, len(beds_series)) if beds_series[i-1] > 0]

    if not v_pct_change or not b_pct_change:
        return None

    # Use average changes
    avg_v_change = sum(v_pct_change) / len(v_pct_change)
    avg_b_change = sum(b_pct_change) / len(b_pct_change)

    if avg_b_change == 0:
        return None

    return round(avg_v_change / avg_b_change, 3)
'''
    filepath = os.path.join(ANALYTICS_DIR, "indicators.py")
    with open(filepath, "a") as f:
        f.write(new_code)
    return "Added demand elasticity indicator"


def experiment_peak_capacity_ratio():
    """Add peak-to-average capacity ratio indicator."""
    new_code = '''

def peak_capacity_ratio(monthly_occupancy: list) -> float:
    """
    Peak-to-average occupancy ratio.
    Higher = more extreme seasonality (invest in seasonal capacity, not permanent)
    Lower = stable demand (invest in permanent capacity)
    """
    if not monthly_occupancy:
        return None
    avg = sum(monthly_occupancy) / len(monthly_occupancy)
    peak = max(monthly_occupancy)
    if avg == 0:
        return None
    return round(peak / avg, 3)
'''
    filepath = os.path.join(ANALYTICS_DIR, "indicators.py")
    with open(filepath, "a") as f:
        f.write(new_code)
    return "Added peak capacity ratio indicator"


def experiment_visitor_concentration_index():
    """Add Herfindahl index for visitor concentration across governorates."""
    new_code = '''

def visitor_concentration_index(visitors_by_gov: dict) -> float:
    """
    Herfindahl-Hirschman Index for visitor concentration.
    0 = perfectly distributed, 1 = all visitors in one governorate.
    Higher = more concentrated (risky for tourism sector).
    """
    total = sum(visitors_by_gov.values())
    if total == 0:
        return None
    shares = [v / total for v in visitors_by_gov.values()]
    hhi = sum(s ** 2 for s in shares)
    return round(hhi, 4)
'''
    filepath = os.path.join(ANALYTICS_DIR, "indicators.py")
    with open(filepath, "a") as f:
        f.write(new_code)
    return "Added visitor concentration index (HHI)"


def experiment_growth_acceleration():
    """Add growth acceleration indicator (is growth speeding up or slowing down?)."""
    new_code = '''

def growth_acceleration(visitors_by_year: list) -> float:
    """
    Growth acceleration: change in growth rate.
    Positive = growth is accelerating (good for investment)
    Negative = growth is decelerating (caution needed)
    """
    if len(visitors_by_year) < 3:
        return None

    growth_rates = []
    for i in range(1, len(visitors_by_year)):
        if visitors_by_year[i-1] > 0:
            growth_rates.append((visitors_by_year[i] - visitors_by_year[i-1]) / visitors_by_year[i-1])

    if len(growth_rates) < 2:
        return None

    accelerations = [growth_rates[i] - growth_rates[i-1] for i in range(1, len(growth_rates))]
    return round(sum(accelerations) / len(accelerations), 4)
'''
    filepath = os.path.join(ANALYTICS_DIR, "indicators.py")
    with open(filepath, "a") as f:
        f.write(new_code)
    return "Added growth acceleration indicator"


def experiment_investment_roi_proxy():
    """Add simple ROI proxy for tourism investment."""
    new_code = '''

def investment_roi_proxy(
    current_visitors: int,
    forecast_visitors: int,
    current_beds: int,
    added_beds: int,
    avg_revenue_per_visitor: float = 150.0,
    avg_cost_per_bed: float = 50000.0,
) -> dict:
    """
    Simple ROI proxy for tourism infrastructure investment.
    Estimates additional revenue from added capacity vs investment cost.
    """
    if current_beds <= 0 or added_beds <= 0:
        return None

    # Estimate additional visitors enabled by added beds
    current_visitors_per_bed = current_visitors / current_beds
    additional_visitors = int(added_beds * current_visitors_per_bed * 0.7)  # 70% utilization target

    # Revenue
    additional_revenue = additional_visitors * avg_revenue_per_visitor

    # Cost
    investment_cost = added_beds * avg_cost_per_bed

    # Simple payback period (years)
    if additional_revenue > 0:
        payback_years = round(investment_cost / additional_revenue, 1)
    else:
        payback_years = float('inf')

    return {
        "additional_visitors": additional_visitors,
        "additional_revenue_annual": round(additional_revenue),
        "investment_cost": round(investment_cost),
        "payback_years": payback_years,
        "roi_5year": round(((additional_revenue * 5) - investment_cost) / investment_cost * 100, 1),
    }
'''
    filepath = os.path.join(ANALYTICS_DIR, "scoring.py")
    with open(filepath, "a") as f:
        f.write(new_code)
    return "Added investment ROI proxy"


# ==========================================
# Experiment registry
# ==========================================

EXPERIMENTS = [
    (
        "New Indicator",
        "Seasonal capacity classification",
        experiment_seasonal_indicators,
        "Seasonal classification reveals patterns hidden in annual averages",
    ),
    (
        "New Indicator",
        "Demand elasticity",
        experiment_demand_elasticity,
        "Measures how responsive demand is to capacity changes",
    ),
    (
        "New Indicator",
        "Peak capacity ratio",
        experiment_peak_capacity_ratio,
        "Quantifies seasonality severity for investment decisions",
    ),
    (
        "New Indicator",
        "Visitor concentration (HHI)",
        experiment_visitor_concentration_index,
        "Identifies if tourism is too concentrated in few governorates",
    ),
    (
        "New Indicator",
        "Growth acceleration",
        experiment_growth_acceleration,
        "Detects if growth is speeding up or slowing down",
    ),
    (
        "New Indicator",
        "Investment ROI proxy",
        experiment_investment_roi_proxy,
        "Estimates payback period for infrastructure investment",
    ),
]


def run_experiment(exp_index):
    """Run a single experiment."""
    category, description, impl_fn, hypothesis = EXPERIMENTS[
        exp_index % len(EXPERIMENTS)
    ]

    print(f"\n--- Experiment: {description} ---")

    # Check if already added (idempotent)
    target_file = {
        experiment_seasonal_indicators: "classification.py",
        experiment_demand_elasticity: "indicators.py",
        experiment_peak_capacity_ratio: "indicators.py",
        experiment_visitor_concentration_index: "indicators.py",
        experiment_growth_acceleration: "indicators.py",
        experiment_investment_roi_proxy: "scoring.py",
    }.get(impl_fn, "unknown")

    filepath = os.path.join(ANALYTICS_DIR, target_file)

    # Read current file
    with open(filepath, "r") as f:
        content = f.read()

    # Check if function already exists
    func_name = impl_fn.__name__.replace("experiment_", "")
    if func_name in content:
        print(f"  SKIP: {func_name} already exists")
        return None

    # Score before
    before = get_score()
    print(f"  Before: {before}/100")

    # Backup
    backup_dir = backup_analytics()

    try:
        # Implement
        result = impl_fn()
        print(f"  Implemented: {result}")

        # Score after
        after = get_score()
        print(f"  After: {after}/100")

        # Keep or discard
        kept = after >= before
        if not kept:
            restore_analytics(backup_dir)
            print(f"  DISCARDED (score dropped by {after - before:.1f})")
        else:
            print(f"  KEPT (score improved by +{after - before:.1f})")

        learning = f"{result}. Score {'improved' if kept else 'dropped'} by {after - before:+.1f}"
        return {
            "category": category,
            "description": description,
            "hypothesis": hypothesis,
            "before": before,
            "after": after,
            "kept": kept,
            "learning": learning,
        }
    except Exception as e:
        restore_analytics(backup_dir)
        print(f"  ERROR: {e}")
        return {
            "category": category,
            "description": description,
            "hypothesis": hypothesis,
            "before": before,
            "after": before,
            "kept": False,
            "learning": f"Error: {str(e)}",
        }


def run_loop(iterations=None):
    """Run the autoresearch loop."""
    print("=" * 60)
    print("  AUTORESEARCH LOOP — Jordan Tourism AI-GIS")
    print("=" * 60)

    # Initialize log
    os.makedirs(DOCS_DIR, exist_ok=True)
    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, "w") as f:
            f.write("# AutoResearch Log\n\n")

    # Count existing experiments
    with open(LOG_PATH, "r") as f:
        exp_count = f.read().count("## Experiment #")

    total_experiments = iterations or len(EXPERIMENTS)

    for i in range(total_experiments):
        exp_index = exp_count + i
        result = run_experiment(exp_index)

        if result:
            log_experiment(
                exp_index + 1,
                result["category"],
                result["description"],
                result["hypothesis"],
                result["before"],
                result["after"],
                result["kept"],
                result["learning"],
            )

    # Final score
    final = get_score()
    print(f"\n{'=' * 60}")
    print(f"  FINAL SCORE: {final}/100")
    print(f"  Experiments run: {total_experiments}")
    print(f"  Log: {LOG_PATH}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--iterations", type=int, default=None, help="Number of experiments to run"
    )
    args = parser.parse_args()

    run_loop(args.iterations)
