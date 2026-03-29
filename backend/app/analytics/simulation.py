"""
What-If Simulation Module for Jordan Tourism AI-GIS.

Per RFP ToR Section 3.2.4:
- Accommodation capacity scenario: add beds in a region, recalculate indicators
- Visitor demand scenario: increase/decrease visitors, recalculate indicators
- Compare baseline forecast vs scenario with difference table
- Transparent, formula-based, reproducible

Two scenario types:
  1. accommodation_scenario: Add/remove beds in a governorate
  2. demand_scenario: Increase/decrease visitor numbers
"""

from app.analytics.indicators import compute_indicators_for_period
from app.analytics.classification import classify_capacity


def accommodation_scenario(
    baseline: dict,
    governorate_name: str,
    added_beds: int,
    added_rooms: int = None,
    avg_stay_nights: float = 2.5,
) -> dict:
    """
    Simulate adding accommodation capacity to a governorate.

    Args:
        baseline: Current state with total_rooms, total_beds, total_visitors,
                  avg_occupancy, peak_occupancy, visitors_prev_year, visitors_2yr_ago
        governorate_name: Name of the governorate
        added_beds: Number of beds to add (can be negative)
        added_rooms: Number of rooms to add (auto-estimated if None)
        avg_stay_nights: Average length of stay

    Returns:
        dict with baseline indicators, scenario indicators, and comparison
    """
    if added_rooms is None:
        added_rooms = max(0, added_beds // 2)  # estimate: 2 beds per room

    # Scenario state
    scenario = {
        "total_rooms": baseline["total_rooms"] + added_rooms,
        "total_beds": baseline["total_beds"] + added_beds,
        "total_visitors": baseline["total_visitors"],
        "avg_occupancy": baseline.get("avg_occupancy", 0),
        "peak_occupancy": baseline.get("peak_occupancy"),
        "visitors_prev_year": baseline.get("visitors_prev_year"),
        "visitors_2yr_ago": baseline.get("visitors_2yr_ago"),
    }

    # Adjust occupancy (more beds = lower occupancy if visitors stay same)
    if baseline["total_beds"] > 0 and added_beds != 0:
        occupancy_factor = baseline["total_beds"] / scenario["total_beds"]
        scenario["avg_occupancy"] = min(
            100, baseline.get("avg_occupancy", 0) * occupancy_factor
        )
        if scenario.get("peak_occupancy"):
            scenario["peak_occupancy"] = min(
                100, baseline["peak_occupancy"] * occupancy_factor
            )

    # Compute indicators for both
    base_indicators = compute_indicators_for_period(
        total_rooms=baseline["total_rooms"],
        total_beds=baseline["total_beds"],
        total_visitors=baseline["total_visitors"],
        avg_occupancy=baseline.get("avg_occupancy", 0),
        peak_occupancy=baseline.get("peak_occupancy"),
        visitors_prev_year=baseline.get("visitors_prev_year"),
        visitors_2yr_ago=baseline.get("visitors_2yr_ago"),
    )

    scenario_indicators = compute_indicators_for_period(
        total_rooms=scenario["total_rooms"],
        total_beds=scenario["total_beds"],
        total_visitors=scenario["total_visitors"],
        avg_occupancy=scenario["avg_occupancy"],
        peak_occupancy=scenario["peak_occupancy"],
        visitors_prev_year=scenario.get("visitors_prev_year"),
        visitors_2yr_ago=scenario.get("visitors_2yr_ago"),
    )

    base_class = classify_capacity(base_indicators)
    scenario_class = classify_capacity(scenario_indicators)

    return {
        "scenario_type": "accommodation",
        "governorate": governorate_name,
        "changes": {
            "added_beds": added_beds,
            "added_rooms": added_rooms,
        },
        "baseline": {
            "total_rooms": baseline["total_rooms"],
            "total_beds": baseline["total_beds"],
            "indicators": base_indicators,
            "classification": base_class,
        },
        "scenario": {
            "total_rooms": scenario["total_rooms"],
            "total_beds": scenario["total_beds"],
            "indicators": scenario_indicators,
            "classification": scenario_class,
        },
        "difference": _compute_difference(
            base_indicators, scenario_indicators, base_class, scenario_class
        ),
    }


def demand_scenario(
    baseline: dict,
    governorate_name: str,
    visitor_change_pct: float,
    avg_stay_nights: float = 2.5,
) -> dict:
    """
    Simulate a change in visitor demand.

    Args:
        baseline: Current state
        governorate_name: Name of the governorate
        visitor_change_pct: Percentage change in visitors (e.g., +20 = 20% increase)

    Returns:
        dict with baseline, scenario, and comparison
    """
    visitor_multiplier = 1 + (visitor_change_pct / 100)

    scenario_visitors = int(baseline["total_visitors"] * visitor_multiplier)

    # Adjust occupancy (more visitors = higher occupancy if beds stay same)
    scenario_occupancy = min(100, baseline.get("avg_occupancy", 0) * visitor_multiplier)
    scenario_peak = None
    if baseline.get("peak_occupancy"):
        scenario_peak = min(100, baseline["peak_occupancy"] * visitor_multiplier)

    base_indicators = compute_indicators_for_period(
        total_rooms=baseline["total_rooms"],
        total_beds=baseline["total_beds"],
        total_visitors=baseline["total_visitors"],
        avg_occupancy=baseline.get("avg_occupancy", 0),
        peak_occupancy=baseline.get("peak_occupancy"),
        visitors_prev_year=baseline.get("visitors_prev_year"),
        visitors_2yr_ago=baseline.get("visitors_2yr_ago"),
    )

    scenario_indicators = compute_indicators_for_period(
        total_rooms=baseline["total_rooms"],
        total_beds=baseline["total_beds"],
        total_visitors=scenario_visitors,
        avg_occupancy=scenario_occupancy,
        peak_occupancy=scenario_peak,
        visitors_prev_year=baseline.get("visitors_prev_year"),
        visitors_2yr_ago=baseline.get("visitors_2yr_ago"),
    )

    base_class = classify_capacity(base_indicators)
    scenario_class = classify_capacity(scenario_indicators)

    return {
        "scenario_type": "demand",
        "governorate": governorate_name,
        "changes": {
            "visitor_change_pct": visitor_change_pct,
            "visitors_before": baseline["total_visitors"],
            "visitors_after": scenario_visitors,
        },
        "baseline": {
            "total_visitors": baseline["total_visitors"],
            "indicators": base_indicators,
            "classification": base_class,
        },
        "scenario": {
            "total_visitors": scenario_visitors,
            "indicators": scenario_indicators,
            "classification": scenario_class,
        },
        "difference": _compute_difference(
            base_indicators, scenario_indicators, base_class, scenario_class
        ),
    }


def _compute_difference(
    base_indicators, scenario_indicators, base_class, scenario_class
):
    """Compute the difference between baseline and scenario."""
    diff = {}
    for key in base_indicators:
        b = base_indicators[key]
        s = scenario_indicators.get(key)
        if b is not None and s is not None:
            diff[key] = {
                "baseline": b,
                "scenario": s,
                "change": round(s - b, 3),
                "change_pct": round(((s - b) / b) * 100, 1) if b != 0 else None,
            }

    diff["classification_changed"] = base_class != scenario_class
    diff["classification_before"] = base_class
    diff["classification_after"] = scenario_class

    return diff
